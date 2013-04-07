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

    def test_get_files(self):
        res = requests.request('GET', CONNECTOR_URL + '/files')
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(json.dumps(data) == json.dumps(os.listdir('fixtures')))

    def test_get_file(self):
        res = requests.request('GET', CONNECTOR_URL + '/files/file1')
        self.assertTrue(res is not None)
        self.assertTrue(res.ok)
        self.assertTrue(res.status_code == 200)

        self.assertIsSuccessfulJsend(res.json())

        with open('fixtures/file1') as fp:
            file1_content = fp.read()

        data = res.json()['data']
        self.assertTrue(data['content'] == file1_content)

    def test_invalid_api_route(self):
        res = requests.request('GET', CONNECTOR_URL + '/invalid_route')
        self.assertTrue(res is not None)
        self.assertFalse(res.ok)
        self.assertTrue(res.status_code == 400)

        self.assertIsUnsuccessfulJsend(res.json())

        data = res.json()['data']
        self.assertTrue(data == "Not a valid api route")



if __name__ == '__main__':
    unittest.main()
