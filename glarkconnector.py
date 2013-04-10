#!/usr/bin/python
"""Connector for the glark.io editor. """

__version__ = "0.1"

import BaseHTTPServer
import base64
import getpass
import json
import os
import re
import sys

CONFIGURATION_FILENAME = '.glarkconnector.conf'


class ConnectorRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Request handler exposing a REST api to the underlying filesystem"""

    server_version = "glarkconnector/" + __version__
    allow_origin = "http://glark.io"
    # allow_origin = "*" # Allow any origin (not for production!)

    def do_GET(self):
        """Serve a GET request."""
        # Route request.
        print('Request path: ' + self.path)
        # print('Request headers:\n' + str(self.headers))
        if (self.path == '/connector/secure'):
            if self.is_authenticated():
                self.send_jsend('welcome')
        elif (self.path == '/connector'):
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
        self.send_header("Access-Control-Allow-Headers", "accept, origin, x-requested-with")
        self.end_headers()

    def do_HEAD(self):
        """Serve a HEAD request."""
        raise NotImplemented

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
        commands['get_file_content'] = base_url + '/files/{filename}'
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
                    print('PUT request body:\n' + body)

                    body = json.loads(body)

                    # Check body consistency.
                    if not 'filename' in body:
                        self.route_400("body must contain a 'filename' field")
                    if not 'content' in body:
                        self.route_400("body must contain a 'content' field")

                    new_filename = body['filename']
                    if not self.is_authorized_path(new_filename):
                        self.route_403()
                        return

                    fp.write(str(body['content']))

                # Now check if the file must be renamed.
                if os.path.realpath(new_filename) != os.path.realpath(requested_file):
                    os.rename(os.path.realpath(requested_file), os.path.realpath(new_filename))

                # If everything was fine, send back the new content of the file.
                self.send_file_content(new_filename)

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
        else:
            try:
                paths = os.listdir(dirname)
            except os.error:
                self.route_404()
                return

        self.send_jsend(paths)

    def send_file_content(self, filename):
        """Send the content of filename if it is in an authorized dir."""
        if not self.is_authorized_path(filename):
            self.route_403()
            return
        else:
            try:
                # Always read in binary mode. Opening files in text mode may cause
                # newline translations, making the actual size of the content
                # transmitted *less* than the content-length!
                with open(os.path.realpath(filename), 'rb') as fp:
                    file_content = fp.read()
                    file_stat = os.fstat(fp.fileno())
                    file_size = str(file_stat[6])
                    file_mtime = str(file_stat.st_mtime)
            except IOError:
                self.route_404()
                return

            data = {'filename': filename, 'content': file_content, 'size': file_size, 'mtime': file_mtime}
            self.send_jsend(data)

    def is_authorized_path(self, path):
        """Check that the given path is inside or under os.getcwd()."""
        return self.is_in_directory(path, os.getcwd())

    def is_in_directory(self, path, directory_path):
        """Check that path is inside directory_path or any of its
        subdirectories, following symlinks."""
        real_dir = os.path.realpath(directory_path)
        real_path = os.path.realpath(path)
        return os.path.commonprefix([real_path, real_dir]) == real_dir

    def is_authenticated(self):
        # Build the authentication string.
        with open(CONFIGURATION_FILENAME) as fp:
            authentication_string = json.load(fp)
            print authentication_string

        if (self.headers.getheader('Authorization') is None or
            self.headers.getheader('Authorization') != authentication_string):
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


def exist_conf_file():
    return os.path.exists(CONFIGURATION_FILENAME)


def startConnector(port):
    httpd = BaseHTTPServer.HTTPServer(('', port), ConnectorRequestHandler)

    print('Serving directory:\n' + os.getcwd() + '\nat port ' + str(port))
    httpd.serve_forever()


def main():
    port = 3000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    if not exist_conf_file():
        print(r"""
                .__                __        .__
           ____ |  | _____ _______|  | __    |__| ____
          / ___\|  | \__  \\_  __ \  |/ /    |  |/  _ \
         / /_/  >  |__/ __ \|  | \/    <     |  (  <_> )
         \___  /|____(____  /__|  |__|_ \ /\ |__|\____/
        /_____/           \/           \/ \/
                """)
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

        # Dump the authentication string in the conf file.
        realm = base64.b64encode(username + ':' + password1)
        authentication_string = 'Basic ' + realm
        with open(CONFIGURATION_FILENAME, 'w') as fp:
            json.dump(authentication_string, fp)

    startConnector(port)


if __name__ == '__main__':
    main()
