name: Automated Account and Key Generator

on:
  schedule:
    - cron: "0 0 * * *" # Chạy tự động vào lúc 00:00 UTC mỗi ngày
  workflow_dispatch:
    inputs:
      account:
        description: 'Số lượng tài khoản cần tạo (mặc định = 0)'
        required: false
        default: '0'
        type: string
      key:
        description: 'Số lượng khóa cần tạo (mặc định = 1)'
        required: false
        default: '1'
        type: string
      branch:
        description: "Nhánh kho lưu trữ (không chạm vào nếu bạn không biết gì về nó!!!)"
        required: false
        type: choice
        options:
          - main
          - test
        default: main

jobs:
  generate-account-and-key:
    runs-on: ubuntu-latest # Chạy trên môi trường Ubuntu mới nhất
    permissions:
      contents: write # Cấp quyền ghi vào kho lưu trữ để cập nhật file Markdown
    steps:
      - name: Kiểm tra kho lưu trữ
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          ref: ${{ github.event.inputs.branch || 'main' }}

      - name: Thiết lập môi trường Python
        run: |
          sudo apt update
          sudo apt install -y python3-pip python3-venv

      - name: Tạo Swap File (để tránh lỗi hết bộ nhớ)
        run: |
          echo "Tạo swap file 4G..."
          sudo fallocate -l 4G /swapfile # Tạo file swap kích thước 4GB
          sudo chmod 600 /swapfile        # Thiết lập quyền chỉ đọc/ghi cho root
          sudo mkswap /swapfile           # Định dạng file thành không gian swap
          sudo swapon /swapfile           # Kích hoạt swap file
          echo "Swap file đã được tạo và kích hoạt."

      - name: Thử tất cả tổ hợp cho đến khi thành công
        shell: bash
        env:
          ACCOUNT: ${{ github.event.inputs.account || '0' }}
          KEY: ${{ github.event.inputs.key || '1' }}
        run: |
          # Clone công cụ tạo key
          git clone -b ${{ github.event.inputs.branch || 'main' }} https://github.com/rzc0d3r/ESET-KeyGen.git
          cd ESET-KeyGen
          
          # Tạo và kích hoạt môi trường ảo Python
          python3 -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt

          # Định nghĩa tất cả tổ hợp có thể của nhà cung cấp mail, loại key và hệ điều hành
          MAIL_PROVIDERS=("1secmail" "guerrillamail" "developermail" "mailticking" "fakemail" "inboxes" "incognitomail" "emailfake")
          KEY_TYPES=("--key" "--small-business-key")
          OS_LIST=("Linux" "Windows" "macOS")
          
          # Ngẫu nhiên hóa thứ tự các tổ hợp để thử
          SHUFFLED_MAILS=($(printf "%s\n" "${MAIL_PROVIDERS[@]}" | shuf))
          SHUFFLED_KEYS=($(printf "%s\n" "${KEY_TYPES[@]}" | shuf))
          SHUFFLED_OS=($(printf "%s\n" "${OS_LIST[@]}" | shuf))

          SUCCESS=0
          echo "Bắt đầu thử các tổ hợp ngẫu nhiên..."

          # Function để chạy command với timeout, tránh việc script bị treo
          run_with_timeout() {
            local timeout_duration=90 # Thời gian timeout là 90 giây
            local command=("$@")
            
            # Chạy command trong nền
            "${command[@]}" & pid=$!
            
            # Chờ trong timeout_duration giây
            for ((i=1; i<=timeout_duration; i++)); do
              if ! kill -0 $pid 2>/dev/null; then
                # Process đã kết thúc bình thường
                wait $pid
                return $?
              fi
              sleep 1
            done
            
            # Kill process nếu vẫn còn chạy sau timeout
            kill -9 $pid 2>/dev/null
            wait $pid 2>/dev/null
            echo "Process timed out after ${timeout_duration}s"
            return 124 # Mã lỗi cho timeout
          }

          # Thử từng tổ hợp cho đến khi thành công
          for CURRENT_OS in "${SHUFFLED_OS[@]}"; do
            export CURRENT_OS # Xuất biến này để có thể sử dụng trong các bước sau
            echo "=== Thử với OS: $CURRENT_OS ==="
            
            for MAIL in "${SHUFFLED_MAILS[@]}"; do
              for KEY_TYPE in "${SHUFFLED_KEYS[@]}"; do
                echo "=== Thử tổ hợp: OS=$CURRENT_OS, Mail=$MAIL, Key Type=$KEY_TYPE ==="
                
                # Xóa các file kết quả cũ để đảm bảo sạch sẽ
                rm -f output.log *KEYS.txt *ACCOUNTS.txt

                # Chạy tạo tài khoản nếu cần
                if [[ "$ACCOUNT" != "0" ]]; then
                  echo "Tạo $ACCOUNT tài khoản với $MAIL..."
                  run_with_timeout python3 main.py --auto-detect-browser --account --email-api "$MAIL" \
                    --skip-update-check --no-logo --disable-progress-bar --disable-logging \
                    --repeat "$ACCOUNT" | tee -a output.log
                fi
                
                # Chạy tạo key nếu cần
                if [[ "$KEY" != "0" ]]; then
                  echo "Tạo $KEY khóa với $MAIL và $KEY_TYPE..."
                  run_with_timeout python3 main.py --auto-detect-browser "$KEY_TYPE" --email-api "$MAIL" \
                    --skip-update-check --no-logo --disable-progress-bar --disable-logging \
                    --repeat "$KEY" | tee -a output.log

                  # Kiểm tra kết quả để đảm bảo tất cả các trường cần thiết đều có
                  if grep -q "License Key:" output.log && \
                      grep -q "Account Email:" output.log && \
                      grep -q "Account Password:" output.log && \
                      grep -q "License Out Date:" output.log && \
                      grep -q "License Name:" output.log; then
                    echo "✅ Tạo khóa thành công với OS=$CURRENT_OS!"
                    SUCCESS=1
                    break 3  # Thoát khỏi tất cả các vòng lặp nếu thành công
                  else
                    echo "❌ Không thể tạo khóa với tổ hợp này hoặc thông tin bị thiếu, thử tổ hợp tiếp theo..."
                  fi
                else
                  # Nếu không cần tạo key, chỉ tạo tài khoản và coi là thành công
                  if [[ "$ACCOUNT" != "0" ]]; then
                    echo "Chỉ tạo tài khoản, không tạo khóa. Coi là thành công."
                    SUCCESS=1
                    break 3
                  fi
                fi
              done
            done
          done

          # Kiểm tra kết quả cuối cùng của tất cả các lần thử
          if [[ $SUCCESS -eq 0 ]]; then
            echo "❌ Đã thử tất cả tổ hợp nhưng không thành công!"
            exit 1 # Kết thúc workflow với lỗi
          fi

      - name: Cập nhật bảng Markdown với Python
        if: success() # Chỉ chạy bước này nếu các bước trước đó thành công
        shell: bash
        run: |
          # Truyền đường dẫn tệp output.log vào script Python
          python3 update_markdown.py ESET-KeyGen/output.log

      - name: Cập nhật và đẩy kết quả
        if: success() # Chỉ chạy bước này nếu các bước trước đó thành công
        shell: bash
        run: |
          # Cấu hình thông tin người dùng cho git commit
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          # Kiểm tra xem file markdown có tồn tại không và có thay đổi để commit/push không
          if [ -f "generated_results.md" ]; then
            git add generated_results.md
            if ! git diff --cached --quiet; then
              # Sử dụng env.CURRENT_OS vì biến này đã được export trong bước trước
              git commit -m "Cập nhật kết quả từ ${{ env.CURRENT_OS }} [skip ci]"
              git push origin HEAD:${{ github.event.inputs.branch || 'main' }}
            else
              echo "Không có thay đổi để commit/push."
            fi
          fi
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} # Sử dụng GitHub token để xác thực
