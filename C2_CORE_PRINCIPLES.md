# C2_CORE_PRINCIPLES

## Phạm vi và cách đếm

Chỉ tổng hợp từ năm báo cáo khảo cổ đã được cung cấp. “Frequency” là số báo cáo trong tập năm báo cáo có ghi nhận trực tiếp nguyên lý hoặc một biểu hiện tương đương; đây là tần suất xuất hiện trong hồ sơ, không phải mức độ được áp dụng thực tế. Evidence chỉ dẫn tới năm báo cáo cho phép; không đọc nguồn khác. FACT ghi điều báo cáo nêu; INFERENCE ghi khái quát hóa.

## 1. Human authority at consequential gates

- **Description:** Giữ quyền phê duyệt cuối cùng của người có thẩm quyền đối với hành động có tác động; hệ thống có thể thu thập bằng chứng và đề xuất nhưng không tự cấp quyền.
- **Evidence:** `DECISION_REPORT.md` phần 2–3, FACT; `KNOWLEDGE_REPORT.md` mục 4 và 6; `UNIVERSAL_KNOWLEDGE.md` mục B.
- **Frequency:** 4/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Phê duyệt của người và quyền có kiểm soát được nêu làm gate trước tác động. **INFERENCE:** Mức giám sát nên tăng theo độ khó đảo ngược và hậu quả.

## 2. Preserve invariants; replace only what must change

- **Description:** Phân biệt phần lõi cần bảo toàn với phần phụ thuộc bối cảnh cần thay; cô lập thay đổi và kiểm tra tương thích.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 1; `DECISION_REPORT.md` mục 1 và inference; `UNIVERSAL_KNOWLEDGE.md` FACT 1, inference A.
- **Frequency:** 3/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Mô hình này được ghi nhận là chiến lược chuyển đổi. **INFERENCE:** Bất biến có thể tái dùng nên được xác định trước khi đổi kiến trúc.

## 3. Verify before trust

- **Description:** Đầu ra, dù đến từ nội bộ hay bên ngoài, phải qua xác thực, kiểm tra độc lập và khả năng từ chối.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 2, 8; `FAILURE_LIBRARY.md` mục rủi ro; `UNIVERSAL_KNOWLEDGE.md` FACT 2, 6 và inference B.
- **Frequency:** 4/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Schema validation, critics và probes được mô tả. **INFERENCE:** Không lấy sự tự tin hay tính trôi chảy làm chứng cứ đúng.

## 4. Separate proposal, evaluation, authorization, and action

- **Description:** Tách việc tạo phương án, thẩm định, phê chuẩn và thực thi thành các bước có thể kiểm tra riêng.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 3, 7; `DECISION_REPORT.md` mục 3 và inference; `UNIVERSAL_KNOWLEDGE.md` FACT 2, inference B.
- **Frequency:** 3/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Các bước critic, phê duyệt và triển khai được ghi riêng. **INFERENCE:** Tách vai trò làm giảm khả năng tự xác nhận sai sót của chính bộ phận tạo ra đề xuất.

## 5. Require explicit, structured acceptance

- **Description:** Làm rõ đầu vào, lưu thành đặc tả có trạng thái và yêu cầu xác nhận tường minh trước khi đóng băng hoặc thay đổi.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 6; `DECISION_REPORT.md` mục 3; `UNIVERSAL_KNOWLEDGE.md` FACT 4, inference A.
- **Frequency:** 3/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Quy trình nhiều trạng thái, xác nhận và đóng băng được báo cáo. **INFERENCE:** Không suy diễn đồng thuận từ im lặng hoặc câu trả lời mơ hồ.

## 6. Constrain generation with explicit contracts

- **Description:** Chỉ chấp nhận kết quả nằm trong schema, luật và phạm vi được định nghĩa; giữ quyền từ chối kết quả lệch chuẩn.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 2; `FAILURE_LIBRARY.md` rủi ro 1; `UNIVERSAL_KNOWLEDGE.md` FACT 2 và inference A/B.
- **Frequency:** 3/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Schema guard và luật hợp lệ được mô tả là gate. **INFERENCE:** Hợp đồng nên được kiểm tra trước khi kết quả gây tác động.

## 7. Evaluate across declared independent criteria

- **Description:** Đánh giá phương án theo nhiều chiều độc lập được công bố trước, không để một tiêu chí đơn lẻ che lấp trade-off.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 3; `DECISION_REPORT.md` inference về trade-off; `UNIVERSAL_KNOWLEDGE.md` FACT 2, inference A.
- **Frequency:** 3/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Thiết kế yêu cầu đánh giá đa chiều. **INFERENCE:** Chỉ số phải có định nghĩa, baseline, trọng số và ngưỡng; thiếu chúng thì điểm chỉ có tính tham khảo.

## 8. Prefer evidence over completion claims

- **Description:** Đối chiếu trạng thái tuyên bố với artifact, bằng chứng kiểm tra và phạm vi thực tế.
- **Evidence:** `INVENTORY_REPORT.md` phạm vi và mục phiên bản; `DECISION_REPORT.md` mục điều chỉnh; `FAILURE_LIBRARY.md` chênh lệch tài liệu/kho; `UNIVERSAL_KNOWLEDGE.md` FACT 8, inference C.
- **Frequency:** 4/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Báo cáo ghi nhận chênh lệch giữa một tuyên bố hoàn tất và inventory checkout. **INFERENCE:** Mọi trạng thái “xong” cần được chứng thực bằng artifact và kết quả có thể kiểm tra.

