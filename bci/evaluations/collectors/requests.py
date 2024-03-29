import http.server
import json
import logging
import socketserver
from threading import Thread

from .base import BaseCollector

logger = logging.getLogger(__name__)

PORT = 5001


class RequestHandler(http.server.BaseHTTPRequestHandler):

    def __init__(self, collector, request, client_address, server) -> None:
        self.collector = collector
        self.request_body = None
        super().__init__(request, client_address, server)

    def log_message(self, *_):
        if not self.request_body:
            logger.debug('Received request without body')
            return

        logger.debug(f'Received request with body: {self.request_body}')
        request_body = json.loads(self.request_body)
        self.collector.data['requests'].append(request_body)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        self.request_body = body.decode('utf-8')
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Post request received')


class RequestCollector(BaseCollector):

    def __init__(self):
        super().__init__()
        self.__httpd = None
        self.__thread = None
        self.data['requests'] = []
        self.data['req_vars'] = []

    def start(self):
        logger.debug('Starting collector...')
        socketserver.TCPServer.allow_reuse_address = True
        self.__httpd = socketserver.TCPServer(("", PORT), lambda *args, **kwargs: RequestHandler(self, *args, **kwargs))
        # self.__httpd.allow_reuse_address = True
        self.__thread = Thread(target=self.__httpd.serve_forever)
        self.__thread.start()

    def stop(self):
        data = []
        regex = r'bughog_(.+)=(.+)'
        if self.__httpd:
            self.__httpd.shutdown()
            self.__thread.join()
            self.__httpd.server_close()
        request_urls = [request['url'] for request in self.data['requests'] if 'url' in request]
        data = self._parse_bughog_variables(request_urls, regex)
        self.data['req_vars'] = data
