#!/usr/bin/env python
import sys
from test_manga_reader_features import test_ai_summary_endpoint, test_manga_reader_template_contains_ui_elements

if __name__ == '__main__':
    try:
        test_ai_summary_endpoint()
        print('AI summary endpoint test passed')
        test_manga_reader_template_contains_ui_elements()
        print('Manga reader template UI test passed')
        sys.exit(0)
    except AssertionError as e:
        print('Test failed:', e)
        sys.exit(2)
    except Exception as e:
        print('Test error:', e)
        sys.exit(3)
