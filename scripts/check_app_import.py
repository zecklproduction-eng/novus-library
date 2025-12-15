try:
    import app
    print('app import: OK')
except Exception as e:
    import traceback
    print('app import: FAILED', e)
    traceback.print_exc()
    raise
