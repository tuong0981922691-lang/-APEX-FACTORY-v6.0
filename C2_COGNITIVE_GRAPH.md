# C2_COGNITIVE_GRAPH

## Quy ước

Graph này chỉ được tổng hợp từ `C2_CORE_PRINCIPLES.md`, `C2_DECISION_GRAPH.md`, `C2_FAILURE_PATTERNS.md` và `APEX_CORE_WISDOM.md`. “Brain” nghĩa là **năng lực nhận thức được mô hình hóa**, không xác nhận một agent/phần mềm độc lập.

**FACT:** Quy trình trong tài liệu tách đầu vào, làm rõ, đề xuất, đánh giá, quyết định, hành động, audit và học hỏi.  
**INFERENCE:** Có thể biểu diễn chúng thành node nối tiếp và một vòng học quay lại.  
**UNKNOWN:** Bốn tài liệu không xác nhận số brain tự trị hoặc topology nội bộ.

## Sơ đồ

```text
[B1 Intake & Evidence]
          ↓
[B2 Clarification & Framing]
          ↓
[B3 Proposal / Synthesis]
          ↓
[B4 Evaluation / Critic] ── thiếu evidence ──→ [Hold / UNKNOWN]
          ↓
[B5 Decision & Authorization — C2 / human authority]
          ↓ authorized only
[B6 Action / Execution]
          ↓
[B7 Audit & Memory]
          ↓ verified review
[B8 Learning / Knowledge Update]
          └──────────── feedback to B2/B3/B4 ────────────┘

[Meta-orchestration across B1–B8: UNKNOWN as an independent brain]
```

Node labels B1–B8 là nhãn sơ đồ tiện dụng, không phải khẳng định về “bảy bộ não” hoặc danh sách chính thức.

## Nodes

### B1 — Intake & Evidence Gathering

- **Brain:** Năng lực tiếp nhận/thu thập bằng chứng; brain riêng UNKNOWN.
- **Function:** Tập hợp yêu cầu, đầu vào, provenance và bằng chứng ban đầu.
- **Input:** Nguồn và dữ kiện có sẵn.
- **Output:** Tập input có nguồn gốc và các thiếu hụt được nhận diện.
- **Dependencies:** Cần B2 để đánh giá tính đủ/độ rõ; cần B7 để lưu dấu nguồn (đây là liên kết suy luận).
- **Evidence:** `C2_CORE_PRINCIPLES.md`, nguyên lý 5, 12; `C2_DECISION_GRAPH.md`, C1/C2.
- **FACT:** Nguồn/evidence được dùng làm đầu vào quyết định.
- **INFERENCE:** Có thể phân rã thành intake function.
- **UNKNOWN:** Cách tiếp nhận và provenance trong mọi tình huống.

### B2 — Clarification & Framing

- **Brain:** Năng lực làm rõ và cấu trúc hóa.
- **Function:** Phát hiện ambiguity/gap, đặt câu hỏi, chuyển đầu vào thành đặc tả có thể xác nhận.
- **Input:** Output B1, các trường thiếu, tiêu chí và bối cảnh được cung cấp.
- **Output:** Yêu cầu/đặc tả rõ hơn hoặc trạng thái hold/UNKNOWN.
- **Dependencies:** B1 cung cấp nguồn; B3 cần output rõ; B5 cần trạng thái xác nhận (liên kết phụ thuộc được suy ra).
- **Evidence:** `C2_DECISION_GRAPH.md`, C1; `C2_CORE_PRINCIPLES.md`, nguyên lý 5, 12–13.
- **FACT:** Làm rõ và xác nhận trước khi đóng băng được mô tả.
- **INFERENCE:** Đây là một chức năng nhận thức riêng biệt.
- **UNKNOWN:** Brain/agent nào thực hiện, tiêu chí đủ, cách xử lý mâu thuẫn.

### B3 — Proposal / Synthesis

