#!/usr/bin/python
"""Unit tests for the glarkconnector project.

To run the tets, a glarkconnector must be running at CONNECTOR_URL, serving the
directory 'fixtures'."""


from requests.auth import HTTPBasicAuth as Auth
import json
import os
import requests
import shutil
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
        if os.path.exists('fixtures/new_file'):
            os.remove('fixtures/new_file')
        if os.path.exists('fixtures/subdirectory/new_subdirectory'):
            shutil.rmtree('fixtures/subdirectory/new_subdirectory')

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
        self.assertEquals(res.status_code, 401)

        self.assertIsUnsuccessfulJsend(res.json())

    def test_put_unauthenticated(self):
        res = requests.put(CONNECTOR_URL + '/connector')
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertEquals(res.status_code, 401)

        self.assertIsUnsuccessfulJsend(res.json())

    def test_get_commands(self):
        res = requests.get(CONNECTOR_URL + '/connector', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertEquals(res.status_code, 200)

        self.assertIsSuccessfulJsend(res.json())

    def test_get_server_version(self):
        res = requests.get(CONNECTOR_URL + '/connector/version', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertEquals(res.status_code, 200)

        self.assertIsSuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data.startswith('glarkconnector/'))

    def test_get_files(self):
        res = requests.get(CONNECTOR_URL + '/connector/files', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertEquals(res.status_code, 200)

        self.assertIsSuccessfulJsend(res.json())

        jsend = res.json()

        self.assertEquals(len(jsend['data']), 4)
        foundFilesCount = 0
        for item in jsend['data']:
            if item['name'] == 'subdirectory':
                self.assertTrue(item['path'] == 'subdirectory')
                self.assertTrue(item['type'] == 'dir')
                foundFilesCount += 1
            if item['name'] == 'file1':
                self.assertTrue(item['path'] == 'file1')
                self.assertTrue(item['type'] == 'file')
                foundFilesCount += 1

        self.assertEquals(foundFilesCount, 2)

    def test_list_dir(self):
        res = requests.get(CONNECTOR_URL + '/connector/files/subdirectory', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertEquals(res.status_code, 200)

        self.assertIsSuccessfulJsend(res.json())

        jsend = res.json()

        self.assertEquals(len(jsend['data']), 3)
        foundFilesCount = 0
        for item in jsend['data']:
            if item['name'] == 'subsubdirectory':
                self.assertTrue(item['path'] == 'subdirectory/subsubdirectory')
                self.assertTrue(item['type'] == 'dir')
                foundFilesCount += 1
            if item['name'] == 'file3':
                self.assertTrue(item['path'] == 'subdirectory/file3')
                self.assertTrue(item['type'] == 'file')
                foundFilesCount += 1

        self.assertEquals(foundFilesCount, 2)

    def test_get_file(self):
        res = requests.get(CONNECTOR_URL + '/connector/files/file1', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertEquals(res.status_code, 200)

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

        payload = {'content': new_content}
        payload = json.dumps(payload)
        res = requests.put(CONNECTOR_URL + '/connector/files/file1',
                            data=payload, auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertEquals(res.status_code, 200)

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
        with open('fixtures/subdirectory/file3') as fp:
            initial_content = fp.read()
        new_content = 'This has been modified'

        payload = {'content': new_content}
        payload = json.dumps(payload)
        res = requests.put(CONNECTOR_URL + '/connector/files/subdirectory/file3',
                            data=payload, auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertEquals(res.status_code, 200)

        self.assertIsSuccessfulJsend(res.json())

        with open('fixtures/subdirectory/file3') as fp:
            current_content = fp.read()

        data = res.json()['data']
        self.assertTrue(data['content'] == current_content)

        # Get back to initial state.
        with open('fixtures/subdirectory/file3', 'w') as fp:
            fp.write(initial_content)

    def test_post_new_file(self):
        """Test creating a new file."""
        payload = {'content': 'new file at fixtures/new_file'}
        payload = json.dumps(payload)
        res = requests.post(CONNECTOR_URL + '/connector/files/new_file',
                            data=payload, auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertEquals(res.status_code, 200)

        self.assertIsSuccessfulJsend(res.json())

        with open('fixtures/new_file') as fp:
            current_content = fp.read()

        data = res.json()['data']
        self.assertTrue(data['content'] == current_content)

        # Get back to initial state.
        os.remove('fixtures/new_file')

    def test_post_new_file_while_existing(self):
        """Test trying to create a file that already exists."""
        with open('fixtures/new_file', 'w') as fp:
            fp.write('touched')

        payload = {'content': 'new file at fixtures/new_file'}
        payload = json.dumps(payload)
        res = requests.post(CONNECTOR_URL + '/connector/files/new_file',
                            data=payload, auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertEquals(res.status_code, 400)

        self.assertIsUnsuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data == "Bad request: File 'new_file' already exists")

        # Get back to initial state.
        os.remove('fixtures/new_file')

    def test_post_new_file_in_subdirectory(self):
        """Test creating a new file in a non existing subdirectory."""
        payload = {'content': 'new file at fixtures/subdirectory/new_subdirectory/new_subsubdirectory/new_file'}
        payload = json.dumps(payload)
        res = requests.post(CONNECTOR_URL + '/connector/files/subdirectory/new_subdirectory/new_subsubdirectory/new_file',
                            data=payload, auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertEquals(res.status_code, 200)

        self.assertIsSuccessfulJsend(res.json())

        with open('fixtures/subdirectory/new_subdirectory/new_subsubdirectory/new_file') as fp:
            current_content = fp.read()

        data = res.json()['data']
        self.assertTrue(data['content'] == current_content)

        # Get back to initial state.
        shutil.rmtree('fixtures/subdirectory/new_subdirectory')

    def test_get_bad_request(self):
        res = requests.get(CONNECTOR_URL + '/invalid_route', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertEquals(res.status_code, 400)

        self.assertIsUnsuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data == "Bad request")

    def test_put_bad_request(self):
        res = requests.put(CONNECTOR_URL + '/invalid_route', auth=Auth('lucho', 'verYseCure'))
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertEquals(res.status_code, 400)

        self.assertIsUnsuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data == "Bad request")


if __name__ == '__main__':
    unittest.main()
