# UNIVERSAL_KNOWLEDGE — Vòng 5: Domain-neutral knowledge

Tài liệu này loại bỏ tên miền, nhãn vai trò và sản phẩm cụ thể. FACT là điều có trong nguồn; INFERENCE là luật tổng quát hóa, không phải cam kết triển khai.

## FACT — các cơ chế nền được nguồn mô tả

1. Blueprint tách cơ chế quản trị/audit/quyền hạn khỏi mô hình miền có thể thay thế (`ARCHITECTURAL_BLUEPRINT_V6.md:50-70`).
2. Blueprint yêu cầu ràng buộc đầu ra bên ngoài bằng schema, loại bỏ kết quả không hợp lệ, chấm chất lượng theo nhiều trục, dùng critic độc lập, kiểm tra trong sandbox và cần phê duyệt trước tác động (`:175-220`).
3. Bản thiết kế chia thay đổi thành các giai đoạn, nêu rủi ro và giới hạn phạm vi ban đầu (`:232-310`).
4. Quy trình làm rõ có các trạng thái rõ ràng, tạo bản đặc tả và chờ xác nhận trước khi đóng băng (`apex_core/customer/cdp.py:19-24,58-97`).
5. Mã nguồn có cơ chế phân tích ba cấp; cấp sâu yêu cầu mệnh đề và dẫn chứng cụ thể (`apex_core/subagent/student.py:1-7,71-95`).
6. Có các probe cho tính nhất quán qua thời gian, so sánh kết quả độc lập, và đối chiếu đặc tả với artifact (`apex_core/probes/silence_probe.py:1-53`, `cross_ai_probe.py:1-35`, `reverse_code_probe.py:7-28`).
7. Tài liệu quy định ghi log append-only và liên kết các giả định/ý tưởng có liên quan (`reports/SCREW_LOG.md:1-8`, `IDEA_INTERLOCK_MATRIX.md:1-23`).
8. Hồ sơ hiện có không chứng minh mọi cơ chế trong blueprint đã được triển khai; danh sách module thật khác với danh sách thiết kế (`ARCHITECTURAL_BLUEPRINT_V6.md:23089-23100`, inventory checkout).

## INFERENCE — bộ quy tắc có thể tái sử dụng

### A. Tạo và kiểm soát phương án

- Chuyển yêu cầu tự nhiên thành đặc tả có cấu trúc, phiên bản hóa và trạng thái xác nhận; hỏi lại khi trường quan trọng còn mơ hồ.
- Tạo phương án trong một ontology/hợp đồng được kiểm soát; kiểm tra tính hợp lệ và phụ thuộc trước khi thực hiện.
- Đánh giá trên các chiều độc lập đã định nghĩa trước; công bố baseline, trọng số, ngưỡng và trường hợp thiếu dữ liệu. Nếu chưa có chúng, kết quả chỉ là gợi ý.

### B. Xác minh và quyền hạn

- Coi đầu ra từ người, mô hình hay dịch vụ ngoài là dữ liệu cần kiểm chứng; ép schema, xác thực nguồn và từ chối kết quả không đạt.
- Tách người/tiến trình tạo đề xuất khỏi evaluator và người có quyền phê duyệt.
- Yêu cầu xác nhận tường minh trước thay đổi khó đảo ngược; giới hạn token/quyền theo hành động và giữ cơ chế dừng.
- Trước khi tác động, chạy sandbox; triển khai theo canary hoặc bước nhỏ có rollback; xác nhận trạng thái sau mỗi gate.

### C. Bằng chứng và học hỏi

- Gắn artifact với đặc tả, nguồn, phiên bản, kết quả kiểm tra và quyết định; giữ audit append-only, bảo vệ dữ liệu nhạy cảm khi chia sẻ.
- Kiểm tra lại cùng đầu vào theo thời gian và qua nguồn độc lập; so sánh artifact thực tế với đặc tả để tìm lệch. Chọn metric phù hợp thay vì coi phép đo từ vựng là bằng chứng ngữ nghĩa.
- Dùng điều tra nhiều cấp: quét nhanh để xác định phạm vi, phân tích để tìm rủi ro, rồi kiểm chứng tuyên bố bằng trích dẫn.
- Khi có cảnh báo, dừng phần tác động, ghi hiện tượng và bằng chứng trước khi sửa; chỉ ghi bài học sau khi nguyên nhân được xác nhận.
- Đối chiếu mọi tuyên bố “hoàn tất” với artifact hiện có và kết quả kiểm tra; phân biệt kế hoạch, mã, chạy thử và triển khai.

## UNKNOWN

Chưa có căn cứ trong kho để cung cấp một bộ ngưỡng phổ quát, công thức điểm tối ưu, mức canary phù hợp cho mọi hệ thống, hay cam kết rằng các quy tắc suy ra này đã được áp dụng ngoài bối cảnh gốc.
