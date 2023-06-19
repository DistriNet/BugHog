import logging
import re
from typing import Optional
from bci.revision_parser.parser import RevisionParser
from bci.util import request_html, request_final_url


REV_ID_BASE_URL = 'https://chromium.googlesource.com/chromium/src/+/'
REV_NUMBER_BASE_URL = 'http://crrev.com/'


class ChromiumRevisionParser(RevisionParser):

    def get_rev_id(self, rev_number: int) -> str:
        final_url = request_final_url(f'{REV_NUMBER_BASE_URL}{rev_number}')
        rev_id = final_url[-40:]
        assert re.match(r'[a-z0-9]{40}', rev_id)
        return rev_id

    def get_rev_number(self, rev_id: str) -> int:
        url = f'{REV_ID_BASE_URL}{rev_id}'
        html = request_html(url).decode()
        rev_number = self.__parse_revision_number(html)
        if rev_number is None:
            logging.getLogger('bci').error(f'Could not parse revision number on \'{url}\'')
            raise AttributeError(f'Could not parse revision number on \'{url}\'')
        assert re.match(r'[0-9]{1,7}', rev_number)
        return int(rev_number)

    @staticmethod
    def __parse_revision_number(html: str) -> Optional[str]:
        matches = re.findall(r'refs\/heads\/(?:master|main)\@\{\#([0-9]{1,7})\}', html)
        if matches:
            return matches[0]
        matches = re.findall(r'svn.chromium.org\/chrome\/trunk\/src\@([0-9]{1,7}) ', html)
        if matches:
            return matches[0]
        return None
