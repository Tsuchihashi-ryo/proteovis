import os
from __init__ import create_app

# The application's entry point for Gunicorn
app = create_app()

if __name__ == '__main__':
    # This is for local development running, not for production
    # In production, Gunicorn will be used as the WSGI server
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
