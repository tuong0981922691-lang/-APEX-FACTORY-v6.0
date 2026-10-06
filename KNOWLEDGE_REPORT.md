# KNOWLEDGE_REPORT — Vòng 2: Knowledge Extraction

## FACT — tri thức được ghi nhận

### Nguyên lý và luật

1. **Giữ bất biến, thay phần phụ thuộc miền:** Blueprint giữ cơ chế phê duyệt con người, audit, state machine và kill switch; thay ontology và các vai trò gắn miền cụ thể (`ARCHITECTURAL_BLUEPRINT_V6.md:50-70`). Đây là chiến lược được mô tả, không xác nhận việc chuyển đổi đã hoàn tất.
2. **Sáng tạo trong hợp đồng có kiểm soát:** Tài liệu mô tả luật cấu trúc, mức vi phạm error/warning/info và yêu cầu dữ liệu đầu ra khớp schema; đầu ra bên ngoài sai schema bị từ chối (`ARCHITECTURAL_BLUEPRINT_V6.md:114-129,175-180`; luật severity ở phần composition khoảng dòng 1791-1795).
3. **Đánh giá nhiều chiều:** Thiết kế phân biệt tốc độ, footprint, ổn định và độ gọn; sau đó có vòng critic riêng và sandbox trước khi C2 duyệt (`ARCHITECTURAL_BLUEPRINT_V6.md:185-220`). Công thức có trọng số nhưng trọng số không được ấn định tại dòng 195.
4. **Quyền con người tại ranh giới tác động:** Blueprint yêu cầu capability token trước khi publish và C2 review trước deploy; mô hình Decision hiện tại cũng mặc định `requires_approval=True` (`ARCHITECTURAL_BLUEPRINT_V6.md:217-220`; `apex_core/governance/decision_brain.py:17-23,37-47`).
5. **Tiến hành theo pha, có giới hạn phạm vi và rủi ro:** Bản thiết kế chia 8 phase và nhận diện rủi ro, gồm output ngoài kém chất lượng, crash khi hot-inject, phạm vi ontology rộng, chi phí và tương thích legacy (`ARCHITECTURAL_BLUEPRINT_V6.md:232-310`).
6. **Đối thoại tuần tự và đóng băng yêu cầu:** CDP định nghĩa 5 trạng thái từ tiếp nhận đến đóng băng; thay đổi chỉ được xác nhận sau giai đoạn làm rõ và Owner ký (`apex_core/customer/cdp.py:1-9,19-24,58-97`). CVP mô tả preview, citation, audit đã che PII, propose-confirm và receipt ký (`apex_core/customer/cvp.py:1-8,30-77`).
7. **Tách đề xuất khỏi phán quyết:** Round Table chỉ trả recommendation keep/kill theo điểm trung bình và ngưỡng 60 (`apex_core/governance/round_table.py:17-43`); blueprint nói critic chỉ tìm lỗi/đề xuất sửa, quyết định qua các mức OK/FIX_LIST/REJECT (`ARCHITECTURAL_BLUEPRINT_V6.md:200-209`).
8. **Thu thập bằng chứng và kiểm tra lệch:** Ba probe làm reverse-spec, so độ nhất quán theo thời gian và giữa các lần trả lời/nguồn (`apex_core/probes/reverse_code_probe.py:7-28`, `silence_probe.py:1-53`, `cross_ai_probe.py:1-35`). Subagent phân tích tăng dần từ tóm tắt, tìm rủi ro đến kiểm chứng với trích dẫn (`apex_core/subagent/student.py:1-7,21-95`).
9. **Log có tính lưu vết:** Construction log và Screw Log tuyên bố append-only; Screw Log yêu cầu ghi lại mỗi lần dừng do cảnh báo (`reports/CONSTRUCTION_LOG.md:1-13`; `reports/SCREW_LOG.md:1-8`). Ma trận yêu cầu mỗi ý tưởng liên kết ít nhất một ý khác (`reports/IDEA_INTERLOCK_MATRIX.md:1-23`).
10. **Quy tắc vận hành repo:** Hướng dẫn nêu EXTEND-only, tích hợp router qua hookup, dịch vụ bên ngoài phải thật khi deploy, và dừng/ghi log cảnh báo (`AGENTS.md:63-78`; `apex_core/orchestrator_v6/_hookup.py:5-17`).

### Checklist và luồng được mô tả

**FACT:** Pipeline thiết kế là: nhận brief → trích ý định → tìm ứng viên theo catalog → tổng hợp biến thể → chấm đa chiều → phản biện độc lập → chạy sandbox → người có quyền duyệt và cấp quyền triển khai (`ARCHITECTURAL_BLUEPRINT_V6.md:143-220`). Dùng schema guard trước khi tin kết quả ngoài và audit request/response là yêu cầu của thiết kế (`:177-180,301-310`).

**FACT:** NT26 có checker cho các vùng source/UI/test (`scripts/lint_no_self_reference.py:12-20,36-61`); `pyproject.toml` quy định pytest và Ruff (`pyproject.toml:6-17`). Đây là cơ chế tồn tại; việc chạy thành công trong phiên khảo cổ này không được khẳng định.

## INFERENCE — tri thức tái sử dụng được suy ra

- Giữ ổn định lớp quyền hạn, audit và hợp đồng khi thay đổi mô hình nghiệp vụ; đặt thay đổi sau adapter và kiểm tra tương thích.
- Mọi sinh/đề xuất nên bị ràng buộc bởi schema, bộ quy tắc độc lập và khả năng từ chối; không coi sự trôi chảy của đầu ra là bằng chứng đúng.
- Tách “đề xuất”, “đánh giá”, “phê duyệt” và “tác động” thành các bước có thể kiểm toán; quyền người vận hành tăng lên theo mức độ không thể đảo ngược.
- Tạo ít nhất vài phương án có tiêu chí đo trước, nhưng không giả vờ có một điểm số khách quan khi baseline, trọng số hoặc ngưỡng chưa được xác định.
- Lưu dấu vết đầu vào, phiên bản đặc tả, bằng chứng, kết quả gate và quyết định; chỉ ghi “đã thành công” khi có artifact kiểm chứng.
- Tăng độ sâu điều tra theo rủi ro: sàng lọc nhanh → xác định điểm rủi ro → kiểm chứng mệnh đề bằng trích dẫn.
- Ma trận phụ thuộc có thể phát hiện giả định bị cô lập; liên kết ý tưởng không tự nó chứng minh tính đúng hoặc mức độ ưu tiên.

## UNKNOWN

Ngưỡng/trọng số Radar, baseline, tiêu chí pass chính thức, định nghĩa đầy đủ của các nguyên tắc NT1–NT10 và độ bao phủ triển khai không được suy diễn từ ví dụ hoặc từ tên gọi.
