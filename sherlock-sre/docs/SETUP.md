# Sherlock SRE - Setup Guide

Complete guide to get Sherlock up and running.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Running Modes](#running-modes)
5. [Slack Setup](#slack-setup)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- **Python 3.11+**
- **kubectl** configured with access to your Kubernetes cluster
- **Anthropic API key** (get from https://console.anthropic.com/)

### Optional (for full features)
- **Slack workspace** (for bot interface)
- **Docker** (for containerized deployment)
- **Kubernetes cluster** (for production deployment)

---

## Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
cd sherlock-sre

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env and add your API keys
# Minimum required:
#   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### 3. Test with CLI

```bash
# Check if kubectl works
kubectl get pods

# Run cluster health check
python -m src.cli health

# Try an investigation
python -m src.cli investigate "Why is my pod crashlooping?"
```

That's it! You now have a working Sherlock CLI.

---

## Configuration

### Environment Variables

All configuration is done via `.env` file or environment variables.

#### Required Settings

```bash
# AI/ML
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here  # Required!
```

#### Kubernetes Settings

```bash
# Leave empty to use default kubeconfig or in-cluster config
KUBECONFIG_PATH=

# Or specify path
KUBECONFIG_PATH=/path/to/kubeconfig
```

#### Slack Settings (Optional)

```bash
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token
SLACK_SIGNING_SECRET=your-secret
SLACK_CHANNEL=#incidents
```

#### Database Settings (Future - Phase 2)

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sherlock
POSTGRES_USER=sherlock
POSTGRES_PASSWORD=your-password

REDIS_HOST=localhost
REDIS_PORT=6379
```

#### Feature Flags

```bash
# Safety first! Keep auto-remediation disabled until you trust it
ENABLE_AUTO_REMEDIATION=false

# Learning from incidents (Phase 3)
ENABLE_PREDICTIVE_ALERTS=true
ENABLE_INCIDENT_LEARNING=true
```

#### Application Settings

```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
ENVIRONMENT=development  # development, staging, production
```

---

## Running Modes

Sherlock can run in multiple modes depending on your needs.

### Mode 1: CLI (Development & Testing)

**Use case:** Testing, development, one-off investigations

```bash
# Activate virtual environment
source venv/bin/activate

# Run investigations
python -m src.cli investigate "API is returning 502s"

# Check cluster health
python -m src.cli health

# Run diagnostics
python -m src.cli diagnostics

# Save results to JSON
python -m src.cli investigate "pod issues" --json results.json
```

**Pros:**
- Quick to test
- No Slack setup needed
- Good for debugging

**Cons:**
- Manual invocation
- No persistent monitoring

---

### Mode 2: Slack Bot (Recommended for Teams)

**Use case:** Team collaboration, conversational interface

#### Prerequisites
- Slack workspace admin access
- Ability to create Slack apps

#### Setup Steps

**1. Create Slack App**

Go to https://api.slack.com/apps and click "Create New App"

**2. Configure App Manifest**

Use this manifest (replace `YOUR_WORKSPACE` with your workspace name):

```yaml
display_information:
  name: Sherlock SRE
  description: AI-Powered Incident Investigation Copilot
  background_color: "#2c2d30"

features:
  bot_user:
    display_name: Sherlock
    always_online: true

oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - chat:write
      - chat:write.public
      - im:history
      - im:read
      - im:write

settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.im
  interactivity:
    is_enabled: true
  org_deploy_enabled: false
  socket_mode_enabled: true
```

**3. Get Tokens**

- Go to "OAuth & Permissions" → Copy **Bot User OAuth Token** → Set as `SLACK_BOT_TOKEN`
- Go to "Basic Information" → Generate **App-Level Token** (with `connections:write` scope) → Set as `SLACK_APP_TOKEN`
- Go to "Basic Information" → Copy **Signing Secret** → Set as `SLACK_SIGNING_SECRET`

**4. Install App to Workspace**

- Go to "Install App"
- Click "Install to Workspace"
- Authorize the app

**5. Start Sherlock Bot**

```bash
# Make sure tokens are in .env
source venv/bin/activate
python -m src.main
```

You should see:
```
✅ Sherlock is ready!
Starting Slack bot... (Ctrl+C to stop)
⚡️ Bolt app is running!
```

**6. Test in Slack**

```
# In any channel, invite the bot first
/invite @sherlock

# Then try:
@sherlock help
@sherlock investigate API is slow
```

---

### Mode 3: Docker (Isolated Environment)

**Use case:** Consistent environment, easy deployment

```bash
# Build image
docker build -t sherlock-sre:latest -f deploy/docker/Dockerfile .

# Run with environment file
docker run --rm \
  --env-file .env \
  -v ~/.kube:/root/.kube:ro \
  sherlock-sre:latest
```

---

### Mode 4: Kubernetes (Production)

**Use case:** Production deployment, high availability

```bash
# 1. Create namespace
kubectl create namespace sherlock

# 2. Create secrets
kubectl create secret generic sherlock-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-your-key \
  --from-literal=SLACK_BOT_TOKEN=xoxb-your-token \
  --from-literal=SLACK_APP_TOKEN=xapp-your-token \
  --from-literal=SLACK_SIGNING_SECRET=your-secret \
  -n sherlock

# 3. Deploy
kubectl apply -f deploy/kubernetes/ -n sherlock

# 4. Check logs
kubectl logs -f deployment/sherlock -n sherlock
```

---

## Slack Setup (Detailed)

### Creating a Slack App

1. **Go to Slack API Dashboard**
   - Visit https://api.slack.com/apps
   - Click "Create New App"
   - Choose "From scratch"
   - Name: "Sherlock SRE"
   - Pick your workspace

2. **Enable Socket Mode**
   - Go to "Socket Mode" in sidebar
   - Toggle "Enable Socket Mode" to ON
   - Create app-level token with scope `connections:write`
   - Save this as `SLACK_APP_TOKEN`

3. **Configure Bot**
   - Go to "OAuth & Permissions"
   - Add these Bot Token Scopes:
     - `app_mentions:read` - Read mentions
     - `chat:write` - Send messages
     - `chat:write.public` - Send to any channel
     - `im:history` - Read DMs
     - `im:read` - Read DM channel info
     - `im:write` - Send DMs

4. **Subscribe to Events**
   - Go to "Event Subscriptions"
   - Enable Events
   - Subscribe to bot events:
     - `app_mention`
     - `message.im`

5. **Install to Workspace**
   - Go to "Install App"
   - Click "Install to Workspace"
   - Authorize
   - Copy "Bot User OAuth Token" → This is `SLACK_BOT_TOKEN`

6. **Get Signing Secret**
   - Go to "Basic Information"
   - Under "App Credentials", copy "Signing Secret"
   - This is `SLACK_SIGNING_SECRET`

### Testing Slack Integration

```bash
# 1. Set all three tokens in .env
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...

# 2. Start the bot
python -m src.main

# 3. In Slack, DM the bot:
@sherlock help

# 4. Or in a channel:
/invite @sherlock
@sherlock investigate my pod is crashlooping
```

---

## Deployment

### Development

```bash
# Use CLI for quick testing
python -m src.cli health
python -m src.cli investigate "issue description"
```

### Staging

```bash
# Run in Docker
docker-compose up -d

# View logs
docker-compose logs -f sherlock
```

### Production

```bash
# Deploy to Kubernetes
kubectl apply -f deploy/kubernetes/

# Monitor
kubectl logs -f -n sherlock deployment/sherlock

# Scale if needed
kubectl scale deployment sherlock --replicas=2 -n sherlock
```

---

## Troubleshooting

### "API key not found"

```bash
# Check if environment variable is set
echo $ANTHROPIC_API_KEY

# If empty, load from .env
export $(cat .env | xargs)
```

### "kubectl: command not found"

```bash
# Install kubectl
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify
kubectl version --client
```

### "Failed to connect to Kubernetes"

```bash
# Check kubeconfig
kubectl config view

# Test access
kubectl get pods

# If using kubeconfig file, set in .env:
KUBECONFIG_PATH=/path/to/kubeconfig
```

### "Slack bot not responding"

```bash
# 1. Check tokens are set correctly
env | grep SLACK

# 2. Check bot logs for errors
# Look for connection messages

# 3. Verify Socket Mode is enabled in Slack app config

# 4. Reinstall app to workspace if needed
```

### "No events collected"

```bash
# 1. Check if kubectl works
kubectl get pods --all-namespaces

# 2. Check if there are actually issues
python -m src.cli health

# 3. Try with verbose logging
LOG_LEVEL=DEBUG python -m src.cli investigate "test"
```

### "Import errors"

```bash
# Ensure you're in virtual environment
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.11+
```

---

## Next Steps

Once Sherlock is running:

1. **Try investigations**
   ```bash
   @sherlock investigate API latency high
   @sherlock investigate pod crashlooping
   ```

2. **Monitor cluster health**
   ```bash
   python -m src.cli health
   ```

3. **Review recommendations**
   - Sherlock will provide kubectl commands
   - Review them before executing
   - Learn patterns over time

4. **Phase 2 enhancements** (coming soon)
   - Add log collectors (Elasticsearch, CloudWatch)
   - Add metrics collectors (Prometheus, Datadog)
   - Cross-system correlation

5. **Phase 3 features** (future)
   - Historical incident learning (RAG)
   - Predictive alerts
   - Auto-remediation (with approval)

---

## Support

- **Documentation**: Check `docs/ARCHITECTURE.md` for system design
- **Issues**: Open an issue on GitHub
- **Questions**: Ask in your team's Slack channel

---

**You're all set!** Start investigating incidents with AI assistance. 🚀
