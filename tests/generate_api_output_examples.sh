#!/bin/bash

# This script needs the httpie library. Get it with:
# pip install httpie

echo -e 'Route: /connector\n'
http --verbose --pretty=format GET  localhost:3000/connector

echo -e '\n\n----------'
echo -e 'Route: /connector\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector

echo -e '\n\n----------'
echo -e 'Route: /connector/version\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector/version

echo -e '\n\n----------'
echo -e 'Route: /connector/files\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector/files

echo -e '\n\n----------'
echo -e 'Route: /connector/files/file1\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector/files/file1

echo -e '\n\n----------'
echo -e 'Route: /connector/files/subdirectory\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector/files/subdirectory

echo -e '\n\n----------'
echo -e 'Route: /connector/files/subdirectory/file1\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector/files/subdirectory/file1
