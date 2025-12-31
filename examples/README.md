# Test Examples

This directory contains sample GitHub event payloads for testing the agent locally.

## Files

- **test_event_pr.json**: Meaningful PR (should POST)
- **test_event_issue.json**: Feature request issue (should POST)
- **test_event_skip.json**: Trivial PR (should SKIP)

## Usage

### Test with PR Event

```bash
export GITHUB_EVENT_PATH=examples/test_event_pr.json
export GITHUB_TOKEN=your_token
export AI_API_KEY=your_key
export X_BEARER_TOKEN=your_token

python agent.py
```

### Expected Behavior

**test_event_pr.json** → AI should generate tweet like:
```
Fixed a race condition in our event scheduler. Queue wasn't thread-safe 🐛 
Added proper locking + tests. #opensource #python https://github.com/...
```

**test_event_issue.json** → AI should generate tweet like:
```
Working on dark mode support! 50+ users requested this 🌙 
Theme toggle + system preference detection coming soon. #webdev https://github.com/...
```

**test_event_skip.json** → AI should output:
```
SKIP
```

## Creating Custom Test Events

1. Trigger a real event in your repo
2. Download the event payload from GitHub Actions:
   - Go to Actions → Workflow run → "View workflow file"
   - The event payload is available in the workflow context
3. Save as JSON file
4. Test locally

## Dry Run Mode

To test without actually posting to X, modify `agent.py`:

```python
# Comment out the actual posting
# success = post_to_x(ai_response)

# Instead, just print
print(f"Would post: {ai_response}")
success = True
```
