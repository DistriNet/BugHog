import json
from abc import ABC, abstractmethod

from websockets.sync.client import ClientConnection, connect


# Returns true if:
# - required == True -> all fields from `pattern` are present in `data` with the same value
# - required == False -> all fields from `pattern` which are present in `data` have the same value
def dictionaries_match(pattern: dict, data: dict, required: bool) -> bool:
    for key in pattern:
        if required and key not in data:
            return False

        if key in data:
            # Equal values, up to slashes
            if (
                not dictionaries_match(pattern[key], data[key], required)
                if isinstance(pattern[key], dict)
                else str(data[key]).replace('/', '') != str(pattern[key]).replace('/', '')
            ):
                return False
    return True


class Browser(ABC):
    request_id: int = 0
    ws_timeout: float
    ws: ClientConnection

    public_methods: list[str] = ['navigate', 'click']

    def __init__(self, browser_id: str = '', port: int = 9222, host: str = '127.0.0.1', autoclose_timeout: float = 2):
        self.ws_timeout = autoclose_timeout
        self.ws = connect(self.get_ws_endpoint(host, port, browser_id), close_timeout=autoclose_timeout)
        self.initialize_connection(browser_id, port, host)

    def req_id(self) -> int:
        self.request_id += 1
        return self.request_id

    def send(self, data: dict) -> dict:
        data['id'] = self.req_id()

        self.ws.send(json.dumps(data))

        return self.receive({'method': data['method'], 'id': data['id']}, False)

    def listen(self, event: str, params: dict) -> dict:
        return self.receive({'type': 'event', 'method': event, 'params': params}, True)

    def receive(self, data: dict, required: bool) -> dict:
        result = None

        while result == None or (not dictionaries_match(data, result, required)):
            result = json.loads(self.ws.recv(self.ws_timeout))

            if 'type' in result and result['type'] == 'error':
                raise Exception(f'Received browser error: {result}')

        return result

    # --- BROWSER-SPECIFIC METHODS ---
    @abstractmethod
    def get_ws_endpoint(self, host: str, port: int, browser_id: str) -> str:
        pass

    @abstractmethod
    def initialize_connection(self, _browserId, _port, _host):
        pass

    @abstractmethod
    def close_connection(
        self,
    ):
        pass

    @abstractmethod
    def navigate(self, _url):
        pass

    @abstractmethod
    def click(self, _x, _y):
        pass
