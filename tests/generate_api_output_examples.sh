#!/bin/bash

# This script needs the httpie library. Get it with:
# pip install httpie

http GET  localhost:3000/connector
http -a lucho:verYseCure GET localhost:3000/connector
http -a lucho:verYseCure GET localhost:3000/connector/version

http -a lucho:verYseCure GET localhost:3000/connector/files
http -a lucho:verYseCure GET localhost:3000/connector/files/file1
http -a lucho:verYseCure GET localhost:3000/connector/files/subdirectory
http -a lucho:verYseCure GET localhost:3000/connector/files/subdirectory/file1
