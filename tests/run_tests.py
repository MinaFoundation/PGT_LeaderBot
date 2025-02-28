import unittest
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_openai_retry import TestOpenAIRetryMechanism
from tests.test_process_commit_day import TestProcessCommitDay


def run_async_tests(test_class):
    """Run async tests for a given test class."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(test_class)
    
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Close the loop
    loop.close()
    
    return result


if __name__ == "__main__":
    # Run the tests
    print("Running OpenAI Retry Mechanism Tests...")
    retry_result = run_async_tests(TestOpenAIRetryMechanism)
    
    print("\nRunning Process Commit Day Tests...")
    process_result = run_async_tests(TestProcessCommitDay)
    
    # Check if any tests failed
    if not (retry_result.wasSuccessful() and process_result.wasSuccessful()):
        sys.exit(1) 