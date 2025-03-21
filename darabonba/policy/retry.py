import random
from typing import List, Any, Dict

MAX_DELAY_TIME = 120 * 1000
MIN_DELAY_TIME = 100

class BackoffPolicy:
    def __init__(self, option: Dict[str, Any]):
        self.policy = option.get("policy")

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        raise NotImplementedError('un-implemented')

    @staticmethod
    def new_backoff_policy(option: Dict[str, Any]) -> 'BackoffPolicy':
        policy_map = {
            'Fixed': FixedBackoffPolicy,
            'Random': RandomBackoffPolicy,
            'Exponential': ExponentialBackoffPolicy,
            'EqualJitter': EqualJitterBackoffPolicy,
            'ExponentialWithEqualJitter': EqualJitterBackoffPolicy,
            'FullJitter': FullJitterBackoffPolicy,
            'ExponentialWithFullJitter': FullJitterBackoffPolicy,
        }
        policy_class = policy_map.get(option.get('policy'))
        if policy_class:
            return policy_class(option)
        raise ValueError(f"Unknown policy: {option.get('policy')}")

class FixedBackoffPolicy(BackoffPolicy):
    def __init__(self, option: Dict[str, Any]):
        super().__init__(option)
        self.period = option.get('period')

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        return self.period

class RandomBackoffPolicy(BackoffPolicy):
    def __init__(self, option: Dict[str, Any]):
        super().__init__(option)
        self.period = option.get('period')
        self.cap = option.get('cap', 20 * 1000)

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        random_time = random.randint(0, ctx.retries_attempted * self.period)
        return min(random_time, self.cap)

class ExponentialBackoffPolicy(BackoffPolicy):
    def __init__(self, option: Dict[str, Any]):
        super().__init__(option)
        self.period = option.get('period')
        self.cap = option.get('cap', 3 * 24 * 60 * 60 * 1000)

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        random_time = min(2 ** (ctx.retries_attempted * self.period), self.cap)
        return random_time

class EqualJitterBackoffPolicy(BackoffPolicy):
    def __init__(self, option: Dict[str, Any]):
        super().__init__(option)
        self.period = option.get('period')
        self.cap = option.get('cap', 3 * 24 * 60 * 60 * 1000)

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        ceil = min(self.cap, 2 ** (ctx.retries_attempted * self.period))
        return ceil // 2 + random.randint(0, ceil // 2)

class FullJitterBackoffPolicy(BackoffPolicy):
    def __init__(self, option: Dict[str, Any]):
        super().__init__(option)
        self.period = option.get('period')
        self.cap = option.get('cap', 3 * 24 * 60 * 60 * 1000)

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        ceil = min(self.cap, 2 ** (ctx.retries_attempted * self.period))
        return random.randint(0, ceil)

class RetryCondition:
    def __init__(self, condition: Dict[str, Any]):
        self.max_attempts = condition.get('maxAttempts')
        self.backoff = condition.get('backoff') and BackoffPolicy.new_backoff_policy(condition['backoff'])
        self.exception = condition.get('exception', [])
        self.error_code = condition.get('errorCode', [])
        self.max_delay = condition.get('maxDelay')

class RetryOptions:
    def __init__(self, options: Dict[str, Any]):
        self.retryable = options.get('retryable', True)
        self.retry_condition = [RetryCondition(condition) for condition in options.get('retryCondition', [])]
        self.no_retry_condition = [RetryCondition(condition) for condition in options.get('noRetryCondition', [])]
    
    def validate(self) -> bool:
        if not isinstance(self.retryable, bool):
            raise ValueError("retryable must be a boolean.")
        if not isinstance(self.retry_condition, list) or not all(isinstance(cond, RetryCondition) for cond in self.retry_condition):
            raise ValueError("retryCondition must be a list of RetryCondition.")
        if not isinstance(self.no_retry_condition, list) or not all(isinstance(cond, RetryCondition) for cond in self.no_retry_condition):
            raise ValueError("noRetryCondition must be a list of RetryCondition.")
        return True

    def to_map(self) -> Dict[str, Any]:
        return {
            'retryable': self.retryable,
            'retryCondition': [cond.to_dict() for cond in self.retry_condition],
            'noRetryCondition': [cond.to_dict() for cond in self.no_retry_condition]
        }
    
    @staticmethod
    def from_map(data: Dict[str, Any]) -> 'RetryOptions':
        options = {
            'retryable': data.get('retryable', True),
            'retryCondition': [RetryCondition.from_dict(cond) for cond in data.get('retryCondition', [])],
            'noRetryCondition': [RetryCondition.from_dict(cond) for cond in data.get('noRetryCondition', [])]
        }
        return RetryOptions(options)

class RetryPolicyContext:
    def __init__(self, 
                 key: str = None, 
                 retries_attempted: int = 0, 
                 http_request: Any = None, 
                 http_response: Any = None, 
                 exception: Exception = None):
        self.key = key
        self.retries_attempted = retries_attempted
        self.http_request = http_request
        self.http_response = http_response
        self.exception = exception

def should_retry(options: RetryOptions, ctx: RetryPolicyContext) -> bool:
    if ctx.retries_attempted == 0:
        return True
    
    if not options or not options.retryable:
        return False

    retries_attempted = ctx.retries_attempted
    ex = ctx.exception

    for condition in options.no_retry_condition:
        if ex and (ex.name in condition.exception or ex.code in condition.error_code):
            return False

    for condition in options.retry_condition:
        if (ex and (ex.name in condition.exception or ex.code in condition.error_code)):
            if retries_attempted >= condition.max_attempts:
                return False
            return True

    return False

def get_backoff_delay(options: RetryOptions, ctx: RetryPolicyContext) -> int:
    ex = ctx.exception
    for condition in options.retry_condition:
        if (ex and (ex.name in condition.exception or ex.code in condition.error_code)):
            max_delay = condition.max_delay or MAX_DELAY_TIME
            retry_after = getattr(ex, 'retryAfter', None)
            if retry_after is not None:
                return min(retry_after, max_delay)

            if not condition.backoff:
                return MIN_DELAY_TIME
            
            return min(condition.backoff.get_delay_time(ctx), max_delay)

    return MIN_DELAY_TIME