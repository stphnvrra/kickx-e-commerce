import os
import sys

# Add the parent directory to sys.path to enable imports of root-level files
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from kickx_app import app

# Vercel expects a module-level variable named `app` pointing to the WSGI application
