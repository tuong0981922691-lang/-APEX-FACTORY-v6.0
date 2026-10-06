# C2_FAILURE_PATTERNS

## Giới hạn chứng cứ

Nguồn duy nhất cho phần này là `FAILURE_LIBRARY.md`. Báo cáo đó không tìm thấy sự cố lịch sử, thử nghiệm hỏng hay hướng đi bị bỏ có nguyên nhân đã xác nhận. Vì vậy, các mục dưới đây là **failure mode suy ra từ rủi ro được ghi nhận hoặc điều kiện lỗi được mô hình hóa**, không phải tuyên bố rằng sự cố từng xảy ra.

## Pattern 1 — Completion claim without artifact evidence

1. **Tên thất bại:** Tuyên bố hoàn tất không khớp với artifact được kiểm kê.
2. **Dấu hiệu nhận biết:** Tài liệu nói một phạm vi đã xong nhưng inventory hiện thời không có artifact tương ứng.
3. **Nguyên nhân:** **FACT:** Chênh lệch giữa blueprint và checkout được ghi nhận. **INFERENCE:** Trạng thái tài liệu/artifact chưa được đồng bộ.
4. **Hậu quả:** Người ra quyết định có thể tin nhầm thiết kế là triển khai thực tế.
5. **Cách tránh:** Đối chiếu từng tuyên bố với artifact và bằng chứng kiểm tra; ghi UNKNOWN khi chưa xác minh.
6. **FACT / INFERENCE:** **FACT:** Chênh lệch hiện diện trong báo cáo khảo cổ. **INFERENCE:** Đây là pattern rủi ro thông tin, chưa được chứng minh là sự cố gây hậu quả.

## Pattern 2 — Missing evidence interpreted as negative quality

1. **Tên thất bại:** Thiếu dữ liệu bị tính như kết quả xấu đã được xác nhận.
2. **Dấu hiệu nhận biết:** Tập đánh giá rỗng được chuyển thành điểm 0 và khuyến nghị loại.
3. **Nguyên nhân:** **FACT:** Failure Library ghi điều kiện này trong logic được khảo cổ. **INFERENCE:** Không phân biệt “chưa đo” với “đã đo và không đạt”.
4. **Hậu quả:** Quyết định có thể loại nhầm đối tượng hoặc đánh đồng lỗi dữ liệu với chất lượng.
5. **Cách tránh:** Dùng trạng thái `UNKNOWN/insufficient evidence`; tạm giữ quyết định đến khi có đầu vào hợp lệ.
6. **FACT / INFERENCE:** **FACT:** Hành vi nhánh rỗng được báo cáo. **INFERENCE:** Nguy cơ quyết định sai là hệ quả có thể xảy ra, không phải sự kiện được log.

## Pattern 3 — Missing comparison file treated as a completed probe

1. **Tên thất bại:** Kiểm tra lệch không đủ dữ liệu nhưng bị hiểu như đã đánh giá ổn định.
2. **Dấu hiệu nhận biết:** Một phiên bản đối chiếu thiếu; kết quả chỉ báo lỗi và không có điểm drift.
3. **Nguyên nhân:** **FACT:** Failure Library ghi nhánh thiếu tệp. **INFERENCE:** Người đọc hoặc caller có thể bỏ qua trạng thái lỗi.
4. **Hậu quả:** Độ ổn định không được chứng minh nhưng vẫn có thể bị xem là đã kiểm tra.
5. **Cách tránh:** Buộc caller phân biệt kết quả lỗi với kết quả pass; không gán mặc định đạt khi metric là null.
6. **FACT / INFERENCE:** **FACT:** Có nhánh lỗi thiếu dữ liệu. **INFERENCE:** Hiểu nhầm đầu ra có thể tạo false assurance; không có log xác nhận việc đó từng xảy ra.

## Pattern 4 — Unvalidated external output enters consequential workflow

1. **Tên thất bại:** Đầu ra ngoài sai hợp đồng đi tiếp vào quy trình có tác động.
2. **Dấu hiệu nhận biết:** Output không qua schema validation hoặc bị tiếp nhận chỉ vì có vẻ hợp lý.
3. **Nguyên nhân:** **FACT:** Đây là rủi ro dự đoán trong Failure Library. **INFERENCE:** Thiếu gate hoặc gate không được thực thi.
4. **Hậu quả:** Dữ liệu sai có thể lan sang quyết định, artifact hoặc tác động tiếp theo.
5. **Cách tránh:** Validate schema và quy tắc, reject lệch chuẩn, audit đầu vào/đầu ra, đánh giá độc lập trước khi dùng.
6. **FACT / INFERENCE:** **FACT:** Rủi ro và các biện pháp dự kiến được nêu. **INFERENCE:** Hậu quả là khả năng; không có bằng chứng rủi ro đã thành sự cố.

