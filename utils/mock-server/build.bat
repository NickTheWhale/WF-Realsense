cd /d H:\ && cd "intel realsense"\code && .\venv\scripts\activate && cd utils\mock-server && pyinstaller -F --clean server-data.py -n "Mock Server"
@pause