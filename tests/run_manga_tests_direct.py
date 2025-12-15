import tests.test_manga_reader_features as t
print('running ai summary test')
t.test_ai_summary_endpoint()
print('ai summary test ok')
print('running template ui test')
t.test_manga_reader_template_contains_ui_elements()
print('template ui test ok')
print('all done')