## Pattern 5 — Uncontrolled change causes operational breakage

1. **Tên thất bại:** Thay đổi có tác động được áp dụng mà thiếu quyền, thử nghiệm hoặc rollout an toàn.
2. **Dấu hiệu nhận biết:** Không có phê duyệt/quyền hợp lệ, sandbox, canary hoặc phương án rollback.
3. **Nguyên nhân:** **FACT:** Crash khi hot-inject được nêu là rủi ro dự đoán. **INFERENCE:** Ranh giới quyền hoặc bước kiểm tra bị bỏ qua.
4. **Hậu quả:** Gián đoạn hoặc lỗi trên môi trường đang hoạt động.
5. **Cách tránh:** Phê duyệt người, quyền tối thiểu, sandbox, rollout từng bước, theo dõi và rollback.
6. **FACT / INFERENCE:** **FACT:** Rủi ro crash và biện pháp phòng ngừa được ghi. **INFERENCE:** Không có crash thực tế nào được xác nhận.

## Pattern 6 — Scope expands beyond what can be specified or verified

1. **Tên thất bại:** Phạm vi quá rộng làm đặc tả rỗng hoặc không thể kiểm chứng.
2. **Dấu hiệu nhận biết:** Mục tiêu bao trùm nhiều khả năng nhưng thiếu tiêu chí pass, giới hạn và thứ tự ưu tiên.
3. **Nguyên nhân:** **FACT:** Rủi ro phạm vi ontology quá rộng được ghi trong báo cáo. **INFERENCE:** Không chia nhỏ hoặc không giới hạn MVP.
4. **Hậu quả:** Công việc khó hoàn tất, chất lượng khó đo và quyết định bị trì hoãn.
5. **Cách tránh:** Giới hạn phạm vi ban đầu, chia phase, định nghĩa đầu ra và tiêu chí trước khi mở rộng.
6. **FACT / INFERENCE:** **FACT:** Đây là rủi ro được dự báo. **INFERENCE:** Hậu quả là suy luận phòng ngừa, không phải sự cố lịch sử.

## Pattern 7 — Costly work begins before cost is bounded

1. **Tên thất bại:** Cam kết nguồn lực cho nhánh chi phí cao trước khi có giới hạn/điểm duyệt.
2. **Dấu hiệu nhận biết:** Công việc tốn tài nguyên nằm trong phạm vi ban đầu mà thiếu budget hoặc lựa chọn bật/tắt.
3. **Nguyên nhân:** **FACT:** Chi phí ngoài cao được nhận diện như rủi ro. **INFERENCE:** Không có cost gate hay phase boundary.
4. **Hậu quả:** Vượt ngân sách hoặc làm chậm phần có giá trị ưu tiên cao hơn.
5. **Cách tránh:** Ước lượng, đặt ngưỡng chi, tách phase, yêu cầu phê duyệt khi vượt ngưỡng.
6. **FACT / INFERENCE:** **FACT:** Rủi ro chi phí được ghi. **INFERENCE:** Không có bằng chứng từng vượt ngân sách.

## Pattern 8 — Audit trail is incomplete or mutable

1. **Tên thất bại:** Không thể tái dựng nguồn gốc và lý do của quyết định.
2. **Dấu hiệu nhận biết:** Thiếu log đầu vào/đầu ra, phiên bản, gate hoặc xác nhận; log có thể bị sửa/xóa.
3. **Nguyên nhân:** **FACT:** Mất audit được nêu là rủi ro. **INFERENCE:** Ghi nhận không được nối xuyên suốt hoặc không bất biến.
4. **Hậu quả:** Khó điều tra, xác minh trách nhiệm và lặp lại kết quả.
5. **Cách tránh:** Audit append-only liên kết artifact, đặc tả, kết quả gate, thời điểm và quyền phê duyệt.
6. **FACT / INFERENCE:** **FACT:** Rủi ro và cách phòng ngừa được báo cáo. **INFERENCE:** Không có bằng chứng một audit trail đã thực sự mất.

## Pattern 9 — Compatibility breaks during replacement

