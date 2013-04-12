#!/bin/bash

# This script needs the httpie library. Get it with:
# pip install httpie

http --verbose --pretty=format GET  localhost:3000/connector
echo -e '\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector
echo -e '\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector/version
echo -e '\n'

http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector/files
echo -e '\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector/files/file1
echo -e '\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector/files/subdirectory
echo -e '\n'
http --verbose --pretty=format --auth lucho:verYseCure GET localhost:3000/connector/files/subdirectory/file1
echo -e '\n'
