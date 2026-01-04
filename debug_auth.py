
import os
import sys
import time
import requests
import email.utils
from requests_oauthlib import OAuth1

def load_env_vars():
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"Loading {env_file}...")
        with open(env_file, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        os.environ[key.strip()] = value.strip()
                    except ValueError:
                        pass

def get_time_offset():
    """Calculate offset between local time and Google server time."""
    try:
        print("Checking time synchronization...")
        print(f"Local time: {time.time()} ({time.ctime()})")
        resp = requests.head("https://www.google.com", timeout=5)
        server_date = resp.headers.get("Date")
        if server_date:
            # Parse HTTP Date format (RFC 1123): e.g., "Tue, 15 Nov 1994 08:12:31 GMT"
            # parsedate_to_datetime returns awareness if timezone provided, but let's convert to timestamp
            # email.utils.parsedate_to_datetime handles it well
            dt = email.utils.parsedate_to_datetime(server_date)
            server_time = dt.timestamp()
            local_time = time.time()
            offset = server_time - local_time
            print(f"Server time: {server_time} ({dt})")
            print(f"Offset: {offset:.2f} seconds")
            
            if abs(offset) > 300: # 5 minutes
                print("WARNING: Significant time drift detected!")
                return offset
            else:
                print("Time is synchronized.")
                return 0
    except Exception as e:
        print(f"Failed to check time offset: {e}")
    return 0

def patch_time(offset):
    if offset == 0:
        return
    print(f"Patching time.time() with offset {offset:.2f}s")
    orig_time = time.time
    def mocked_time():
        return orig_time() + offset
    time.time = mocked_time

def verify_twitter_auth():
    print("-" * 40)
    print("Verifying Twitter Auth...")
    
    # Keys
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
    consumer_key = os.getenv("X_API_KEY")
    consumer_secret = os.getenv("X_API_KEY_SECRET")
    
    if not all([access_token, access_token_secret, consumer_key, consumer_secret]):
        print("ERROR: Missing keys in env.")
        # Print masked for debugging
        print(f"Token: {'Set' if access_token else 'Missing'}")
        print(f"Secret: {'Set' if access_token_secret else 'Missing'}")
        print(f"Key: {'Set' if consumer_key else 'Missing'}")
        print(f"Key Secret: {'Set' if consumer_secret else 'Missing'}")
        return

    auth = OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)
    
    url = "https://api.twitter.com/2/users/me"
    
    # User-Agent to pass WAF
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; OpenSourceAIAgent/1.0; +https://github.com/os-ai-agent)"
    }
    
    try:
        response = requests.get(url, auth=auth, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text[:500]}")
        
        if response.status_code == 200:
            print("SUCCESS! Auth working.")
        elif response.status_code == 401:
            print("FAILED: 401 Unauthorized (Check keys or time)")
        elif response.status_code == 403:
            print("FAILED: 403 Forbidden (WAF or Permissions)")
            
    except Exception as e:
        print(f"Request Error: {e}")

if __name__ == "__main__":
    load_env_vars()
    offset = get_time_offset()
    patch_time(offset)
    verify_twitter_auth()
