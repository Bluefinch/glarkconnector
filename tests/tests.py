#!/usr/bin/python
import os
import unittest
import requests


# The url to use to connect to the running glarkconnector.
CONNECTOR_URL = 'http://localhost:3000'


class GlarkConnectorTest(unittest.TestCase):
    def test_get_files(self):
        res = requests.request('GET', CONNECTOR_URL + '/files')
        print(res.json())
        self.assertTrue(res is not None)


if __name__ == '__main__':
    unittest.main()
