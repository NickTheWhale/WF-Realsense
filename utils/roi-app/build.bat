cd /d H:\ && cd "intel realsense"\code && .\venv\scripts\activate && cd utils\roi-app && pyinstaller -F -w --clean --collect-data sv_ttk main.py -n "Client Utility"
@pause