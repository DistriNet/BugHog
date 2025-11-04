import unittest

from bughog.subject import factory


class TestPocParameterParsing(unittest.TestCase):

    def test_js_engine_param_parsing(self):
        framework = factory.create_evaluation_framework('js_engine')

        assert framework._parse_bughog_poc_param_line('// bughog_test: true', 'test') == 'true'
        assert framework._parse_bughog_poc_param_line(' //  bughog_test:  false   ', 'test') == 'false'
        assert framework._parse_bughog_poc_param_line('//bughog_test:value', 'test') == 'value'

    # def test_wasm_runtime_param_parsing(self):
    #     framework = factory.create_evaluation_framework('wasm_runtime')

    #     assert framework._parse_bughog_poc_param_line(';; bughog_test: true ', 'test') == 'true'
    #     assert framework._parse_bughog_poc_param_line(' ;;  bughog_test:  false   ', 'test') == 'false'
    #     assert framework._parse_bughog_poc_param_line(';;bughog_test:value', 'test') == 'value'

    def test_web_browser_param_parsing(self):
        framework = factory.create_evaluation_framework('web_browser')

        assert framework._parse_bughog_poc_param_line('<!-- bughog_test: true -->', 'test') == 'true'
        assert framework._parse_bughog_poc_param_line(' <!--  bughog_test:  false  --> ', 'test') == 'false'
        assert framework._parse_bughog_poc_param_line('<!--bughog_test:value-->', 'test') == 'value'

