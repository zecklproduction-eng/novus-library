#!/usr/bin/env python
import sys
from test_e2e_ai_manga import test_manga_ai_summary

if __name__ == '__main__':
    try:
        test_manga_ai_summary()
        print('E2E AI manga test passed')
        sys.exit(0)
    except AssertionError as e:
        print('E2E AI manga test failed:', e)
        sys.exit(2)
    except Exception as e:
        print('E2E AI manga test error:', e)
        sys.exit(3)
