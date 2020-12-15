# Ph-t-tri-n-ph-n-m-m
Project bộ môn phát triển phần mềm

- Đề tài: Nhận diện đối tượng trong ảnh
- Thành viên nhóm: Đỗ Thành Nam, Nguyễn Minh Đức, Nguyễn Quốc Khoa

I. Tính năng hệ thống:
  - Upload ảnh, file pdf 
  - Chia trang cho các node con xử lý
  - Các Node con nhận file và xử lý nhận dạng văn bản
  - Xuất kết quả nhận dạng ra file text, ảnh png , json tương ứng với ảnh, văn bản nhận được.

II. Triển khai:
  Hệ thống triển khai trong môi trường python trên hệ điều hành Window
1. Cài đặt thư viện:
    + Dowload tại https://www.python.org/downloads/
    + Settings environnment PATH (thư mục chứa python sau khi cài đặt).
    + Các thư viện cần sử dụng trong requirements.txt
    + Cài đặt qua lệnh : pip -r install path/requirements.txt 

2. Hệ thống chính(Master) nhận ảnh, quản lý các node.
  - Chạy hệ thống cấu hình các thành phần, vai trò của máy:
      + Địa chỉ
      + Tài khoản, mật khẩu  ftp để kết nối
3. Các Node con
  - Chạy hệ thống: 
  + Lưu ý: chạy dưới quyền admin( Run as administrator) lỗi gặp k load được thư viện tessaract ocr trên window
  + python manage.py runserver. Mặc định sẽ là 127.0.0.1:8000 cổng 8000
  + python manage.py runserver address:port để custom .
