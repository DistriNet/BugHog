from time import sleep

from .browser import Browser


class Chromium(Browser):
    session_id: str

    def get_ws_endpoint(self, host: str, port: int, browser_id: str) -> str:
        return f'ws://{host}:{port}/devtools/browser/{browser_id}'

    def initialize_connection(self, browserId, port, host):
        # Get list of all targets and find a "page" target.
        target_response = self.send(
            {
                'method': 'Target.getTargets',
            }
        )

        page_target = list(filter(lambda info: (info['type'] == 'page'), target_response['result']['targetInfos']))[0][
            'targetId'
        ]

        # Attach to the page target.
        session = self.send({'method': 'Target.attachToTarget', 'params': {'targetId': page_target, 'flatten': True}})

        self.session_id = session['result']['sessionId']

    def close_connection(self):
        pass

    def navigate(self, url):
        self.send({'sessionId': self.session_id, 'method': 'Page.navigate', 'params': {'url': url}})
        sleep(0.5)

    def click(self, x, y):
        self.send(
            {
                'sessionId': self.session_id,
                'method': 'Input.dispatchMouseEvent',
                'params': {'x': x, 'y': y, 'type': 'mousePressed', 'clickCount': 1, 'button': 'left'},
            }
        )

        self.send(
            {
                'sessionId': self.session_id,
                'method': 'Input.dispatchMouseEvent',
                'params': {'x': x, 'y': y, 'type': 'mouseReleased', 'button': 'left'},
            }
        )
