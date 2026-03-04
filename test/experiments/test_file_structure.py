import os
import tempfile
from unittest.mock import mock_open, patch

import pytest

from bughog.evaluation.file_structure import File, Folder


class TestFileType:
    def test_html(self):
        assert File('index.html', '/').file_type == 'html'

    def test_js(self):
        assert File('script.js', '/').file_type == 'js'

    def test_css(self):
        assert File('style.css', '/').file_type == 'css'

    def test_no_extension_returns_none(self):
        assert File('Makefile', '/').file_type is None

    def test_multiple_dots_uses_last(self):
        assert File('style.min.css', '/').file_type == 'css'


class TestCommentDelimiters:
    def test_html_has_closing_delimiter(self):
        prefix, suffix = File('index.html', '/').comment_delimiters
        assert suffix is not None

    def test_xml_same_as_html(self):
        assert File('doc.xml', '/').comment_delimiters == File('index.html', '/').comment_delimiters

    def test_js_no_closing_delimiter(self):
        _, suffix = File('script.js', '/').comment_delimiters
        assert suffix is None

    def test_wat_no_closing_delimiter(self):
        _, suffix = File('module.wat', '/').comment_delimiters
        assert suffix is None

    def test_unknown_type_returns_none(self):
        assert File('data.json', '/').comment_delimiters is None

    def test_no_extension_returns_none(self):
        assert File('Makefile', '/').comment_delimiters is None


class TestGetBughogPocParameter:
    def test_stops_at_first_non_comment_line(self):
        file = File('index.html', '/')
        mock_data = '\n'.join(
            [
                '<!-- bughog_test1: present -->',
                '<html>',
                '<!-- bughog_test2: absent -->',
            ]
        )
        with patch('builtins.open', mock_open(read_data=mock_data)):
            assert file.get_bughog_poc_parameter('test1') == 'present'
            assert file.get_bughog_poc_parameter('test2') is None

    def test_doctype_does_not_stop_parsing(self):
        file = File('index.html', '/')
        mock_data = '\n'.join(
            [
                '<!DOCTYPE html>',
                '<!-- bughog_test1: found -->',
            ]
        )
        with patch('builtins.open', mock_open(read_data=mock_data)):
            assert file.get_bughog_poc_parameter('test1') == 'found'

    def test_missing_parameter_returns_none(self):
        file = File('index.html', '/')
        mock_data = '<!-- bughog_other: value -->'
        with patch('builtins.open', mock_open(read_data=mock_data)):
            assert file.get_bughog_poc_parameter('missing') is None

    def test_unsupported_file_type_returns_none(self):
        assert File('data.json', '/').get_bughog_poc_parameter('test') is None


class TestFolderValidation:
    def test_name_with_space_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Folder('root', tmpdir)
            with pytest.raises(AttributeError, match='invalid'):
                folder.create_file('my file.html', b'')

    def test_name_with_slash_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Folder('root', tmpdir)
            with pytest.raises(AttributeError):
                folder.create_file('path/traversal.html', b'')

    def test_empty_name_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Folder('root', tmpdir)
            with pytest.raises(AttributeError):
                folder.create_file('', b'')

    def test_duplicate_name_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Folder('root', tmpdir)
            folder.create_file('test.html', b'first')
            with pytest.raises(AttributeError, match='already exists'):
                folder.create_file('test.html', b'second')

    def test_valid_name_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Folder('root', tmpdir)
            folder.create_file('test.html', b'content')
            assert os.path.isfile(os.path.join(tmpdir, 'test.html'))


class TestFolderParse:
    def test_parses_files_and_subfolders(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, 'index.html'), 'w').close()
            sub = os.path.join(tmpdir, 'sub')
            os.mkdir(sub)
            open(os.path.join(sub, 'script.js'), 'w').close()

            folder = Folder.parse(tmpdir)
            assert len(folder.files) == 1
            assert folder.files[0].name == 'index.html'
            assert len(folder.subfolders) == 1
            assert folder.subfolders[0].name == 'sub'

    def test_ignores_ds_store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, '.DS_Store'), 'w').close()
            open(os.path.join(tmpdir, 'index.html'), 'w').close()

            folder = Folder.parse(tmpdir)
            names = [f.name for f in folder.files]
            assert '.DS_Store' not in names
            assert 'index.html' in names

    def test_ignores_readme(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, 'README.md'), 'w').close()
            folder = Folder.parse(tmpdir)
            assert not any(f.name == 'README.md' for f in folder.files)

    def test_get_file_raises_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Folder.parse(tmpdir)
            with pytest.raises(Exception):
                folder.get_file('nonexistent.html')

    def test_get_folder_raises_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Folder.parse(tmpdir)
            with pytest.raises(Exception):
                folder.get_folder('nonexistent')


class TestFolderSerialize:
    def test_serialize_has_required_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = Folder.parse(tmpdir).serialize()
            assert {'name', 'path', 'tags', 'subfolders', 'files'} <= set(s.keys())
            assert isinstance(s['subfolders'], list)
            assert isinstance(s['files'], list)
            assert isinstance(s['tags'], list)
