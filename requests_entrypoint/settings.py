import os

BLOCKED_NAMES = os.getenv("BLOCKED_NAMES", "setup.py,__init__.py,__main__.py,main.py").split(",")
