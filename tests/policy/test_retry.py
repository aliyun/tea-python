import unittest
from unittest.mock import MagicMock
from darabonba.policy.retry import (
    BackoffPolicy, FixedBackoffPolicy, RandomBackoffPolicy, ExponentialBackoffPolicy,
    EqualJitterBackoffPolicy, FullJitterBackoffPolicy, RetryCondition, RetryOptions, RetryPolicyContext,
    should_retry, get_backoff_delay
)

from darabonba.exceptions import DaraException

class AException(DaraException):
        def __init__(self, dic):
            super().__init__(dic)
            self.name = 'AException'

class TestBackoffPolicy(unittest.TestCase):
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

class TestRetryOptions(unittest.TestCase):
    def test_retry_options(self):
        options = RetryOptions({
            'retryable': True,
            'retryCondition': [
                {'maxAttempts': 3, 'backoff': {'policy': 'Fixed', 'period': 1000}, 'exception': ['Exception1'], 'errorCode': ['Error1'], 'maxDelay': 5000}
            ],
            'noRetryCondition': [
                {'maxAttempts': 3, 'backoff': {'policy': 'Fixed', 'period': 1000}, 'exception': ['Exception2'], 'errorCode': ['Error2'], 'maxDelay': 5000}
            ]
        })
        self.assertTrue(options.retryable)
        self.assertEqual(len(options.retry_condition), 1)
        self.assertEqual(len(options.no_retry_condition), 1)

    def test_validate(self):
        options = RetryOptions({
            'retryable': True,
            'retryCondition': [
                {'maxAttempts': 3, 'backoff': {'policy': 'Fixed', 'period': 1000}, 'exception': ['Exception1'], 'errorCode': ['Error1'], 'maxDelay': 5000}
            ],
            'noRetryCondition': [
                {'maxAttempts': 3, 'backoff': {'policy': 'Fixed', 'period': 1000}, 'exception': ['Exception2'], 'errorCode': ['Error2'], 'maxDelay': 5000}
            ]
        })
        self.assertTrue(options.validate())

class TestShouldRetry(unittest.TestCase):
    def test_should_retry(self):
        options = RetryOptions({
            'retryable': True,
            'retryCondition': [
                {'maxAttempts': 3, 'backoff': {'policy': 'Fixed', 'period': 1000}, 'exception': ['Exception1'], 'errorCode': ['Error1'], 'maxDelay': 5000}
            ],
            'noRetryCondition': [
                {'maxAttempts': 3, 'backoff': {'policy': 'Fixed', 'period': 1000}, 'exception': ['Exception2'], 'errorCode': ['Error2'], 'maxDelay': 5000}
            ]
        })
        ctx = RetryPolicyContext(retries_attempted=2, exception=MagicMock(name='Exception1', code='Error1'))
        self.assertTrue(should_retry(options, ctx))

        ctx = RetryPolicyContext(retries_attempted=3, exception=MagicMock(name='Exception1', code='Error1'))
        self.assertFalse(should_retry(options, ctx))

        ctx = RetryPolicyContext(retries_attempted=2, exception=MagicMock(name='Exception2', code='Error2'))
        self.assertFalse(should_retry(options, ctx))

class TestGetBackoffDelay(unittest.TestCase):
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