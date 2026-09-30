# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Thị Phương Duyên
- **MSSV:** 2A202603001
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/dyu-dyu/K4-L3B-Day13-NguyenThiPhuongDuyen-2A202603001-Monitoring-LLMOps.git
- **Commit SHA cuối:** Cập nhật sau khi tạo commit nộp bài cuối cùng.
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2a202603001`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08a-trace-metadata-baseline.png`, `evidence/08b-generation-usage-baseline.png`, `evidence/08c-trace-metadata-candidate.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10a-prompt-promote.png`, `evidence/10b-production-v2-trace.png`, `evidence/10-prompt-rollback.png`, `evidence/10c-production-v1-after-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đã bổ sung correlation ID, log enrichment và PII scrubbing; 188 records được kiểm tra, không thiếu field/context |
| `validate_dashboard.py` | 6/6 | 6/6 | Dashboard contract giữ đủ sáu panel và được validator xác nhận hợp lệ |
| `pytest` | 18 passed, 4 setup errors | 30 passed | Toàn bộ test hoàn tất trong 3.45 giây; xem `evidence/01-pytest.png` |
| Số traces hợp lệ | 10 | ≥10 | Có root observation và hai child observations retrieval/generation; trace baseline, candidate, rollback và incident đã được xác nhận trên Langfuse |
| Số PII leak | 0 | 0 | Không phát hiện PII thô trong 188 log records khi chạy validator cuối |
| Latency P95 / TTFT P95 | 1598 ms / 50 ms | 1401 ms / 50 ms | Số liệu trạng thái bình thường trên dashboard trước khi inject challenge; incident P95 tăng lên 3374 ms |
| Retrieval success rate | 100% (10/10) | 100% | Tính từ các event `response_sent` có `tool_success=true` |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware nhận `x-request-id` từ request nếu client cung cấp; nếu không thì tạo ID dạng `req-<8 ký tự hex>`. ID được bind vào `structlog.contextvars`, lưu tại `request.state`, trả lại qua response header `x-request-id` và truyền vào agent/trace để nối log với Langfuse. Middleware gọi `clear_contextvars()` ở đầu mỗi request để tránh rò context giữa các request đồng thời.
- **Các metadata được ghi vào structured log:** Mỗi event có `service`, `event`, `level`, `ts`, `correlation_id`, `session_id`, `user_id_hash`, `feature`, `model` và `env`. Event `response_sent` còn có `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success` và answer preview; response header có thêm `x-response-time-ms`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `user_id` được băm SHA-256 và chỉ giữ 12 ký tự đầu. Message/answer chỉ ghi preview qua `summarize_text()`. Processor `scrub_event` chạy trong pipeline trước `JsonlFileProcessor`, áp dụng `scrub_text()` lên các chuỗi trong `payload` và tên event. Các pattern che email, số điện thoại Việt Nam, CCCD, thẻ tín dụng, hộ chiếu, địa chỉ, tài khoản ngân hàng, mã số thuế, ngày sinh và địa chỉ IP.
- **Cách kiểm chứng kết quả:** Test tự động bao phủ các pattern PII và luồng observability; kết quả cuối là `30 passed`. `validate_logs.py` kiểm tra 188 records và đạt `100/100`, không thiếu schema/context, tìm thấy 84 correlation ID duy nhất và phát hiện `0` PII leak. Evidence tương ứng nằm tại `evidence/01-pytest.png`, `evidence/02-log-validator.png`, `evidence/04-structured-log.png` và `evidence/05-pii-redaction.png`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Tôi chạy workload từ repository cá nhân và kiểm tra các trace mới trong project Langfuse `day13-k4-l3b-2a202603001`. Evidence `evidence/06-trace-list.png` cho thấy danh sách traces trong project cá nhân; `evidence/07-trace-waterfall.png`, `evidence/08a-trace-metadata-baseline.png`, `evidence/08b-generation-usage-baseline.png` và `evidence/08c-trace-metadata-candidate.png` hiển thị thời gian chạy, model, prompt version và metadata của các request do tôi tạo.
- **Cấu trúc root/retrieval/generation observations:** Trace `day13-agent-request` chứa root observation `lab-agent-run`; bên dưới có hai child observations là `retrieval` loại retriever và `generation` loại generation. Generation baseline dùng model `claude-sonnet-4-5`, ghi nhận 120 tokens và cost `0.001464 USD`; input/output chỉ lưu preview đã scrub.
- **Cách nối trace với log:** Dùng trường `correlation_id` xuất hiện trong cả trace metadata và structured log. Request baseline có `correlation_id=req-ab061bd6`; cùng ID này xuất hiện ở hai event `request_received` và `response_sent` trong `data/logs.jsonl`, với `latency_ms=153`, `ttft_ms=50`, `tokens_in=28`, `tokens_out=92` và `cost_usd=0.001464`.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** Version 1, labels `baseline` và `production`; trace metadata ghi `prompt_source=langfuse`, `prompt_label=baseline`, `prompt_version=1`.
- **Version/label candidate:** Version 2, labels `candidate` và `latest`; nội dung candidate bổ sung vai trò monitoring assistant, yêu cầu dùng documents khi phù hợp, đưa kết luận chính lên trước và trả lời ngắn gọn.
- **Trace ID của mỗi version:** Baseline v1: `febc2e8b842f1d45e6d6642872ae4fdf` (`correlation_id=req-ab061bd6`); Candidate v2: `6744c4d4dafb12ed83d4693f3f6d020a` (`correlation_id=req-f40a97e6`).
- **Cách promote và rollback `production`:** Ban đầu `production` trỏ tới version 1. Tôi chuyển label `production` sang version 2 để promote (`evidence/10a-prompt-promote.png`), sau đó chạy request kiểm chứng với trace ID `f0f18944421b6a434ff9334db08843e2`, `correlation_id=req-ad771a2d`, `prompt_label=production` và `prompt_version=2` (`evidence/10b-production-v2-trace.png`). Tiếp theo tôi chuyển `production` về version 1 (`evidence/10-prompt-rollback.png`) và chạy lại request; trace sau rollback ghi `correlation_id=req-dec301e2`, `prompt_label=production`, `prompt_version=1` (`evidence/10c-production-v1-after-rollback.png`).

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard Streamlit đọc trực tiếp `data/logs.jsonl`, dùng cửa sổ 60 phút và tự refresh mỗi 30 giây. Sáu panel gồm latency P50/P95/P99 và TTFT P95; traffic; error rate và retrieval success; cost; input/output tokens; quality proxy. Evidence `evidence/11-dashboard-overview.png` ghi nhận latency P50/P95/P99 lần lượt là `153/1401/2062 ms`, TTFT P95 `50 ms`, 60 requests, error rate `0%`, retrieval success `100%`, total cost `0.129117 USD`, 3,114 input tokens, 7,985 output tokens và quality trung bình `0.880`. Dashboard contract đạt 6/6 tại `evidence/03-dashboard-validator.png`.
- **SLO và lý do chọn:** SLO chính trong `config/slo.yaml` yêu cầu 99.5% request trong cửa sổ 28 ngày vừa thành công vừa có latency không vượt 3000 ms. Ngưỡng 3000 ms cao hơn baseline P95 `1401 ms`, tạo khoảng an toàn cho tail latency nhưng vẫn giới hạn thời gian chờ của người dùng. Các guardrail bổ sung là error rate ≤2%, daily cost ≤2.5 USD, quality trung bình ≥0.75 và retrieval success ≥90%.
- **Cách tính error budget:** Target 99.5% tương ứng error budget 0.5%. Nếu có 10,000 request trong cửa sổ 28 ngày thì tối đa `10,000 × 0.5% = 50` request được phép lỗi hoặc có latency vượt 3000 ms; vượt 50 request nghĩa là đã tiêu hết error budget.
- **Ba alert và runbook tương ứng:** `config/alert_rules.yaml` định nghĩa ba alert symptom-based: `HighLatencyP95` mức `warning` khi latency P95 >3000 ms trong 5 phút; `HighErrorRate` mức `critical` khi error rate >2% trong 5 phút; và `LowRetrievalSuccess` mức `warning` khi retrieval success <90% trong 5 phút. Cả ba alert gửi qua Slack, có owner `student-2A202603001` và liên kết tới runbook tương ứng trong `docs/alerts.md`. Mỗi runbook mô tả ảnh hưởng người dùng, ba bước điều tra Metrics → Logs → Traces và mitigation tạm thời.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** Khoảng `06:53 UTC` ngày `30/09/2026` (`13:53`, múi giờ Asia/Ho_Chi_Minh), ngay sau khi chạy 5 request của challenge.
- **Triệu chứng từ metrics:** Dashboard ghi nhận tail latency tăng cao: P50 `2653 ms`, P95 `3374 ms` và P99 `3846 ms`; P95 đã vượt ngưỡng SLO/alert `3000 ms`. Trong khi đó TTFT P95 vẫn là `50 ms`, error rate `0%`, retrieval success `100%` và chi phí không tăng bất thường, nên đây là sự cố chậm chứ không phải lỗi request hoặc cost spike.
- **Log line và correlation ID liên quan:** Log `response_sent` của request đại diện có `correlation_id=req-ae05262f`, `latency_ms=2653`, `ttft_ms=50`, `tool_name=retrieval` và `tool_success=true`. Correlation ID này nối request trong structured log với trace tương ứng trên Langfuse.
- **Trace ID và span gây ảnh hưởng:** Trace ID `b7255edd727ae9c8f59e7f0dd8497bcb`, cùng `correlation_id=req-ae05262f`, có tổng thời gian khoảng `2.65 s`. Span `retrieval` mất khoảng `2.50 s`, trong khi span `generation` chỉ khoảng `0.15 s`.
- **Root cause:** Đường retrieval bị tăng độ trễ. Span retrieval chiếm gần như toàn bộ thời gian của trace, còn generation, TTFT, error rate và cost đều bình thường; vì vậy bottleneck nằm ở retrieval chứ không phải mô hình sinh câu trả lời.
- **Fix action:** Tắt incident được inject để khôi phục retrieval về trạng thái bình thường, sau đó chạy lại request và kiểm tra latency P95 trở xuống dưới `3000 ms`; nếu xảy ra ở production thì rollback thay đổi retrieval gần nhất hoặc chuyển sang retrieval backend/fallback ổn định.
- **Preventive measure:** Duy trì alert `HighLatencyP95` và runbook Metrics → Logs → Traces; bổ sung timeout, circuit breaker/fallback và theo dõi riêng latency của span retrieval để phát hiện sớm và tránh retrieval chậm kéo dài toàn bộ request.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Tôi dùng cùng `correlation_id` trong response header, structured log và trace metadata. Đây là khóa liên kết giúp đi từ triệu chứng tổng hợp trên dashboard tới đúng request và đúng span, thay vì phải đoán nguyên nhân từ các nguồn dữ liệu rời rạc.
- **Một lỗi/blocker đã gặp:** Pytest ban đầu báo bốn setup error do thư mục tạm mặc định `C:\\Users\\DienDien\\AppData\\Local\\Temp\\pytest-of-DienDien` bị từ chối quyền truy cập trên Windows; lỗi không nằm trong logic ứng dụng.
- **Cách tìm nguyên nhân và xử lý:** Tôi đọc traceback để xác định lỗi xuất hiện khi fixture `tmp_path` tạo thư mục, sau đó chạy pytest trong môi trường terminal có quyền ghi thư mục tạm phù hợp. Kết quả cuối đạt `30 passed`, đồng thời hai validator độc lập vẫn đạt `100/100` và `6/6`.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics dùng để phát hiện loại triệu chứng và khoanh vùng thời gian; log trong khoảng đó cung cấp một request đại diện cùng correlation ID; trace có cùng ID tách thời gian theo từng span để xác định bước gây ảnh hưởng. Trong challenge, P95 tăng quá 3000 ms, log `req-ae05262f` có latency 2653 ms và trace tương ứng cho thấy retrieval chiếm 2.50/2.65 giây.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version và label giúp thử candidate có kiểm soát, truy vết request đang dùng nội dung nào và rollback nhanh về bản production ổn định. Token/cost cho biết tác động tài nguyên, còn SLO/error budget đặt ranh giới chất lượng có thể đo được để quyết định khi nào cần cảnh báo hoặc ưu tiên khắc phục.
- **Điều quan trọng nhất đã học:** Observability cho LLM cần liên kết cả hành vi ứng dụng, retrieval và generation. Chỉ nhìn lỗi HTTP là chưa đủ vì request có thể thành công nhưng vẫn vi phạm SLO do một span chậm; correlation ID và span-level tracing làm root cause có thể kiểm chứng được.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Lab dùng FakeLLM và dashboard đọc JSONL cục bộ nên chưa phản ánh đầy đủ độ biến động, tải phân tán và độ bền của hệ thống production. Quality score hiện là proxy; hệ thống thực tế cần evaluator trên tập dữ liệu chuẩn, backend metrics tập trung và alert channel thật. Commit SHA cuối sẽ được cập nhật sau khi làm sạch evidence và tạo commit nộp bài.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
