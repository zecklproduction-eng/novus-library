import sys, traceback
from test_manga_reader_features import (
    test_ai_summary_endpoint,
    test_manga_reader_template_contains_ui_elements,
    test_chapter_page_images_embedded,
)
from test_admin_ai_summaries import (
    test_admin_access_control,
    test_admin_list_and_clear_actions,
)

tests = [
    test_ai_summary_endpoint,
    test_manga_reader_template_contains_ui_elements,
    test_chapter_page_images_embedded,
    test_admin_access_control,
    test_admin_list_and_clear_actions,
]

for t in tests:
    try:
        t()
        print(f"{t.__name__}: OK")
    except Exception as e:
        print(f"{t.__name__}: FAILED -> {e}")
        traceback.print_exc()
        sys.exit(2)

print('All tests OK')
