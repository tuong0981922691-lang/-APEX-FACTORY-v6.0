# C2_DECISION_GRAPH

Chỉ tái dựng từ năm báo cáo đã cho. “C2” được dùng như tên vai trò phê duyệt trong hồ sơ; không gán thêm nhận dạng hay động cơ. Mỗi graph phân biệt FACT ghi nhận với INFERENCE về cách khái quát.

## Content Decisions

### C1. Đầu vào có đủ rõ để chốt yêu cầu không?

**Decision**  
↓  
**Input:** Yêu cầu ban đầu, câu trả lời làm rõ, các trường còn thiếu trong đặc tả.  
↓  
**Reasoning:** Hồ sơ ghi một quy trình tuần tự nhiều trạng thái; tóm tắt để xác nhận và chỉ đóng băng sau khi hoàn thành bước xác nhận (`KNOWLEDGE_REPORT.md`, nguyên lý 6; `UNIVERSAL_KNOWLEDGE.md`, FACT 4).  
↓  
**Outcome:** Nếu đủ rõ và được xác nhận → đặc tả có trạng thái đóng băng. Nếu thiếu/không rõ → tiếp tục hỏi hoặc giữ UNKNOWN; chưa có bằng chứng về luật xử lý mọi loại câu trả lời.

- **FACT:** Quy trình xác nhận/đóng băng được mô tả.
- **INFERENCE:** “Chấp nhận” cần yêu cầu rõ, trường trọng yếu đủ dữ liệu, xác nhận tường minh.
- **UNKNOWN:** Mức độ hoàn chỉnh tối thiểu và cơ chế giải quyết bất đồng.

### C2. Có thể tin một tuyên bố hoặc đầu ra chưa được xác minh không?

**Decision**  
↓  
**Input:** Nội dung, cấu trúc, nguồn và bằng chứng độc lập hiện có.  
↓  
**Reasoning:** Hồ sơ yêu cầu schema, critic, probes và so sánh với artifact; nguồn thiếu chứng cứ không được nâng thành факт (`KNOWLEDGE_REPORT.md`, nguyên lý 2, 8; `FAILURE_LIBRARY.md`, mục 3).  
↓  
**Outcome:** Đạt kiểm tra đã công bố → đủ điều kiện qua gate đó; lệch chuẩn → từ chối hoặc yêu cầu sửa; bằng chứng thiếu → UNKNOWN, không kết luận đạt.

- **FACT:** Có thiết kế về schema guard và kiểm chứng độc lập.
- **INFERENCE:** Chấp nhận có điều kiện theo gate, không phải tin tuyệt đối.
- **UNKNOWN:** Các tiêu chí pass đầy đủ và cách xử lý xung đột giữa nguồn.

## Technical Decisions

### T1. Nên bảo toàn hay thay một phần hệ thống khi đổi hướng?

**Decision**  
↓  
**Input:** Thành phần hiện hữu, nguyên lý bất biến, phần phụ thuộc bối cảnh và rủi ro tương thích.  
↓  
**Reasoning:** Decision Report nói rõ đề xuất giữ quyền hạn/audit/state-machine, thay phần miền cụ thể và dùng adapter/tương thích (`DECISION_REPORT.md`, mục 1; `KNOWLEDGE_REPORT.md`, nguyên lý 1).  
↓  
**Outcome:** Bảo toàn invariant được xác nhận; thay phần phụ thuộc; kiểm tra tương thích theo từng bước.

- **FACT:** Đây là chiến lược được blueprint ghi nhận.
- **INFERENCE:** Chọn thay đổi tối thiểu cần thiết thay vì viết lại mọi thứ.
- **UNKNOWN:** Danh sách invariant hoàn chỉnh và kết quả migration.

### T2. Đầu ra có được dùng làm đầu vào cho bước kế tiếp không?

**Decision**  
↓  
**Input:** Đầu ra ứng viên, schema/hợp đồng, kiểm tra quy tắc và đánh giá độc lập.  
↓  
**Reasoning:** Contract sai phải bị từ chối; critic phát hiện vấn đề; sandbox kiểm tra trước tác động (`UNIVERSAL_KNOWLEDGE.md`, FACT 2; `FAILURE_LIBRARY.md`, mục rủi ro).  
↓  
**Outcome:** Hợp lệ theo tất cả gate cần thiết → cho phép bước kế tiếp; không hợp lệ → reject/fix; thiếu kiểm tra → chưa chấp thuận.

