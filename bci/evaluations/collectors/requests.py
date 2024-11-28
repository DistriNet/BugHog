import http.server
import json
import logging
import socket
import socketserver
from threading import Thread

from .base import BaseCollector

logger = logging.getLogger(__name__)

PORT = 5001


class RequestHandler(http.server.BaseHTTPRequestHandler):
    """
    Handles requests sent to the collector.
    """

    def __init__(self, collector, request, client_address, server) -> None:
        self.collector = collector
        self.request_body = None
        super().__init__(request, client_address, server)

    def log_message(self, format: str, *args) -> None:
        """
        Handle and store the received body.
        """
        if not self.request_body:
            logger.debug('Received request without body')
            return

        request_body = json.loads(self.request_body)
        logger.debug(f'Received request information with {len(request_body.keys())} attributes.')
        self.collector.data['requests'].append(request_body)

    def do_POST(self):
        """
        This function is called upon receiving a POST request.
        It sets `self.request_body`, which will be parsed later by `self.log_message`.
        """
        # We have to read the body before allowing it to be thrashed when connection clusure is confirmed.
        if self.headers['Content-Length'] is not None:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.request_body = body.decode('utf-8')

        # Because of our hacky NGINX methodology, we have to allow premature socket closings.
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write('Post request received!\n'.encode('utf-8'))
        except socket.error:
            logger.debug('Socket closed by NGINX (expected)')


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
        self.__httpd = socketserver.TCPServer(('', PORT), lambda *args, **kwargs: RequestHandler(self, *args, **kwargs))
        # self.__httpd.allow_reuse_address = True
        self.__thread = Thread(target=self.__httpd.serve_forever)
        self.__thread.start()

    def stop(self):
        data = []
        # Important: we only consider requests to the /report/ endpoint where the bughog parameter immediately follows.
        # Otherwise conditional endpoints (e.g., /report/if/Referer/) cause false positives.
        regex = r'/report/\?bughog_(.+)=(.+)'
        if self.__httpd:
            self.__httpd.shutdown()
            if self.__thread:
                self.__thread.join()
            self.__httpd.server_close()
        request_urls = [request['url'] for request in self.data['requests'] if 'url' in request]
        data = self._parse_bughog_variables(request_urls, regex)
        self.data['req_vars'] = data