- **Brain:** Năng lực tạo/hợp nhất phương án.
- **Function:** Tạo đề xuất từ yêu cầu và bằng chứng mà không tự biến đề xuất thành phán quyết.
- **Input:** Đặc tả đã làm rõ, constraints, evidence từ B1/B2.
- **Output:** Một hoặc nhiều phương án có cấu trúc và căn cứ.
- **Dependencies:** B2 cung cấp mục tiêu; B4 thẩm định; B5 chọn/authorize (suy luận).
- **Evidence:** `C2_CORE_PRINCIPLES.md`, nguyên lý 1, 4; `C2_DECISION_GRAPH.md`, S1 và Acceptance / Rejection Gates.
- **FACT:** Hệ thống được mô tả tạo đề xuất tách khỏi phê duyệt.
- **INFERENCE:** Có thể mô hình hóa thành proposal/synthesis brain.
- **UNKNOWN:** Có bao nhiêu phương án được tạo và phương pháp hợp nhất cụ thể.

### B4 — Evaluation / Critic

- **Brain:** Năng lực đánh giá; số và tính độc lập của brain reviewer UNKNOWN.
- **Function:** Kiểm tra hợp đồng, bằng chứng, tiêu chí độc lập, rủi ro và thiếu hụt.
- **Input:** Phương án B3, tiêu chí được công bố, nguồn và kết quả kiểm tra.
- **Output:** Acceptable / findings-to-fix / reject recommendation / insufficient evidence.
- **Dependencies:** Cần output B3, framing/criteria B2; cung cấp evidence cho B5; findings có thể quay lại B3.
- **Evidence:** `C2_CORE_PRINCIPLES.md`, nguyên lý 3, 6–7; `C2_DECISION_GRAPH.md`, C2/T2/Q1–Q3.
- **FACT:** Nguồn mô tả validators, critics, metric và outcome phân biệt.
- **INFERENCE:** Nhiều evaluator độc lập có thể triển khai chức năng này.
- **UNKNOWN:** Số evaluator, cách resolve bất đồng, độ chính xác.

### B5 — Decision & Authorization

- **Brain:** Vai trò quyết định/ủy quyền; tài liệu gắn quyền cuối với con người có thẩm quyền.
- **Function:** Chọn accept/revise/reject/hold và cấp hoặc từ chối quyền cho hành động có tác động.
- **Input:** Proposal B3, assessment B4, UNKNOWN/gaps, risk, quyền và yêu cầu.
- **Output:** Quyết định có căn cứ; authorization hoặc hold/reject.
- **Dependencies:** Cần framing, proposal, evaluation và ranh quyền; kích hoạt B6 chỉ sau authorization.
- **Evidence:** `C2_CORE_PRINCIPLES.md`, nguyên lý 1, 4, 12; `C2_DECISION_GRAPH.md`, T3, Acceptance / Rejection Gates.
- **FACT:** Human authority được nhắc là gate cuối.
- **INFERENCE:** C2 là decision authority trong mô hình.
- **UNKNOWN:** “C2” là cá nhân, nhóm, vai trò hay cơ chế nào; có machine decision brain độc lập không.

### B6 — Action / Execution

- **Brain:** Năng lực thực hiện được ủy quyền; không có bằng chứng về execution brain độc lập.
- **Function:** Thực hiện quyết định theo quyền, giới hạn và phương án phục hồi.
- **Input:** Quyết định đã được authorize, scope, constraints và gate results.
- **Output:** Thay đổi/tác động cùng trạng thái/kết quả thực tế.
- **Dependencies:** B5 authorization; B7 audit; B4/B8 có thể nhận kết quả để xác minh/học (suy luận).
- **Evidence:** `C2_CORE_PRINCIPLES.md`, nguyên lý 4, 11, 19; `C2_DECISION_GRAPH.md`, T3.
- **FACT:** Action được tách khỏi authorization và được mô tả như downstream.
- **INFERENCE:** Thực thi nên giới hạn theo quyền và staged.
- **UNKNOWN:** Chủ thể, mức tự động hóa và hệ thống thực thi.

### B7 — Audit & Evidence Memory

