from app import create_app
from flask import request

class PathRewriteMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        # Vercel might pass '/api/index.py' or '/api/index'
        for prefix in ['/api/index.py', '/api/index']:
            if path.startswith(prefix):
                path = path[len(prefix):]
                break
        if not path:
            path = '/'
        environ['PATH_INFO'] = path
        return self.wsgi_app(environ, start_response)

app = create_app()
app.wsgi_app = PathRewriteMiddleware(app.wsgi_app)

print("DEBUG STARTUP: Flask url_map:")
print(app.url_map)

@app.before_request
def log_request_info():
    print(f"DEBUG REQUEST: PATH_INFO={request.environ.get('PATH_INFO')}, SCRIPT_NAME={request.environ.get('SCRIPT_NAME')}, request.path={request.path}")

