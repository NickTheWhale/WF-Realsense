
# WF-Realsense

This repository contains two major applications: The client and ROI-Utility. The client
facilitates communication between an OPCUA server and an Intel Realsense D455 depth 
camera. The ROI-Utility is a gui that allows easy configuraion of the client application. 

## Acknowledgements

 - [OPCUA library](https://github.com/FreeOpcUa/python-opcua.git)
 - [Realsense library](https://github.com/IntelRealSense/librealsense.git)


## Features
#### Client
- 8 server-selectable region of interests
- Automatic restart in the event of server or camera disconnect
#### ROI-Utility
- Live depth preview
- Region of interest editor
- Export configuration file


## Installation
#### Currently all scripts are tested against Windows 10 Enterprise version 1909, build 18363.2274 and python 3.9.13
Install as standalone executable 

- [Releases](https://github.com/NickTheWhale/WF-Realsense/releases)

Install and run from source
```bash
  git clone https://github.com/NickTheWhale/WF-Realsense.git
  cd WF-Realsense
  python -m venv venv
  .\venv\scripts\activate
  python -m pip install -r requirements.txt
  cd client\app
  python main.py
```
    
## Workflow
- Create server nodes
  - Depth node - float
  - Invalid node - float
  - Deviation node - float
  - Select node - unsigned integer
  - Status - signed integer
  - Picture trigger (depracated) - boolean
  - Alive - boolean
- Configure settings with ROI Utility (note: anything done in the utility can also be done by manually creating 'configuration.ini'. Use 'defaultconfiguration.ini' as a template)
  - Enter server IP address (ex. opc.tcp://localhost:4840)
  - Enter node id's (ex. ns=3;s="DepthCameraOPC"."opc_roi_depth")
    - Free client software: https://www.unified-automation.com/ or https://github.com/FreeOpcUa/opcua-client-gui
  - Configure regions of interest (**important! you must ensure all regions are complete even if you are not going to use all 8**)
  - Save settings (**important! the client needs a file named 'configuration.ini' in order to run**)

## Screenshots

![Utility](fullscreen.jpg)

## Roadmap

- Proper auto-restart
- Ditch the ROI Utility for a web based viewer
  - Due to limitations of the usb camera connection, only one program may connect to the camera. In the future, a web based viewer can solve this issue by broadcasting the camera data with a web server
- Use networked Realsense cameras
- Add filter detection (more roi's, glob detection, etc.)
- Use something other than pyinstaller to be platform agnostic

## Authors

- [@NickTheWhale](https://github.com/NickTheWhale)
