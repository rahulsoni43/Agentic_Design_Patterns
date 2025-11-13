#!/usr/bin/env python3
"""
Simple Log Analyzer - Your First AI Agent

This is the SIMPLEST possible agent. Perfect for learning.
Run: python 01_simple_log_analyzer.py
"""

import os
from anthropic import Anthropic

# Initialize Claude
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def analyze_logs(log_content):
    """
    Analyze logs using Claude.
    This is the simplest form - just one API call.
    """

    prompt = f"""
    You are an expert SRE analyzing system logs.

    Analyze these logs and provide:
    1. Summary of what's happening
    2. Any errors or warnings found
    3. Severity level (LOW/MEDIUM/HIGH/CRITICAL)
    4. Recommended actions

    Logs:
    {log_content}
    """

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


# Example usage
if __name__ == "__main__":
    # Sample nginx error logs
    sample_logs = """
2025-01-13 14:23:15 [error] 1234#1234: *5678 connect() failed (111: Connection refused) while connecting to upstream, client: 192.168.1.100, server: api.example.com, request: "GET /api/users HTTP/1.1", upstream: "http://127.0.0.1:8080/api/users", host: "api.example.com"
2025-01-13 14:23:16 [error] 1234#1234: *5679 connect() failed (111: Connection refused) while connecting to upstream, client: 192.168.1.101, server: api.example.com, request: "GET /api/users HTTP/1.1", upstream: "http://127.0.0.1:8080/api/users", host: "api.example.com"
2025-01-13 14:23:17 [error] 1234#1234: *5680 connect() failed (111: Connection refused) while connecting to upstream, client: 192.168.1.102, server: api.example.com, request: "GET /api/users HTTP/1.1", upstream: "http://127.0.0.1:8080/api/users", host: "api.example.com"
2025-01-13 14:24:01 [warn] 1234#1234: *5681 upstream server temporarily disabled while connecting to upstream, client: 192.168.1.103, server: api.example.com
    """

    print("=" * 60)
    print("SIMPLE LOG ANALYZER")
    print("=" * 60)
    print("\nAnalyzing logs...\n")

    result = analyze_logs(sample_logs)

    print(result)
    print("\n" + "=" * 60)

    # Challenge: Modify this to read from a real log file
    # Hint: Use open('/path/to/log', 'r').read()