- **Brain:** Năng lực ghi nhận/kiểm toán; auditor brain tự trị UNKNOWN.
- **Function:** Lưu dấu vết nguồn, quyết định, gate, quyền và outcome để truy nguyên.
- **Input:** Events từ B1–B6, artifact/evidence và trạng thái.
- **Output:** Audit trail có thể kiểm tra, trạng thái incident/risk/UNKNOWN.
- **Dependencies:** Nhận dữ liệu từ các node trước; B8 dựa trên record đã xác minh.
- **Evidence:** `C2_CORE_PRINCIPLES.md`, nguyên lý 9, 14; `APEX_CORE_WISDOM.md`, nguyên lý 22–23, 45.
- **FACT:** Append-only audit và sự phân biệt risk/incident được nêu.
- **INFERENCE:** Audit có thể được mô hình như bộ nhớ nhận thức hỗ trợ learning.
- **UNKNOWN:** Tính năng tự động phát hiện gian lận/sai lệch hoặc tự kiểm toán.

### B8 — Learning / Knowledge Update

- **Brain:** Năng lực học/hậu kiểm; adaptive brain UNKNOWN.
- **Function:** Tổng kết so sánh, hậu kiểm và cập nhật tri thức khi nguyên nhân/bằng chứng đã đủ.
- **Input:** Audit B7, kết quả thực, chênh lệch, bằng chứng lặp/độc lập.
- **Output:** Bài học đã phân loại FACT/INFERENCE/UNKNOWN và giả thuyết cần điều tra tiếp.
- **Dependencies:** B7 lưu evidence; B2/B3/B4 có thể dùng tri thức đã duyệt (feedback link suy luận).
- **Evidence:** `APEX_CORE_WISDOM.md`, nguyên lý 21, 29, 49–50; `C2_CORE_PRINCIPLES.md`, nguyên lý 10, 12, 14.
- **FACT:** Học từ lỗi đã xác minh được nêu; không có incident lịch sử đã xác nhận trong corpus.
- **INFERENCE:** Knowledge update nên versioned và có người/qui trình duyệt.
- **UNKNOWN:** Learning có tự cập nhật hành vi hay không.

### M — Meta-orchestration

- **Brain:** Meta-brain điều phối.
- **Function:** Có thể điều phối luồng, trạng thái, dependencies và gate giữa các node.
- **Input:** Trạng thái/evidence của B1–B8.
- **Output:** Lệnh chuyển tiếp, hold, retry hoặc escalation (đây chỉ là mô hình giả định).
- **Dependencies:** Theo giả thuyết sẽ bao trùm các node; không có bằng chứng dependency graph vận hành.
- **Evidence:** `C2_DECISION_GRAPH.md`, Acceptance / Rejection Gates; `C2_CORE_PRINCIPLES.md`, nguyên lý 4.
- **FACT:** Các tài liệu mô tả pipeline và phân tách trách nhiệm.
- **INFERENCE:** Cần có một cơ chế điều phối luồng, nhưng nó có thể là con người hoặc quy trình.
- **UNKNOWN:** Meta-brain riêng có tồn tại không; ai điều phối trên thực tế.

## Cognitive assets không phụ thuộc lĩnh vực

**FACT:** Bốn nguồn giữ lại các mô hình: clarify → decision gates; proposal/evaluation/authority/action separation; evidence-first validation; audit/memory; postmortem/learning; uncertainty handling.

**INFERENCE:** Các tài sản có khả năng tái sử dụng nhất là:

1. **Mô hình tư duy:** Tách điều đã biết, suy luận và chưa biết.
2. **Mô hình quyết định:** Accept / revise / reject / hold; quyết định gắn với bằng chứng và quyền.
3. **Mô hình học:** Chỉ chuyển incident/evidence thành lesson sau xác minh.
4. **Mô hình kiểm toán:** Lưu provenance, gate, decision, authorization và outcome có thể truy lại.
5. **Mô hình điều phối:** Chuyển trạng thái tuần tự, dừng ở gate chưa đạt, tiếp tục khi đủ điều kiện.

**UNKNOWN:** Các cơ chế này có được hiện thực thành nhiều brain hay chỉ được biểu diễn bằng một quy trình/con người.
