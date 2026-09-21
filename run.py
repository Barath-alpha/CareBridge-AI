import os
import sys
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Detect if running under VS Code debugger (debugpy) to disable reloader and avoid SystemExit: 3
    is_debugger = sys.gettrace() is not None or 'debugpy' in sys.modules
    use_reloader = not is_debugger

    try:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=use_reloader)
    except SystemExit:
        pass
