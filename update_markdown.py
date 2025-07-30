import re
import os
from datetime import datetime, timezone  # UTC time

def parse_output_log(log_file_path):
    """
    Phân tích file output.log để trích xuất thông tin tài khoản và license.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file log: {log_file_path}")
        return []

    # Regex cải tiến – không phụ thuộc số dòng ở giữa
    pattern = re.compile(
        r"Account Email:\s*(?P<account_email>[^\n]+)\s*"
        r"Account Password:\s*(?P<account_password>[^\n]+)\s*"
        r"License Name:\s*(?P<license_name>[^\n]+)\s*"
        r"License Key:\s*(?P<license_key>[^\n]+)\s*"
        r"License Out Date:\s*(?P<license_out_date>[^\n]+)",
        re.DOTALL
    )

    matches = pattern.finditer(content)
    return [match.groupdict() for match in matches]

def update_markdown_table(results, markdown_file_path="generated_results.md"):
    """
    Cập nhật bảng markdown với kết quả mới, tránh trùng lặp.
    """
    header = "| License Key | Account Email | Account Password | License Out Date | License Name | Generated On (UTC) |\n"
    separator = "|---|---|---|---|---|---|\n"

    existing_rows = set()
    existing_content = ""
    if os.path.exists(markdown_file_path):
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
            for line in existing_content.splitlines():
                if line.startswith("|") and not line.startswith("|---") and not line.startswith("| License Key"):
                    existing_rows.add(line.strip())

    if not existing_content.strip() or not existing_content.startswith(header):
        new_content = header + separator
    else:
        new_content = existing_content

    for result in results:
        generated_on = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        row = (
            f"| {result.get('license_key', 'N/A')} "
            f"| {result.get('account_email', 'N/A')} "
            f"| {result.get('account_password', 'N/A')} "
            f"| {result.get('license_out_date', 'N/A')} "
            f"| {result.get('license_name', 'N/A')} "
            f"| {generated_on} |"
        )
        if row not in existing_rows:
            new_content += row + "\n"

    with open(markdown_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Đã cập nhật generated_results.md")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("❌ Cách sử dụng: python update_markdown.py <đường_dẫn_tới_output.log>")
        sys.exit(1)

    log_file = sys.argv[1]
    parsed_data = parse_output_log(log_file)
    if parsed_data:
        update_markdown_table(parsed_data)
    else:
        print(f"⚠️ Không tìm thấy dữ liệu license trong {log_file}")
