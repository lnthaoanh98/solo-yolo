# AI Content Strategist Agent

Agent web chat dùng LangChain, Pandas và Plotly để phân tích hiệu suất nội dung Zalo Video từ file CSV/Excel.

Repo nộp bài: [lnthaoanh98/solo-yolo.git](https://github.com/lnthaoanh98/solo-yolo.git)

## Mô tả bài toán

AI Content Strategist Agent được xây dựng để giải quyết bài toán phát triển nội dung và xây dựng kênh cho đối tác nhà sáng tạo/người nổi tiếng trên nền tảng Zalo Video. Dữ liệu hiệu suất có nhiều nhưng khó chuyển thành quyết định nội dung cụ thể. Đội ngũ Partnership thường phải tải file CSV/Excel, đọc các chỉ số như views, like, comment, share, save, followers gained, thời gian đăng và content pillar, rồi tự suy luận video nào tốt, video nào kém, nên đăng lúc nào và nên sản xuất gì. Quy trình thủ công này tốn thời gian, dễ sai sót và phụ thuộc vào cảm tính.

Người dùng mục tiêu là đội ngũ Partnership Zalo Video và có thể nhân rộng thêm cho nhà sáng tạo/MCN cần hiểu nhanh tình hình kênh nhưng không có đội data riêng. Họ cần một công cụ giúp đọc dữ liệu, giải thích kết quả và biến insight thành kế hoạch hành động rõ ràng.

Agent giải quyết vấn đề bằng cách cho phép upload file CSV hoặc Excel chứa dữ liệu video. Backend dùng Python và Pandas để chuẩn hóa cột, tính engagement rate, performance score, phân tích từng video, so sánh content pillar, tìm khung giờ đăng tối ưu, phát hiện pattern thành công/thất bại và dự báo tăng trưởng. LangChain kết nối LLM provider OpenAI-compatible để sinh executive summary, nhận xét chiến lược và khuyến nghị nội dung dễ hiểu. Frontend hiển thị kết quả qua dashboard với KPI cards, charts, bảng dữ liệu, insight cards và content calendar cho tháng tiếp theo.

Giá trị chính là giúp người dùng rút ngắn thời gian phân tích từ nhiều giờ xuống vài phút, ra quyết định dựa trên dữ liệu, ưu tiên đúng pillar, tối ưu lịch đăng, cải thiện engagement và xây dựng chiến lược tăng trưởng bền vững hơn.

## Tính năng

- Upload CSV/Excel chứa dữ liệu video.
- Chấm điểm hiệu suất từng video.
- Xác định content pillar hiệu quả nhất.
- Tìm khung giờ đăng tối ưu.
- Phát hiện pattern thắng/thua.
- Dự báo tăng trưởng 30 ngày.
- Đề xuất content calendar cho tháng tiếp theo.
- Sinh dashboard và executive summary.

## Cấu hình LLM

Tạo file `.env` từ `.env.example`:

```powershell
Copy-Item .env.example .env
```

Điền provider OpenAI-compatible:

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-key
LLM_MODEL=gpt-4o-mini
```

Nếu chưa cấu hình LLM, app vẫn chạy ở fallback mode và dùng summary deterministic từ dữ liệu.

## Chạy local

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Mở `http://127.0.0.1:8080`.

## Test nhanh

```powershell
pytest
```

File mẫu nằm tại `sample_data/content_performance_sample.csv`.

## Docker

```powershell
docker build -t ai-content-strategist-agent .
docker run --env-file .env -p 8080:8080 ai-content-strategist-agent
```

## Cột dữ liệu khuyến nghị

App tự map nhiều tên cột phổ biến. Các cột tốt nhất gồm:

| Nhóm | Tên cột gợi ý |
| --- | --- |
| Nội dung | `title`, `platform`, `content_pillar` |
| Thời gian | `posted_at` |
| Hiệu suất | `views`, `likes`, `comments`, `shares`, `saves`, `followers_gained` |
| Retention | `duration_seconds`, `avg_watch_duration` |
