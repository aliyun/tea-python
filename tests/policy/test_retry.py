import unittest
from darabonba.policy.retry import (
    BackoffPolicy,
    FixedBackoffPolicy,
    RandomBackoffPolicy,
    ExponentialBackoffPolicy,
    EqualJitterBackoffPolicy,
    FullJitterBackoffPolicy,
    RetryOptions,
    RetryPolicyContext,
    should_retry,
    get_backoff_delay
)

class TestRetryPolicies(unittest.TestCase):

    def setUp(self):
        self.retry_context = RetryPolicyContext({'key': 'test', 'retriesAttempted': 0})

    def test_fixed_backoff_policy(self):
        option = {'policy': 'Fixed', 'period': 100}
        backoff_policy = FixedBackoffPolicy(option)
        self.assertEqual(backoff_policy.get_delay_time(self.retry_context), 100)

    def test_random_backoff_policy(self):
        option = {'policy': 'Random', 'period': 100, 'cap': 1000}
        backoff_policy = RandomBackoffPolicy(option)
        self.retry_context.retries_attempted = 5  # Simulate 5 attempts
        delay = backoff_policy.get_delay_time(self.retry_context)
        self.assertLessEqual(delay, 1000)
        self.assertGreaterEqual(delay, 0)

    def test_exponential_backoff_policy(self):
        option = {'policy': 'Exponential', 'period': 100, 'cap': 1000}
        backoff_policy = ExponentialBackoffPolicy(option)
        self.retry_context.retries_attempted = 3  # Simulate 3 attempts
        delay = backoff_policy.get_delay_time(self.retry_context)
        self.assertLessEqual(delay, 1000)

    def test_should_retry(self):
        options = RetryOptions({
            'retryable': True,
            'retryCondition': [{
                'maxAttempts': 5,
                'exception': ['ExceptionA'],
            }]
        })
        self.retry_context.exception = type('Exception', (object,), {'name': 'ExceptionA'})
        self.assertTrue(should_retry(options, self.retry_context))

        self.retry_context.retries_attempted = 5
        self.assertFalse(should_retry(options, self.retry_context))

    def test_get_backoff_delay(self):
        options = RetryOptions({
            'retryCondition': [{
                'maxAttempts': 5,
                'backoff': {'policy': 'Fixed', 'period': 200},
                'exception': ['ExceptionA'],
                'maxDelay': 5000
            }]
        })
        self.retry_context.exception = type('Exception', (object,), {'name': 'ExceptionA'})
        
        # First attempt
        delay = get_backoff_delay(options, self.retry_context)
        self.assertEqual(delay, 200)  # Expect fixed delay of 200ms

        # Second attempt
        self.retry_context.retries_attempted = 1
        delay = get_backoff_delay(options, self.retry_context)
        self.assertEqual(delay, 200)  # Expect fixed delay of 200ms again
