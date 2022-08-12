cd /d H:\ && cd "intel realsense"\code && .\venv\scripts\activate && cd client\app && pyinstaller -F -w --clean main.py -n "Depth Client"
@pause