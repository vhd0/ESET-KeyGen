import sys
import re
from datetime import datetime
import os

def parse_log_output(log_file_path):
    """
    Phân tích file log và trích xuất thông tin tài khoản/khóa.
    Mỗi mục nhập (entry) bao gồm email, password, license name, license key, và expires date.
    """
    entries = []
    current_entry = {}
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Sử dụng biểu thức chính quy để trích xuất giá trị sau tiền tố
                if "Account Email:" in line:
                    # Nếu có một entry đang dở dang, reset nó để bắt đầu entry mới
                    # Điều này giúp tránh việc các trường bị lẫn lộn giữa các entry
                    current_entry = {
                        "email": "",
                        "password": "",
                        "license_name": "",
                        "license_key": "",
                        "expires_date": ""
                    }
                    match = re.search(r"Account Email: *(.*)", line)
                    if match:
                        current_entry["email"] = match.group(1).strip()
                elif "Account Password:" in line:
                    match = re.search(r"Account Password: *(.*)", line)
                    if match:
                        current_entry["password"] = match.group(1).strip()
                elif "License Name:" in line:
                    match = re.search(r"License Name: *(.*)", line)
                    if match:
                        current_entry["license_name"] = match.group(1).strip()
                elif "License Key:" in line:
                    match = re.search(r"License Key: *(.*)", line)
                    if match:
                        current_entry["license_key"] = match.group(1).strip()
                elif "License Out Date:" in line:
                    match = re.search(r"License Out Date: *(.*)", line)
                    if match:
                        date_str = match.group(1).strip()
                        # Xử lý cả định dạng dd.MM.yyyy và dd/MM/yyyy
                        dt_object = None
                        try:
                            dt_object = datetime.strptime(date_str, "%d.%m.%Y")
                        except ValueError:
                            try:
                                dt_object = datetime.strptime(date_str, "%d/%m/%Y")
                            except ValueError:
                                pass # Giữ nguyên chuỗi nếu không khớp định dạng

                        current_entry["expires_date"] = dt_object.strftime("%Y-%m-%d") if dt_object else date_str
                        
                        # Khi tất cả các trường của một entry đã được thu thập, thêm vào danh sách
                        if all(current_entry.values()): # Kiểm tra tất cả các giá trị đều không rỗng
                            entries.append(current_entry)
                            current_entry = {} # Reset để chuẩn bị cho entry tiếp theo
    except FileNotFoundError:
        print(f"Lỗi: File log '{log_file_path}' không tìm thấy.", file=sys.stderr)
    except Exception as e:
        print(f"Lỗi khi đọc hoặc phân tích file log: {e}", file=sys.stderr)

    return entries

def escape_markdown_table_cell(text):
    """
    Thoát (escape) các ký tự đặc biệt trong văn bản để hiển thị đúng trong ô bảng Markdown.
    Cụ thể là ký tự '|' sẽ được chuyển thành '\|'.
    """
    if text is None:
        return ""
    # Thoát ký tự '|' trước
    text = str(text).replace('|', '\\|')
    # Có thể thêm các ký tự khác nếu cần thiết (ví dụ: '\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!')
    # Tuy nhiên, chỉ '|' là nguyên nhân chính gây lỗi cột trong bảng.
    return text

def update_markdown_file(new_entries_data, results_file_path):
    """
    Cập nhật file Markdown với các mục nhập mới.
    Các mục mới sẽ được thêm vào đầu và chỉ giữ lại 30 mục gần nhất.
    """
    existing_rows = []
    if os.path.exists(results_file_path):
        try:
            with open(results_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Tìm vị trí bắt đầu của dữ liệu bảng (sau tiêu đề và dấu phân cách)
                table_start_index = -1
                for i, line in enumerate(lines):
                    if line.strip() == "|-----|----------|----------|--------------|--------------|":
                        table_start_index = i + 1
                        break
                
                if table_start_index != -1:
                    for line in lines[table_start_index:]:
                        line = line.strip()
                        # Chỉ lấy các dòng có định dạng bảng Markdown
                        if line and line.startswith('|') and line.endswith('|'):
                            existing_rows.append(line)
        except Exception as e:
            print(f"Cảnh báo: Không thể đọc file Markdown hiện có '{results_file_path}': {e}", file=sys.stderr)

    # Định dạng các mục nhập mới thành các hàng bảng Markdown
    formatted_new_rows = []
    for entry in new_entries_data:
        key = escape_markdown_table_cell(entry.get("license_key"))
        email = escape_markdown_table_cell(entry.get("email"))
        password = escape_markdown_table_cell(entry.get("password"))
        expires = escape_markdown_table_cell(entry.get("expires_date"))
        license_name = escape_markdown_table_cell(entry.get("license_name"))
        formatted_new_rows.append(f"| {key} | {email} | {password} | {expires} | {license_name} |")

    # Kết hợp các hàng mới và các hàng hiện có (hàng mới nhất ở trên cùng)
    combined_rows = formatted_new_rows + existing_rows
    
    # Giới hạn chỉ 30 mục nhập gần nhất
    max_entries = 30
    final_rows = combined_rows[:max_entries]

    current_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    runner_os = os.environ.get('RUNNER_OS', 'Unknown') # Lấy tên hệ điều hành của runner

    # Ghi lại nội dung Markdown đã cập nhật vào file
    try:
        with open(results_file_path, 'w', encoding='utf-8') as f:
            f.write("# Kết quả tạo tài khoản và khóa\n\n")
            f.write(f"_Generated at: {current_datetime} UTC_\n")
            f.write(f"_OS của trình chạy: {runner_os}_\n\n")
            f.write("| Key | Username | Password | Expires Date | License Name |\n")
            f.write("|-----|----------|----------|--------------|--------------|\n")
            for row in final_rows:
                f.write(f"{row}\n")
        print(f"Cập nhật '{results_file_path}' thành công.")
    except Exception as e:
        print(f"Lỗi khi ghi vào file Markdown '{results_file_path}': {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cách sử dụng: python update_markdown.py <đường_dẫn_đến_output_log>", file=sys.stderr)
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    # Đường dẫn tuyệt đối đến generated_results.md
    # Script này sẽ được chạy từ thư mục ESET-KeyGen,
    # và generated_results.md nằm ở thư mục cha.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_file_path = os.path.join(script_dir, "..", "generated_results.md")

    parsed_data = parse_log_output(log_file)
    if parsed_data:
        update_markdown_file(parsed_data, results_file_path)
    else:
        print("Không tìm thấy dữ liệu hợp lệ để cập nhật bảng Markdown.", file=sys.stderr)
        sys.exit(1) # Báo lỗi nếu không có dữ liệu để cập nhật
