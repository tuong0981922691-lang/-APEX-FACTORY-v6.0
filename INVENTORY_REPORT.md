# INVENTORY_REPORT — Vòng 1: Inventory

## Phạm vi và phương pháp

**FACT:** Khảo sát 95 tệp được Git theo dõi tại thời điểm bắt đầu; năm báo cáo khảo cổ này chưa nằm trong mẫu đếm. Kiểm kê theo cây thư mục, đọc các tài liệu nền tảng, đối chiếu module Python, giao diện, kiểm thử, workflow và log. Blueprint dài 23.108 dòng nên được khảo sát theo mục lục, phần nguyên tắc/quyết định/rủi ro và các đoạn kết luận, không xem nội dung được đề xuất trong đó là mã đã triển khai.

**INFERENCE:** Bản kiểm kê phân biệt “có trong kho” với “được blueprint tuyên bố/đề xuất”; sự hiện diện trong tài liệu thiết kế không chứng minh tính năng đã chạy.

Kho làm việc: `/home/runner/work/-APEX-FACTORY-v6.0/-APEX-FACTORY-v6.0`.

## Cây thư mục và số lượng tệp

**FACT:** Trước khi tạo báo cáo, 95 tệp được theo dõi: 41 tệp gốc, 35 tệp dưới `apex_core/`, 9 dưới `public_site/`, 5 dưới `tests/`, 3 dưới `reports/`, 1 dưới `scripts/`, 1 workflow dưới `.github/workflows/`.

```text
/
├── .github/workflows/
├── apex_core/
│   ├── auth/ c2/ customer/ db/ governance/ intake/
│   ├── orchestrator_v6/ precombat/ probes/ routers/
│   └── scheduler/ subagent/ triangle/
├── public_site/
│   ├── c2/ command-room/ orders/ shared/ static/css/
├── reports/
└── scripts/ tests/botthongminh/
```

**FACT — toàn bộ tệp gốc theo nhóm:**

- Quy tắc/cấu hình/tài liệu: `/home/runner/work/-APEX-FACTORY-v6.0/-APEX-FACTORY-v6.0/.env.example`, `.gitignore`, `AGENTS.md`, `ARCHITECTURAL_BLUEPRINT_V6.md`, `CONSTITUTION_V6.md`, `README.md`, `pyproject.toml`, `requirements.txt`.
- Giao diện HTML (33): `apex-sovereign-core-v1.html`, `apex-sovereign-core-v1_1.html`, `app.html`, `ban-html-DA-SUA.html`, `bang_dac_biet_tuan_100_tuan_no_ai.html`, `bang_dac_biet_tuan_100_tuan_no_ai (1).html`, `c2_rap_2_khong_gian.html`, `dien_dan_cau_keo_bridge_stream_core.html`, `index.html`, `khong_gian_bao_cao_ai_audio_stream_core.html`, `khong_gian_tao_bao_cao_ai_stream_core.html`, `live_space_xo_so_3_mien_final_brown_validated.html`, các bản `(1)`, `(2)`, `(3)` của tệp đó, `live_space_xo_so_3_mien_final_fixed_v2.html`, các bản `(1)`, `(2)`, `(3)` của tệp đó, `live_space_xo_so_3_mien_no_vietlott.html`, `ma_tran_thong_ke_100_ngay_tich_hop.html`, `merged.html`, `module_video_ai_4_the_da_dinh_dang.html`, `super-app-xoso-v10.html`, `super-app-xoso-v10_1.html`, `thong_ke_tan_suat_lo_backend_stream_core.html`, `xsmb_ai_console_c2_full.html`, `xsmb_ket_qua_xo_so_clean.html`, `xsmb_ket_qua_xo_so_clean (1).html`, `xsmn_100_bang_ket_qua.html`, `xsmn_100_bang_ket_qua (1).html`, `xsmt_100_ban_hoan_chinh.html`, `xsmt_100_ban_hoan_chinh (1).html`.

**FACT — module và tài sản còn lại:**

