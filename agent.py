#!/usr/bin/env python3
"""
OpenSource AI Agent
Monitors GitHub events and intelligently posts to X using AI reasoning.
"""

import json
import os
import requests
import sys
import hashlib
import hmac
import base64
import secrets
import time
from urllib.parse import quote
from typing import Dict, Optional, Tuple

# Configuration
GITHUB_EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("OS_GITHUB_TOKEN")
AI_API_KEY = os.getenv("GEMINI_API_KEY")

# X API OAuth 1.0a credentials
X_ACCESS_TOKEN = os.getenv("ACESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("ACESS_TOKEN_SECRET")
X_CONSUMER_KEY = os.getenv("X_API_KEY")
X_CONSUMER_SECRET = os.getenv("OS_X_API_KEY_SECRET")

# AI API Configuration (Google Gemini)
AI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
AI_MODEL = "gemini-1.5-flash"
AI_TEMPERATURE = 0.7

# X API Configuration
X_API_URL = "https://api.twitter.com/2/tweets"


def validate_environment() -> None:
    """Validate all required environment variables are set."""
    required_vars = {
        "GITHUB_EVENT_PATH": GITHUB_EVENT_PATH,
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "GEMINI_API_KEY": AI_API_KEY,
        "ACESS_TOKEN": X_ACCESS_TOKEN,
        "ACESS_TOKEN_SECRET": X_ACCESS_TOKEN_SECRET,
        "X_API_KEY": X_CONSUMER_KEY,
        "OS_X_API_KEY_SECRET": X_CONSUMER_SECRET,
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    print("Environment validated")


def load_github_event() -> Dict:
    """Load and parse the GitHub event JSON."""
    try:
        with open(GITHUB_EVENT_PATH, "r", encoding="utf-8") as f:
            event = json.load(f)
        print(f"Loaded GitHub event from {GITHUB_EVENT_PATH}")
        return event
    except FileNotFoundError:
        print(f"ERROR: Event file not found: {GITHUB_EVENT_PATH}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in event file: {e}")
        sys.exit(1)


def extract_event_data(event: Dict) -> Optional[Tuple[str, str, str, str, str]]:
    """Extract relevant data from GitHub event."""
    is_pr = "pull_request" in event
    is_issue = "issue" in event
    
    if not (is_pr or is_issue):
        print("Event is not a PR or Issue. Exiting.")
        return None
    
    event_type = "PR" if is_pr else "Issue"
    repo = event["repository"]["full_name"]
    
    if is_pr:
        pr = event["pull_request"]
        link = pr["html_url"]
        title = pr["title"]
        body = pr.get("body", "") or ""
        diff_summary = fetch_pr_diff(pr["url"])
    else:
        issue = event["issue"]
        link = issue["html_url"]
        title = issue["title"]
        body = issue.get("body", "") or ""
        diff_summary = ""
    
    print(f"Extracted {event_type} data: {title[:50]}...")
    return event_type, repo, link, title, body, diff_summary


def fetch_pr_diff(pr_url: str) -> str:
    """Fetch PR diff summary from GitHub API."""
    try:
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3.diff"
        }
        response = requests.get(pr_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        diff = response.text[:3000]
        print(f"Fetched PR diff ({len(diff)} chars)")
        return diff
    except requests.RequestException as e:
        print(f"WARNING: Failed to fetch PR diff: {e}")
        return ""


def load_system_prompt() -> str:
    """Load the AI system prompt from prompt.txt."""
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            prompt = f.read().strip()
        print("Loaded system prompt")
        return prompt
    except FileNotFoundError:
        print("ERROR: prompt.txt not found")
        sys.exit(1)


def call_ai(system_prompt: str, user_prompt: str) -> str:
    """Call AI API to analyze the event and generate response."""
    try:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": combined_prompt
                }]
            }],
            "generationConfig": {
                "temperature": AI_TEMPERATURE,
                "maxOutputTokens": 300
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        api_url_with_key = f"{AI_API_URL}?key={AI_API_KEY}"
        
        print("Calling Gemini AI API...")
        response = requests.post(api_url_with_key, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        ai_response = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        print(f"AI Response: {ai_response[:100]}...")
        return ai_response
        
    except requests.RequestException as e:
        print(f"ERROR: AI API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def generate_oauth_signature(method: str, url: str, params: dict) -> dict:
    """Generate OAuth 1.0a signature for X API."""
    oauth_params = {
        "oauth_consumer_key": X_CONSUMER_KEY,
        "oauth_nonce": secrets.token_hex(32),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": X_ACCESS_TOKEN,
        "oauth_version": "1.0"
    }
    
    all_params = {**oauth_params, **params}
    
    sorted_params = sorted(all_params.items())
    param_string = "&".join([f"{quote(str(k), safe='')}={quote(str(v), safe='')}" for k, v in sorted_params])
    signature_base = f"{method}&{quote(url, safe='')}&{quote(param_string, safe='')}"
    
    signing_key = f"{quote(X_CONSUMER_SECRET, safe='')}&{quote(X_ACCESS_TOKEN_SECRET, safe='')}"
    
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), signature_base.encode(), hashlib.sha1).digest()
    ).decode()
    
    oauth_params["oauth_signature"] = signature
    return oauth_params


def post_to_x(tweet_text: str) -> bool:
    """Post tweet to X using OAuth 1.0a."""
    try:
        payload = {"text": tweet_text}
        
        oauth_params = generate_oauth_signature("POST", X_API_URL, {})
        
        auth_header = "OAuth " + ", ".join([
            f'{quote(k, safe="")}="{quote(v, safe="")}"'
            for k, v in sorted(oauth_params.items())
        ])
        
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json"
        }
        
        print("Posting to X...")
        response = requests.post(X_API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 201:
            tweet_data = response.json()
            tweet_id = tweet_data.get("data", {}).get("id", "unknown")
            print(f"Tweet posted successfully! ID: {tweet_id}")
            return True
        else:
            print(f"ERROR: Failed to post tweet: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"ERROR: X API error: {e}")
        return False


def main():
    """Main agent execution flow."""
    print("=" * 60)
    print("OpenSource AI Agent Starting...")
    print("=" * 60)
    
    validate_environment()
    event = load_github_event()
    
    event_data = extract_event_data(event)
    if not event_data:
        sys.exit(0)
    
    event_type, repo, link, title, body, diff_summary = event_data
    
    system_prompt = load_system_prompt()
    
    user_prompt = f"""
Event Type: {event_type}
Repository: {repo}
Title: {title}

Description:
{body[:1000]}

{f"Diff Summary:\n{diff_summary}" if diff_summary else ""}

Link: {link}
"""
    
    ai_response = call_ai(system_prompt, user_prompt)
    
    if ai_response.upper() == "SKIP":
        print("AI decided to SKIP this event")
        sys.exit(0)
    
    if len(ai_response) > 280:
        print(f"WARNING: Tweet too long ({len(ai_response)} chars), truncating...")
        ai_response = ai_response[:277] + "..."
    
    success = post_to_x(ai_response)
    
    if success:
        print("=" * 60)
        print("Agent completed successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("ERROR: Agent failed to post tweet")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
