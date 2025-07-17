import os

def write_license_info_to_markdown(
    account_email,
    account_password,
    license_name,
    license_key,
    license_out_date
):
    """
    Ghi thông tin giấy phép vào một tệp Markdown có tên 'generated_results.md'.

    Đối số:
        account_email (str): Email liên kết với tài khoản.
        account_password (str): Mật khẩu của tài khoản.
        license_name (str): Tên giấy phép.
        license_key (str): Khóa giấy phép.
        license_out_date (str): Ngày hết hạn giấy phép.
    """
    file_path = "generated_results.md"

    # Chuẩn bị nội dung sẽ được ghi vào định dạng Markdown
    markdown_content = f"""
```
Email tài khoản: {account_email}
Mật khẩu tài khoản: {account_password}
Tên giấy phép: {license_name}
Khóa giấy phép: {license_key}
Ngày hết hạn giấy phép: {license_out_date}
```
-------------------------------------------------
"""
    try:
        # Mở tệp ở chế độ nối thêm ('a') để thêm nội dung, tạo tệp nếu chưa tồn tại
        # Sử dụng mã hóa 'utf-8' để hỗ trợ các ký tự đặc biệt
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Đã ghi thông tin giấy phép thành công vào tệp: {file_path}")
    except IOError as e:
        # Xử lý lỗi nếu có vấn đề khi ghi tệp
        print(f"Lỗi khi ghi vào tệp {file_path}: {e}")

# Chi tiết giấy phép bạn đã cung cấp
email = "blitzedsmurf@clonemailsieure.com"
password = "081cu]?WIrpj+!?V%E"
name = "ESET HOME Security Premium"
key = "B74A-X4CS-SVCW-T6UM-XVHK"
out_date = "16.08.2025"

# Gọi hàm để ghi thông tin
if __name__ == "__main__":
    write_license_info_to_markdown(email, password, name, key, out_date)
