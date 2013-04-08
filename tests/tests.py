#!/usr/bin/python
"""Unit tests for the glarkconnector project.

To run the tets, a glarkconnector must be running at CONNECTOR_URL, serving the
directory 'fixtures'."""


import json
import os
import requests
import unittest


# The url to use to connect to the running glarkconnector.
CONNECTOR_URL = 'http://localhost:3000'


class GlarkConnectorTest(unittest.TestCase):
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

    def test_get_commands(self):
        res = requests.get(CONNECTOR_URL + '/connector')
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

    def test_get_server_version(self):
        res = requests.get(CONNECTOR_URL + '/connector/version')
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data.startswith('glarkconnector/'))

    def test_get_files(self):
        res = requests.get(CONNECTOR_URL + '/connector/files')
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(json.dumps(data) == json.dumps(os.listdir('fixtures')))

    def test_get_file(self):
        res = requests.get(CONNECTOR_URL + '/connector/files/file1')
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

        payload = {'filename': 'file1', 'content': new_content}
        payload = json.dumps(payload)
        res = requests.put(CONNECTOR_URL + '/connector/files/file1', data=payload)
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

    def test_put_rename_file(self):
        with open('fixtures/file1') as fp:
            initial_content = fp.read()

        payload = {'filename': 'renamed_file', 'content': initial_content}
        payload = json.dumps(payload)
        res = requests.put(CONNECTOR_URL + '/connector/files/file1', data=payload)
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        self.assertFalse(os.path.exists('fixtures/file1'))
        self.assertTrue(os.path.exists('fixtures/renamed_file'))

        with open('fixtures/renamed_file') as fp:
            current_content = fp.read()

        data = res.json()['data']
        self.assertTrue(data['content'] == current_content)
        self.assertTrue(data['filename'] == 'renamed_file')

        # Get back to initial state.
        with open('fixtures/file1', 'w') as fp:
            fp.write(initial_content)

    def test_get_bad_request(self):
        res = requests.get(CONNECTOR_URL + '/invalid_route')
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertTrue(res.status_code == 400)

        self.assertIsUnsuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data == "Bad request")

    def test_put_bad_request(self):
        res = requests.put(CONNECTOR_URL + '/invalid_route')
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertTrue(res.status_code == 400)

        self.assertIsUnsuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data == "Bad request")


if __name__ == '__main__':
    unittest.main()
