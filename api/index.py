import sys
import os

# Add v1/backend to Python search path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "v1", "backend"))

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import the Flask application instance
from app import app

# Expose WSGI application handler for Vercel serverless runtime
handler = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
