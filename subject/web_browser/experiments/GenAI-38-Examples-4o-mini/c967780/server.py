#!/usr/bin/env python3
from http.server import HTTPServer, SimpleHTTPRequestHandler, test
import sys

class CustomHTTPRequestHandler (SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/download.txt':
            self.send_response(302)
            self.send_header('Location', "javascript: window.open()")
            self.end_headers()
        else:
            SimpleHTTPRequestHandler.do_GET(self)

    def end_headers (self):
        self.send_header('Content-Security-Policy', "script-src 'self';")
        SimpleHTTPRequestHandler.end_headers(self)

if __name__ == '__main__':
    test(CustomHTTPRequestHandler, HTTPServer, port=int(sys.argv[1]) if len(sys.argv) > 1 else 8000)