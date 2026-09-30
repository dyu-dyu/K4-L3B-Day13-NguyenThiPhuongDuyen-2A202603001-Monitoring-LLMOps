# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`; SLO chính yêu cầu request thành công có latency không vượt 3000 ms.
- Điều kiện và thời gian duy trì: `p95(response_sent.latency_ms) > 3000ms` liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn ngưỡng SLO trước khi nhận câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Latency để xác nhận P95/P99, TTFT và khoảng thời gian vượt ngưỡng.
  2. Lọc `data/logs.jsonl` trong khoảng đó và chọn một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh thời gian của retrieval và generation để xác định span chậm.
- Mitigation tạm thời: rollback prompt nếu latency tăng sau khi đổi version; nếu retrieval chậm thì khôi phục cấu hình/dịch vụ liên quan hoặc tắt practice scenario `rag_slow` khi demo.
- Owner: `student-2A202603001`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack
- SLI/SLO liên quan: tỷ lệ `request_failed` trên `request_received`; guardrail yêu cầu error rate không vượt 2%.
- Điều kiện và thời gian duy trì: `count(request_failed) / count(request_received) * 100 > 2%` liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: một phần request trả lỗi và người dùng không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors để xác nhận error rate, error breakdown và khoảng thời gian tăng.
  2. Lọc event `request_failed` trong `data/logs.jsonl`, ghi lại `error_type` và một `correlation_id` đại diện.
  3. Mở trace cùng `correlation_id` trên Langfuse để xác định retrieval hay generation phát sinh lỗi.
- Mitigation tạm thời: khôi phục dependency hoặc cấu hình vừa thay đổi, chuyển sang fallback an toàn và tắt practice scenario `tool_fail` khi demo.
- Owner: `student-2A202603001`

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack
- SLI/SLO liên quan: tỷ lệ `tool_success=true` trên các event có `tool_success`; guardrail yêu cầu retrieval success tối thiểu 90%.
- Điều kiện và thời gian duy trì: `count(tool_success == true) / count(tool_success != null) * 100 < 90%` liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: hệ thống thiếu context phù hợp, có thể trả lời fallback hoặc giảm chất lượng câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors để xác nhận retrieval success và khoảng thời gian giảm dưới ngưỡng.
  2. Lọc các log có `tool_name=retrieval` và `tool_success=false`, sau đó lấy một `correlation_id` đại diện.
  3. Mở trace cùng `correlation_id` trên Langfuse, kiểm tra trạng thái và metadata của observation retrieval.
- Mitigation tạm thời: khôi phục vector store/index hoặc cấu hình retrieval, bật câu trả lời fallback an toàn và tắt practice scenario `tool_fail` khi demo.
- Owner: `student-2A202603001`
