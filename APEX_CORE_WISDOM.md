# APEX_CORE_WISDOM

## Phạm vi chứng cứ

Chỉ kết tinh từ `INVENTORY_REPORT.md`, `KNOWLEDGE_REPORT.md`, `DECISION_REPORT.md`, `FAILURE_LIBRARY.md` và `UNIVERSAL_KNOWLEDGE.md`. Không bổ sung bằng cách đọc repository hoặc nguồn ngoài.

**FACT** dưới đây là điều được ghi trong năm báo cáo, không nhất thiết là sự kiện đã xảy ra ngoài hồ sơ. **INFERENCE** là quy tắc tổng quát hóa. **UNKNOWN** nêu giới hạn chứng cứ. Những pattern thất bại là rủi ro hoặc nhánh lỗi được mô tả, không được nâng thành incident lịch sử.

# I. 50 nguyên lý quan trọng

1. **Quyền con người ở gate tác động.** **FACT:** Các báo cáo nêu phê duyệt người có thẩm quyền trước tác động. **INFERENCE:** Độ chặt gate tăng theo hậu quả/khó hoàn tác. **UNKNOWN:** Mô hình quyền thống nhất.
2. **Tách đề xuất khỏi phán quyết.** **FACT:** Có phân biệt critic/đề xuất với phê duyệt. **INFERENCE:** Người tạo phương án không nên tự phê chuẩn phương án đó. **UNKNOWN:** Phân công vai trò luôn độc lập đến mức nào.
3. **Kiểm chứng trước khi tin.** **FACT:** Schema, critics, probes và so khớp artifact được ghi nhận. **INFERENCE:** Mọi đầu ra cần bằng chứng tương ứng với rủi ro. **UNKNOWN:** Bộ xác minh đầy đủ.
4. **Hợp đồng rõ trước khi sinh kết quả.** **FACT:** Báo cáo mô tả kiểm tra schema và luật. **INFERENCE:** Định nghĩa hợp lệ trước khi thực thi. **UNKNOWN:** Schema áp dụng cho mọi luồng.
5. **Cho phép từ chối.** **FACT:** Đầu ra sai chuẩn có thể bị reject. **INFERENCE:** Hệ thống không nên bị buộc phải chọn một phương án không đạt. **UNKNOWN:** Tiêu chí reject toàn diện.
6. **Đánh giá đa chiều.** **FACT:** Chất lượng được mô tả theo nhiều trục. **INFERENCE:** Một điểm tổng không nên che khuất trade-off. **UNKNOWN:** Trọng số, baseline và ngưỡng.
7. **Ghi rõ chuẩn đo.** **FACT:** Báo cáo nêu các trọng số/baseline còn thiếu là UNKNOWN. **INFERENCE:** Không trình bày metric chưa hiệu chỉnh như chân lý. **UNKNOWN:** Chuẩn phù hợp từng bối cảnh.
8. **Bảo toàn invariant.** **FACT:** Chiến lược được ghi là giữ lõi quản trị/quyền/audit khi thay phần phụ thuộc bối cảnh. **INFERENCE:** Phân biệt invariant với lựa chọn triển khai trước khi đổi. **UNKNOWN:** Danh sách bất biến đầy đủ.
9. **Thay đổi tối thiểu có chủ đích.** **FACT:** Blueprint được báo cáo mô tả adapter và thay phần chuyên biệt. **INFERENCE:** Cô lập vùng đổi giúp giảm phạm vi lỗi. **UNKNOWN:** Hiệu quả thực tế.
10. **Không nhầm thiết kế với triển khai.** **FACT:** Có chênh lệch giữa tuyên bố hoàn tất và artifact được kiểm kê. **INFERENCE:** Mỗi trạng thái phải gắn artifact xác nhận. **UNKNOWN:** Nguyên nhân của chênh lệch.
11. **Không nhầm triển khai với vận hành.** **FACT:** Báo cáo phân biệt đề xuất, artifact và trạng thái triển khai. **INFERENCE:** Cần các nhãn planned/implemented/tested/deployed riêng. **UNKNOWN:** Trạng thái vận hành ngoài mẫu.
12. **Đặc tả phải có cấu trúc.** **FACT:** Quy trình làm rõ và đóng băng đặc tả được ghi. **INFERENCE:** Yêu cầu tự nhiên nên được chuyển thành trường có thể kiểm tra. **UNKNOWN:** Bộ trường bắt buộc chung.
13. **Xác nhận phải tường minh.** **FACT:** Quy trình mô tả xác nhận trước đóng băng. **INFERENCE:** Im lặng hoặc mơ hồ không phải chấp thuận. **UNKNOWN:** Luật xử lý mọi loại phản hồi.
14. **Làm rõ trước khi hành động.** **FACT:** Có quy trình nhiều trạng thái để hỏi, tóm tắt, bổ sung. **INFERENCE:** Thiếu dữ kiện trọng yếu thì hold và hỏi thêm. **UNKNOWN:** Ngưỡng “đủ rõ”.
15. **Chia giai đoạn.** **FACT:** Blueprint được mô tả theo các phase. **INFERENCE:** Mỗi phase nên có đầu ra kiểm chứng được. **UNKNOWN:** Mức phân kỳ tối ưu.
16. **Giới hạn phạm vi ban đầu.** **FACT:** Rủi ro phạm vi quá rộng và biện pháp giới hạn MVP được ghi. **INFERENCE:** Bắt đầu nhỏ giúp phát hiện thiếu sót sớm. **UNKNOWN:** Quy mô tối thiểu phù hợp.
17. **Có gate trước tác động.** **FACT:** Báo cáo nêu schema, sandbox, capability và người duyệt. **INFERENCE:** Không bước qua gate chỉ vì lịch trình hoặc chi phí đã bỏ ra. **UNKNOWN:** Thứ tự gate trong mọi quy trình.
18. **Ưu tiên khả năng đảo ngược.** **FACT:** Sandbox/canary/rollback được ghi như cơ chế phòng ngừa. **INFERENCE:** Thử nhỏ trước khi cam kết lớn. **UNKNOWN:** Rollback khả thi ở mọi môi trường.
19. **Quyền tối thiểu cho hành động.** **FACT:** Capability/token gắn với hành động tác động được mô tả. **INFERENCE:** Cấp quyền đúng phạm vi và thời hạn. **UNKNOWN:** Quy trình cấp/thu hồi.
20. **Dừng khi có cảnh báo.** **FACT:** Quy tắc yêu cầu dừng và ghi nhận cảnh báo. **INFERENCE:** Chặn lan truyền trước khi điều tra. **UNKNOWN:** Thực tế mọi cảnh báo đã được ghi.
21. **Ghi bằng chứng trước khi giải thích.** **FACT:** Failure Library cấm suy diễn nguyên nhân khi thiếu incident record. **INFERENCE:** Tách quan sát khỏi giả thuyết. **UNKNOWN:** Nguyên nhân gốc của rủi ro từng thành sự cố.
22. **Giữ log có thể kiểm toán.** **FACT:** Append-only được nêu cho log/audit. **INFERENCE:** Lưu nguồn, phiên bản, quyết định và kết quả. **UNKNOWN:** Mức bất biến trong hệ thống chạy.
23. **Nối quyết định với artifact.** **FACT:** Báo cáo khuyến nghị gắn artifact với đặc tả và gate. **INFERENCE:** Mỗi quyết định nên truy vết được tới chứng cứ. **UNKNOWN:** Độ phủ hiện tại.
24. **Phân biệt UNKNOWN với FAIL.** **FACT:** Các báo cáo đánh dấu thiếu dữ liệu là UNKNOWN. **INFERENCE:** Không có bằng chứng không đồng nghĩa bằng chứng thất bại. **UNKNOWN:** Cách xử lý thống nhất mọi nơi.
25. **Phân biệt rủi ro với incident.** **FACT:** Failure Library tách rủi ro, nhánh lỗi và sự cố; không có incident được ghi. **INFERENCE:** Không kể rủi ro như lịch sử. **UNKNOWN:** Sự cố ngoài phạm vi hồ sơ.
26. **Thiếu đầu vào không tạo kết luận chắc chắn.** **FACT:** Nhánh dữ liệu rỗng/thiếu được ghi nhận. **INFERENCE:** Dùng “insufficient evidence”, không áp score mặc định. **UNKNOWN:** Guardrail đã vận hành ra sao.
27. **Dùng phép đo có giới hạn nhận thức.** **FACT:** Các probe và giới hạn metric được mô tả. **INFERENCE:** Metric bề mặt không thay thế đánh giá ngữ nghĩa/chất lượng. **UNKNOWN:** Độ tương quan metric với chất lượng thật.
28. **Kiểm tra qua nguồn độc lập.** **FACT:** Có probe so sánh nhiều nguồn/lần chạy. **INFERENCE:** Tính độc lập quan trọng hơn số lượng nguồn. **UNKNOWN:** Mức độc lập thực tế.
29. **Kiểm tra lại theo thời gian.** **FACT:** Probe so sánh phản hồi ở các thời điểm được mô tả. **INFERENCE:** Drift có thể là tín hiệu cần điều tra. **UNKNOWN:** Ngưỡng phổ quát.
30. **So đặc tả với kết quả thực.** **FACT:** Reverse comparison để tìm gap được ghi. **INFERENCE:** Xác minh cả chiều “ý định → kết quả” và “kết quả → mô tả”. **UNKNOWN:** Độ bao phủ phép so sánh.
31. **Tăng độ sâu theo rủi ro.** **FACT:** Phương pháp khảo sát ba cấp được ghi. **INFERENCE:** Phân bổ công sức điều tra theo tác động và bất định. **UNKNOWN:** Hàm phân loại rủi ro.
32. **Phản biện độc lập trước lựa chọn.** **FACT:** Vòng critic đa góc được mô tả. **INFERENCE:** Tìm lỗi trước khi hợp thức hóa phương án. **UNKNOWN:** Chất lượng thực tế của critic.
33. **Cho sửa rồi đánh giá lại khi phù hợp.** **FACT:** Các outcome phân biệt OK/FIX/REJECT được ghi. **INFERENCE:** Lỗi sửa được không cần dẫn thẳng tới loại bỏ. **UNKNOWN:** Ranh giới fixable.
34. **Tách lỗi chặn khỏi cảnh báo.** **FACT:** Báo cáo tri thức nhắc phân loại mức vi phạm. **INFERENCE:** Severity nên gắn hậu quả và hành động. **UNKNOWN:** Ma trận severity chung.
35. **Theo dõi phụ thuộc.** **FACT:** Ma trận liên kết và kiểm tra phụ thuộc được báo cáo. **INFERENCE:** Phụ thuộc rõ giúp nhận diện giả định cô lập. **UNKNOWN:** Tính đúng của mọi liên kết.
36. **Liên kết không đồng nghĩa chứng minh.** **FACT:** Báo cáo nói rõ graph liên kết không chứng minh đúng. **INFERENCE:** Mỗi liên kết vẫn cần bằng chứng. **UNKNOWN:** Mức độ graph bao phủ.
37. **Công bố trade-off.** **FACT:** Các báo cáo nói về lựa chọn và nhiều tiêu chí. **INFERENCE:** Ghi vì sao chấp nhận hy sinh tiêu chí nào. **UNKNOWN:** Trade-off định lượng.
38. **Không để metric quyết định ngoài thẩm quyền.** **FACT:** Điểm số là input cho quyết định, còn gate người được ghi. **INFERENCE:** Score hỗ trợ chứ không thay quyền phán quyết. **UNKNOWN:** Trường hợp override.
39. **Chi phí cần gate.** **FACT:** Chi phí cao được nhận diện như rủi ro cần phân kỳ. **INFERENCE:** Đặt giới hạn ngân sách và ngưỡng xin duyệt. **UNKNOWN:** Mức ngân sách.
40. **Bảo vệ tương thích.** **FACT:** Rủi ro breaking change và adapter được ghi. **INFERENCE:** Kiểm tra hợp đồng/phụ thuộc trước khi thay. **UNKNOWN:** Tỷ lệ tương thích.
41. **Không mở rộng trước khi chứng minh nền tảng.** **FACT:** Tài liệu khuyến nghị phase và MVP. **INFERENCE:** Mở rộng sau khi gate cơ bản đạt. **UNKNOWN:** Các gate đã đạt chưa.
42. **Lưu phiên bản của đặc tả.** **FACT:** Các báo cáo mô tả đặc tả đóng băng và audit liên kết. **INFERENCE:** Thay yêu cầu cần tạo phiên bản mới thay vì ghi đè. **UNKNOWN:** Chính sách versioning toàn cục.
43. **Bảo vệ dữ liệu khi chia sẻ audit.** **FACT:** Che thông tin nhạy cảm được ghi trong cơ chế xác minh. **INFERENCE:** Minh bạch cần đi cùng giới hạn lộ dữ liệu. **UNKNOWN:** Chuẩn che dữ liệu đầy đủ.
44. **Tuyên bố có thể tái kiểm tra.** **FACT:** Nhu cầu evidence và citation được nêu. **INFERENCE:** Người khác cần có thể lần ngược căn cứ. **UNKNOWN:** Mức tái lập độc lập.
45. **Log trống cũng là trạng thái cần diễn giải thận trọng.** **FACT:** Log sự cố không có entry. **INFERENCE:** Không kết luận “không từng có sự cố”. **UNKNOWN:** Vì chưa có hay chưa ghi.
46. **Định nghĩa pass trước khi đo.** **FACT:** Các ngưỡng/baseline có chỗ UNKNOWN. **INFERENCE:** Tiêu chí hậu nghiệm dễ tạo thiên lệch. **UNKNOWN:** Giá trị chuẩn.
47. **Không ép điểm tổng khi tiêu chí chưa cân bằng.** **FACT:** Công thức tổng hợp thiếu trọng số được ghi. **INFERENCE:** Báo cáo vector/trade-off cho tới khi weights được xác định. **UNKNOWN:** Cách cân bằng tối ưu.
48. **Giữ dấu vết của thay đổi hướng.** **FACT:** Decision Report ghi nhận lý do/điều chỉnh trong blueprint nhưng thiếu lịch sử đầy đủ. **INFERENCE:** Log quyết định nên giữ lựa chọn, phương án thay thế và thời điểm. **UNKNOWN:** Toàn bộ lịch sử.
49. **Học từ lỗi đã xác minh.** **FACT:** Failure Library yêu cầu không gán nguyên nhân nếu thiếu chứng cứ. **INFERENCE:** Chỉ cập nhật nguyên lý sau hậu kiểm. **UNKNOWN:** Những bài học thực tế chưa ghi.
50. **Trung thực về giới hạn tri thức.** **FACT:** Năm báo cáo đánh dấu khoảng trống dữ liệu. **INFERENCE:** Uy tín hệ thống phụ thuộc vào việc không giả vờ biết. **UNKNOWN:** Mọi điều nằm ngoài năm báo cáo.

