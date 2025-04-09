import unittest
from unittest.mock import MagicMock
from typing import Dict, Any
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
        option = {'policy': 'Fixed', 'period': 100}
        fixed_policy = FixedBackoffPolicy(option)
        expected_map = {'policy': 'Fixed', 'period': 100}
        self.assertEqual(fixed_policy.to_map(), expected_map)

    def test_random_backoff_policy(self):
        policy = RandomBackoffPolicy({'period': 1000, 'cap': 2000})
        ctx = RetryPolicyContext(retries_attempted=5)
        delay_time = policy.get_delay_time(ctx)
        self.assertGreaterEqual(delay_time, 0)
        self.assertLessEqual(delay_time, 2000)
        option = {'policy': 'Random', 'period': 100, 'cap': 5000}
        random_policy = RandomBackoffPolicy(option)
        expected_map = {'policy': 'Random', 'period': 100, 'cap': 5000}
        self.assertEqual(random_policy.to_map(), expected_map)

    def test_exponential_backoff_policy(self):
        policy = ExponentialBackoffPolicy({'period': 1, 'cap': 10000})
        ctx = RetryPolicyContext(retries_attempted=5)
        delay_time = policy.get_delay_time(ctx)
        self.assertGreaterEqual(delay_time, 0)
        self.assertLessEqual(delay_time, 10000)
        option = {'policy': 'Exponential', 'period': 100, 'cap': 100000}
        exponential_policy = ExponentialBackoffPolicy(option)
        expected_map = {'policy': 'Exponential', 'period': 100, 'cap': 100000}
        self.assertEqual(exponential_policy.to_map(), expected_map)

    def test_equal_jitter_backoff_policy(self):
        policy = EqualJitterBackoffPolicy({'period': 1, 'cap': 10000})
        ctx = RetryPolicyContext(retries_attempted=5)
        delay_time = policy.get_delay_time(ctx)
        self.assertGreaterEqual(delay_time, 0)
        self.assertLessEqual(delay_time, 10000)
        option = {'policy': 'EqualJitter', 'period': 100, 'cap': 100000}
        equal_jitter_policy = EqualJitterBackoffPolicy(option)
        expected_map = {'policy': 'EqualJitter', 'period': 100, 'cap': 100000}
        self.assertEqual(equal_jitter_policy.to_map(), expected_map)

    def test_full_jitter_backoff_policy(self):
        policy = FullJitterBackoffPolicy({'period': 1, 'cap': 10000})
        ctx = RetryPolicyContext(retries_attempted=5)
        delay_time = policy.get_delay_time(ctx)
        self.assertGreaterEqual(delay_time, 0)
        self.assertLessEqual(delay_time, 10000)
        option = {'policy': 'FullJitter', 'period': 100, 'cap': 100000}
        full_jitter_policy = FullJitterBackoffPolicy(option)
        expected_map = {'policy': 'FullJitter', 'period': 100, 'cap': 100000}
        self.assertEqual(full_jitter_policy.to_map(), expected_map)

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
        condition = {
            'maxAttempts': 3,
            'backoff': {'policy': 'Fixed', 'period': 100},
            'exception': ['ExceptionA'],
            'errorCode': ['ErrorA']
        }
        retry_condition = RetryCondition(condition)
        expected_backoff = {'policy': 'Fixed', 'period': 100}
        expected_map = {
            'maxAttempts': 3,
            'backoff': expected_backoff,
            'exception': ['ExceptionA'],
            'errorCode': ['ErrorA']
        }
        self.assertEqual(retry_condition.to_map(), expected_map)
        
        data: Dict[str, Any] = {
            'maxAttempts': 3,
            'backoff': {'policy': 'Fixed', 'period': 100},
            'exception': ['ExceptionA'],
            'errorCode': ['ErrorA']
        }
        retry_condition = RetryCondition.from_map(data)
        self.assertEqual(retry_condition.max_attempts, 3)
        self.assertEqual(retry_condition.backoff.policy, 'Fixed')
        self.assertEqual(retry_condition.backoff.period, 100)
        self.assertEqual(retry_condition.exception, ['ExceptionA'])
        self.assertEqual(retry_condition.error_code, ['ErrorA'])
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
        expected_map = {'retryable': True, 'retryCondition': [{'maxAttempts': 5, 'maxDelay': 5000}], 'noRetryCondition': [{'maxAttempts': 2}]}
        self.assertTrue(retry_options.retryable)
        self.assertEqual(len(retry_options.retry_condition), 1)
        self.assertEqual(len(retry_options.no_retry_condition), 1)
        self.assertTrue(retry_options.validate())
        self.assertEqual(retry_options.to_map(), expected_map)
        retry_options = RetryOptions.from_map(expected_map)
        self.assertTrue(retry_options.to_map() == expected_map)
        

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