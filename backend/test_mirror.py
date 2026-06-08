import requests
try:
    r = requests.get('https://hf-mirror.com', timeout=5)
    print("Mirror Status:", r.status_code)
except Exception as e:
    print("Mirror failed:", e)
