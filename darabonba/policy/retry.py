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
        
    def to_map(self):
        return {
            'policy': self.policy,
            'period': self.period,
        }

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        return self.period

class RandomBackoffPolicy(BackoffPolicy):
    def __init__(self, option: Dict[str, Any]):
        super().__init__(option)
        self.period = option.get('period')
        self.cap = option.get('cap', 20 * 1000)
        
    def to_map(self):
        return {
            'policy': self.policy,
            'period': self.period,
            'cap': self.cap,
        }

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        random_time = random.randint(0, ctx.retries_attempted * self.period)
        return min(random_time, self.cap)

class ExponentialBackoffPolicy(BackoffPolicy):
    def __init__(self, option: Dict[str, Any]):
        super().__init__(option)
        self.period = option.get('period')
        self.cap = option.get('cap', 3 * 24 * 60 * 60 * 1000)
        
    def to_map(self):
        return {
            'policy': self.policy,
            'period': self.period,
            'cap': self.cap,
        }

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        random_time = min(2 ** (ctx.retries_attempted * self.period), self.cap)
        return random_time

class EqualJitterBackoffPolicy(BackoffPolicy):
    def __init__(self, option: Dict[str, Any]):
        super().__init__(option)
        self.period = option.get('period')
        self.cap = option.get('cap', 3 * 24 * 60 * 60 * 1000)
    

    def to_map(self):
        return {
            'policy': self.policy,
            'period': self.period,
            'cap': self.cap,
        }

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        ceil = min(self.cap, 2 ** (ctx.retries_attempted * self.period))
        return ceil // 2 + random.randint(0, ceil // 2)

class FullJitterBackoffPolicy(BackoffPolicy):
    def __init__(self, option: Dict[str, Any]):
        super().__init__(option)
        self.period = option.get('period')
        self.cap = option.get('cap', 3 * 24 * 60 * 60 * 1000)
    
    def to_map(self):
        return {
            'policy': self.policy,
            'period': self.period,
            'cap': self.cap,
        }

    def get_delay_time(self, ctx: 'RetryPolicyContext') -> int:
        ceil = min(self.cap, 2 ** (ctx.retries_attempted * self.period))
        return random.randint(0, ceil)

class RetryCondition:
    def __init__(self, condition: Dict[str, Any]):
        self.max_attempts = condition.get('maxAttempts', None)
        self.backoff = self._ensure_backoff_policy(condition.get('backoff', None))
        self.exception = condition.get('exception', [])
        self.error_code = condition.get('errorCode', [])
        self.max_delay = condition.get('maxDelay', None)
    
    def _ensure_backoff_policy(self, backoff):
        if isinstance(backoff, dict):
            return BackoffPolicy.new_backoff_policy(backoff)
        elif isinstance(backoff, BackoffPolicy):
            return backoff

    def to_map(self):
        result = dict()
        if self.max_attempts:
            result['maxAttempts'] = self.max_attempts
        if self.backoff:
            result['backoff'] = self.backoff.to_map()
        if self.exception:
            result['exception'] = self.exception
        if self.error_code:
            result['errorCode'] = self.error_code
        if self.max_delay:
            result['maxDelay'] = self.max_delay
        return result

    @staticmethod
    def from_map(data: Dict[str, Any]) -> 'RetryCondition':
        return RetryCondition({
            'maxAttempts': data.get('maxAttempts'),
            'backoff': data.get('backoff'),
            'exception': data.get('exception', []),
            'errorCode': data.get('errorCode', []),
            'maxDelay': data.get('maxDelay')
        })

class RetryOptions:
    def __init__(self, options: Dict[str, Any]):
        self.retryable = options.get('retryable', True)
        self.retry_condition = [self._ensure_retry_condition(cond) for cond in options.get('retryCondition', [])]
        self.no_retry_condition = [self._ensure_retry_condition(cond) for cond in options.get('noRetryCondition', [])]

    def _ensure_retry_condition(self, condition):
        if isinstance(condition, dict):
            return RetryCondition(condition)
        elif isinstance(condition, RetryCondition):
            return condition
        else:
            raise ValueError("Condition must be either a dictionary or a RetryCondition instance")

    def validate(self) -> bool:
        if not isinstance(self.retryable, bool):
            raise ValueError("retryable must be a boolean.")
        if not isinstance(self.retry_condition, list) or not all(isinstance(cond, RetryCondition) for cond in self.retry_condition):
            raise ValueError("retryCondition must be a list of RetryCondition.")
        if not isinstance(self.no_retry_condition, list) or not all(isinstance(cond, RetryCondition) for cond in self.no_retry_condition):
            raise ValueError("noRetryCondition must be a list of RetryCondition.")
        return True
    
    def to_map(self):
        result = dict()
        if self.retryable:
            result['retryable'] = self.retryable
        if self.retry_condition:
            result['retryCondition'] = [cond.to_map() for cond in self.retry_condition]
        if self.no_retry_condition:
            result['noRetryCondition'] = [cond.to_map() for cond in self.no_retry_condition]
        return result

    @staticmethod
    def from_map(data: Dict[str, Any]) -> 'RetryOptions':
        options = {
            'retryable': data.get('retryable', True),
            'retryCondition': [cond for cond in data.get('retryCondition', [])],
            'noRetryCondition': [cond for cond in data.get('noRetryCondition', [])]
        }
        return RetryOptions(options)

class RetryPolicyContext:
    def __init__(self, retries_attempted = None, http_request = None, http_response = None, exception = None):
        self.retries_attempted = retries_attempted
        self.http_request = http_request
        self.http_response = http_response
        self.exception = exception

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