## 9. Make auditability durable

- **Description:** Giữ dấu vết bất biến hoặc append-only cho quyết định, thay đổi, cảnh báo và bằng chứng.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 4, 9; `DECISION_REPORT.md` mục 1, 3; `FAILURE_LIBRARY.md` bài học; `UNIVERSAL_KNOWLEDGE.md` FACT 1, 7 và inference C.
- **Frequency:** 4/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Append-only audit/log được mô tả. **INFERENCE:** Log nên nối đầu vào, phiên bản, gate, người phê duyệt và kết quả để có thể tái dựng quyết định.

## 10. Stop, record, then investigate warnings

- **Description:** Khi có cảnh báo, dừng phần tác động, lưu hiện tượng và bằng chứng; không bịa nguyên nhân.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 9–10; `FAILURE_LIBRARY.md` mục 1 và bài học; `UNIVERSAL_KNOWLEDGE.md` inference C.
- **Frequency:** 3/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Quy tắc dừng và ghi log được nêu, nhưng log hiện không có sự cố. **INFERENCE:** Chỉ kết luận nguyên nhân gốc sau điều tra có bằng chứng.

## 11. Prefer reversible, staged change

- **Description:** Chia thay đổi thành giai đoạn nhỏ, kiểm tra trước tác động và giữ khả năng rollback.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 5; `DECISION_REPORT.md` mục 3 và inference; `FAILURE_LIBRARY.md` bài học; `UNIVERSAL_KNOWLEDGE.md` FACT 3 và inference B.
- **Frequency:** 4/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Lộ trình theo phase, sandbox và canary được mô tả như thiết kế/biện pháp. **INFERENCE:** Bước đi nên nhỏ tương ứng với mức rủi ro, có tiêu chí dừng và phục hồi.

## 12. Treat missing evidence as UNKNOWN

- **Description:** Không biến dữ liệu thiếu thành khẳng định, kết quả đạt, hoặc nguyên nhân được xác nhận.
- **Evidence:** `INVENTORY_REPORT.md` mục UNKNOWN; `DECISION_REPORT.md` mục UNKNOWN; `FAILURE_LIBRARY.md` mục 1 và UNKNOWN; `UNIVERSAL_KNOWLEDGE.md` FACT 8, UNKNOWN.
- **Frequency:** 4/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Các báo cáo đánh dấu rõ những khoảng trống không thể xác minh. **INFERENCE:** UNKNOWN là trạng thái hợp lệ cần giữ cho tới khi có chứng cứ.

## 13. Scale investigation depth with risk

- **Description:** Dùng sàng lọc nhanh cho phạm vi rộng, rồi tăng độ sâu và yêu cầu trích dẫn khi rủi ro hoặc độ bất định cao.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 8 và inference; `UNIVERSAL_KNOWLEDGE.md` FACT 5, inference C.
- **Frequency:** 2/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Phương pháp phân tích ba cấp được ghi nhận. **INFERENCE:** Chi phí kiểm chứng nên tương xứng với hệ quả của quyết định.

## 14. Keep failure evidence distinct from risk forecasts

- **Description:** Phân biệt sự cố đã xảy ra, nhánh lỗi được mô hình hóa, và rủi ro giả định.
- **Evidence:** `FAILURE_LIBRARY.md` mục 1–3 và UNKNOWN; `UNIVERSAL_KNOWLEDGE.md` FACT 8, inference C.
- **Frequency:** 2/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Failure Library không tìm thấy sự cố lịch sử, nhưng có rủi ro dự đoán và nhánh lỗi trong mô hình. **INFERENCE:** Gộp ba loại này sẽ làm sai lệch bài học và mức độ tin cậy.

## 15. Connect assumptions without mistaking connection for proof

- **Description:** Theo dõi quan hệ giữa các ý tưởng để lộ giả định cô lập, nhưng không coi liên kết là bằng chứng đúng.
- **Evidence:** `KNOWLEDGE_REPORT.md` nguyên lý 9 và inference cuối; `UNIVERSAL_KNOWLEDGE.md` FACT 7, inference cuối.
- **Frequency:** 2/5 báo cáo.
- **FACT / INFERENCE:** **FACT:** Ma trận liên kết yêu cầu ý tưởng có kết nối. **INFERENCE:** Graph phụ thuộc hữu ích cho truy vấn và kiểm tra độ phủ, không thay thế kiểm chứng.

## 16. Frequency summary

**FACT:** Các tần suất trên đếm báo cáo có diễn đạt nguyên lý hoặc biểu hiện tương đương, không đếm số lần câu chữ lặp lại bên trong cùng tài liệu. Hai nguyên lý có thể cùng được hỗ trợ bởi một báo cáo; không cộng tần suất như xác suất hoặc biểu quyết.

**INFERENCE:** Các cụm được lặp nổi bật nhất là quyền con người, kiểm chứng, audit, staged change và đối chiếu tuyên bố với bằng chứng. Đây là mức ưu tiên lưu giữ trong bộ hồ sơ, không phải phép đo tâm lý nội tại của C2.

**UNKNOWN:** Không đủ bằng chứng để xác lập mọi niềm tin riêng tư hay toàn bộ nguyên lý của C2; báo cáo chỉ thể hiện tri thức đã được ghi nhận trong năm tài liệu được phép.
