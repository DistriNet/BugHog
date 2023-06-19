import asyncio
import logging
import threading
import time

from mitmproxy import http, options
from mitmproxy.tools.dump import DumpMaster

logger = logging.getLogger('bci.proxy')

HOST = '127.0.0.1'
PORT = 8080


class ProxyThread(threading.Thread):

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            self.__reset()
            return
        super().__init__()
        self.__initialized = True

        self.__mitmproxy_master = None
        self.__addon = None
        self.__task = None
        self.start()

    @property
    def requests(self) -> list:
        assert self.__addon is not None
        return self.__addon.requests

    def __reset(self):
        assert self.__addon is not None
        self.__addon.requests = []
        self.__addon.responses = []
        logger.debug('Proxy has been reset')

    def run(self):
        assert self.__mitmproxy_master is None
        assert self.__task is None

        async def run():
            # Set up the options for mitmproxy
            mitmproxy_options = options.Options(
                listen_host=HOST,
                listen_port=PORT,
                ssl_insecure=True,
                # ciphers_client='DEFAULT@SECLEVEL=0'
                tls_version_client_min='UNBOUNDED'
                # ssl_version_client='all',
                # ssl_version_server='all'
            )
            # Set up the mitmproxy dump master
            self.__mitmproxy_master = DumpMaster(options=mitmproxy_options)

            class LogRequests:

                def __init__(self) -> None:
                    self.requests = []
                    self.responses = []

                def request(self, flow: http.HTTPFlow) -> None:
                    self.requests.append({
                        'url': flow.request.url,
                        'method': flow.request.method,
                        'headers': flow.request.headers,
                        'content': flow.request.content
                    })
                    self.responses.append(str(flow.response))

            # Set the request and response handlers for mitmproxy
            self.__addon = LogRequests()
            self.__mitmproxy_master.addons.add(self.__addon)
            # Start mitmproxy
            self.__task = asyncio.create_task(self.__mitmproxy_master.run())
            try:
                await self.__task
            except asyncio.CancelledError:
                logger.debug('Proxy task cancelled')

        def run_task():
            try:
                logger.debug('Starting proxy task...')
                asyncio.set_event_loop(asyncio.new_event_loop())
                asyncio.run(run())
            except Exception as e:
                logger.error(f'Something went wrong {e}', exc_info=True)
                raise

        run_task()


if __name__ == '__main__':
    p1 = ProxyThread()
    print('main')
    time.sleep(5)
    print(p1.requests)

    print('main2')

    p2 = ProxyThread()
    print(p1.requests)

    time.sleep(100)
