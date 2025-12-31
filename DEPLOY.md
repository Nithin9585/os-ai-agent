# Deployment Guide

## Quick Deploy (3 Steps)

### Step 1: Add Secrets to GitHub

Go to your repo → Settings → Secrets and variables → Actions

Add these 5 secrets:

```
GEMINI_API_KEY          [your Gemini API key]
X_CONSUMER_KEY          [from X Developer Portal]
X_CONSUMER_SECRET       [from X Developer Portal]
X_ACCESS_TOKEN          [from X Developer Portal]
X_ACCESS_TOKEN_SECRET   [from X Developer Portal]
```

Get X credentials: https://developer.twitter.com → Your App → Keys and Tokens

### Step 2: Push Code

```bash
cd os-ai-agent
git init
git add .
git commit -m "AI agent"
git branch -M main
git remote add origin https://github.com/Nithin9585/your-repo.git
git push -u origin main
```

### Step 3: Test

1. Go to Actions tab
2. Click "Profile-Wide AI Agent"
3. Click "Run workflow"
4. Create a test issue in any repo
5. Run workflow again
6. Check X for tweet

## What Gets Posted

- PRs you open in any repo
- Issues you open in any repo  
- Meaningful changes only (AI filters trivial updates)

## Schedule

Runs every 15 minutes automatically.

Edit `.github/workflows/profile-monitor.yml` to change frequency.

Done!
