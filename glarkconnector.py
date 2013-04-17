#!/usr/bin/python
# Copyright 2013 Florent Galland & Luc Verdier
#
# This file is part of glarkconnector.
#
# glarkconnector is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# at your option) any later version.
#
# glarkconnector is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with glarkconnector.  If not, see <http://www.gnu.org/licenses/>.
"""Connector for the glark.io editor. """

__version__ = "0.2"

import BaseHTTPServer
import base64
import getpass
import json
import os
import re
import sys


CONFIGURATION_FILENAME = '.glarkconnector.conf'
CONFIG = {}

# Files that must not be displayed by the connector.
BLACKLISTED_FILES = [os.path.basename(__file__), CONFIGURATION_FILENAME]


class ConnectorRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Request handler exposing a REST api to the underlying filesystem"""

    server_version = "glarkconnector/" + __version__
    allow_origin = "http://glark.io"
    allow_origin = "*" # Allow any origin (not for production!)

    def do_GET(self):
        """Serve a GET request."""
        # Route request.
        if not self.is_authenticated():
            return

        if (self.path == '/connector'):
            self.route_get_api_description()
        elif (self.path == '/connector/version'):
            self.route_get_server_version()
        elif (self.path == '/connector/files'):
            self.route_get_list_files()
        elif (re.match(r'/connector/files/(.+)$', self.path)):
            requested_file = re.match(r'/connector/files/(.+)$', self.path).group(1)
            self.route_get_file(requested_file)
        else:
            self.route_400()

    def do_PUT(self):
        """Serve a PUT request."""
        # Route request.
        if not self.is_authenticated():
            return
        
        if self.headers.getheader('content-type') != 'application/json;charset=UTF-8':
            self.route_400('Content-Type header must be application/json')
            return
        
        if (self.path == '/connector/files'):
            self.route_404()
        elif (re.match(r'/connector/files/(.+)$', self.path)):
            requested_file = re.match(r'/connector/files/(.+)$', self.path).group(1)
            self.route_put_file(requested_file)
        else:
            self.route_400()

    def do_OPTIONS(self):
        """Serve a OPTIONS request."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", self.allow_origin)
        self.send_header("Access-Control-Allow-Methods", "GET, PUT")
        self.send_header("Access-Control-Allow-Headers",
                        "accept, origin, x-requested-with, authorization, content-type")
        self.end_headers()

    def do_HEAD(self):
        """Serve a HEAD request."""
        raise NotImplementedError

    # ----------
    # Routes:
    def route_get_api_description(self):
        """Return a dynamically built list of the commands of the connector api.

        If you create a new command, don't forget to add it here."""
        base_url = ('http://' + self.server.server_name + ':' +
                    str(self.server.server_port) + '/connector')

        commands = {}
        commands['get_commands'] = base_url
        commands['get_files_list'] = base_url + '/files'
        commands['get_file_content'] = base_url + '/files/:filename'
        commands['get_server_version'] = base_url + '/version'

        self.send_jsend(commands)

    def route_get_server_version(self):
        self.send_jsend(self.server_version)
        return

    def route_get_list_files(self):
        self.send_listdir(os.getcwd())

    def route_get_file(self, requested_path):
        # Check is the requested path is a file or a directory.
        if not self.is_authorized_path(requested_path):
            self.route_403()
            return
        else:
            if os.path.isfile(requested_path):
                self.send_file_content(requested_path)
            else:
                self.send_listdir(requested_path)

    def route_put_file(self, requested_file):
        if not self.is_authorized_path(requested_file):
            self.route_403()
            return
        else:
            if not os.path.isfile(os.path.realpath(requested_file)):
                self.route_400("The requested file is a directory")
                return

            try:
                with open(os.path.realpath(requested_file), 'w') as fp:
                    # Read request body.
                    content_len = int(self.headers.getheader('content-length'))
                    body = self.rfile.read(content_len)
                    # print('PUT request body:\n' + body)

                    body = json.loads(body)

                    # Check body consistency.
                    if not 'path' in body:
                        self.route_400("body must contain a 'path' field")
                    if not 'content' in body:
                        self.route_400("body must contain a 'content' field")

                    # Check if the path matches the url.
                    if body['path'] != requested_file:
                        self.route_400("The path in request body must match the url path")
                        return

                    fp.write(str(body['content']))

                # If everything was fine, send back the new content of the file.
                self.send_file_content(body['path'])

            except IOError:
                self.route_404()
                return
            except KeyError:
                self.route_400()
                return

    def route_400(self, explanation=None):
        message = "Bad request"
        if explanation is not None:
            message += ": " + explanation

        self.send_jsend(message, False, 400)

    def route_403(self):
        self.send_jsend("Forbidden path", False, 403)

    def route_404(self):
        self.send_jsend("Not found", False, 404)

    # ----------
    # Helpers
    def send_jsend(self, data, success=True, status_code=None):
        """Send data in jsend format.

        The data parameter is any json dumpable Python object. Defaults status is
        success and default status_code is 200."""
        jsend = self.make_jsend(data, success)
        self.send_json(jsend, status_code)

    def make_jsend(self, data, success=True):
        """Transform any json dumpable Python object in a jsend string.

        Default status is success."""
        if success:
            status = 'success'
        else:
            status = 'failure'

        formatted = {'status': status, 'data': data}
        return json.dumps(formatted)

    def send_json(self, json_string, status_code=None):
        """Send some json with the correct headers and the given status code.

        Default status code is 200. The given json_string must be a valid json
        string."""
        if status_code is None:
            status_code = 200

        self.send_response(status_code)
        self.send_header("Access-Control-Allow-Origin", self.allow_origin)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/json; charset=%s" % encoding)
        self.send_header("Content-Length", str(len(json_string)))
        self.end_headers()

        self.wfile.write(json_string)

    def send_listdir(self, dirname):
        """Send the listdir result of the given dirname if it is in an
        authorized dir."""
        if not self.is_authorized_path(dirname):
            self.route_403()
            return
        elif os.path.isfile(dirname):
            self.route_400(dirname + ' is not a directory')
            return
        else:
            try:
                paths = []
                for item in os.listdir(dirname):
                    if not self.is_blacklisted_path(item):
                        entry = {}
                        entry['name'] = item
                        if os.path.normpath(os.path.relpath(dirname, os.getcwd())) == os.curdir:
                            entry['path'] = item
                        else:
                            entry['path'] = os.path.join(os.path.relpath(dirname, os.getcwd()), item)
                        entry['type'] = 'file' if os.path.isfile(os.path.join(dirname, item)) else 'dir'
                        paths.append(entry)
            except os.error:
                self.route_404()
                return

        self.send_jsend(paths)

    def send_file_content(self, filepath):
        """Send the content of filepath if it is in an authorized dir."""
        if not self.is_authorized_path(filepath):
            self.route_403()
            return
        elif not os.path.isfile(filepath):
            self.route_400(filepath + ' is not a file')
        else:
            try:
                # Always read in binary mode. Opening files in text mode may cause
                # newline translations, making the actual size of the content
                # transmitted *less* than the content-length!
                with open(os.path.realpath(filepath), 'rb') as fp:
                    file_content = fp.read()
                    file_stat = os.fstat(fp.fileno())
                    file_size = str(file_stat[6])
                    file_mtime = str(file_stat.st_mtime)
            except IOError:
                self.route_404()
                return

            entry = {'name': os.path.basename(filepath), 'content': file_content,
                    'size': file_size, 'mtime': file_mtime, 'type': 'file'}
            if os.path.normpath(os.path.relpath(filepath, os.getcwd())) == os.curdir:
                entry['path'] = filepath
            else:
                entry['path'] = os.path.relpath(filepath, os.getcwd())
            self.send_jsend(entry)

    def is_authorized_path(self, path):
        """Check that the given path is inside or under os.getcwd()."""
        if not os.path.exists(os.path.realpath(path)):
            return False
        elif self.is_blacklisted_path(path):
            return False
        else:
            return self.is_in_directory(path, os.getcwd())

    def is_in_directory(self, path, directory_path):
        """Check that path is inside directory_path or any of its
        subdirectories, following symlinks."""
        real_dir = os.path.realpath(directory_path)
        real_path = os.path.realpath(path)
        return os.path.commonprefix([real_path, real_dir]) == real_dir

    def is_authenticated(self):
        if (self.headers.getheader('Authorization') is None or
            self.headers.getheader('Authorization') != CONFIG['authentication_string']):
            print('Unauthorized request from ' + str(self.client_address))
            print('Request headers:\n' + str(self.headers))
            jsend = self.make_jsend('Unauthorized', False)

            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm=\"insert realm\"')
            # self.send_header("Access-Control-Allow-Origin", self.allow_origin)
            encoding = sys.getfilesystemencoding()
            self.send_header("Content-type", "text/json; charset=%s" % encoding)
            self.send_header("Content-Length", str(len(jsend)))
            self.end_headers()

            self.wfile.write(jsend)
            return False
        else:
            return True

    def is_blacklisted_path(self, path):
        """Is the given path in the BLACKLISTED_FILES collection?"""
        # return (path in BLACKLISTED_FILES)
        return (os.path.realpath(path) in [os.path.realpath(item) for item in BLACKLISTED_FILES])


