# AI Content Strategist Agent

## Mô tả bài toán

AI Content Strategist Agent được xây dựng để giải quyết bài toán phát triển nội dung và xây dựng kênh cho đối tác nhà sáng tạo/người nổi tiếng trên nền tảng Zalo Video. Dữ liệu hiệu suất có nhiều nhưng khó chuyển thành quyết định nội dung cụ thể. Đội ngũ Partnership thường phải tải file CSV/Excel, đọc các chỉ số như views, like, comment, share, save, followers gained, thời gian đăng và content pillar, rồi tự suy luận video nào tốt, video nào kém, nên đăng lúc nào và nên sản xuất gì. Quy trình thủ công này tốn thời gian, dễ sai sót và phụ thuộc vào cảm tính.

Người dùng mục tiêu là đội ngũ Partnership Zalo Video và có thể nhân rộng thêm cho nhà sáng tạo/MCN cần hiểu nhanh tình hình kênh nhưng không có đội data riêng. Họ cần một công cụ giúp đọc dữ liệu, giải thích kết quả và biến insight thành kế hoạch hành động rõ ràng.

Agent giải quyết vấn đề bằng cách cho phép upload file CSV hoặc Excel chứa dữ liệu video. Backend dùng Python và Pandas để chuẩn hóa cột, tính engagement rate, performance score, phân tích từng video, so sánh content pillar, tìm khung giờ đăng tối ưu, phát hiện pattern thành công/thất bại và dự báo tăng trưởng. LangChain kết nối LLM provider OpenAI-compatible để sinh executive summary, nhận xét chiến lược và khuyến nghị nội dung dễ hiểu. Frontend hiển thị kết quả qua dashboard với KPI cards, charts, bảng dữ liệu, insight cards và content calendar cho tháng tiếp theo.

Giá trị chính là giúp người dùng rút ngắn thời gian phân tích từ nhiều giờ xuống vài phút, ra quyết định dựa trên dữ liệu, ưu tiên đúng pillar, tối ưu lịch đăng, cải thiện engagement và xây dựng chiến lược tăng trưởng bền vững hơn.
