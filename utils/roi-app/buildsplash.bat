cd /d H:\ && cd "intel realsense"\code && .\venv\scripts\activate && cd utils\roi-app && pyinstaller -F -w --clean --splash "H:\Intel Realsense\Code\utils\roi-app\assets\splash.png" --collect-data sv_ttk main.py -n "Depth Utility"
@pause