def exist_conf_file():
    return os.path.exists(CONFIGURATION_FILENAME)


def startConnector(port):
    httpd = BaseHTTPServer.HTTPServer(('', port), ConnectorRequestHandler)

    print('Connector v' + __version__ + ' serving directory:\n' + os.getcwd() + '\nat port ' + str(port))
    httpd.serve_forever()


def main():
    global CONFIG
    port = 3000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    # Greetings.
    print(r"""
            .__                __        .__
       ____ |  | _____ _______|  | __    |__| ____
      / ___\|  | \__  \\_  __ \  |/ /    |  |/  _ \
     / /_/  >  |__/ __ \|  | \/    <     |  (  <_> )
     \___  /|____(____  /__|  |__|_ \ /\ |__|\____/
    /_____/           \/           \/ \/
            """)

    if exist_conf_file():
        with open(CONFIGURATION_FILENAME) as fp:
            CONFIG = json.load(fp)
    else:
        print("There is no '" + CONFIGURATION_FILENAME + "' configuration file in this directory yet.\n"
                "This might be the first time that you glarkconnect this directory.\n"
                "Please enter a username and password that will be required\n"
                "to access this connector from the glark.io editor.\n"
                "If you want to change these, simply delete the " + CONFIGURATION_FILENAME +
                "\nthat will be created in this directory.")
        username = raw_input('Username:')

        ask_again = True
        while ask_again:
            password1 = getpass.getpass('Password:')
            password2 = getpass.getpass('Re-enter Password:')
            if password1 == password2:
                ask_again = False
            else:
                print("Passwords do not match. Please try again.")

        # Build the config object and dump it to config file.
        realm = base64.b64encode(username + ':' + password1)
        authentication_string = 'Basic ' + realm
        CONFIG['authentication_string'] = authentication_string

        with open(CONFIGURATION_FILENAME, 'w') as fp:
            json.dump(CONFIG, fp)

    startConnector(port)


if __name__ == '__main__':
    main()
