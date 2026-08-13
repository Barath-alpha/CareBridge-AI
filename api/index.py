from app import create_app
from flask import request

app = create_app()

print("DEBUG STARTUP: Flask url_map:")
print(app.url_map)

@app.before_request
def log_request_info():
    print(f"DEBUG REQUEST: PATH_INFO={request.environ.get('PATH_INFO')}, SCRIPT_NAME={request.environ.get('SCRIPT_NAME')}, request.path={request.path}")

