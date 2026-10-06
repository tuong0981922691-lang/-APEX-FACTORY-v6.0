# DECISION_REPORT — Vòng 3: Decision Extraction

## FACT — quyết định và dấu vết

### 1. Chuyển hướng kiến trúc

Blueprint ghi nhận chuyển từ ontology và vai trò gắn với một miền cũ sang một mô hình sản xuất tổng quát hơn. Nó đề xuất giữ các bất biến như capability token, nguyên tắc, state machine, audit và sandbox; thay ontology và vai trò B2/B3/B7, đồng thời giữ ý tưởng hội tụ đa trục và vòng phản biện (`ARCHITECTURAL_BLUEPRINT_V6.md:50-70`). Đây là lý do được ghi trong blueprint, không phải bằng chứng so sánh hiệu năng.

### 2. Bốn quyết định C2 được ghi nhận

Tài liệu ban đầu yêu cầu xác nhận framework, quyền gọi dịch vụ ngoài, vị trí legacy và thứ tự ưu tiên trước khi tiếp tục (`ARCHITECTURAL_BLUEPRINT_V6.md:314-331`). Phần sau ghi nhận:

- ưu tiên React + TypeScript + Tailwind;
- bật Borrowing Protocol nhưng bắt mọi đầu ra ngoài qua Schema Guard;
- chuyển legacy vào `apex_core/legacy/`, giữ nguyên lõi bảo mật;
- thứ tự Web → App → Video.

Nguồn: `ARCHITECTURAL_BLUEPRINT_V6.md:1726-1734`.

### 3. Phân kỳ triển khai và quyền

Blueprint đề xuất 8 phase với phạm vi từ foundation đến orchestration (`ARCHITECTURAL_BLUEPRINT_V6.md:232-299`). Cùng blueprint đặt capability token và review của C2 ở ranh giới deploy (`:217-220`), đồng thời nêu rủi ro và biện pháp trước khi bắt đầu (`:301-323`). Mô hình Decision trong mã hiện có cũng giữ cờ yêu cầu phê duyệt (`apex_core/governance/decision_brain.py:17-23,37-47`).

### 4. Những điều chỉnh được ghi nhận

- Hai nguyên tắc mới được nêu khi chuyển sang mô hình thiết kế/giao diện: tính toàn vẹn hệ design system và accessibility (`ARCHITECTURAL_BLUEPRINT_V6.md:234-242`).
- Phần đầu yêu cầu xác nhận trước Phase 1; phần tường thuật sau cho biết C2 đưa bốn lựa chọn và nhóm tiếp tục từng lô Phase 0 (`:314-331,1726-1734`). Đây là thay đổi tiến trình được ghi trong cùng tài liệu.
- Blueprint kết thúc bằng tuyên bố toàn bộ phase/tệp đã xong (`:23089-23100`), trong khi inventory hiện tại không có các thư mục/tệp Phase 0–7 được nêu. Chênh lệch này là bằng chứng về trạng thái tài liệu không đồng nhất, không xác định được thời điểm hay nguyên nhân.

## INFERENCE — quy trình ra quyết định

- C2 được mô tả như người giữ quyền phê duyệt và chọn trade-off; hệ thống tạo bằng chứng/đề xuất, không tự có quyền hợp thức hóa deploy.
- Quyết định kiến trúc được chia thành bất biến (quyền, audit, lifecycle) và phần thay thế (ontology/logic miền) để giảm rủi ro khi đổi hướng.
- Các lựa chọn công nghệ được ghi rõ sau khi nêu phương án, giúp phân biệt giả thuyết ban đầu với quyết định đã chốt trong tài liệu.
- Tuyên bố hoàn tất không đủ xác nhận trạng thái repo nếu không đối chiếu artifact, test và lịch sử có thể kiểm tra.

## UNKNOWN

- “C2” không có định nghĩa vai trò/quyền hạn đầy đủ ngoài vai trò phê duyệt được ngữ cảnh thể hiện.
- Không có bản ghi phiên họp, chữ ký, commit cụ thể hay phê duyệt bên ngoài blueprint để xác minh độc lập các quyết định.
- Không biết lý do định lượng cho lựa chọn framework, weights, thứ tự ưu tiên hay các phase bị triển khai/không triển khai.
- Clone chỉ cung cấp lịch sử Git rút gọn; không thể tái dựng mọi lần sửa, đổi hướng hoặc người quyết định.
