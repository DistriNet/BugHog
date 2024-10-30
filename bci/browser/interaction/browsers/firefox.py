from .browser import Browser


class Firefox(Browser):
    browsing_context: str

    def get_ws_endpoint(self, host: str, port: int, browser_id: str) -> str:
        return f'ws://{host}:{port}/session'

    def initialize_connection(self, browserId, port, host):
        # Initiate the session
        session_id = self.send({'method': 'session.new', 'params': {'capabilities': {}}})['result']['sessionId']

        # Subscribe to browser events
        self.send(
            {
                'method': 'session.subscribe',
                'params': {
                    'events': [
                        'browsingContext.domContentLoaded',
                    ]
                },
            }
        )

        # Create the browsing context
        user_context = self.send({'method': 'browser.createUserContext', 'params': {}})['result']['userContext']

        self.browsing_context = self.send(
            {'method': 'browsingContext.create', 'params': {'type': 'tab', 'userContext': user_context}}
        )['result']['context']

    def close_connection(self):
        self.send(
            {
                'method': 'session.end',
                'params': {},
            }
        )

    def navigate(self, url):
        navigation = self.send(
            {'method': 'browsingContext.navigate', 'params': {'url': url, 'context': self.browsing_context}}
        )['result']['navigation']

        # Wait for the DOM to load
        self.listen(
            'browsingContext.domContentLoaded',
            {}
            #{
            #    'url': url,
            #    'context': self.browsing_context,
            #    'navigation': navigation,
            #},
        )

    def click(self, x, y):
        self.send(
            {
                'method': 'input.performActions',
                'params': {
                    'context': self.browsing_context,
                    'actions': [
                        {
                            'type': 'pointer',
                            'id': str(self.req_id()),
                            'actions': [
                                {'type': 'pointerDown', 'button': 1, 'width': x, 'height': y},
                                {'type': 'pointerUp', 'button': 1, 'width': x, 'height': y},
                            ],
                        }
                    ],
                },
            }
        )
