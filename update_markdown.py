import re
import os
from datetime import datetime, timezone # Import timezone

def parse_output_log(log_file_path): # Hàm này nhận đường dẫn tệp log
    """
    Parses the output log file to extract key information.
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
        return []

    # Regex để bắt các thông tin cần thiết, đã điều chỉnh cho định dạng log
    # Nó khớp với thứ tự quan sát và linh hoạt hơn với khoảng trắng và dòng số
    # Sử dụng \s* để khớp 0 hoặc nhiều khoảng trắng (bao gồm cả newline)
    # Sử dụng \n\s*\d+\s*\n để khớp dòng số và các khoảng trắng xung quanh
    pattern = re.compile(
        r"Account Email:\s*(?P<account_email>[^\n]+)\s*\n\s*\d+\s*\n"
        r"Account Password:\s*(?P<account_password>[^\n]+)\s*\n\s*\d+\s*\n"
        r"License Name:\s*(?P<license_name>[^\n]+)\s*\n\s*\d+\s*\n"
        r"License Key:\s*(?P<license_key>[^\n]+)\s*\n\s*\d+\s*\n"
        r"License Out Date:\s*(?P<license_out_date>[^\n]+)\s*\n\s*\d+\s*\n(?:-+\s*\n)?", # Thêm optional dashes và newline cuối cùng
        re.DOTALL
    )

    matches = pattern.finditer(content)
    results = []
    for match in matches:
        results.append(match.groupdict())
    return results

def update_markdown_table(results, markdown_file_path="generated_results.md"):
    """
    Cập nhật hoặc tạo một tệp Markdown với các kết quả đã phân tích.
    Nếu tệp tồn tại, nó sẽ thêm các kết quả duy nhất mới.
    """
    header = "| License Key | Account Email | Account Password | License Out Date | License Name | Generated On (UTC) |\n"
    separator = "|---|---|---|---|---|---|\n"

    # Kiểm tra xem tệp có tồn tại không và đọc nội dung hiện có
    existing_rows = set()
    existing_content = ""
    if os.path.exists(markdown_file_path):
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
            # Trích xuất các hàng hiện có để tránh trùng lặp
            for line in existing_content.splitlines():
                if line.strip() and not line.startswith('| License Key') and not line.startswith('|---'):
                    existing_rows.add(line.strip())

    # Nếu tệp mới hoặc trống, hoặc thiếu tiêu đề, thêm tiêu đề và dấu phân cách
    if not existing_content.strip() or not existing_content.startswith(header):
        new_content_to_write = header + separator
    else:
        new_content_to_write = existing_content # Giữ lại nội dung hiện có nếu tiêu đề đã có

    # Thêm các kết quả mới, tránh trùng lặp
    for result in results:
        # Sử dụng datetime.now(timezone.UTC) thay vì datetime.utcnow()
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

    # Ghi nội dung đã cập nhật trở lại tệp
    with open(markdown_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content_to_write)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Cách sử dụng: python update_markdown.py <đường_dẫn_tới_output_log>")
        sys.exit(1)

    # Đọc đường dẫn tệp log trực tiếp từ đối số dòng lệnh đầu tiên
    log_file = sys.argv[1]
    
    parsed_data = parse_output_log(log_file) # Gọi hàm mới
    if parsed_data:
        update_markdown_table(parsed_data)
        print(f"Đã cập nhật generated_results.md thành công với dữ liệu từ {log_file}.")
    else:
        print(f"Không tìm thấy thông tin khóa license mới trong {log_file}.")
