import unittest
from unittest.mock import MagicMock
from darabonba.policy.retry import (
    BackoffPolicy, FixedBackoffPolicy, RandomBackoffPolicy, ExponentialBackoffPolicy,
    EqualJitterBackoffPolicy, FullJitterBackoffPolicy, RetryCondition, RetryOptions, RetryPolicyContext,
    get_backoff_delay
)

from darabonba.exceptions import DaraException

class AException(DaraException):
        def __init__(self, dic):
            super().__init__(dic)
            self.name = 'AException'

class TestBackoffPolicy(unittest.TestCase):
    def test_back_off_policy(self):
        option_fixed = {"policy": "Fixed"}
        backoff_policy_fixed = BackoffPolicy(option_fixed)
        self.assertEqual(backoff_policy_fixed.policy, "Fixed")
        with self.assertRaises(NotImplementedError) as context:
            backoff_policy_fixed.get_delay_time(None)
        self.assertEqual(str(context.exception), "un-implemented")
        policy_fixed = BackoffPolicy.new_backoff_policy(option_fixed)
        self.assertIsInstance(policy_fixed, FixedBackoffPolicy)

        option_random = {"policy": "Random"}
        policy_random = BackoffPolicy.new_backoff_policy(option_random)
        self.assertIsInstance(policy_random, RandomBackoffPolicy)

        option_exponential = {"policy": "Exponential"}
        policy_exponential = BackoffPolicy.new_backoff_policy(option_exponential)
        self.assertIsInstance(policy_exponential, ExponentialBackoffPolicy)

        option_equal_jitter = {"policy": "EqualJitter"}
        policy_equal_jitter = BackoffPolicy.new_backoff_policy(option_equal_jitter)
        self.assertIsInstance(policy_equal_jitter, EqualJitterBackoffPolicy)

        option_full_jitter = {"policy": "FullJitter"}
        policy_full_jitter = BackoffPolicy.new_backoff_policy(option_full_jitter)
        self.assertIsInstance(policy_full_jitter, FullJitterBackoffPolicy)

        option_unknown = {"policy": "UnknownPolicy"}
        with self.assertRaises(ValueError) as context:
            BackoffPolicy.new_backoff_policy(option_unknown)
        
        self.assertEqual(str(context.exception), "Unknown policy: UnknownPolicy")

    
    def test_fixed_backoff_policy(self):
        policy = FixedBackoffPolicy({'period': 1000})
        ctx = RetryPolicyContext(retries_attempted=5)
        self.assertEqual(policy.get_delay_time(ctx), 1000)

    def test_random_backoff_policy(self):
        policy = RandomBackoffPolicy({'period': 1000, 'cap': 2000})
        ctx = RetryPolicyContext(retries_attempted=5)
        delay_time = policy.get_delay_time(ctx)
        self.assertGreaterEqual(delay_time, 0)
        self.assertLessEqual(delay_time, 2000)

    def test_exponential_backoff_policy(self):
        policy = ExponentialBackoffPolicy({'period': 1, 'cap': 10000})
        ctx = RetryPolicyContext(retries_attempted=5)
        delay_time = policy.get_delay_time(ctx)
        self.assertGreaterEqual(delay_time, 0)
        self.assertLessEqual(delay_time, 10000)

    def test_equal_jitter_backoff_policy(self):
        policy = EqualJitterBackoffPolicy({'period': 1, 'cap': 10000})
        ctx = RetryPolicyContext(retries_attempted=5)
        delay_time = policy.get_delay_time(ctx)
        self.assertGreaterEqual(delay_time, 0)
        self.assertLessEqual(delay_time, 10000)

    def test_full_jitter_backoff_policy(self):
        policy = FullJitterBackoffPolicy({'period': 1, 'cap': 10000})
        ctx = RetryPolicyContext(retries_attempted=5)
        delay_time = policy.get_delay_time(ctx)
        self.assertGreaterEqual(delay_time, 0)
        self.assertLessEqual(delay_time, 10000)

class TestRetryCondition(unittest.TestCase):
    def test_retry_condition(self):
        condition = RetryCondition({
            'maxAttempts': 3,
            'backoff': {'policy': 'Fixed', 'period': 1000},
            'exception': ['Exception1'],
            'errorCode': ['Error1'],
            'maxDelay': 5000
        })
        self.assertEqual(condition.max_attempts, 3)
        self.assertIsInstance(condition.backoff, FixedBackoffPolicy)
        self.assertEqual(condition.exception, ['Exception1'])
        self.assertEqual(condition.error_code, ['Error1'])
        self.assertEqual(condition.max_delay, 5000)
    def test_retry_options(self):
        options = {
            'retryable': True,
            'retryCondition': [
                {
                    'maxAttempts': 5,
                    'exception': [],
                    'errorCode': [],
                    'maxDelay': 5000
                }
            ],
            'noRetryCondition': [
                {
                    'maxAttempts': 2,
                    'exception': [],
                    'errorCode': []
                }
            ]
        }
        
        retry_options = RetryOptions(options)

        self.assertTrue(retry_options.retryable)
        self.assertEqual(len(retry_options.retry_condition), 1)
        self.assertEqual(len(retry_options.no_retry_condition), 1)
        self.assertTrue(retry_options.validate())

    def test_get_backoff_delay(self):
        options = RetryOptions({
            'retryable': True,
            'retryCondition': [
                {'maxAttempts': 3, 'backoff': {'policy': 'Fixed', 'period': 1000}, 'exception': ['Exception1'], 'errorCode': ['Error1'], 'maxDelay': 5000}
            ],
            'noRetryCondition': [
                {'maxAttempts': 3, 'backoff': {'policy': 'Fixed', 'period': 1000}, 'exception': ['Exception2'], 'errorCode': ['Error2'], 'maxDelay': 5000}
            ]
        })
        ctx = RetryPolicyContext(retries_attempted=2, exception=AException({"name":'Exception1', "code":'Error1'}))
        self.assertEqual(get_backoff_delay(options, ctx), 1000)
        ctx.exception.retryAfter = 6000
        self.assertEqual(get_backoff_delay(options, ctx), 5000)
        options = RetryOptions({
            'retryable': True,
            'retryCondition': [
                {'maxAttempts': 3, 'exception': ['Exception1'], 'errorCode': ['Error1'], 'maxDelay': 5000}
            ],
            'noRetryCondition': [
                {'maxAttempts': 3, 'backoff': {'policy': 'Fixed', 'period': 1000}, 'exception': ['Exception2'], 'errorCode': ['Error2'], 'maxDelay': 5000}
            ]
        })
        ctx.exception.retryAfter = None
        self.assertEqual(get_backoff_delay(options, ctx), 100)
        self.assertEqual(get_backoff_delay(RetryOptions({}), ctx), 100)
