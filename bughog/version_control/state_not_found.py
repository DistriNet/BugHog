from typing import Optional


class StateNotFound(Exception):

    def __init__(self, missing_attribute: str, using_attribute: str, using_url: Optional[str] = None) -> None:
        self.missing_attribute = missing_attribute
        self.using_attribute = using_attribute
        self.using_url = using_url

    def __str__(self) -> str:
        if self.using_url:
            return f'Cound not find state for {self.missing_attribute} using {self.using_attribute} and {self.using_url}.'
        else:
            return f'Cound not find state for {self.missing_attribute} using {self.using_attribute}.'
