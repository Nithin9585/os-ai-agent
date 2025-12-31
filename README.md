# OpenSource AI Agent

Autonomous AI agent that monitors your GitHub activity and intelligently shares meaningful updates on X (Twitter).

## Features

- Monitors ALL your GitHub repositories
- AI-powered decision making (Google Gemini)
- Natural tweet generation
- OAuth 1.0a authentication for X
- Runs automatically every 15 minutes

## Setup

### 1. Add GitHub Secrets

Go to repo Settings → Secrets and variables → Actions

Add these 5 secrets:
- `GEMINI_API_KEY` - Your Gemini API key
- `X_CONSUMER_KEY` - X API Key
- `X_CONSUMER_SECRET` - X API Secret Key
- `X_ACCESS_TOKEN` - X Access Token
- `X_ACCESS_TOKEN_SECRET` - X Access Token Secret

### 2. Push Code

```bash
git init
git add .
git commit -m "Add AI agent"
git branch -M main
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
```

### 3. Trigger Workflow

Go to Actions tab → Profile-Wide AI Agent → Run workflow

## How It Works

1. Every 15 minutes, fetches your recent GitHub events
2. Filters for new PRs/Issues (opened/reopened)
3. AI analyzes and decides SKIP or POST
4. Posts natural tweet to X using OAuth 1.0a

## Files

- `agent.py` - Main agent logic
- `profile_monitor.py` - Profile-wide event fetcher
- `prompt.txt` - AI instructions
- `.github/workflows/profile-monitor.yml` - Scheduler

## Customization

Edit `prompt.txt` to change tweet style, tone, or decision criteria.

Change check frequency in `.github/workflows/profile-monitor.yml`:
- Every 15 min: `*/15 * * * *`
- Every 30 min: `*/30 * * * *`
- Every hour: `0 * * * *`

## License

MIT
