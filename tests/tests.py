#!/usr/bin/python
"""Unit tests for the glarkconnector project.

To run the tets, a glarkconnector must be running at CONNECTOR_URL, serving the
directory 'fixtures'."""


import json
import os
import requests
from requests.auth import HTTPBasicAuth as Auth
import unittest


# The url to use to connect to the running glarkconnector.
CONNECTOR_URL = 'http://localhost:3000'


class GlarkConnectorTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        if os.path.exists('fixtures/renamed_file'):
            os.remove('fixtures/renamed_file')
        with open('fixtures/file1', 'w') as fp:
            fp.write('This is fixtures/file1')

    def assertIsJsend(self, json):
        """Assert that the given json responds to the jsend format."""
        self.assertIn('status', json)
        self.assertIn('data', json)
        self.assertTrue(len(json) == 2)

    def assertIsSuccessfulJsend(self, json):
        """Assert that the given json is a valid jsend with a success status."""
        self.assertIsJsend(json)
        self.assertTrue(json['status'] == 'success')

    def assertIsUnsuccessfulJsend(self, json):
        """Assert that the given json is a valid jsend with a failure status."""
        self.assertIsJsend(json)
        self.assertTrue(json['status'] == 'failure')

    def test_get_unauthenticated(self):
        res = requests.get(CONNECTOR_URL + '/connector')
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertTrue(res.status_code == 401)

        self.assertIsUnsuccessfulJsend(res.json())

    def test_put_unauthenticated(self):
        res = requests.put(CONNECTOR_URL + '/connector')
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertTrue(res.status_code == 401)

        self.assertIsUnsuccessfulJsend(res.json())

    def test_get_commands(self):
        res = requests.get(CONNECTOR_URL + '/connector', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

    def test_get_server_version(self):
        res = requests.get(CONNECTOR_URL + '/connector/version', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data.startswith('glarkconnector/'))

    def test_get_files(self):
        res = requests.get(CONNECTOR_URL + '/connector/files', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        jsend = res.json()
        jsend_ref = {"status": "success", "data": [{"path": ".glarkconnector.conf", "type": "file", "name": ".glarkconnector.conf"}, {"path": "subdirectory", "type": "dir", "name": "subdirectory"}, {"path": "subdirectory with spaces", "type": "dir", "name": "subdirectory with spaces"}, {"path": "file1", "type": "file", "name": "file1"}, {"path": "file2", "type": "file", "name": "file2"}]}

        print 'jsend:'
        print json.dumps(jsend)
        print 'jsend_ref:'
        print json.dumps(jsend_ref)
        print ''
        self.assertTrue(json.dumps(jsend) == json.dumps(jsend_ref))

    def test_list_dir(self):
        res = requests.get(CONNECTOR_URL + '/connector/files/subdirectory', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        jsend = res.json()
        jsend_ref = {"status": "success", "data": [{"path": "subdirectory/empty_subdirectory", "type": "dir", "name": "empty_subdirectory"}, {"path": "subdirectory/file1", "type": "file", "name": "file1"}, {"path": "subdirectory/file2", "type": "file", "name": "file2"}]}
        print 'jsend:'
        print json.dumps(jsend)
        print 'jsend_ref:'
        print json.dumps(jsend_ref)
        print ''
        self.assertTrue(json.dumps(jsend) == json.dumps(jsend_ref))

    def test_get_file(self):
        res = requests.get(CONNECTOR_URL + '/connector/files/file1', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        with open('fixtures/file1') as fp:
            file1_content = fp.read()

        data = res.json()['data']
        self.assertTrue(data['content'] == file1_content)

    def test_put_file_content(self):
        """Test sending new file content."""
        with open('fixtures/file1') as fp:
            initial_content = fp.read()
        new_content = 'This has been modified'

        payload = {'path': 'file1', 'content': new_content}
        payload = json.dumps(payload)
        res = requests.put(CONNECTOR_URL + '/connector/files/file1',
                            data=payload, auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        with open('fixtures/file1') as fp:
            current_content = fp.read()

        data = res.json()['data']
        self.assertTrue(data['content'] == current_content)

        # Get back to initial state.
        with open('fixtures/file1', 'w') as fp:
            fp.write(initial_content)

    def test_put_file_content_in_subdirectory(self):
        """Test sending new file content for file in subdirectory."""
        with open('fixtures/subdirectory/file1') as fp:
            initial_content = fp.read()
        new_content = 'This has been modified'

        payload = {'path': 'subdirectory/file1', 'content': new_content}
        payload = json.dumps(payload)
        res = requests.put(CONNECTOR_URL + '/connector/files/subdirectory/file1',
                            data=payload, auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        with open('fixtures/subdirectory/file1') as fp:
            current_content = fp.read()

        data = res.json()['data']
        self.assertTrue(data['content'] == current_content)

        # Get back to initial state.
        with open('fixtures/subdirectory/file1', 'w') as fp:
            fp.write(initial_content)

    def test_put_rename_file(self):
        with open('fixtures/file1') as fp:
            initial_content = fp.read()

        payload = {'path': 'renamed_file', 'content': initial_content}
        payload = json.dumps(payload)
        res = requests.put(CONNECTOR_URL + '/connector/files/file1',
                            data=payload, auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertTrue(res.status_code == 400)

        self.assertIsUnsuccessfulJsend(res.json())

        self.assertTrue(os.path.exists('fixtures/file1'))
        self.assertFalse(os.path.exists('fixtures/renamed_file'))

    def test_get_bad_request(self):
        res = requests.get(CONNECTOR_URL + '/invalid_route', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertTrue(res.status_code == 400)

        self.assertIsUnsuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data == "Bad request")

    def test_put_bad_request(self):
        res = requests.put(CONNECTOR_URL + '/invalid_route', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertTrue(res.status_code == 400)

        self.assertIsUnsuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data == "Bad request")


if __name__ == '__main__':
    unittest.main()
