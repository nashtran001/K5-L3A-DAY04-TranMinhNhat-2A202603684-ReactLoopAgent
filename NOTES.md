# Ghi chú phân tích · Day 04

Họ và tên: Trần Minh Nhật
MSSV: 2A202603684

## 1. Case được chọn

Tôi chọn case **H6**, đạt 60/100 ở lần chạy đầu. Agent đã đọc sự cố GitHub nhưng bỏ qua liên kết đến bản tổng hợp, rồi kết luận chưa có nguyên nhân cụ thể.

Tôi cũng xem thêm A5 và H1. Ở A5, agent khẳng định không có sự cố năm 2025 dù công cụ chỉ tìm trong dữ liệu gần đây.

## 2. Bằng chứng trong trace

Trace H6 trong `eval_before.json`, rút gọn:

```text
step 1: get_status(provider="github", component="actions")
step 1: get_incident_details(provider="github", incident_id="h02n9572mx9y")
  updates[0].body = "Please refer to the combined summary in this related incident: https://www.githubstatus.com/incidents/xr3myzj7ms51"
step 2: model finish="stop"
```

Agent dừng ở bước 2 mà chưa gọi tool đọc `xr3myzj7ms51`. Phần kiểm tra nguồn cũ chỉ yêu cầu câu trả lời có URL đã đọc, nên không phát hiện việc bỏ qua bản tổng hợp.

## 3. Thay đổi đã thực hiện

Tôi sửa `agent.py` để agent thu thập đủ bằng chứng trước khi trả lời:

- Làm rõ prompt: trả lời đúng thời gian được hỏi, nêu giới hạn tìm kiếm và phân biệt dữ liệu lưu sẵn với trạng thái hiện tại.
- Thêm `linked_incidents` để nhận diện liên kết sự cố GitHub/Cloudflare. Nếu agent chưa thử đọc sự cố được liên kết, chương trình nhắc gọi tool và ghi `validation_unread_incidents` vào trace.
- Giữ giới hạn `max_steps`; không ép thử lại liên tục khi tra cứu thất bại.

Đã thêm tests cho phần kiểm tra liên kết. Cả **46 tests** chính và bonus đều pass. Các thay đổi không sửa dữ liệu mẫu hay cách chấm điểm.

## 4. So sánh hai lần chạy

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---|---|
| Điểm tổng, đủ 22/22 case | 77,64/100 | 83,18/100 |
| Điểm H6 | 60 | 75 |
| Điểm A5 / H1 | 55 / 60 | 65 / 80 |
| Số lần gọi model của agent | 51 | 53 |
| Token agent / judge | 47.198 / 45.538 | 70.790 / 39.400 |
| Tổng chi phí API, USD (làm tròn) | 0,020141 | 0,021736 |

Hai lần chạy dùng cùng model `openai/gpt-4o-mini` qua OpenRouter cho agent và judge, cùng dữ liệu lưu sẵn, bộ `core` và `max_steps=8`. Chi phí được cộng từ số liệu API trả về, gồm cả agent và judge.

Sau cải tiến, H6 được nhắc ở bước 2, đọc bản tổng hợp ở bước 3 rồi mới trả lời. Agent đã tìm được phần nêu nguyên nhân. A5 cũng thừa nhận chưa đủ dữ liệu để kết luận về toàn bộ năm 2025. Điểm tổng tăng **5,54 điểm**: 13 case tăng, 5 giảm và 4 giữ nguyên.

Vẫn còn lỗi: E1 giảm từ 65 xuống 30, dùng từ “hiện tại” cho dữ liệu lưu sẵn và ghép nhầm thông tin sự cố. A5 vẫn liệt kê sự cố ngoài năm được hỏi và nhầm số mục hiển thị với số mục khớp. H6 còn diễn đạt chưa rõ quan hệ giữa hai sự cố và nhầm thời gian cập nhật với thời gian xử lý xong.

## 5. Giới hạn

- Điểm judge chỉ để tham khảo vì model có thể chấm sai. Cần đọc cả câu trả lời và trace để kiểm tra.
- Dữ liệu được lưu ngày 09/11/2026, không phản ánh trạng thái trực tiếp. Công cụ chỉ tìm trong 50 sự cố gần nhất, trả tối đa 5 mục khớp và có thể lược bớt nội dung.
- Mỗi phiên bản chỉ chạy một lần, nên chưa thể khẳng định mức tăng điểm sẽ ổn định.
- Việc đọc thêm liên kết làm tăng token và chi phí. Kiểm tra liên kết giúp agent đọc thêm bằng chứng, nhưng chưa đảm bảo mọi kết luận đều đúng.
