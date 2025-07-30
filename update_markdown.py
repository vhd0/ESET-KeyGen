import re
import os
from datetime import datetime, timezone # Import timezone

def parse_output_log(log_file_path):
    """
    Parses the output log file to extract key information.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
        return []

    # Regex to capture the required information, adjusted for log format
    # It now matches the observed order and optionally skips line numbers
    pattern = re.compile(
        r"Account Email:\s*(?P<account_email>[^\n]+)(?:\n\d+)?\n"
        r"Account Password:\s*(?P<account_password>[^\n]+)(?:\n\d+)?\n"
        r"License Name:\s*(?P<license_name>[^\n]+)(?:\n\d+)?\n"
        r"License Key:\s*(?P<license_key>[^\n]+)(?:\n\d+)?\n"
        r"License Out Date:\s*(?P<license_out_date>[^\n]+)(?:\n\d+)?",
        re.DOTALL
    )

    matches = pattern.finditer(content)
    results = []
    for match in matches:
        results.append(match.groupdict())
    return results

def update_markdown_table(results, markdown_file_path="generated_results.md"):
    """
    Updates or creates a Markdown file with the parsed results.
    If the file exists, it appends new unique results.
    """
    header = "| License Key | Account Email | Account Password | License Out Date | License Name | Generated On (UTC) |\n"
    separator = "|---|---|---|---|---|---|\n"

    # Check if file exists and read existing content
    existing_rows = set()
    existing_content = ""
    if os.path.exists(markdown_file_path):
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
            # Extract existing rows to avoid duplicates
            for line in existing_content.splitlines():
                if line.strip() and not line.startswith('| License Key') and not line.startswith('|---'):
                    existing_rows.add(line.strip())

    # If the file is new or empty, or header is missing, add header and separator
    if not existing_content.strip() or not existing_content.startswith(header):
        new_content_to_write = header + separator
    else:
        new_content_to_write = existing_content # Preserve existing content if header is present

    # Append new results, avoiding duplicates
    for result in results:
        # Use datetime.now(timezone.UTC) instead of datetime.utcnow()
        generated_on = datetime.now(timezone.UTC).strftime("%Y-%m-%d %H:%M:%S")
        row = (
            f"| {result.get('license_key', 'N/A')} "
            f"| {result.get('account_email', 'N/A')} "
            f"| {result.get('account_password', 'N/A')} "
            f"| {result.get('license_out_date', 'N/A')} "
            f"| {result.get('license_name', 'N/A')} "
            f"| {generated_on} |"
        )
        if row not in existing_rows:
            new_content_to_write += row + "\n"

    # Write the updated content back to the file
    with open(markdown_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content_to_write)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python update_markdown.py <path_to_output_log>")
        sys.exit(1)

    log_file = sys.argv[1]
    
    parsed_data = parse_output_log(log_file)
    if parsed_data:
        update_markdown_table(parsed_data)
        print(f"Successfully updated generated_results.md with data from {log_file}")
    else:
        print(f"No new license key information found in {log_file}")
