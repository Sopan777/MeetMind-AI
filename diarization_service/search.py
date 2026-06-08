import os
import glob

print("Searching...")
for f in glob.glob('venv/Lib/site-packages/pyannote/**/*.py', recursive=True):
    try:
        with open(f, encoding='utf-8') as file:
            for i, line in enumerate(file):
                if 'get_audio_backend' in line:
                    print(f"{f}:{i+1}: {line.strip()}")
    except Exception as e:
        pass
print("Done.")