# II. 50 quyết định quan trọng

Mỗi mục là dạng quyết định tổng quát hóa từ hồ sơ. “Outcome” ở đây là quy tắc đề xuất hoặc outcome được báo cáo, không khẳng định mọi quyết định đã được thi hành.

1. **Chốt yêu cầu?** **FACT:** Quy trình làm rõ rồi xác nhận. **INFERENCE:** Chốt khi dữ kiện trọng yếu đủ và được xác nhận. **UNKNOWN:** Ngưỡng đủ.
2. **Hỏi thêm?** **FACT:** Có các trạng thái làm rõ. **INFERENCE:** Hỏi khi thiếu hoặc mơ hồ. **UNKNOWN:** Số vòng tối đa.
3. **Đóng băng đặc tả?** **FACT:** Có bước freeze. **INFERENCE:** Chỉ freeze sau xác nhận. **UNKNOWN:** Cơ chế mở lại.
4. **Chấp nhận đầu ra?** **FACT:** Schema/rule gates được ghi. **INFERENCE:** Chỉ accept khi gate liên quan đạt. **UNKNOWN:** Toàn bộ gates.
5. **Từ chối đầu ra?** **FACT:** Reject khi lệch schema được mô tả. **INFERENCE:** Reject vi phạm không thể chấp nhận. **UNKNOWN:** Ma trận ngoại lệ.
6. **Yêu cầu sửa?** **FACT:** Outcome fix-list/revision tồn tại trong hồ sơ. **INFERENCE:** Chọn sửa khi vấn đề có thể khắc phục và kiểm thử lại. **UNKNOWN:** Fixability criteria.
7. **Giữ phương án ở trạng thái chờ?** **FACT:** UNKNOWN được giữ riêng. **INFERENCE:** Hold khi thiếu chứng cứ/quyền. **UNKNOWN:** SLA chờ.
8. **Dùng score tổng?** **FACT:** Metric đa chiều được đề xuất, weights chưa biết. **INFERENCE:** Chỉ dùng tổng điểm sau hiệu chỉnh. **UNKNOWN:** Weights.
9. **Chấp nhận metric?** **FACT:** Nhiều probe được mô tả. **INFERENCE:** Chọn metric phù hợp câu hỏi, ghi giới hạn. **UNKNOWN:** Metric chuẩn từng trường hợp.
10. **Chấp nhận vì nhiều nguồn đồng thuận?** **FACT:** Có tổng hợp nhiều nguồn. **INFERENCE:** Chỉ khi nguồn độc lập và provenance rõ. **UNKNOWN:** Mức độc lập.
11. **Tin kết quả ngoài?** **FACT:** Schema guard/kiểm chứng được ghi. **INFERENCE:** Không tin trước khi validate. **UNKNOWN:** Cấu hình thực tế.
12. **Cho phép tác động?** **FACT:** Người và capability ở gate. **INFERENCE:** Chỉ thực hiện khi quyền và approval hợp lệ. **UNKNOWN:** Quy trình quyền.
13. **Cần phê duyệt người?** **FACT:** Requires approval và human gate được ghi. **INFERENCE:** Có với thay đổi consequential. **UNKNOWN:** Ngưỡng consequential.
14. **Dừng khi cảnh báo?** **FACT:** Quy tắc stop/log được ghi. **INFERENCE:** Dừng đường tác động liên quan. **UNKNOWN:** Điều kiện resume.
15. **Ghi incident hay risk?** **FACT:** Hai loại cần phân biệt. **INFERENCE:** Chỉ gọi incident khi có event evidence. **UNKNOWN:** Sự kiện chưa ghi.
16. **Gán nguyên nhân gốc?** **FACT:** Chưa có incident record. **INFERENCE:** Chờ hậu kiểm bằng chứng. **UNKNOWN:** Nguyên nhân lịch sử.
17. **Tuyên bố hoàn tất?** **FACT:** Từng có mismatch claim/artifact. **INFERENCE:** Chỉ claim cho phạm vi artifact/test xác nhận. **UNKNOWN:** Trạng thái ngoài checkout.
18. **Đổi kiến trúc toàn phần?** **FACT:** Chiến lược ghi là preserve invariants, replace contextual logic. **INFERENCE:** Ưu tiên migration có phạm vi. **UNKNOWN:** Phương án thay thế.
19. **Giữ thành phần cũ?** **FACT:** Adapter/compatibility được đề xuất. **INFERENCE:** Giữ khi invariant/phụ thuộc còn giá trị. **UNKNOWN:** Danh sách đầy đủ.
20. **Thay thành phần cũ?** **FACT:** Logic miền được đề xuất thay. **INFERENCE:** Thay khi không còn phù hợp mục tiêu mới. **UNKNOWN:** Ngưỡng bằng chứng.
21. **Dùng adapter?** **FACT:** Biện pháp tương thích được nêu. **INFERENCE:** Dùng để cô lập thay đổi. **UNKNOWN:** Chi phí dài hạn.
22. **Chia phase?** **FACT:** Kế hoạch theo phase. **INFERENCE:** Chia khi rủi ro/phụ thuộc khác nhau. **UNKNOWN:** Số phase tối ưu.
23. **Mở rộng scope?** **FACT:** Rủi ro scope rộng được nhận diện. **INFERENCE:** Mở rộng khi phase trước đạt criteria. **UNKNOWN:** Criteria chính thức.
24. **Bắt đầu với MVP?** **FACT:** Hạn chế scope ban đầu được đề xuất. **INFERENCE:** Chọn lát cắt có thể xác minh. **UNKNOWN:** Kích thước MVP.
25. **Cho phép chi phí cao?** **FACT:** Cost risk và phase/toggle được ghi. **INFERENCE:** Cần budget approval. **UNKNOWN:** Budget/ROI.
26. **Triển khai ngay hay sandbox?** **FACT:** Sandbox trước tác động được mô tả. **INFERENCE:** Sandbox trước hành động rủi ro. **UNKNOWN:** Coverage sandbox.
27. **Rollout rộng hay canary?** **FACT:** Canary được nêu là biện pháp. **INFERENCE:** Thử nhóm nhỏ, quan sát, rồi mở rộng. **UNKNOWN:** Tỷ lệ canary.
28. **Rollback?** **FACT:** Rollback được gợi ý trong tri thức trung tính. **INFERENCE:** Chuẩn bị đường phục hồi trước tác động. **UNKNOWN:** Khả năng rollback từng loại.
29. **Chấp nhận rủi ro compatibility?** **FACT:** Breaking change được nhận diện. **INFERENCE:** Chỉ accept sau test tương thích hoặc waiver có quyền. **UNKNOWN:** Waiver process.
30. **Chọn giữa phương án?** **FACT:** Multi-axis comparison được ghi. **INFERENCE:** So sánh theo tiêu chí đã công bố và ghi trade-off. **UNKNOWN:** Trọng số.
31. **Tạo nhiều phương án?** **FACT:** Blueprint mô tả biến thể cạnh tranh. **INFERENCE:** Tạo lựa chọn khi trade-off chưa rõ. **UNKNOWN:** Số lượng cần thiết.
32. **Chấp nhận phương án điểm cao?** **FACT:** Scoring được thiết kế. **INFERENCE:** Chỉ accept nếu không vi phạm gate cứng. **UNKNOWN:** Tương quan điểm với kết quả.
33. **Dùng independent review?** **FACT:** Vòng critics được ghi. **INFERENCE:** Đánh giá riêng trước khi chốt. **UNKNOWN:** Tính độc lập của reviewers.
34. **Phản hồi lỗi như thế nào?** **FACT:** OK/FIX/REJECT được nêu. **INFERENCE:** Phân loại theo mức và khả năng khắc phục. **UNKNOWN:** Severity rubric đầy đủ.
35. **Chấp nhận test thiếu?** **FACT:** Thiếu bằng chứng được coi UNKNOWN. **INFERENCE:** Không coi thiếu test là pass. **UNKNOWN:** Waiver condition.
36. **Kết luận probe khi thiếu file?** **FACT:** Probe trả lỗi/không có metric. **INFERENCE:** Báo incomplete, không pass/fail. **UNKNOWN:** Caller behavior.
37. **Xử lý score trống?** **FACT:** Có hành vi score 0/kill được nêu. **INFERENCE:** Sửa thành insufficient data thay vì negative score. **UNKNOWN:** Có override thật không.
38. **Ghi log nào?** **FACT:** Append-only log được đề xuất. **INFERENCE:** Ghi event đủ tái dựng. **UNKNOWN:** Retention/access.
39. **Chia sẻ audit ra sao?** **FACT:** Che dữ liệu nhạy cảm được ghi. **INFERENCE:** Chia sẻ tối thiểu cần thiết. **UNKNOWN:** Quy tắc phân loại dữ liệu.
40. **Liên kết giả định?** **FACT:** Idea matrix yêu cầu kết nối. **INFERENCE:** Dùng graph để phát hiện cô lập, rồi kiểm chứng cạnh. **UNKNOWN:** Coverage.
41. **Chọn độ sâu nghiên cứu?** **FACT:** Ba tier phân tích được ghi. **INFERENCE:** Tăng độ sâu theo risk/uncertainty. **UNKNOWN:** Threshold.
42. **Nâng một giả thuyết thành fact?** **FACT:** Deep analysis cần citation. **INFERENCE:** Chỉ nâng khi evidence trực tiếp ủng hộ. **UNKNOWN:** Chuẩn proof mọi domain.
43. **Tin kiểm tra lặp?** **FACT:** Drift probe tồn tại trong hồ sơ. **INFERENCE:** Dùng lặp để phát hiện biến thiên, không chứng minh đúng. **UNKNOWN:** Ngưỡng.
44. **Chọn ưu tiên?** **FACT:** C2 chốt một thứ tự trong tài liệu; lý do định lượng UNKNOWN. **INFERENCE:** Lưu lý do, trade-off và phương án bị hoãn. **UNKNOWN:** Tiêu chí gốc.
45. **Sửa hướng đi?** **FACT:** Blueprint ghi điều chỉnh/phân kỳ. **INFERENCE:** Sửa khi evidence, risk hoặc constraint đổi; lưu phiên bản. **UNKNOWN:** Toàn bộ các lần đổi.
46. **Khi nào chấp thuận ngoại lệ?** **FACT:** Override/approval được nhắc nhưng chưa giải thích đầy đủ. **INFERENCE:** Chỉ người có quyền, có lý do và audit. **UNKNOWN:** Quy trình override.
47. **Đóng incident?** **FACT:** Không có incident record trong hồ sơ. **INFERENCE:** Chỉ đóng khi remediation được xác minh. **UNKNOWN:** Close criteria thực tế.
48. **Khi nào công bố bài học?** **FACT:** Không được gán nguyên nhân khi thiếu evidence. **INFERENCE:** Công bố sau khi hậu kiểm phân biệt fact/assumption. **UNKNOWN:** Incident chưa biết.
49. **Khi nào dừng mở rộng?** **FACT:** Warnings, scope, cost và risk gates được nhắc. **INFERENCE:** Dừng khi tiêu chí an toàn/nguồn lực không đạt. **UNKNOWN:** Threshold cụ thể.
50. **Khi nào nói “đã biết”?** **FACT:** Báo cáo sử dụng UNKNOWN để ghi khoảng trống. **INFERENCE:** Chỉ khẳng định trong ranh evidence. **UNKNOWN:** Mọi tri thức chưa có trong năm báo cáo.