- **FACT:** Schema, critics và sandbox được mô tả.
- **INFERENCE:** “Chấp nhận” là một quyết định theo gate, không phải đánh giá chủ quan đơn lẻ.
- **UNKNOWN:** Tiêu chí kỹ thuật cụ thể ngoài những ví dụ đã ghi trong báo cáo.

### T3. Thay đổi có được đi vào trạng thái tác động không?

**Decision**  
↓  
**Input:** Kết quả xác minh, sandbox, quyền/capability và xác nhận của người chịu trách nhiệm.  
↓  
**Reasoning:** Tài liệu đặt review và capability ở ranh giới tác động, đồng thời đề xuất rollout thận trọng (`KNOWLEDGE_REPORT.md`, nguyên lý 4–5; `UNIVERSAL_KNOWLEDGE.md`, inference B).  
↓  
**Outcome:** Chỉ qua gate khi người có thẩm quyền phê duyệt và quyền hợp lệ; nếu thiếu một gate thì không thực hiện.

- **FACT:** Gate con người và capability được ghi nhận trong blueprint.
- **INFERENCE:** Mức kiểm soát cần tăng theo mức độ khó hoàn tác.
- **UNKNOWN:** Cách cấp, thu hồi, kiểm tra quyền trong mọi môi trường.

## Strategic Decisions

### S1. Nên đổi toàn bộ hay giữ các năng lực có thể tái sử dụng?

**Decision**  
↓  
**Input:** Bất biến có giá trị lâu dài, logic phụ thuộc bối cảnh, chi phí và rủi ro thay đổi.  
↓  
**Reasoning:** Báo cáo quyết định ghi nhận giữ các cơ chế quản trị/audit/quyền hạn và thay logic phụ thuộc miền (`DECISION_REPORT.md`, mục 1, inference).  
↓  
**Outcome:** Giữ invariant, thay logic miền qua adapter/giai đoạn; tránh coi toàn bộ lịch sử cũ là phải giữ hoặc phải bỏ.

- **FACT:** Chiến lược giữ/thay có trong blueprint.
- **INFERENCE:** Đây là phương pháp chuyển đổi có kiểm soát.
- **UNKNOWN:** Bằng chứng so sánh định lượng giữa các phương án.

### S2. Có nên tuyên bố một giai đoạn hoàn tất?

**Decision**  
↓  
**Input:** Tuyên bố, artifact đã có, test/kiểm tra, phạm vi mục tiêu và lịch sử xác minh.  
↓  
**Reasoning:** Inventory và Failure Library ghi nhận không khớp giữa tuyên bố hoàn tất với artifact hiện có; khẳng định tài liệu không tự chứng minh hiện trạng (`INVENTORY_REPORT.md`, mục phiên bản; `FAILURE_LIBRARY.md`, mục chênh lệch).  
↓  
**Outcome:** Chỉ tuyên bố hoàn tất cho phạm vi có artifact và bằng chứng; nếu thiếu thì ghi UNKNOWN/đang chờ.

- **FACT:** Có chênh lệch giữa hai loại bằng chứng trong hồ sơ.
- **INFERENCE:** Mọi tuyên bố tiến độ cần đối chiếu nguồn hiện hành.
- **UNKNOWN:** Nguyên nhân và diễn tiến lịch sử của chênh lệch đó.

### S3. Nên đầu tư trước vào phạm vi nào?

**Decision**  
↓  
**Input:** Rủi ro, chi phí, phụ thuộc, lợi ích và sự chấp thuận của người có thẩm quyền.  
↓  
**Reasoning:** Tài liệu đề xuất rollout theo giai đoạn, giới hạn phạm vi đầu và tách phần có rủi ro/chi phí cao (`KNOWLEDGE_REPORT.md`, nguyên lý 5; `DECISION_REPORT.md`, mục 3).  
↓  
**Outcome:** Chọn phạm vi nhỏ có thể xác minh trước; chỉ mở rộng sau khi gate đạt.

