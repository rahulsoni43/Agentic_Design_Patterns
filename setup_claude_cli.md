# Integrate Claude into Your Daily Workflow

## Option 1: Claude API via CLI (Custom Scripts)

### Setup
```bash
# Install Anthropic Python SDK
pip install anthropic python-dotenv

# Set your API key
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Create Reusable CLI Tool

Create `~/.local/bin/ask-claude` (or any location in your PATH):

```bash
#!/usr/bin/env python3
import os
import sys
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Get question from command line args
question = " ".join(sys.argv[1:])

if not question:
    print("Usage: ask-claude 'your question here'")
    sys.exit(1)

# Call Claude
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": question}
    ]
)

print(message.content[0].text)
```

Make it executable:
```bash
chmod +x ~/.local/bin/ask-claude
```

### Usage Examples

```bash
# Quick questions
ask-claude "explain this error: connection timeout to 10.0.1.5:443"

# Analyze logs (pipe input)
tail -100 /var/log/nginx/error.log | ask-claude "summarize these errors"

# Review configs
cat nginx.conf | ask-claude "find security issues in this config"

# Generate commands
ask-claude "give me a kubectl command to find pods using more than 1GB memory"

# Explain commands
ask-claude "explain: awk '{print $1}' | sort | uniq -c | sort -rn"
```

---

## Option 2: VSCode Integration

### Method A: Use Existing Extensions

**1. Anthropic Claude Extension (Official)**
- Open VSCode
- Go to Extensions (Ctrl+Shift+X)
- Search "Claude" or "Anthropic"
- Install and configure with API key

**Features:**
- Chat in sidebar
- Explain code selections
- Generate code from comments
- Refactor suggestions

**2. Continue.dev (AI Code Assistant)**
- More configurable, supports Claude
- Better for custom workflows

```bash
# Install Continue extension in VSCode
# Then configure to use Claude in settings.json:
{
  "continue.anthropic.apiKey": "your-api-key",
  "continue.modelName": "claude-sonnet-4-5-20250929"
}
```

---

## Option 3: Terminal Integration (Oh My Zsh / Bash)

### Add Claude as Shell Function

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Quick Claude queries
claude() {
    python3 -c "
import os, sys
from anthropic import Anthropic
client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
question = ' '.join(sys.argv[1:])
message = client.messages.create(
    model='claude-sonnet-4-5-20250929',
    max_tokens=1024,
    messages=[{'role': 'user', 'content': question}]
)
print(message.content[0].text)
" "$@"
}

# Explain last command
explain-cmd() {
    last_cmd=$(fc -ln -1)
    claude "Explain this command in simple terms: $last_cmd"
}

# Fix last command
fix-cmd() {
    last_cmd=$(fc -ln -1)
    claude "This command failed: '$last_cmd'. Suggest a fix."
}
```

### Usage:
```bash
$ claude "what does awk NR==5 mean?"
$ explain-cmd  # explains the last command you ran
$ fix-cmd      # helps fix failed commands
```

---

## Getting Your API Key

1. Go to: https://console.anthropic.com/
2. Sign up / Log in
3. Go to API Keys section
4. Create a new key
5. Set in environment:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Add to ~/.bashrc or ~/.zshrc to persist
```

---

## Cost Considerations

- Claude API pricing: https://www.anthropic.com/pricing
- Sonnet 4.5: ~$3 per million input tokens, ~$15 per million output tokens
- Typical CLI usage: $5-20/month for heavy daily use
- Set budget alerts in Anthropic console

---

## Next: Build Custom Agents (See custom_agents_setup.md)