- `/home/runner/work/-APEX-FACTORY-v6.0/-APEX-FACTORY-v6.0/apex_core/`: `__init__.py`; `auth/{__init__.py,router.py,session_store.py,user_store.py}`; `c2/__init__.py`; `customer/{__init__.py,cdp.py,cvp.py,saint_protocol.py}`; `db/{__init__.py,botthongminh_schema.py}`; `governance/{__init__.py,decision_brain.py,round_table.py}`; `intake/__init__.py`; `orchestrator_v6/{__init__.py,_hookup.py,c2_hub_router.py,notifications.py,orders_router.py,recovery_router.py,studio_entry.py,twofa_router.py}`; `precombat/__init__.py`; `probes/{__init__.py,cross_ai_probe.py,reverse_code_probe.py,silence_probe.py}`; `routers/{__init__.py,botthongminh_router.py}`; `scheduler/__init__.py`; `subagent/{__init__.py,student.py}`; `triangle/__init__.py`.
- `/home/runner/work/-APEX-FACTORY-v6.0/-APEX-FACTORY-v6.0/public_site/`: `c2/login.html`, `command-room/index.html`, `customer-chat.html`, `orders/{index.html,new.html}`, `portal.html`, `shared/{api.js,style.css}`, `static/css/saint.css`.
- `/home/runner/work/-APEX-FACTORY-v6.0/-APEX-FACTORY-v6.0/tests/`: `__init__.py`, `botthongminh/__init__.py`, `botthongminh/test_2fa.py`, `test_c2_hub.py`, `test_orders.py`.
- Báo cáo/log đã có: `reports/CONSTRUCTION_LOG.md`, `reports/IDEA_INTERLOCK_MATRIX.md`, `reports/SCREW_LOG.md`; công cụ: `scripts/lint_no_self_reference.py`; workflow: `.github/workflows/python-package-conda.yml`.

## Module, agent, graph, SOP và nghiên cứu

**FACT:** Module hoạt động tập trung vào xác thực, API/orchestration, quy trình khách hàng, SQLite, governance, probes và một subagent phân tích ba cấp (`apex_core/subagent/student.py:1-7,21-95`). Bốn package `c2/`, `intake/`, `precombat/`, `scheduler/`, `triangle/` chỉ có `__init__.py` rỗng; không thấy triển khai agent/brain riêng trong đó.

**FACT:** Tài liệu blueprint đề xuất B1–B7, bộ chấm Radar 4D, bảy critic, DesignGraph và SceneGraph; tên và trạng thái đề xuất thể hiện trong `/home/runner/work/-APEX-FACTORY-v6.0/-APEX-FACTORY-v6.0/ARCHITECTURAL_BLUEPRINT_V6.md:143-220,232-299`. Các module đó không xuất hiện trong danh sách tệp được theo dõi hiện tại. `decision_brain.py` ghép đầu vào thành bản nháp và mặc định yêu cầu phê duyệt (`apex_core/governance/decision_brain.py:17-23,26-47`); đây không phải graph thực thi.

**FACT:** Không tìm thấy tệp/thư mục SOP riêng. Quy tắc vận hành nằm rải rác trong `AGENTS.md`, blueprint, cấu hình và log. Tài liệu nghiên cứu/thiết kế chính là blueprint, ma trận liên kết ý tưởng (`reports/IDEA_INTERLOCK_MATRIX.md:1-23`) và các probe mã hóa cách kiểm tra giả thuyết (`apex_core/probes/`).

**INFERENCE:** Trong mẫu hiện có, “brain/agent” là khái niệm thiết kế hoặc mô-đun phân tích nhỏ, chưa phải một hệ thống nhiều agent có đầy đủ định nghĩa và luồng chạy.

## Phiên bản, bản trùng và giới hạn

**FACT:** So sánh SHA-256 tìm thấy các bản HTML trùng byte: cặp `apex-sovereign-core-v1(.html/_1.html)`, `bang_dac_biet_tuan_100_tuan_no_ai(.html/ (1).html)`, `xsmb_ket_qua_xo_so_clean(.html/ (1).html)`, cặp `xsmn_100_bang_ket_qua`, cặp `xsmt_100_ban_hoan_chinh`, bốn bản `live_space_xo_so_3_mien_final_brown_validated`, bốn bản `live_space_xo_so_3_mien_final_fixed_v2`, và cặp `super-app-xoso-v10`. `app.html` và `merged.html` là hai tệp lớn riêng biệt.

**FACT:** Blueprint cuối tự tuyên bố 7/7 phase, 34/34 tệp và khoảng 15.790 dòng hoàn tất (`ARCHITECTURAL_BLUEPRINT_V6.md:23089-23100`), nhưng các tệp nền tảng/brain/emitter/factory được nêu ở trên không thuộc 95 tệp thực tế.

**INFERENCE:** Sự khác nhau giữa tài liệu và checkout là chênh lệch trạng thái/tư liệu; chỉ từ bằng chứng này không thể xác định nguyên nhân, thời điểm, hay liệu một bản khác từng triển khai các tệp đó.

## UNKNOWN

- Nội dung runtime của `data/` và `storage/` không thể kiểm kê từ tệp theo dõi; ghi chú môi trường cho biết chúng bị Git bỏ qua (`AGENTS.md:53-77`).
- Lịch sử Git nhìn thấy trong clone nông không đủ xác nhận toàn bộ diễn tiến trước đó.
- Không có bằng chứng để khẳng định các graph, brain hay SOP được đề xuất từng chạy ở môi trường khác.
