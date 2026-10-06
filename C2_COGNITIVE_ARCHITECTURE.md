# C2_COGNITIVE_ARCHITECTURE

## Phạm vi

Chỉ dùng bốn tài liệu cho phép: `C2_CORE_PRINCIPLES.md`, `C2_DECISION_GRAPH.md`, `C2_FAILURE_PATTERNS.md`, `APEX_CORE_WISDOM.md`. Không coi “brain” trong mô hình tư duy là một module phần mềm có thật nếu tài liệu không xác nhận điều đó. Không ép đủ bảy brain.

### FACT

- Bốn tài liệu mô tả các năng lực tư duy: làm rõ yêu cầu, tạo đề xuất, đánh giá bằng tiêu chí, phê duyệt có thẩm quyền, hành động có gate, ghi audit và học từ bằng chứng.
- Tài liệu có nói tới các critic/evaluator, kiểm toán, orchestration và quy trình learning, nhưng chủ yếu như chức năng hoặc khái quát hóa; không xác nhận mỗi chức năng là một brain tự trị.
- Không tài liệu nào trong bốn tài liệu chứng minh một hệ thống bảy brain hoạt động đầy đủ.

### INFERENCE

Cấu trúc nhận thức phù hợp nhất với bằng chứng là **chuỗi năng lực có gate**, không phải một tập cố định các “não” độc lập:

`Sensing/Intake → Clarification & Framing → Proposal/Synthesis → Evaluation → Human Decision → Authorized Action → Audit → Evidence-based Learning`

Các mắt xích trên là chức năng suy ra từ quy trình; chúng không hàm ý triển khai bằng agent, mô hình hay dịch vụ riêng.

### UNKNOWN

- Số lượng cognitive brain thực thể, ranh giới nội bộ và việc chúng có chạy độc lập hay không.
- Có một mô hình nhận thức riêng của C2 ngoài những gì bốn tài liệu ghi lại hay không.
- Vòng học có cập nhật quy tắc/khả năng ra quyết định tự động hay chỉ là lưu lại bài học cho người đọc.

## Phân loại các “brain” được chứng cứ hỗ trợ

| Năng lực/brain chức năng | Trạng thái chứng cứ | FACT | INFERENCE | UNKNOWN |
|---|---|---|---|---|
| **1. Intake / Evidence Gathering** | Được nhắc gián tiếp, có bằng chứng về chức năng | Các tài liệu mô tả thu thập đầu vào, nguồn và bằng chứng trước quyết định (`C2_CORE_PRINCIPLES.md`, nguyên lý 5, 12; `C2_DECISION_GRAPH.md`, C1/C2). | Có thể mô hình hóa thành năng lực tiếp nhận và provenance. | Có brain độc lập hay chỉ là bước quy trình. |
| **2. Clarification / Framing** | Có bằng chứng về chức năng; brain riêng chỉ là giả thuyết | Decision graph có quyết định làm rõ, cấu trúc đầu vào, xác nhận và UNKNOWN khi thiếu (`C2_DECISION_GRAPH.md`, C1). | Một năng lực biến yêu cầu mơ hồ thành câu hỏi/đặc tả có thể kiểm tra. | Tự động hóa, chủ thể thực hiện và cách giải quyết bất đồng. |
| **3. Proposal / Synthesis** | Được nhắc gián tiếp, có bằng chứng về vai trò | Hệ thống được mô tả có thể thu thập bằng chứng và đưa đề xuất; tách đề xuất khỏi phán quyết (`C2_CORE_PRINCIPLES.md`, nguyên lý 1, 4). | Một năng lực hợp nhất đầu vào và đề xuất lựa chọn. | Brain nào tổng hợp, thuật toán nào dùng, và có độc lập với evaluator không. |
| **4. Evaluation / Critic** | Có bằng chứng về chức năng đánh giá; brain độc lập chưa xác nhận | Nguồn mô tả đánh giá đa chiều, critics, schema/rule gates và các outcome accept/fix/reject (`C2_CORE_PRINCIPLES.md`, nguyên lý 3, 6–7; `C2_DECISION_GRAPH.md`, Q1/T2). | Có thể tách các reviewer theo tiêu chí và risk. | Số critic, mức độc lập, cách giải quyết bất đồng, tính tự trị. |
| **5. Decision / Authorization** | Vai trò quyết định con người có bằng chứng; “brain” máy là UNKNOWN | Quyền phê duyệt con người trước hành động có tác động được nhắc nhiều lần (`C2_CORE_PRINCIPLES.md`, nguyên lý 1, 4; `C2_DECISION_GRAPH.md`, T3). | C2 là điểm quyết định cuối; chức năng decision orchestration có thể chuẩn bị lựa chọn và trạng thái. | C2 là một người, nhóm hay vai trò tổ chức; có một decision brain tự trị không. |
| **6. Action / Execution** | Được nhắc như giai đoạn downstream; brain riêng UNKNOWN | Quy trình tách authorization khỏi action, có gate và rollout (`C2_CORE_PRINCIPLES.md`, nguyên lý 4, 11; `C2_DECISION_GRAPH.md`, T3). | Đây là năng lực thực thi theo quyền sau khi quyết định được chấp thuận. | Agent thực thi, giới hạn quyền và mức tự động hóa. |
| **7. Audit / Memory** | Có bằng chứng về chức năng lưu vết; auditor brain riêng UNKNOWN | Append-only audit, evidence linkage và phân loại UNKNOWN được nêu (`C2_CORE_PRINCIPLES.md`, nguyên lý 9, 12, 14). | Có thể xem như bộ nhớ kiểm toán phục vụ truy nguyên. | Có brain tự đọc log, phát hiện sai lệch hay báo động không. |
| **8. Learning / Adaptation** | Có tài sản học từ bằng chứng ở mức tri thức; adaptive brain UNKNOWN | Nguồn nêu probe, hậu kiểm và chỉ cập nhật bài học khi nguyên nhân được xác minh (`APEX_CORE_WISDOM.md`, nguyên lý 21, 29, 49). | Vòng học nên biến hậu kiểm thành tri thức có phiên bản. | Quy tắc có tự thay đổi, ai phê chuẩn bài học, và có đo cải thiện không. |
| **9. Meta-orchestration** | Chỉ là khái niệm chức năng tổng hợp | Các báo cáo có mô hình hóa pipeline và phân tách proposal/evaluation/authorization/action (`C2_DECISION_GRAPH.md`, Acceptance / Rejection Gates). | Có thể có tầng điều phối chuyển trạng thái, nhưng điều phối có thể do quy trình hoặc con người đảm nhiệm. | Có meta-brain riêng điều phối các brain khác không. |

