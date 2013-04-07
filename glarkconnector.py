#!/usr/bin/python
"""Connector for the glark.io editor. """

__version__ = "0.1"

import BaseHTTPServer
import json
import os
import re
import sys


class ConnectorRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """Request handler exposing a REST api to the underlying filesystem"""

    server_version = "glarkconnector/" + __version__
    allow_origin = "http://glark.io"
    # allow_origin = "*" # Allow any origin (not for production!)

    def do_GET(self):
        """Serve a GET request."""
        # Route request.
        print('Request path: ' + self.path)
        if (self.path == '/files'):
            self.route_get_list_files()
        elif (re.match(r'/files/(.+)$', self.path)):
            requested_file = re.match(r'/files/(.+)$', self.path).group(1)
            self.route_get_file(requested_file)
        else:
            self.route_400()

    def do_OPTIONS(self):
        """Serve a OPTIONS request."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", self.allow_origin)
        self.send_header("Access-Control-Allow-Headers", "accept, origin, x-requested-with")
        self.end_headers()

    def do_HEAD(self):
        """Serve a HEAD request."""
        raise NotImplemented

    # ----------
    # Routes:
    def route_get_list_files(self):
        try:
            files = os.listdir(os.getcwd())
        except os.error:
            self.route_403()
            return

        self.jsend(files)

    def route_get_file(self, requested_file):
        if not self.is_in_directory(requested_file, os.getcwd()):
            self.route_403()
        else:
            try:
                # Always read in binary mode. Opening files in text mode may cause
                # newline translations, making the actual size of the content
                # transmitted *less* than the content-length!
                with open(os.path.realpath(requested_file), 'rb') as fp:
                    file_content = fp.read()
                    file_stat = os.fstat(fp.fileno())
                    file_size = str(file_stat[6])
                    file_mtime = str(file_stat.st_mtime)
            except IOError:
                self.route_404()
                return

            data = {'content': file_content, 'size': file_size, 'mtime': file_mtime}
            self.jsend(data)

    def route_400(self):
        self.jsend("Not a valid api route", False, 400)

    def route_403(self):
        self.jsend("Forbidden path", False, 403)

    def route_404(self):
        self.jsend("Not found", False, 404)

    # ----------
    # Helpers
    def jsend(self, data, success=True, status_code=None):
        """Send data in jsend format.

        The data parameter is any json dumpable Python objet. Defaults status is
        success and default status_code is 200."""
        if success:
            status = 'success'
        else:
            status = 'failure'

        formatted = {'status': status, 'data': data}
        self.send_json(formatted, status_code)

    def send_json(self, data, status_code=None):
        """Send some json with the correct headers and the given status code.

        Default status code is 200. The json parameter is in fact a dictionary,
        it is dumped to json here."""
        jsend = json.dumps(data)

        if status_code is None:
            status_code = 200

        self.send_response(status_code)
        self.send_header("Access-Control-Allow-Origin", self.allow_origin)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/json; charset=%s" % encoding)
        self.send_header("Content-Length", str(len(jsend)))
        self.end_headers()

        self.wfile.write(jsend)

    def is_in_directory(self, file_path, directory_path):
        """Check that file_path is inside directory_path or any of its
        subdirectories, following symlinks."""
        real_dir = os.path.realpath(directory_path)
        real_file = os.path.realpath(file_path)
        return os.path.commonprefix([real_file, real_dir]) == real_dir


def startConnector(port):
    httpd = BaseHTTPServer.HTTPServer(('', port), ConnectorRequestHandler)

    print('Serving directory:\n' + os.getcwd() + '\nat port ' + str(port))
    httpd.serve_forever()


def main():
    port = 3000
    if len(sys.argv) > 1:
        port = sys.argv[1]

    startConnector(port)


if __name__ == '__main__':
    main()
