# My Work AI Agents

Personal AI agents for daily SRE/DevOps tasks.

## Agents Built

1. **Log Analyzer** - Analyze logs and find patterns
2. **Config Reviewer** - Review configs for issues
3. **Incident Helper** - Help during incidents
4. **Command Explainer** - Explain complex commands
5. **Cost Optimizer** - Analyze cloud costs
6. **Security Checker** - Find security issues

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run an agent
python agents/log_analyzer.py --file /var/log/syslog

# Or use the CLI
./work-agent logs analyze /var/log/nginx/error.log
./work-agent config review nginx.conf
./work-agent incident diagnose "API returning 502"
```

## Project Structure

```
my_work_agents/
├── agents/           # Individual agent implementations
├── tools/            # Shared tools (API calls, file readers, etc)
├── configs/          # Agent configurations
├── examples/         # Example usage
└── work-agent        # Main CLI entry point
```

## Learning Path

1. Start with `examples/01_simple_log_analyzer.py`
2. Move to `agents/log_analyzer.py` (uses patterns from repo)
3. Build your own agent using templates
4. Integrate into your daily workflow

## Patterns Used

- **Prompt Chaining** (Chapter 1) - Multi-step analysis
- **Tool Use** (Chapter 5) - Execute commands, read files
- **Reflection** (Chapter 4) - Self-review and improve answers
- **RAG** (Chapter 14) - Query past incidents, runbooks
