import unittest
from unittest.mock import mock_open, patch

from bughog.evaluation.file_structure import File


class TestPocParameterParsing(unittest.TestCase):

    def test_html_file_param_parsing(self):
        file = File('index.html', '/')

        mock_data = [
            '<!DOCTYPE html>',
            '<!-- bughog_test1: true -->',
            ' <!--  bughog_test2:  false  --> ',
            '<!--bughog_test3:value-->',
        ]
        m = mock_open(read_data='\n'.join(mock_data))

        with patch('builtins.open', m):
            assert file.get_bughog_poc_parameter('test1') == 'true'
            assert file.get_bughog_poc_parameter('test2') == 'false'
            assert file.get_bughog_poc_parameter('test3') == 'value'

    def test_css_file_param_parsing(self):
        file = File('stylesheet.css', '/')

        mock_data = [
            '/* bughog_test1: true */',
            ' /*  bughog_test2:  false  */ ',
            '/*bughog_test3:value*/',
        ]
        m = mock_open(read_data='\n'.join(mock_data))

        with patch('builtins.open', m):
            assert file.get_bughog_poc_parameter('test1') == 'true'
            assert file.get_bughog_poc_parameter('test2') == 'false'
            assert file.get_bughog_poc_parameter('test3') == 'value'

    def test_js_file_param_parsing(self):
        file = File('script.js', '/')

        mock_data = [
            '// bughog_test1: true',
            ' //  bughog_test2:  false   ',
            '//bughog_test3:value',
        ]
        m = mock_open(read_data='\n'.join(mock_data))

        with patch('builtins.open', m):
            assert file.get_bughog_poc_parameter('test1') == 'true'
            assert file.get_bughog_poc_parameter('test2') == 'false'
            assert file.get_bughog_poc_parameter('test3') == 'value'

    def test_wat_file_param_parsing(self):
        file = File('poc.wat', '/')

        mock_data = [
            ';; bughog_test1: true',
            ' ;;  bughog_test2:  false   ',
            ';;bughog_test3:value',
        ]
        m = mock_open(read_data='\n'.join(mock_data))

        with patch('builtins.open', m):
            assert file.get_bughog_poc_parameter('test1') == 'true'
            assert file.get_bughog_poc_parameter('test2') == 'false'
            assert file.get_bughog_poc_parameter('test3') == 'value'
