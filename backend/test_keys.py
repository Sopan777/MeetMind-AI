import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

async def test_whisper():
    api_key = os.getenv("WHISPER_API_KEY")
    api_url = os.getenv("WHISPER_API_URL", "https://api.openai.com/v1")
    if not api_key or "your_" in api_key:
        print("[FAIL] WHISPER_API_KEY is missing or not updated.")
        return False
    
    print(f"Testing Whisper API at {api_url}...")
    client = AsyncOpenAI(api_key=api_key, base_url=api_url)
    try:
        await client.models.list()
        print("[SUCCESS] Whisper API Key is VALID and working!")
        return True
    except Exception as e:
        print(f"[FAIL] Whisper API Key test FAILED: {e}")
        return False

async def test_nvidia():
    api_key = os.getenv("NVIDIA_API_KEY")
    api_url = os.getenv("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1")
    if not api_key or "your_" in api_key:
        print("[FAIL] NVIDIA_API_KEY is missing or not updated.")
        return False
    
    print(f"Testing NVIDIA Build API at {api_url}...")
    client = AsyncOpenAI(api_key=api_key, base_url=api_url)
    try:
        await client.models.list()
        print("[SUCCESS] NVIDIA Build API Key is VALID and working!")
        return True
    except Exception as e:
        print(f"[FAIL] NVIDIA API Key test FAILED: {e}")
        return False

async def main():
    print("--- API Key Verification ---")
    await test_whisper()
    print("-" * 20)
    await test_nvidia()
    print("----------------------------")

if __name__ == "__main__":
    asyncio.run(main())
