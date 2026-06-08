import sys
import os

# Check where numpy is being imported from
try:
    import numpy as np
    print("numpy location:", np.__file__)
    print("numpy version:", np.__version__)
except Exception as e:
    print("numpy import failed:", e)
    print("sys.path:", sys.path)
    print("cwd:", os.getcwd())
