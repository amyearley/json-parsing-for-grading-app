#!/usr/bin/env python3
"""
Transcript Formatter for Call Grading
Converts raw transcript JSON into a token-efficient format for Claude Console.
Usage: python transcript_formatter.py <path_to_transcript.json>
"""

import json
import sys
from pathlib import Path


def format_transcript(transcript_data: dict) -> str:
    """
    Convert raw transcript JSON into a token-efficient formatted string.
    Strips word-level Items arrays (which balloon token count from ~4k to ~30k+)
    while preserving all signal needed for rubric evaluation.
    """
    lines = []

    call = transcript_data.get("call", {})
    agent = transcript_data.get("agent", {})
    client_info = transcript_data.get("client", {})
    analysis = transcript_data.get("analysis", {})

    lines.append("=== CALL METADATA ===")
    lines.append(f"Call ID: {call.get('call_id', 'N/A')}")
    lines.append(f"Duration: {call.get('duration', 'N/A')}")
    lines.append(f"Agent: {agent.get('name', 'N/A')}")
    lines.append(f"Client: {client_info.get('name', 'N/A')} ({client_info.get('location', 'N/A')})")
    lines.append("")

    lines.append("=== CALL ANALYSIS SUMMARY ===")
    lines.append(
        f"Agent  — avg loudness: {analysis.get('agent_loudness_avg', 'N/A')} dB | "
        f"avg sentiment: {analysis.get('agent_sentiment_avg', 'N/A')} | "
        f"talk speed: {analysis.get('agent_talkspeed', 'N/A')} wpm | "
        f"total talk time: {analysis.get('agent_totaltalktime', 'N/A')}"
    )
    lines.append(
        f"Client — avg loudness: {analysis.get('client_loudness_avg', 'N/A')} dB | "
        f"avg sentiment: {analysis.get('client_sentiment_avg', 'N/A')} | "
        f"talk speed: {analysis.get('client_talkspeed', 'N/A')} wpm | "
        f"total talk time: {analysis.get('client_totaltalktime', 'N/A')}"
    )
    lines.append("")

    lines.append("=== TRANSCRIPT ===")
    lines.append("(Format: [timestamp] ROLE | avg_loudness dB | SENTIMENT)")
    lines.append("")

    raw_content = transcript_data.get("transcript", {}).get("raw_content", [])
    for turn in raw_content:
        role = turn.get("ParticipantRole", "UNKNOWN")
        content = turn.get("Content", "")
        sentiment = turn.get("Sentiment", "UNKNOWN")
        loudness_scores = turn.get("LoudnessScores", [])
        avg_loudness = (
            round(sum(loudness_scores) / len(loudness_scores), 1)
            if loudness_scores else "N/A"
        )
        begin_ms = turn.get("BeginOffsetMillis", 0)
        minutes = begin_ms // 60000
        seconds = (begin_ms % 60000) // 1000
        timestamp = f"{minutes}:{seconds:02d}"

        lines.append(f"[{timestamp}] {role} | {avg_loudness} dB | {sentiment}")
        lines.append(content)
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcript_formatter.py <path_to_transcript.json>")
        print("\nExample: python transcript_formatter.py short_call_transcript.json")
        sys.exit(1)

    transcript_path = Path(sys.argv[1])

    if not transcript_path.exists():
        print(f"❌ Error: File not found: {transcript_path}")
        sys.exit(1)

    try:
        with open(transcript_path, "r") as f:
            transcript_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON file: {e}")
        sys.exit(1)

    formatted = format_transcript(transcript_data)

    # Save to output file
    output_path = transcript_path.stem + "_formatted.txt"
    with open(output_path, "w") as f:
        f.write(formatted)

    print(f"✓ Transcript formatted successfully!")
    print(f"✓ Output saved to: {output_path}")
    print(f"\nFormatted transcript ({len(formatted)} characters):")
    print("=" * 60)
    print(formatted)
    print("=" * 60)
    print(f"\nCopy the formatted transcript above and paste it into Claude Console.")


if __name__ == "__main__":
    main()