# III. 50 bài học thất bại quan trọng

> Trong từng mục, FACT mô tả bằng chứng trực tiếp hoặc nói rõ “không có incident”; INFERENCE là bài học phòng ngừa; UNKNOWN là phần chưa thể khẳng định.

1. **Claim/artifact mismatch.** **FACT:** Chênh lệch được báo cáo. **INFERENCE:** Audit từng claim với artifact. **UNKNOWN:** Vì sao xảy ra.
2. **Thiếu artifact bị coi như đã hoàn tất.** **FACT:** Mismatch hiện hữu trong hồ sơ. **INFERENCE:** Không suy trạng thái từ tài liệu đơn lẻ. **UNKNOWN:** Lịch sử triển khai.
3. **Score rỗng bị biến thành negative verdict.** **FACT:** Nhánh này được mô tả. **INFERENCE:** Thiếu data phải là UNKNOWN. **UNKNOWN:** Từng gây quyết định sai chưa.
4. **Thiếu file probe bị coi như pass.** **FACT:** Probe trả lỗi/metric vắng. **INFERENCE:** Không diễn giải null thành ổn định. **UNKNOWN:** Caller có xử lý sai chưa.
5. **Output không đúng schema lọt qua.** **FACT:** Đây là risk trong báo cáo. **INFERENCE:** Gate fail-closed. **UNKNOWN:** Có lần lọt qua không.
6. **Đầu ra trôi chảy bị nhầm với đúng.** **FACT:** Báo cáo yêu cầu verification. **INFERENCE:** Đòi evidence thay vì phong cách. **UNKNOWN:** Tần suất lỗi.
7. **Thay đổi tác động thiếu quyền.** **FACT:** Rủi ro hot-change được nêu. **INFERENCE:** Chặn khi thiếu token/approval. **UNKNOWN:** Có thay đổi trái quyền không.
8. **Thay đổi tác động thiếu sandbox.** **FACT:** Sandbox được đề xuất. **INFERENCE:** Kiểm tra trước triển khai. **UNKNOWN:** Có crash thật không.
9. **Rollout không có canary/rollback.** **FACT:** Canary là mitigation dự kiến. **INFERENCE:** Chuẩn bị phục hồi trước khi mở rộng. **UNKNOWN:** Mức sử dụng thực tế.
10. **Scope quá lớn.** **FACT:** Rủi ro scope rộng được ghi. **INFERENCE:** Giới hạn MVP và chia giai đoạn. **UNKNOWN:** Có dự án bị dừng vì scope không.
11. **Đặc tả quá rỗng.** **FACT:** Rủi ro blueprint rỗng được nêu. **INFERENCE:** Không bắt đầu khi acceptance criteria mơ hồ. **UNKNOWN:** Trường hợp thật.
12. **Chi phí vượt kiểm soát.** **FACT:** Cost risk được nêu. **INFERENCE:** Budget gate và tách phase. **UNKNOWN:** Có vượt budget không.
13. **Audit mất hoặc không đầy đủ.** **FACT:** Đây là rủi ro thiết kế. **INFERENCE:** Append-only trace từ đầu vào tới outcome. **UNKNOWN:** Có audit bị mất không.
14. **Tương thích bị phá khi thay thế.** **FACT:** Breaking-change risk được ghi. **INFERENCE:** Adapter và compatibility test. **UNKNOWN:** Có migration hỏng không.
15. **Kế hoạch bị nhầm với triển khai.** **FACT:** Chênh lệch claim/artifact. **INFERENCE:** Gắn nhãn trạng thái lifecycle. **UNKNOWN:** Mức độ nhầm lẫn đã xảy ra.
16. **Thiết kế bị nhầm với vận hành.** **FACT:** Hồ sơ không xác nhận một số biện pháp đã chạy. **INFERENCE:** Đòi runtime evidence. **UNKNOWN:** Trạng thái ngoài checkout.
17. **Risk bị kể như incident.** **FACT:** Không có incident cụ thể được ghi. **INFERENCE:** Dùng taxonomy risk/modeled/incident. **UNKNOWN:** Những incident chưa được ghi.
18. **Nguyên nhân bị suy diễn.** **FACT:** Failure Library cảnh báo không gán root cause thiếu chứng cứ. **INFERENCE:** Quan sát tách khỏi giả thuyết. **UNKNOWN:** Root causes thực.
19. **Log trống bị hiểu là không xảy ra lỗi.** **FACT:** Log không có entries. **INFERENCE:** Trạng thái log trống không chứng minh không có event. **UNKNOWN:** Chưa có hay chưa ghi.
20. **Metric không có baseline.** **FACT:** Baseline còn UNKNOWN. **INFERENCE:** Không xếp hạng tuyệt đối khi thiếu chuẩn. **UNKNOWN:** Baseline đúng.
21. **Trọng số không xác định nhưng score vẫn được tin.** **FACT:** Weights chưa biết. **INFERENCE:** Báo vector thay vì score có vẻ chính xác. **UNKNOWN:** Weights dự định.
22. **Threshold không được công bố.** **FACT:** Tiêu chí pass chính thức UNKNOWN. **INFERENCE:** Định nghĩa trước lúc đo. **UNKNOWN:** Ngưỡng nào phù hợp.
23. **Metric từ vựng thay thế ngữ nghĩa.** **FACT:** Báo cáo nhắc giới hạn metric probe. **INFERENCE:** Chọn phép đo theo câu hỏi, bổ sung đánh giá nội dung. **UNKNOWN:** Accuracy metric.
24. **Nguồn tương quan bị tính như độc lập.** **FACT:** Số nguồn không tự chứng minh đúng. **INFERENCE:** Kiểm tra provenance và độc lập. **UNKNOWN:** Correlation thực tế.
25. **Lặp ý tưởng bị tính thành bằng chứng.** **FACT:** Ma trận liên kết không chứng minh tính đúng. **INFERENCE:** Link cần evidence riêng. **UNKNOWN:** Mức độ giả định lặp.
26. **Không hỏi lại khi yêu cầu mơ hồ.** **FACT:** Flow làm rõ được mô tả. **INFERENCE:** Hold và hỏi khi dữ kiện trọng yếu thiếu. **UNKNOWN:** Mọi trường hợp ambiguity.
27. **Im lặng bị hiểu là đồng thuận.** **FACT:** Yêu cầu xác nhận tường minh được báo cáo. **INFERENCE:** Không suy đồng ý từ không phản hồi. **UNKNOWN:** Từng có hiểu nhầm chưa.
28. **Đặc tả thay đổi nhưng không version.** **FACT:** Freeze và audit liên kết được mô tả. **INFERENCE:** Tạo phiên bản mới cho change. **UNKNOWN:** Versioning hiện thực.
29. **Reviewer không độc lập với người tạo.** **FACT:** Tách proposal/evaluation/approval là inference được nêu. **INFERENCE:** Bảo đảm review độc lập cho risk cao. **UNKNOWN:** Cấu trúc reviewer hiện tại.
30. **Chỉ một chiều đánh giá.** **FACT:** Multi-axis approach được ghi. **INFERENCE:** Kiểm tra trade-off qua các tiêu chí độc lập. **UNKNOWN:** Những chiều còn thiếu.
31. **Score cao vượt qua hard gate.** **FACT:** Schema/security gates được mô tả song song scoring. **INFERENCE:** Hard constraints thắng score. **UNKNOWN:** Thứ tự triển khai thật.
32. **Fixable issue dẫn tới loại bỏ ngay.** **FACT:** OK/FIX/REJECT được phân biệt. **INFERENCE:** Cho vòng sửa nếu an toàn và khả thi. **UNKNOWN:** Đường phân loại.
33. **Lỗi không sửa được vẫn qua.** **FACT:** Reject được mô tả. **INFERENCE:** Cần hard fail conditions. **UNKNOWN:** Danh mục.
34. **Thiếu test bị xem là pass.** **FACT:** Báo cáo khuyến nghị không coi thiếu chứng cứ là pass. **INFERENCE:** Test coverage gap là hold. **UNKNOWN:** Waiver policy.
35. **Tuyên bố không thể tái kiểm tra.** **FACT:** Citation/evidence được nhấn mạnh. **INFERENCE:** Mọi kết luận quan trọng phải dẫn về chứng cứ. **UNKNOWN:** Tỷ lệ tái lập.
36. **Không lưu provenance.** **FACT:** Audit liên kết nguồn được khuyến nghị. **INFERENCE:** Lưu nguồn và phiên bản. **UNKNOWN:** Provenance coverage.
37. **Không ghi trade-off.** **FACT:** Các báo cáo chỉ ra lý do định lượng nhiều lựa chọn UNKNOWN. **INFERENCE:** Ghi lý do và phương án bỏ qua. **UNKNOWN:** Các trade-off lịch sử.
38. **Quyết định bị score tự động thay thế.** **FACT:** Human gate được ghi nhận. **INFERENCE:** Metric không tự cấp quyền. **UNKNOWN:** Override practice.
39. **Phạm vi mở rộng trước khi phase trước được xác minh.** **FACT:** Phase strategy được mô tả. **INFERENCE:** Dùng exit criteria. **UNKNOWN:** Exit criteria lịch sử.
40. **Biện pháp bảo vệ không được xác minh.** **FACT:** Trạng thái implementation của một số mitigation là UNKNOWN. **INFERENCE:** Test safeguard như một capability. **UNKNOWN:** Coverage.
41. **Warning không được ghi nhận.** **FACT:** Có quy tắc stop/log nhưng log trống. **INFERENCE:** Xác minh tuân thủ log path. **UNKNOWN:** Có warning bị bỏ qua không.
42. **Sự cố không có hậu kiểm.** **FACT:** Không có postmortem được tìm trong hồ sơ. **INFERENCE:** Incident cần lifecycle và bài học. **UNKNOWN:** Sự cố ngoài mẫu.
43. **Bài học được cập nhật trước khi root cause rõ.** **FACT:** Báo cáo yêu cầu không suy diễn. **INFERENCE:** Tách provisional lesson và verified lesson. **UNKNOWN:** Quy trình hiện hành.
44. **Phụ thuộc không được kiểm kê trước khi thay.** **FACT:** Compatibility risk được ghi. **INFERENCE:** Lập dependency map. **UNKNOWN:** Mức phụ thuộc.
45. **Adapter được giả định là đủ an toàn.** **FACT:** Adapter được đề xuất như mitigation. **INFERENCE:** Test adapter và biên tương thích. **UNKNOWN:** Adapter effectiveness.
46. **Quyền quá rộng hoặc kéo dài.** **FACT:** Capability gate được báo cáo. **INFERENCE:** Áp quyền tối thiểu, thời hạn và scope. **UNKNOWN:** Cơ chế hiện tại.
47. **Thông tin audit lộ quá mức.** **FACT:** Masking được ghi trong report. **INFERENCE:** Chỉ chia sẻ phần cần thiết. **UNKNOWN:** Threat model.
48. **Độ sâu kiểm tra không tương xứng rủi ro.** **FACT:** Multi-tier analysis được nêu. **INFERENCE:** Ưu tiên deep review cho quyết định khó đảo ngược. **UNKNOWN:** Triage threshold.
49. **Quyết định đổi hướng không lưu lịch sử.** **FACT:** Full history không thể tái dựng từ clone/report. **INFERENCE:** Ghi lựa chọn, thời điểm, người duyệt, căn cứ. **UNKNOWN:** Những lần đổi hướng thiếu.
50. **Tuyên bố vượt quá tri thức.** **FACT:** Nhiều khoảng UNKNOWN được giữ trong năm báo cáo. **INFERENCE:** Nói rõ giới hạn là kiểm soát chất lượng. **UNKNOWN:** Mọi dữ kiện ngoài corpus được phép.

