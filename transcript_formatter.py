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
    Supports both AWS format (Transcript array at root) and website format (transcript.raw_content).
    Strips word-level Items arrays (which balloon token count from ~4k to ~30k+)
    while preserving all signal needed for rubric evaluation.
    """
    lines = []

    # Detect format and extract data accordingly
    is_aws_format = "Transcript" in transcript_data and isinstance(transcript_data.get("Transcript"), list)
    
    if is_aws_format:
        # AWS format
        call_id = transcript_data.get("JobName", "N/A")
        duration_ms = transcript_data.get("ConversationCharacteristics", {}).get("TotalConversationDurationMillis", 0)
        duration_secs = duration_ms // 1000
        duration_mins = duration_secs // 60
        duration_secs = duration_secs % 60
        duration = f"{duration_mins} min, {duration_secs} secs"
        
        agent_name = "Agent"
        client_name = "Customer"
        client_location = "N/A"
        
        raw_content = transcript_data.get("Transcript", [])
        
        # Extract analysis data
        conv_char = transcript_data.get("ConversationCharacteristics", {})
        talk_time = conv_char.get("TalkTime", {}).get("DetailsByParticipant", {})
        talk_speed = conv_char.get("TalkSpeed", {}).get("DetailsByParticipant", {})
        sentiment = conv_char.get("Sentiment", {}).get("OverallSentiment", {})
        
        agent_talk_time_ms = talk_time.get("AGENT", {}).get("TotalTimeMillis", 0)
        customer_talk_time_ms = talk_time.get("CUSTOMER", {}).get("TotalTimeMillis", 0)
        agent_talk_time = f"{agent_talk_time_ms // 60000} min, {(agent_talk_time_ms % 60000) // 1000} secs"
        customer_talk_time = f"{customer_talk_time_ms // 60000} min, {(customer_talk_time_ms % 60000) // 1000} secs"
        
        agent_wpm = talk_speed.get("AGENT", {}).get("AverageWordsPerMinute", "N/A")
        customer_wpm = talk_speed.get("CUSTOMER", {}).get("AverageWordsPerMinute", "N/A")
        
        agent_sentiment = sentiment.get("AGENT", "N/A")
        customer_sentiment = sentiment.get("CUSTOMER", "N/A")
        
    else:
        # Website format
        call = transcript_data.get("call", {})
        agent = transcript_data.get("agent", {})
        client_info = transcript_data.get("client", {})
        analysis = transcript_data.get("analysis", {})
        
        call_id = call.get("call_id", "N/A")
        duration = call.get("duration", "N/A")
        agent_name = agent.get("name", "Agent")
        client_name = client_info.get("name", "Customer")
        client_location = client_info.get("location", "N/A")
        
        raw_content = transcript_data.get("transcript", {}).get("raw_content", [])
        
        agent_talk_time = analysis.get("agent_totaltalktime", "N/A")
        customer_talk_time = analysis.get("client_totaltalktime", "N/A")
        agent_wpm = analysis.get("agent_talkspeed", "N/A")
        customer_wpm = analysis.get("client_talkspeed", "N/A")
        agent_sentiment = analysis.get("agent_sentiment_avg", "N/A")
        customer_sentiment = analysis.get("client_sentiment_avg", "N/A")

    lines.append("=== CALL METADATA ===")
    lines.append(f"Call ID: {call_id}")
    lines.append(f"Duration: {duration}")
    lines.append(f"Agent: {agent_name}")
    lines.append(f"Client: {client_name} ({client_location})")
    lines.append("")

    lines.append("=== CALL ANALYSIS SUMMARY ===")
    lines.append(
        f"Agent  — sentiment: {agent_sentiment} | "
        f"talk speed: {agent_wpm} wpm | "
        f"total talk time: {agent_talk_time}"
    )
    lines.append(
        f"Client — sentiment: {customer_sentiment} | "
        f"talk speed: {customer_wpm} wpm | "
        f"total talk time: {customer_talk_time}"
    )
    lines.append("")

    lines.append("=== TRANSCRIPT ===")
    lines.append("(Format: [timestamp] ROLE | avg_loudness dB | SENTIMENT)")
    lines.append("")

    for turn in raw_content:
        role = turn.get("ParticipantRole", "UNKNOWN")
        content = turn.get("Content", "")
        sentiment = turn.get("Sentiment", "UNKNOWN")
        loudness_scores = turn.get("LoudnessScores", [])
        
        # Filter out None values and calculate average
        valid_scores = [s for s in loudness_scores if s is not None]
        avg_loudness = (
            round(sum(valid_scores) / len(valid_scores), 1)
            if valid_scores else "N/A"
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
