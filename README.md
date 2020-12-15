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
1. Hệ thống chính(Master) nhận ảnh, quản lý các node.
  - Chạy hệ thống cấu hình các thành phần, vai trò của máy:
      + Địa chỉ
      + Tài khoản, mật khẩu  ftp để kết nối
2. Các Node con
  - Chạy hệ thống: 
  + python manage.py runserver. Mặc định sẽ là 127.0.0.1:8000 cổng 8000
  + python manage.py runserver address:port để custom .