# IV. Trả lời điều kiện thành công

## 1. C2 thực sự suy nghĩ như thế nào?

**FACT:** Năm báo cáo mô tả tư duy ưu tiên quyền phê duyệt con người, xác minh, bằng chứng, audit, kiểm soát phạm vi và tách invariant khỏi logic có thể thay. **INFERENCE:** Có thể khái quát thành tư duy “đề xuất có kiểm soát, kiểm chứng rồi mới tác động”, không phải suy luận trực tiếp về tâm trí cá nhân. **UNKNOWN:** Động cơ riêng tư và những nguyên lý chưa được ghi trong corpus.

## 2. C2 ra quyết định như thế nào?

**FACT:** Hồ sơ ghi các bước làm rõ/đặc tả, phân tích nhiều tiêu chí, critic, sandbox, quyền và phê duyệt; các thiếu hụt được đánh dấu UNKNOWN. **INFERENCE:** Quyết định tốt nhất được mô hình hóa như accept/revise/reject/hold theo gate và bằng chứng. **UNKNOWN:** Weights, ngưỡng, quy trình override và mức nhất quán thực tế.

## 3. Điều gì tạo nên hệ thống APEX?

**FACT:** Theo các báo cáo, tài sản cốt lõi là cơ chế quản trị, quyền con người, hợp đồng/rule validation, audit, quy trình xác minh nhiều bước, đánh giá và vòng phản hồi. **INFERENCE:** Giá trị bền nằm ở các ranh giới kiểm soát và cách thu thập bằng chứng hơn là một cấu hình cụ thể. **UNKNOWN:** Mức các cơ chế đó được hiện thực/vận hành trong mọi phiên bản.

