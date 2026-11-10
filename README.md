# ⚡ EcoWatt - Laptop Total Power Monitor for Windows

Ứng dụng hiển thị **tổng lượng điện năng tiêu thụ (Watt)** của toàn bộ laptop Windows theo thời gian thực với triết lý tối giản, trực quan và tiện dụng tối đa cho người dùng bình thường.

---

## 🎁 Chia sẻ cho bạn bè dùng (Siêu đơn giản)

Bạn chỉ cần gửi **duy nhất 1 file**:
👉 **`EcoWatt.exe`** (nằm ngay trong thư mục gốc `E:\Draft-Gemini\EcoWatt.exe`).

* **Người nhận không cần cài đặt Python!**
* **Không cần gõ bất kỳ câu lệnh nào!**
* Chỉ cần tải file về máy Windows 10/11, nhấp đúp là ứng dụng chạy ngay lập tức.
* Có thể gửi qua **Google Drive, Zalo, Telegram, USB, hoặc đăng lên GitHub**.

---

## ✨ Các tính năng đã hoàn thiện

### 1. 🗔 Giao diện chính (Glanceable Hero Card)
- **Một con số tổng quan to rõ:** Hiển thị tức thì công suất tiêu thụ (ví dụ: `15.8 W`).
- **Màu sắc trạng thái thông minh:**
  - 🟢 *Xanh lá (< 20W): Tiết kiệm (Văn phòng, lướt web)*
  - 🟡 *Vàng (20W - 45W): Tải vừa phải (Đa nhiệm, đồ họa nhẹ)*
  - 🔴 *Đỏ (> 45W): Tải cao (Gaming, render)*
- **Ước tính tiền điện:** Tính tiền điện thời gian thực (đ/giờ) theo đơn giá EVN.
- **Tình trạng nguồn:** Tự động nhận diện cắm sạc hoặc dùng pin (dự đoán thời gian pin còn lại theo giờ:phút).

### 2. 📊 Chi tiết từng linh kiện (Bấm mở rộng)
- **CPU (Intel Core / AMD):** Công suất (W), % tải, xung nhịp thực tế (GHz).
- **GPU (Card đồ họa):** Công suất (W), % tải đồ họa.
- **Màn hình:** Công suất (W) theo mức độ sáng hiện tại (%).
- **Bo mạch chủ & Khác:** Công suất (W) cho RAM, SSD, chipset và quạt.

### 3. 📌 Icon Khay Hệ Thống (Taskbar System Tray Icon)
- **Hiển thị trực tiếp số Watt góc Taskbar:** Icon vẽ số Watt thực tế (ví dụ: `16W` màu xanh/vàng/đỏ) ngay cạnh đồng hồ Windows.
- **Hover xem nhanh:** Rê chuột vào icon để xem tóm tắt: `EcoWatt: 16.5 W (⚡ Sạc 96% | CPU 24%)`.
- **Menu chuột phải:**
  - Mở giao diện chính
  - Bật/Tắt Chế độ Mini Widget
  - Bật/Tắt Khởi động cùng Windows
  - Thoát hoàn toàn

### 4. 🗗 Chế độ Mini Widget (Floating Bar)
- Thu nhỏ thành một thanh nổi mini siêu gọn (`265x66px`).
- Có thể nhấp giữ chuột để kéo thả vị trí bất kỳ trên màn hình khi chơi game hoặc làm việc.

### 5. ⚙️ Tiện ích & Cài đặt hệ thống
- **Khởi động cùng Windows:** Tự động kích hoạt khi mở máy tính.
- **Thu nhỏ về khay khi bấm nút X:** Cửa sổ đóng sẽ tự ẩn xuống khay Taskbar để tiếp tục theo dõi ngầm.
- **Ghim trên cùng (📌 Always on Top):** Cửa sổ luôn nổi trên các ứng dụng khác.
- **Tùy chỉnh giá điện:** Cho phép tự nhập đơn giá điện (VNĐ/kWh).
- **Single-Instance Mutex:** Ngăn chặn việc bấm mở trùng lặp nhiều app cùng lúc.
