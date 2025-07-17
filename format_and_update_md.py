import os
import glob
import re
import datetime

def clean_value(value):
    """Removes newlines and trims whitespace, escapes pipe characters."""
    if value is None:
        return ""
    value = value.strip().replace('\n', ' ').replace('\r', '')
    return value.replace('|', '\\|')

def format_field_for_markdown(field_name, value):
    """Formats a field for Markdown table, wrapping passwords/keys in backticks."""
    cleaned_value = clean_value(value)
    if field_name in ["password", "license_key"]:
        if cleaned_value:
            # Escape backticks within the value itself
            return f'`{cleaned_value.replace("`", "\\`")}`'
        return "" # Return empty string if value is empty, not empty backticks
    return cleaned_value

def parse_and_format_license_data(account_file_patterns, key_file_patterns, output_file, max_entries=30):
    all_entries = []

    # Read existing entries if the file exists (skip header and separator)
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if len(lines) > 2: # Skip header and separator lines
                for line in lines[2:]:
                    line = line.strip()
                    # Check if the line is a valid table row before adding
                    if line.startswith('|') and line.endswith('|') and '|' in line[1:-1]:
                        all_entries.append(line)

    # Process new account and key files
    for patterns in [account_file_patterns, key_file_patterns]:
        for pattern in patterns:
            for filepath in glob.glob(pattern):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Split by lines of at least 20 hyphens, ensuring blocks are clean
                        blocks = [block.strip() for block in re.split(r'-{20,}', content) if block.strip()]
                        
                        for block in blocks:
                            email = re.search(r'Account Email: (.*)', block)
                            password = re.search(r'Account Password: (.*)', block)
                            license_name = re.search(r'License Name: (.*)', block)
                            license_key = re.search(r'License Key: (.*)', block)
                            license_out_date = re.search(r'License Out Date: (.*)', block)

                            email_val = format_field_for_markdown("email", email.group(1)) if email else ""
                            password_val = format_field_for_markdown("password", password.group(1)) if password else ""
                            license_name_val = format_field_for_markdown("license_name", license_name.group(1)) if license_name else ""
                            license_key_val = format_field_for_markdown("license_key", license_key.group(1)) if license_key else ""
                            license_out_date_val = format_field_for_markdown("license_out_date", license_out_date.group(1)) if license_out_date else ""

                            # Only add row if at least one field has content
                            if any([email_val, password_val, license_name_val, license_key_val, license_out_date_val]):
                                all_entries.append(f"| {email_val} | {password_val} | {license_name_val} | {license_key_val} | {license_out_date_val} |")

                except Exception as e:
                    print(f"Error processing file {filepath}: {e}")

    # Keep only the latest max_entries
    all_entries = all_entries[-max_entries:]

    # Write the final Markdown table
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("| Email tài khoản | Mật khẩu tài khoản | Tên giấy phép | Khóa giấy phép | Ngày hết hạn |\n")
        f.write("|-----------------|--------------------|---------------|---------------|--------------|\n")
        if not all_entries:
            f.write("| Không có | Không có | Không có | Không có | Không có |\n")
        else:
            for entry_row in all_entries:
                f.write(entry_row + "\n")

# Main execution block
if __name__ == "__main__":
    # Assuming script is run from ESET-KeyGen directory
    # Adjust paths if your .txt files are in a different subdirectory within the repo
    parse_and_format_license_data(['./*ACCOUNTS.txt'], ['./*KEYS.txt'], 'generated_results.md', 30)