## 4. Những tài sản tri thức nào đáng giữ lại?

**FACT:** Năm báo cáo chứa nguyên tắc giữ invariant, gate phê duyệt, schema/rule, quy trình theo giai đoạn, probes, phân tích nhiều cấp và bài học về UNKNOWN. **INFERENCE:** Bảo tồn taxonomy FACT/INFERENCE/UNKNOWN, decision log, risk-vs-incident distinction, kiểm tra đặc tả–artifact, human gate và staged rollout. **UNKNOWN:** Tài sản nào chưa được đưa vào năm báo cáo.

## 5. Những gì chỉ là domain-specific và không nên mang sang hệ mới?

**FACT:** Các báo cáo yêu cầu domain removal; chúng phân biệt logic gắn miền với cơ chế quản trị có khả năng tái dùng. **INFERENCE:** Không mang tên đối tượng, thuật ngữ nghiệp vụ, ontology, heuristic hay tiêu chí chất lượng chuyên biệt sang bối cảnh mới nếu chưa ánh xạ và xác nhận lại. Chỉ giữ cơ chế trừu tượng như “resource discovery”, “quality gate”, “decision orchestration” khi nghĩa và điều kiện áp dụng đã được định nghĩa. **UNKNOWN:** Không thể lập danh sách đầy đủ các yếu tố chuyên biệt ngoài nội dung năm báo cáo.

## Kết luận về độ tin cậy

**FACT:** Failure Library không có incident lịch sử đã xác nhận; nhiều biện pháp và tuyên bố trạng thái không được xác nhận triển khai.  
**INFERENCE:** Bộ wisdom này nên dùng như bản đồ quyết định và giả thuyết vận hành có nguồn, không phải bản mô tả hoàn chỉnh về tâm lý C2 hoặc bằng chứng rằng mọi quy tắc đã được tuân thủ.  
**UNKNOWN:** Sự kiện, quyết định và bài học không được phản ánh trong năm báo cáo.
