#!/usr/bin/env python3
"""
Profile Monitor - Fetches recent events from entire GitHub profile
"""

import json
import os
import requests
import sys
from datetime import datetime, timedelta

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME") or os.getenv("GITHUB_ACTOR")

STATE_FILE = "last_processed.json"


def load_state():
    """Load the last processed event timestamp."""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"}


def save_state(timestamp):
    """Save the last processed event timestamp."""
    with open(STATE_FILE, "w") as f:
        json.dump({"last_timestamp": timestamp}, f)


def fetch_user_events():
    """Fetch recent events from user's GitHub profile."""
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/events"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    print(f"Fetching events for user: {GITHUB_USERNAME}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        events = response.json()
        print(f"Found {len(events)} recent events")
        return events
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch events: {e}")
        return []


def filter_relevant_events(events, last_timestamp):
    """Filter for PR and Issue events that are newer than last_timestamp."""
    relevant_types = ["PullRequestEvent", "IssuesEvent"]
    relevant_actions = ["opened", "reopened"]
    
    filtered = []
    
    # Limit to strict 15 minute window
    time_limit = datetime.utcnow() - timedelta(minutes=15)
    
    # Sort events by time (newest first)
    events.sort(key=lambda x: x["created_at"], reverse=True)
    
    for event in events:
        event_time = datetime.fromisoformat(event["created_at"].replace('Z', '+00:00')).replace(tzinfo=None)
        
        # SKIP if older than 15 minutes
        if event_time < time_limit:
            continue
            
        # Also SKIP if we processed it before (strictly newer than last timestamp)
        last_ts_dt = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
        if event_time <= last_ts_dt:
            continue
        
        if event["type"] in relevant_types:
            payload = event.get("payload", {})
            action = payload.get("action", "")
            
            if action in relevant_actions:
                filtered.append(event)
                # STRICT RULE: Take only ONE event (the latest one)
                print("Found one valid recent event. Stopping search.")
                break
    
    print(f"Filtered to {len(filtered)} relevant event (Strict 15m limit, max 1 event)")
    return filtered


def convert_to_agent_format(event):
    """Convert GitHub event to format expected by agent.py."""
    event_type = event["type"]
    payload = event.get("payload", {})
    repo = event.get("repo", {})
    
    if event_type == "PullRequestEvent":
        pr = payload.get("pull_request", {})
        return {
            "action": payload.get("action"),
            "pull_request": {
                "html_url": pr.get("html_url"),
                "title": pr.get("title"),
                "body": pr.get("body"),
                "url": pr.get("url"),
                "user": pr.get("user", {})
            },
            "repository": {
                "full_name": repo.get("name"),
                "name": repo.get("name").split("/")[-1] if "/" in repo.get("name", "") else repo.get("name"),
                "owner": {"login": repo.get("name").split("/")[0] if "/" in repo.get("name", "") else ""}
            },
            "sender": payload.get("pull_request", {}).get("user", {})
        }
    elif event_type == "IssuesEvent":
        issue = payload.get("issue", {})
        return {
            "action": payload.get("action"),
            "issue": {
                "html_url": issue.get("html_url"),
                "title": issue.get("title"),
                "body": issue.get("body"),
                "user": issue.get("user", {}),
                "labels": issue.get("labels", [])
            },
            "repository": {
                "full_name": repo.get("name"),
                "name": repo.get("name").split("/")[-1] if "/" in repo.get("name", "") else repo.get("name"),
                "owner": {"login": repo.get("name").split("/")[0] if "/" in repo.get("name", "") else ""}
            },
            "sender": payload.get("issue", {}).get("user", {})
        }
    
    return None


def main():
    """Main profile monitoring logic."""
    print("=" * 60)
    print("Profile-Wide GitHub Event Monitor")
    print("=" * 60)
    
    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN not set")
        sys.exit(1)
    
    if not GITHUB_USERNAME:
        print("ERROR: GITHUB_USERNAME not set")
        sys.exit(1)
    
    state = load_state()
    last_timestamp = state["last_timestamp"]
    print(f"Looking for events after: {last_timestamp}")
    
    events = fetch_user_events()
    if not events:
        print("No events found")
        print("::set-output name=has_events::false")
        sys.exit(0)
    
    relevant_events = filter_relevant_events(events, last_timestamp)
    
    if not relevant_events:
        print("No new relevant events")
        print("::set-output name=has_events::false")
        sys.exit(0)
    
    latest_event = relevant_events[0]
    print(f"\nProcessing latest event:")
    print(f"   Type: {latest_event['type']}")
    print(f"   Repo: {latest_event['repo']['name']}")
    print(f"   Time: {latest_event['created_at']}")
    
    agent_event = convert_to_agent_format(latest_event)
    
    if not agent_event:
        print("ERROR: Failed to convert event")
        sys.exit(1)
    
    event_file = "current_event.json"
    with open(event_file, "w") as f:
        json.dump(agent_event, f, indent=2)
    
    # Save event timestamp for later (agent will save state on success)
    timestamp_file = "event_timestamp.txt"
    with open(timestamp_file, "w") as f:
        f.write(latest_event["created_at"])
    
    os.environ["GITHUB_EVENT_PATH"] = event_file
    
    print(f"Event saved to {event_file}")
    print("::set-output name=has_events::true")
    print("=" * 60)


if __name__ == "__main__":
    main()
