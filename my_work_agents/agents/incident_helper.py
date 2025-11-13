#!/usr/bin/env python3
"""
Incident Response Helper Agent

Helps during production incidents by:
- Suggesting diagnostic commands
- Providing troubleshooting steps
- Generating runbooks on the fly
- Recommending escalation paths

Usage:
  python incident_helper.py "API is returning 502 errors"
  python incident_helper.py "Database connections timing out"
  python incident_helper.py "High CPU usage on prod servers"
"""

import os
import sys
import argparse
from anthropic import Anthropic
from datetime import datetime

class IncidentHelperAgent:
    """AI agent to help during production incidents"""

    def __init__(self, api_key=None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-5-20250929"

    def _call_claude(self, prompt, max_tokens=3072):
        """Helper to call Claude API"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    def analyze_incident(self, description, context=None):
        """
        Analyze incident and provide immediate guidance
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n{'='*70}")
        print(f"🚨 INCIDENT RESPONSE HELPER")
        print(f"Time: {timestamp}")
        print(f"{'='*70}\n")

        print(f"📝 Incident: {description}\n")

        # Step 1: Initial triage
        print("🔍 STEP 1: Initial Triage & Classification")
        print("-" * 70)

        triage_prompt = f"""
You are an expert SRE helping with a production incident.

Incident Description: {description}

Additional Context: {context if context else 'None provided'}

Provide immediate triage:

1. INCIDENT CLASSIFICATION:
   - Type: (Performance/Availability/Security/Data/Other)
   - Severity: (P0-Critical / P1-High / P2-Medium / P3-Low)
   - Likely affected components
   - Potential user impact

2. IMMEDIATE CHECKS (next 2 minutes):
   - What to check first
   - Specific metrics/logs to look at
   - Quick validation commands

3. INITIAL HYPOTHESIS:
   - Most likely root causes (ranked)
   - Why this is the likely cause

Be concise and actionable. Focus on speed.
"""

        triage = self._call_claude(triage_prompt)
        print(triage)
        print()

        # Step 2: Diagnostic runbook
        print("📋 STEP 2: Diagnostic Runbook")
        print("-" * 70)

        runbook_prompt = f"""
Based on this incident, provide a detailed diagnostic runbook.

Incident: {description}
Triage: {triage}

Provide:

1. DIAGNOSTIC COMMANDS (in order of priority):
   For each command, include:
   - The actual shell command to run
   - What you're looking for
   - How to interpret the output

   Cover:
   - Log queries (tail, grep, journalctl)
   - System metrics (top, htop, iostat, vmstat)
   - Network diagnostics (netstat, ss, tcpdump)
   - Application-specific checks (kubectl, docker, systemctl)
   - Database queries (if applicable)

2. COMMON PATTERNS TO LOOK FOR:
   - Error messages
   - Resource exhaustion
   - Timeouts
   - Connection issues

3. DECISION TREE:
   - If you see X → check Y
   - If you see Z → do A

Be specific with actual commands, not generic advice.
"""

        runbook = self._call_claude(runbook_prompt, max_tokens=4096)
        print(runbook)
        print()

        # Step 3: Remediation options
        print("🔧 STEP 3: Remediation Options")
        print("-" * 70)

        remediation_prompt = f"""
Provide remediation options for this incident.

Incident: {description}
Diagnostics: {runbook}

For each remediation option, provide:

1. QUICK MITIGATIONS (< 5 minutes):
   - Temporary fixes to restore service
   - Rollback procedures
   - Traffic rerouting
   - Actual commands to execute

2. PROPER FIXES (5-60 minutes):
   - Root cause resolution
   - Step-by-step procedures
   - Validation steps

3. RISK ASSESSMENT:
   - For each action, note the risks
   - What could go wrong
   - When to abort

4. ESCALATION CRITERIA:
   - When to escalate to senior engineers
   - When to page other teams
   - When to notify management/customers

Prioritize service restoration over perfect fixes.
"""

        remediation = self._call_claude(remediation_prompt, max_tokens=4096)
        print(remediation)
        print()

        # Step 4: Post-incident actions
        print("📊 STEP 4: Post-Incident Actions")
        print("-" * 70)

        postmortem_prompt = f"""
Once the incident is resolved, what should the team do?

Provide:

1. IMMEDIATE POST-INCIDENT:
   - Monitoring to add
   - Alerts to create
   - Documentation to update

2. POST-MORTEM PREP:
   - Key data to collect now
   - Metrics to preserve
   - Logs to archive

3. PREVENTION MEASURES:
   - How to prevent this from happening again
   - Architecture changes to consider
   - Process improvements

Keep it brief - the incident is still ongoing.
"""

        postincident = self._call_claude(postmortem_prompt)
        print(postincident)

        print(f"\n{'='*70}")
        print("✅ INCIDENT ANALYSIS COMPLETE")
        print(f"{'='*70}\n")

        return {
            "timestamp": timestamp,
            "description": description,
            "triage": triage,
            "runbook": runbook,
            "remediation": remediation,
            "post_incident": postincident
        }


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered incident response helper",
        epilog="""
Examples:
  python incident_helper.py "API returning 502 errors"
  python incident_helper.py "High memory usage" --context "Started after deployment"
  python incident_helper.py "Database connection timeouts"
        """
    )
    parser.add_argument('description', help='Incident description')
    parser.add_argument('--context', '-c', help='Additional context')

    args = parser.parse_args()

    agent = IncidentHelperAgent()
    agent.analyze_incident(args.description, args.context)


if __name__ == "__main__":
    main()