- **FACT:** Chiến lược phân kỳ và kiểm soát phạm vi được ghi.
- **INFERENCE:** Ưu tiên có thể dựa trên rủi ro và khả năng xác minh, không chỉ độ hấp dẫn.
- **UNKNOWN:** Hàm ưu tiên, ngân sách và lợi ích định lượng.

## Quality Decisions

### Q1. Phương án có đủ chất lượng để qua vòng đánh giá?

**Decision**  
↓  
**Input:** Đánh giá đa chiều, tiêu chuẩn công bố, findings độc lập và trạng thái rủi ro.  
↓  
**Reasoning:** Thiết kế nêu nhiều trục đánh giá và ba loại outcome cho vòng critic: đạt, cần sửa, từ chối (`KNOWLEDGE_REPORT.md`, nguyên lý 3, 7).  
↓  
**Outcome:** Đạt tiêu chí → accept; lỗi có thể khắc phục → fix/re-evaluate; lỗi không chấp nhận được → reject; thiếu baseline/ngưỡng → điểm chỉ tham khảo.

- **FACT:** Đánh giá đa chiều và trạng thái critic được ghi.
- **INFERENCE:** Quyết định chất lượng tốt cần chỉ rõ tiêu chí pass/fail.
- **UNKNOWN:** Trọng số, baseline và ngưỡng tổng thể.

### Q2. Có nên chấp nhận score hoặc khuyến nghị khi đầu vào rỗng/thiếu?

**Decision**  
↓  
**Input:** Số lượng, độ phủ và độ tin cậy của đánh giá.  
↓  
**Reasoning:** Failure Library nêu một nhánh biên nơi điểm rỗng thành 0 và khuyến nghị loại; probe thiếu file cũng trả lỗi, không có drift (`FAILURE_LIBRARY.md`, mục 3).  
↓  
**Outcome:** Không xem thiếu dữ liệu là kết quả đầy đủ; gắn UNKNOWN/insufficient evidence và xin thêm dữ liệu.

- **FACT:** Hai hành vi thiếu đầu vào được báo cáo.
- **INFERENCE:** Trạng thái dữ liệu thiếu cần tách khỏi đánh giá chất lượng thấp.
- **UNKNOWN:** Có người kiểm tra hoặc override các kết quả biên trong thực tế không.

### Q3. Đã đủ bằng chứng để nói hệ thống ổn định?

**Decision**  
↓  
**Input:** So sánh lặp theo thời gian, nguồn độc lập, đối chiếu đặc tả với artifact.  
↓  
**Reasoning:** Ba probe ghi lại các phép kiểm tra lệch khác nhau; mỗi metric có giới hạn và không tự chứng minh ngữ nghĩa (`KNOWLEDGE_REPORT.md`, nguyên lý 8; `UNIVERSAL_KNOWLEDGE.md`, inference C).  
↓  
**Outcome:** Báo cáo mức nhất quán theo metric và phạm vi đã thử; không tổng quát hóa ngoài chứng cứ.

- **FACT:** Các loại probe hiện diện trong báo cáo khảo cổ.
- **INFERENCE:** Ổn định nên được xác nhận từ nhiều phép đo bổ trợ.
- **UNKNOWN:** Độ đại diện của mẫu và ngưỡng ổn định phù hợp.

## Acceptance / Rejection Gates

**FACT:** Những gate được nguồn ghi nhận gồm: xác nhận/đóng băng đặc tả; schema/rule validation; đánh giá đa chiều; critics; sandbox; capability và phê duyệt người; lưu audit. Các báo cáo không chứng minh tất cả đã được vận hành.

**INFERENCE:** Có thể tổng quát hóa quyết định chấp nhận thành:

1. **Accept:** đầu vào đủ rõ, hợp đồng hợp lệ, tiêu chí chất lượng đạt, kiểm tra an toàn hoàn tất, quyền và phê duyệt hợp lệ.
2. **Reject:** đầu ra vi phạm hợp đồng hoặc vượt ranh giới an toàn/quyền được công bố.
3. **Revise:** phát hiện có thể sửa và có thể kiểm tra lại.
4. **Hold / UNKNOWN:** thiếu dữ liệu, tiêu chí, quyền hoặc chứng cứ; không chuyển trạng thái tác động.

**UNKNOWN:** Không có bằng chứng đủ để khẳng định đây là quy tắc chính thức được thực thi thống nhất trong mọi tình huống.
