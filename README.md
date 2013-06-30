###Connector for the glark.io editor###

[![Build Status](https://travis-ci.org/Bluefinch/glarkconnector.png)](https://travis-ci.org/Bluefinch/glarkconnector)

The glarkconnector is used to edit remote files with the [glark.io](https://github.com/Bluefinch/glark.io) editor.
Just fire a glarkconnector in a directory of your choice:
```bash
cd ~/my/dev/project
python glarkconnector.py
```
Then go to your glark.io editor instance and connect it to your running glarkconnector (click the gear icon in the upper left corner of the editor). The files in your glarkconnected directory are now available for remote editing!  
The glarkconnector only needs Python without any dependency to run, so it can run almost anywhere.  
Access to the files is secured by basic authentication.