1. **Tên thất bại:** Thay cấu phần gây gãy phụ thuộc hoặc hành vi đã tồn tại.
2. **Dấu hiệu nhận biết:** Thay trực tiếp thay vì adapter; phụ thuộc chưa kiểm kê; không kiểm tra khả năng tương thích.
3. **Nguyên nhân:** **FACT:** Breaking change với phần cũ được nêu như rủi ro. **INFERENCE:** Phạm vi phụ thuộc hoặc hợp đồng không được biết đầy đủ.
4. **Hậu quả:** Tác vụ trước đây hoạt động bị lỗi hoặc không thể dùng tiếp.
5. **Cách tránh:** Lập bản đồ phụ thuộc, giữ invariant, thêm adapter, test tương thích và rollout theo bước.
6. **FACT / INFERENCE:** **FACT:** Rủi ro tương thích được ghi nhận. **INFERENCE:** Không có báo cáo sự cố migration đã xảy ra.

## Pattern 10 — Metric without baseline or threshold creates false certainty

1. **Tên thất bại:** Điểm số có vẻ chính xác nhưng thiếu chuẩn so sánh hoặc ngưỡng quyết định.
2. **Dấu hiệu nhận biết:** Có công thức/điểm tổng hợp nhưng trọng số, baseline hoặc threshold chưa xác định.
3. **Nguyên nhân:** **FACT:** UNKNOWN về trọng số/baseline được nêu trong báo cáo tri thức. **INFERENCE:** Số liệu bị diễn giải quá mức.
4. **Hậu quả:** Phương án có thể được xếp hạng hoặc loại dựa trên độ chính xác giả.
5. **Cách tránh:** Công bố metric, nguồn đo, baseline, trọng số, threshold và cách xử lý thiếu dữ liệu; ghi điểm là tham khảo khi chưa đủ.
6. **FACT / INFERENCE:** **FACT:** Các giá trị còn UNKNOWN. **INFERENCE:** False certainty là rủi ro có thể có, không phải sự cố được xác nhận.

## Pattern 11 — Repetition is mistaken for independent confirmation

1. **Tên thất bại:** Nhiều nguồn/ý tưởng lặp lại cùng giả định nhưng bị tính như bằng chứng độc lập.
2. **Dấu hiệu nhận biết:** Đếm số input thay cho kiểm tra độ độc lập, provenance và tương quan.
3. **Nguyên nhân:** **FACT:** Mô hình tổng hợp nhiều input và ma trận ý tưởng được mô tả; tính đúng không suy ra từ liên kết. **INFERENCE:** Tương quan nguồn bị bỏ qua.
4. **Hậu quả:** Mức tin cậy bị thổi phồng hoặc giả định không có kiểm chứng.
5. **Cách tránh:** Theo dõi nguồn gốc, phân biệt nguồn độc lập với bản sao, yêu cầu bằng chứng khác loại và ghi giới hạn metric.
6. **FACT / INFERENCE:** **FACT:** Báo cáo nói liên kết không chứng minh đúng. **INFERENCE:** Lặp lại có thể tạo cảm giác đồng thuận giả.

## Pattern 12 — Planned safeguard is mistaken for deployed safeguard

1. **Tên thất bại:** Biện pháp phòng ngừa trong thiết kế bị xem như đang hoạt động.
2. **Dấu hiệu nhận biết:** Chỉ có mô tả gate/adapter/canary nhưng không có artifact hoặc kết quả kiểm tra xác nhận.
3. **Nguyên nhân:** **FACT:** Failure Library nói các biện pháp dự kiến chưa được xác nhận triển khai. **INFERENCE:** Trạng thái kế hoạch và vận hành bị nhập làm một.
4. **Hậu quả:** Quyết định dựa trên mức bảo vệ không thực sự tồn tại.
5. **Cách tránh:** Đánh dấu riêng planned, implemented, tested, deployed; chỉ nâng trạng thái khi có chứng cứ.
6. **FACT / INFERENCE:** **FACT:** Tình trạng biện pháp được ghi là UNKNOWN. **INFERENCE:** Nhầm trạng thái là pattern nguy hiểm; chưa có sự cố xác nhận.

## Tổng kết

**FACT:** Trong hồ sơ được phép, không có nguyên nhân gốc của một thất bại đã xảy ra, không có thử nghiệm hỏng được ghi và không có hướng đi bị bỏ được chứng minh.

**INFERENCE:** Các pattern trên là thư viện phòng ngừa từ rủi ro và nhánh biên có bằng chứng; không được trích dẫn chúng như “C2 từng gặp” nếu chưa có incident record.

**UNKNOWN:** Tần suất, mức độ nghiêm trọng thực tế, chủ sở hữu khắc phục và trạng thái triển khai biện pháp.
