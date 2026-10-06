# FAILURE_LIBRARY — Vòng 4: Failure Archaeology

## FACT — bằng chứng về thất bại và rủi ro

### Sự cố đã ghi lại

- `reports/SCREW_LOG.md:1-8` định nghĩa log append-only cho các lần dừng do cảnh báo, nhưng hiện chỉ có tiêu đề và chỗ trống; không có sự cố nào được mô tả.
- `reports/CONSTRUCTION_LOG.md:1-13` chỉ ghi mốc khởi tạo ngày 2026-05-02, stack, 16 test pass và server dev chạy. Không có lỗi, thử nghiệm hỏng hay hướng bị bỏ được ghi tại đây.
- Không tìm thấy báo cáo hậu kiểm sự cố riêng trong các tệp được theo dõi. Vì vậy không thể nêu nguyên nhân thực tế, số lần tái diễn hay luật mới phát sinh từ một sự cố cụ thể.

### Rủi ro dự đoán trong thiết kế (không phải sự cố đã xảy ra)

Blueprint nêu sáu rủi ro và biện pháp dự kiến: đầu ra ngoài sai → schema gate/chấm điểm; hot-inject gây crash → capability token/canary; ontology quá rộng → giới hạn MVP; chi phí ngoài cao → tách phase và bật/tắt; mất audit → log append-only; thay đổi làm hỏng legacy → adapter và giữ khả năng import (`ARCHITECTURAL_BLUEPRINT_V6.md:301-310`). Không có bằng chứng tại đây rằng các rủi ro đã xảy ra hoặc biện pháp đã được triển khai.

### Các điều kiện lỗi được mô hình hóa trong mã

- Probe độ lệch trả `error` và `drift=None` nếu thiếu tệp phiên bản (`apex_core/probes/silence_probe.py:25-32`); đây là nhánh xử lý thiếu dữ liệu, không phải log của một lần chạy.
- Round Table cho điểm trung bình 0 khi danh sách điểm rỗng, từ đó đưa ra khuyến nghị `kill` (`apex_core/governance/round_table.py:34-42`); mã chứng minh hành vi biên, không chứng minh đã loại nhầm đối tượng.
- Blueprint có yêu cầu từ chối đầu ra lệch schema và kiểm thử sandbox trước các thay đổi có tác động (`ARCHITECTURAL_BLUEPRINT_V6.md:177-180,211-220,271-282`); đây là thiết kế phòng ngừa.

### Chênh lệch trạng thái tài liệu và kho

**FACT:** Blueprint tự tuyên bố 34/34 tệp và 7/7 phase hoàn tất (`ARCHITECTURAL_BLUEPRINT_V6.md:23089-23100`), nhưng inventory checkout không có nhóm foundation, brain, emitter, sandbox, external hay factory được liệt kê ở cuối cùng (`:23000-23048`).

**FACT:** `README.md` chỉ có hai dòng tiêu đề; `CONSTITUTION_V6.md` hiện chỉ có một ký tự xuống dòng. Nội dung luật 34 tệp xuất hiện ở phần đầu blueprint (`ARCHITECTURAL_BLUEPRINT_V6.md:1-40`), không phải trong hai tệp mang tên này.

**INFERENCE:** Đây là khoảng cách giữa tuyên bố và artifact hiện có, có thể làm người đọc nhầm thiết kế với sản phẩm. Không đủ chứng cứ để gọi đây là lỗi triển khai, xác định nguyên nhân, hay cho rằng các tệp chưa từng tồn tại ở nơi khác.

## INFERENCE — bài học an toàn, không gán cho sự cố lịch sử

- Phân loại rõ “rủi ro dự đoán”, “điều kiện lỗi được kiểm thử/mô hình hóa” và “sự cố có log”; chỉ nhóm cuối mới chứng minh thất bại đã xảy ra.
- Đưa schema, sandbox, quyền con người và canary thành gate độc lập; ghi lại kết quả của mỗi gate và khả năng rollback.
- Không biến thiếu dữ liệu thành điểm số tích cực hoặc quyết định chắc chắn; đầu vào rỗng/thiếu nên được gắn nhãn không đủ bằng chứng để người vận hành xử lý.
- Duy trì sổ sự cố thực sự append-only, có thời gian, triệu chứng, nguyên nhân đã xác nhận, biện pháp, bằng chứng kiểm chứng và luật mới; không điền nguyên nhân bằng suy luận.
- Đồng bộ tuyên bố hoàn tất với danh mục artifact và bằng chứng chạy để tránh nhầm bản thiết kế với hiện trạng.

## UNKNOWN

- Không có hồ sơ để xác định bug cụ thể, lần deploy hỏng, sự cố bảo mật, thử nghiệm thất bại hoặc hướng bị chính thức bỏ.
- Không biết Screw Log trống vì chưa có cảnh báo hay vì quy tắc ghi log chưa được dùng.
- Các biện pháp canary, schema guard và sandbox trong blueprint có được triển khai/kiểm thử hay không chưa được xác nhận.
