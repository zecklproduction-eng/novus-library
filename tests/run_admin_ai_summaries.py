from test_admin_ai_summaries import (
    test_admin_access_control,
    test_admin_list_and_clear_actions,
)

if __name__ == '__main__':
    try:
        test_admin_access_control(); print('test_admin_access_control: OK')
        test_admin_list_and_clear_actions(); print('test_admin_list_and_clear_actions: OK')
        print('All admin AI summary tests OK')
    except Exception as e:
        import traceback
        print('FAILED', e)
        traceback.print_exc()
        raise
