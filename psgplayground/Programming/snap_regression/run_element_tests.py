"""
run_element_tests.py - Discover and run all element update tests, then record results.

Usage:
    python run_element_tests.py                 # run tests, write test_results/latest.json
    python run_element_tests.py --baseline      # additionally save results as the baseline
    python run_element_tests.py test_text_update.py   # run only the named test file(s)

Every run writes:
    test_results/latest.json                    - most recent run (used by compare)
    test_results/results_<timestamp>.json       - permanent copy of this run
    test_results/baseline.json                  - only when --baseline is given

Compare two runs afterwards with:  python compare_test_results.py
"""

import argparse
import datetime
import glob
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, 'test_results')
TEST_FILE_PATTERN = 'test_*_update.py'      # widen this as more method tests are added


class RecordingResult(unittest.TextTestResult):
    """TextTestResult that also records every test's outcome by name."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = {}      # test id -> 'pass' | 'fail' | 'error' | 'skip'

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes[test.id()] = 'pass'

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes[test.id()] = 'fail'

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes[test.id()] = 'error'

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes[test.id()] = 'skip'


def discover_test_files(explicit_files):
    if explicit_files:
        return [os.path.join(HERE, f) if not os.path.isabs(f) else f for f in explicit_files]
    return sorted(glob.glob(os.path.join(HERE, TEST_FILE_PATTERN)))


def build_suite(test_files):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    sys.path.insert(0, HERE)
    for path in test_files:
        module_name = os.path.splitext(os.path.basename(path))[0]
        suite.addTests(loader.loadTestsFromName(module_name))
    return suite


def run(test_files):
    suite = build_suite(test_files)
    runner = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult)
    result = runner.run(suite)
    return result


def save_results(result, test_files, save_baseline):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    payload = {
        'timestamp': timestamp,
        'test_files': [os.path.basename(f) for f in test_files],
        'totals': {
            'run': result.testsRun,
            'passed': sum(1 for v in result.outcomes.values() if v == 'pass'),
            'failed': sum(1 for v in result.outcomes.values() if v == 'fail'),
            'errors': sum(1 for v in result.outcomes.values() if v == 'error'),
            'skipped': sum(1 for v in result.outcomes.values() if v == 'skip'),
        },
        'tests': result.outcomes,
    }

    latest = os.path.join(RESULTS_DIR, 'latest.json')
    stamped = os.path.join(RESULTS_DIR, 'results_{}.json'.format(timestamp))
    with open(stamped, 'w') as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    with open(latest, 'w') as f:
        json.dump(payload, f, indent=2, sort_keys=True)

    written = [stamped, latest]
    if save_baseline:
        baseline = os.path.join(RESULTS_DIR, 'baseline.json')
        with open(baseline, 'w') as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        written.append(baseline)
    return payload, written


def main():
    parser = argparse.ArgumentParser(description='Run the PySimpleGUI element update tests.')
    parser.add_argument('files', nargs='*', help='specific test files to run (default: all {})'.format(TEST_FILE_PATTERN))
    parser.add_argument('--baseline', action='store_true', help='also save this run as the comparison baseline')
    args = parser.parse_args()

    test_files = discover_test_files(args.files)
    if not test_files:
        print('No test files matching {} found in {}'.format(TEST_FILE_PATTERN, HERE))
        return 2

    print('Running {} test file(s): {}'.format(len(test_files), ', '.join(os.path.basename(f) for f in test_files)))
    print('-' * 70)
    result = run(test_files)
    payload, written = save_results(result, test_files, args.baseline)

    print('-' * 70)
    t = payload['totals']
    print('Totals:  {run} run   {passed} passed   {failed} failed   {errors} errors   {skipped} skipped'.format(**t))
    for path in written:
        print('Wrote', os.path.relpath(path, HERE))
    return 0 if (t['failed'] == 0 and t['errors'] == 0) else 1


if __name__ == '__main__':
    sys.exit(main())
