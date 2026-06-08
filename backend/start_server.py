"""
Startup wrapper that forces Python to use the venv site-packages exclusively,
preventing Anaconda from polluting sys.path and causing numpy conflicts.
"""
import sys
import os

# Get the venv site-packages path
venv_dir = os.path.join(os.path.dirname(__file__), "venv")
venv_site_packages = os.path.join(venv_dir, "Lib", "site-packages")

# Remove any paths from Anaconda (or other non-venv Python installs)
cleaned_paths = []
for p in sys.path:
    # Keep venv paths, current directory, and frozen importlib paths
    if (venv_dir in p or 
        p == '' or 
        p == os.path.dirname(__file__) or
        'frozen' in p.lower()):
        cleaned_paths.append(p)
    # Drop anything from Anaconda / other Python installs
    elif 'anaconda' in p.lower() or 'conda' in p.lower():
        pass  # skip
    else:
        cleaned_paths.append(p)

sys.path = cleaned_paths

# Ensure venv site-packages is first
if venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

# Now start the actual uvicorn server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # reload is incompatible with this wrapper
        log_level="info"
    )
