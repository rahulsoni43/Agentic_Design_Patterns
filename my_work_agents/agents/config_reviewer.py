#!/usr/bin/env python3
"""
Configuration File Reviewer Agent

Reviews infrastructure configs for:
- Security issues
- Best practices
- Performance optimizations
- Potential bugs

Supports: nginx, apache, kubernetes, docker-compose, terraform, etc.
"""

import os
import sys
import argparse
from pathlib import Path
from anthropic import Anthropic

class ConfigReviewerAgent:
    """AI agent for reviewing configuration files"""

    def __init__(self, api_key=None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-5-20250929"

    def _call_claude(self, prompt):
        """Helper to call Claude API"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=3072,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"

    def detect_config_type(self, file_path, content):
        """Auto-detect configuration type"""
        path = Path(file_path)
        filename = path.name.lower()

        # Common config files
        if 'nginx' in filename:
            return 'nginx'
        elif 'apache' in filename or 'httpd' in filename:
            return 'apache'
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            if 'docker-compose' in filename:
                return 'docker-compose'
            elif any(k in content for k in ['apiVersion:', 'kind:', 'metadata:']):
                return 'kubernetes'
            else:
                return 'yaml'
        elif filename.endswith('.tf'):
            return 'terraform'
        elif 'dockerfile' in filename:
            return 'dockerfile'
        elif filename == 'sshd_config':
            return 'ssh'
        else:
            return 'generic'

    def review_config(self, file_path):
        """Review a configuration file"""

        # Read file
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

        # Detect config type
        config_type = self.detect_config_type(file_path, content)

        print(f"📋 File: {file_path}")
        print(f"🔍 Detected type: {config_type}")
        print(f"{'='*70}\n")

        # Review prompt
        prompt = f"""
You are an expert SRE and security engineer reviewing infrastructure configuration files.

Review this {config_type} configuration file for:

1. SECURITY ISSUES (HIGH PRIORITY):
   - Hardcoded credentials or secrets
   - Insecure protocols (HTTP instead of HTTPS, etc.)
   - Weak encryption/ciphers
   - Overly permissive access controls
   - Missing security headers
   - Exposed ports or services

2. BEST PRACTICES:
   - Configuration anti-patterns
   - Missing important settings
   - Deprecated directives
   - Resource limits
   - Logging and monitoring

3. PERFORMANCE:
   - Bottlenecks
   - Inefficient configurations
   - Missing caching
   - Connection pooling issues

4. RELIABILITY:
   - Missing error handling
   - No health checks
   - Single points of failure
   - Missing timeouts

For each issue found, provide:
- Severity: CRITICAL/HIGH/MEDIUM/LOW
- Line number (if identifiable)
- Explanation
- Recommended fix with example code

Configuration file content:
{content}

Provide a structured review with clear priorities.
If the config looks good, say so and mention what's done well.
"""

        print("🤖 Analyzing configuration...\n")
        review = self._call_claude(prompt)

        print("📊 REVIEW RESULTS:")
        print("-" * 70)
        print(review)
        print("-" * 70)

        # Ask for improved version
        print("\n🔧 Generating improved configuration...\n")

        improve_prompt = f"""
Based on your review, provide an improved version of this configuration file.

Only include the sections that need changes, with comments explaining what was changed and why.

If no changes needed, say "Configuration is already following best practices."

Original config:
{content}

Your previous review:
{review}
"""

        improved = self._call_claude(improve_prompt)

        print("✨ SUGGESTED IMPROVEMENTS:")
        print("-" * 70)
        print(improved)
        print("-" * 70)

        return {
            "file_path": file_path,
            "config_type": config_type,
            "review": review,
            "improvements": improved
        }


def main():
    parser = argparse.ArgumentParser(description="AI-powered config file reviewer")
    parser.add_argument('file', help='Path to config file')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)

    agent = ConfigReviewerAgent()
    agent.review_config(args.file)


if __name__ == "__main__":
    main()