**FACT:** Bảng phân loại brain chức năng, không phải kiểm kê agent đã triển khai.  
**INFERENCE:** Tám chức năng là cách phân rã hữu ích nhất cho pipeline; chỉ chức năng/cổng được báo cáo là có bằng chứng, còn “brain” độc lập vẫn chưa được chứng minh.  
**UNKNOWN:** Không thể chốt “C2 có N brain” từ bốn tài liệu.

## Thinking pipeline

### FACT — trình tự được báo cáo

1. **INPUT:** Yêu cầu, nguồn, bằng chứng và dữ liệu có thể còn thiếu.
2. **CLARIFY / FRAME:** Làm rõ, cấu trúc hóa và giữ UNKNOWN khi chưa đủ dữ kiện.
3. **PROPOSE:** Tổng hợp thành lựa chọn/đề xuất, không đồng nhất đề xuất với phán quyết.
4. **EVALUATE:** Kiểm tra hợp đồng, tiêu chí độc lập, rủi ro và evidence.
5. **DECISION:** Accept, revise, reject hoặc hold; hành động consequential cần người có thẩm quyền.
6. **ACTION:** Thực hiện sau authorization, theo bước có thể kiểm tra/phục hồi.
7. **AUDIT:** Ghi nguồn, quyết định, quyền, gate và kết quả để truy nguyên.
8. **LEARNING:** So sánh, hậu kiểm và cập nhật bài học chỉ khi có bằng chứng đủ.

**Evidence:** `C2_DECISION_GRAPH.md` C1/C2, T2/T3, S2, Q1–Q3 và Acceptance / Rejection Gates; `C2_CORE_PRINCIPLES.md` nguyên lý 1, 3–5, 8–14; `APEX_CORE_WISDOM.md` phần I.

### INFERENCE — pipeline nhận thức tái dựng

```text
INPUT
  ↓
Clarify & frame (xác định dữ kiện, thiếu hụt, mức UNKNOWN)
  ↓
Synthesize options (tạo đề xuất có cấu trúc)
  ↓
Evaluate (contract + evidence + independent criteria + risk)
  ↓
DECISION (accept / revise / reject / hold; human authority)
  ↓
ACTION (authorized, staged, reversible where possible)
  ↓
AUDIT (append-only evidence trail)
  ↓
LEARNING (verified postmortem → versioned knowledge)
  ↺
```

Vòng quay về đầu chỉ có ý nghĩa khi bài học được xác minh và có người/qui trình chấp thuận áp dụng; nguồn không chứng minh có học tự động.

### UNKNOWN

- Có bước suy luận hoặc brain nào bị ẩn giữa các mắt xích hay không.
- Thứ tự trên có bắt buộc cho mọi quyết định không.
- Learning có làm thay đổi hành vi quyết định, hay chỉ lưu lại knowledge.

## Tái tạo tư duy, không tuyên bố đọc được nội tâm

### FACT

Các tài liệu thể hiện một chuẩn tư duy vận hành: bằng chứng trước khẳng định; thiếu chứng cứ thì UNKNOWN; tách proposal/evaluation/authority/action; chỉ hành động sau gate; lưu dấu vết để kiểm tra.

### INFERENCE

C2 được mô hình hóa như **người giữ ranh giới quyết định**, không phải “một siêu não biết mọi thứ”: chọn điều kiện chấp nhận, yêu cầu bằng chứng, quyết định khi nào sửa/từ chối/hold, và cho phép hoặc không cho phép tác động. Đây là tái dựng từ tài liệu, không phải khẳng định về trạng thái nhận thức bên trong cá nhân.

### UNKNOWN

Ý định, cảm xúc, thói quen nội tâm và những tiêu chí C2 chưa ghi ra.
