#!/usr/bin/env python3
"""
Log Analyzer with Prompt Chaining - Using Pattern from Chapter 1

This demonstrates PROMPT CHAINING:
Step 1: Extract errors from logs
Step 2: Categorize errors
Step 3: Generate action plan

This is more powerful than a single prompt!
"""

import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def call_claude(prompt):
    """Helper function to call Claude"""
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def analyze_logs_with_chaining(log_content):
    """
    Multi-step analysis using Prompt Chaining (Chapter 1 pattern)
    """

    print("🔗 STEP 1: Extracting errors...")
    print("-" * 60)

    # Step 1: Extract structured error information
    step1_prompt = f"""
    Extract all errors and warnings from these logs.

    For each issue, provide:
    - Timestamp
    - Error type
    - Error message
    - Affected component

    Format as a structured list.

    Logs:
    {log_content}
    """

    extracted_errors = call_claude(step1_prompt)
    print(extracted_errors)
    print()

    print("🔗 STEP 2: Categorizing and prioritizing...")
    print("-" * 60)

    # Step 2: Categorize errors (using output from step 1)
    step2_prompt = f"""
    Based on these extracted errors, categorize them by:
    1. Severity (CRITICAL/HIGH/MEDIUM/LOW)
    2. Type (Network/Application/Database/Security)
    3. Impact (User-facing/Internal)

    Prioritize which should be addressed first.

    Errors:
    {extracted_errors}
    """

    categorized = call_claude(step2_prompt)
    print(categorized)
    print()

    print("🔗 STEP 3: Generating action plan...")
    print("-" * 60)

    # Step 3: Generate remediation plan (using outputs from step 1 & 2)
    step3_prompt = f"""
    Based on this error analysis and categorization, create a detailed action plan.

    Include:
    1. Immediate actions (next 15 minutes)
    2. Short-term fixes (next 1 hour)
    3. Long-term improvements (prevent recurrence)
    4. Specific commands to run
    5. Monitoring to add

    Error Analysis:
    {categorized}

    Original Errors:
    {extracted_errors}
    """

    action_plan = call_claude(step3_prompt)
    print(action_plan)
    print()

    return {
        "errors": extracted_errors,
        "categorization": categorized,
        "action_plan": action_plan
    }


if __name__ == "__main__":
    # More complex log scenario
    sample_logs = """
2025-01-13 14:23:15 [error] nginx: connect() failed (111: Connection refused) while connecting to upstream, upstream: "http://127.0.0.1:8080"
2025-01-13 14:23:16 [error] nginx: connect() failed (111: Connection refused) while connecting to upstream, upstream: "http://127.0.0.1:8080"
2025-01-13 14:23:17 [crit] nginx: upstream server temporarily disabled while connecting to upstream
2025-01-13 14:23:20 [error] app: Database connection pool exhausted (active: 100, idle: 0, max: 100)
2025-01-13 14:23:21 [error] app: Query timeout after 30s: SELECT * FROM users WHERE ...
2025-01-13 14:23:22 [warn] app: High memory usage: 7.8GB / 8GB (97.5%)
2025-01-13 14:23:25 [error] app: Failed to process payment for order #12345: Connection timeout to payment gateway
2025-01-13 14:23:30 [error] nginx: *12345 upstream timed out (110: Connection timed out)
    """

    print("=" * 60)
    print("LOG ANALYZER WITH PROMPT CHAINING")
    print("=" * 60)
    print()

    result = analyze_logs_with_chaining(sample_logs)

    print("=" * 60)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 60)

    # You can now save this to a file, send to Slack, create a ticket, etc.
