#!/usr/bin/env python3
"""Single-command test runner and release gate for PN Accuracy Dashboard.

Executes all 4 guardian test suites:
- test_business_rules.py
- test_data_processing.py
- test_azure_and_fallback.py
- test_baseline_invariants.py

Exit code: 0 if all tests pass, 1 on failure.
"""

import os
import sys
import time
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(TESTS_DIR)

if os.path.exists(os.path.join(PARENT_DIR, "release_4_azure", "app.py")):
    APP_DIR = os.path.join(PARENT_DIR, "release_4_azure")
elif os.path.exists(os.path.join(PARENT_DIR, "constants.py")):
    APP_DIR = PARENT_DIR
elif os.path.exists(os.path.join(PARENT_DIR, "app.py")):
    APP_DIR = PARENT_DIR
else:
    APP_DIR = os.getcwd()

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)


def main():
    print("=" * 65)
    print(" ⚡ PN ACCURACY DASHBOARD — GUARDIAN REGRESSION TEST SUITE")
    print("=" * 65)

    start_time = time.time()
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=TESTS_DIR, pattern="test_*.py", top_level_dir=PARENT_DIR)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    elapsed = time.time() - start_time

    print("=" * 65)
    print(f" Tests Run:    {result.testsRun}")
    print(f" Errors:       {len(result.errors)}")
    print(f" Failures:     {len(result.failures)}")
    print(f" Duration:     {elapsed:.2f}s")
    print("=" * 65)

    if result.wasSuccessful():
        print(" ✅ ALL TEST SUITES PASSED — APP INTEGRITY VERIFIED")
        sys.exit(0)
    else:
        print(" ❌ REGRESSION DETECTED — RELEASE GATE BLOCKED")
        sys.exit(1)


if __name__ == "__main__":
    main()
