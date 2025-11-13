#!/usr/bin/env python3
"""
Production-Ready Log Analyzer Agent

Uses multiple patterns from the Agentic Design Patterns book:
- Prompt Chaining (Chapter 1)
- Tool Use (Chapter 5)
- Reflection (Chapter 4)
- Guardrails (Chapter 18)

This can handle real log files from your systems.
"""

import os
import sys
import argparse
from pathlib import Path
from anthropic import Anthropic
from datetime import datetime

class LogAnalyzerAgent:
    """
    AI Agent for analyzing system logs
    """

    def __init__(self, api_key=None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-5-20250929"

    def _call_claude(self, prompt, max_tokens=2048):
        """Helper to call Claude API"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error calling Claude API: {str(e)}"

    def read_log_file(self, file_path, max_lines=1000):
        """
        Tool: Read log file with safety checks (Guardrails - Chapter 18)
        """
        try:
            path = Path(file_path)

            # Guardrail: Check file exists
            if not path.exists():
                return None, f"Error: File {file_path} not found"

            # Guardrail: Check file size (prevent reading huge files)
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > 50:
                return None, f"Error: File too large ({file_size_mb:.1f}MB). Max 50MB."

            # Read file (limit to max_lines)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

                # If file is too long, get last N lines (most recent)
                if len(lines) > max_lines:
                    lines = lines[-max_lines:]
                    content = "".join(lines)
                    return content, f"Note: Showing last {max_lines} lines of {len(lines)} total"
                else:
                    content = "".join(lines)
                    return content, None

        except Exception as e:
            return None, f"Error reading file: {str(e)}"

    def extract_errors(self, log_content):
        """
        Step 1: Extract and structure error information
        """
        prompt = f"""
        You are an expert SRE analyzing system logs.

        Extract all errors, warnings, and critical issues from these logs.

        For each issue found, provide:
        - Timestamp (if available)
        - Severity level (CRITICAL/ERROR/WARNING)
        - Component/Service affected
        - Error message
        - Any relevant context (IP, user, request, etc.)

        Format as a clear, structured list.

        Logs:
        {log_content}

        If no errors found, say "No errors or warnings detected."
        """

        return self._call_claude(prompt)

    def categorize_and_prioritize(self, extracted_errors):
        """
        Step 2: Categorize errors and prioritize
        """
        prompt = f"""
        Analyze these extracted log errors and:

        1. Group by category:
           - Network/Connectivity
           - Application/Code
           - Database
           - Security
           - Performance
           - Other

        2. Assess impact:
           - User-facing (affects customers)
           - Internal (affects operations)
           - Minor (logging/monitoring only)

        3. Prioritize using P0/P1/P2/P3:
           - P0: Critical, immediate action required
           - P1: High priority, address within 1 hour
           - P2: Medium priority, address within 24 hours
           - P3: Low priority, address when possible

        Extracted Errors:
        {extracted_errors}

        Provide clear prioritization with reasoning.
        """

        return self._call_claude(prompt)

    def generate_action_plan(self, extracted_errors, categorization):
        """
        Step 3: Generate actionable remediation plan
        """
        prompt = f"""
        Based on this log analysis, create a detailed action plan for an SRE/DevOps engineer.

        Include:

        1. IMMEDIATE ACTIONS (next 15 min):
           - Specific commands to run
           - Systems to check
           - Initial diagnostics

        2. SHORT-TERM FIXES (1-4 hours):
           - Root cause investigation steps
           - Temporary mitigations
           - Escalation criteria

        3. LONG-TERM IMPROVEMENTS:
           - Prevent recurrence
           - Monitoring/alerting to add
           - Architecture changes to consider

        4. RUNBOOK COMMANDS:
           - Actual shell commands (kubectl, docker, systemctl, etc.)
           - Log queries
           - Metrics to check

        Error Categorization:
        {categorization}

        Original Errors:
        {extracted_errors}

        Be specific and actionable. Assume the engineer has root/admin access.
        """

        return self._call_claude(prompt, max_tokens=3072)

    def reflect_and_improve(self, action_plan):
        """
        Step 4: Self-reflection (Chapter 4 pattern)
        Review the action plan for completeness and safety
        """
        prompt = f"""
        You are a senior SRE reviewing this action plan.

        Check for:
        1. Are the commands safe to run in production?
        2. Are there any missing diagnostic steps?
        3. Is the priority correct?
        4. Are there any risky operations that need confirmation?
        5. Is anything unclear or ambiguous?

        Action Plan to Review:
        {action_plan}

        Provide:
        - Any warnings or concerns
        - Suggestions for improvement
        - A "APPROVED" or "NEEDS REVISION" verdict
        """

        return self._call_claude(prompt)

    def analyze(self, log_file_path=None, log_content=None, verbose=True):
        """
        Full analysis pipeline with prompt chaining
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n{'='*70}")
        print(f"LOG ANALYSIS STARTED: {timestamp}")
        print(f"{'='*70}\n")

        # Step 0: Read log file if path provided
        if log_file_path:
            if verbose:
                print(f"📁 Reading log file: {log_file_path}")
            log_content, warning = self.read_log_file(log_file_path)
            if warning:
                print(f"⚠️  {warning}")
            if not log_content:
                print("❌ Failed to read log file")
                return None
            print(f"✅ Read {len(log_content)} characters\n")

        # Step 1: Extract errors
        if verbose:
            print("🔍 STEP 1: Extracting errors and warnings...")
            print("-" * 70)

        extracted = self.extract_errors(log_content)
        print(extracted)
        print()

        # Step 2: Categorize and prioritize
        if verbose:
            print("📊 STEP 2: Categorizing and prioritizing...")
            print("-" * 70)

        categorized = self.categorize_and_prioritize(extracted)
        print(categorized)
        print()

        # Step 3: Generate action plan
        if verbose:
            print("📋 STEP 3: Generating action plan...")
            print("-" * 70)

        action_plan = self.generate_action_plan(extracted, categorized)
        print(action_plan)
        print()

        # Step 4: Reflect (self-review)
        if verbose:
            print("🤔 STEP 4: Self-review and validation...")
            print("-" * 70)

        reflection = self.reflect_and_improve(action_plan)
        print(reflection)
        print()

        print(f"{'='*70}")
        print("✅ ANALYSIS COMPLETE")
        print(f"{'='*70}\n")

        return {
            "timestamp": timestamp,
            "extracted_errors": extracted,
            "categorization": categorized,
            "action_plan": action_plan,
            "reflection": reflection
        }


def main():
    parser = argparse.ArgumentParser(description="AI-powered log analyzer for SREs")
    parser.add_argument('--file', '-f', help='Path to log file')
    parser.add_argument('--lines', '-n', type=int, default=1000, help='Max lines to analyze')
    parser.add_argument('--quiet', '-q', action='store_true', help='Less verbose output')

    args = parser.parse_args()

    if not args.file:
        print("Usage: python log_analyzer.py --file /path/to/logfile")
        print("\nExample:")
        print("  python log_analyzer.py --file /var/log/syslog")
        print("  python log_analyzer.py --file /var/log/nginx/error.log --lines 500")
        sys.exit(1)

    # Create agent
    agent = LogAnalyzerAgent()

    # Run analysis
    result = agent.analyze(
        log_file_path=args.file,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
