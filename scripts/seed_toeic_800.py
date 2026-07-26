from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.database import Database
from database.schema import create_tables
from repositories.flashcard_repository import FlashcardRepository
from repositories.study_set_repository import StudySetRepository
from services.study_set_service import StudySetService


TITLE = 'TOEIC 800 Vocabulary'
DESCRIPTION = '200 từ vựng TOEIC trung-cao cấp cho công việc và giao tiếp.'

CARDS = [
    ('allocate', 'phân bổ'),
    ('annual', 'hàng năm'),
    ('applicant', 'ứng viên'),
    ('appoint', 'bổ nhiệm'),
    ('authorize', 'ủy quyền'),
    ('budget', 'ngân sách'),
    ('candidate', 'ứng viên'),
    ('capacity', 'công suất; năng lực'),
    ('collaborate', 'hợp tác'),
    ('compensate', 'bồi thường; trả công'),
    ('comply', 'tuân thủ'),
    ('conduct', 'tiến hành'),
    ('confirm', 'xác nhận'),
    ('consent', 'sự đồng ý'),
    ('consult', 'tham khảo; tư vấn'),
    ('contractor', 'nhà thầu'),
    ('coordinate', 'phối hợp'),
    ('deadline', 'hạn chót'),
    ('delegate', 'ủy nhiệm'),
    ('department', 'phòng ban'),
    ('eligible', 'đủ điều kiện'),
    ('evaluate', 'đánh giá'),
    ('executive', 'quản lý cấp cao'),
    ('expertise', 'chuyên môn'),
    ('facilitate', 'tạo điều kiện'),
    ('implement', 'triển khai'),
    ('incentive', 'động lực; ưu đãi'),
    ('mandatory', 'bắt buộc'),
    ('negotiate', 'đàm phán'),
    ('objective', 'mục tiêu'),
    ('personnel', 'nhân sự'),
    ('policy', 'chính sách'),
    ('procedure', 'quy trình'),
    ('promote', 'thăng chức; quảng bá'),
    ('qualification', 'trình độ; bằng cấp'),
    ('recruit', 'tuyển dụng'),
    ('regulation', 'quy định'),
    ('representative', 'đại diện'),
    ('requirement', 'yêu cầu'),
    ('supervise', 'giám sát'),
    ('agenda', 'chương trình họp'),
    ('attendee', 'người tham dự'),
    ('conference', 'hội nghị'),
    ('convene', 'triệu tập'),
    ('discussion', 'thảo luận'),
    ('minutes', 'biên bản cuộc họp'),
    ('presentation', 'bài thuyết trình'),
    ('proposal', 'đề xuất'),
    ('schedule', 'lịch trình'),
    ('seminar', 'hội thảo'),
    ('venue', 'địa điểm'),
    ('postpone', 'hoãn'),
    ('reschedule', 'đổi lịch'),
    ('adjourn', 'tạm dừng cuộc họp'),
    ('briefing', 'buổi phổ biến thông tin'),
    ('participate', 'tham gia'),
    ('clarify', 'làm rõ'),
    ('consensus', 'sự đồng thuận'),
    ('outline', 'dàn ý; phác thảo'),
    ('prioritize', 'ưu tiên'),
    ('acquire', 'mua lại; đạt được'),
    ('asset', 'tài sản'),
    ('audit', 'kiểm toán'),
    ('balance', 'số dư'),
    ('billing', 'lập hóa đơn'),
    ('capital', 'vốn'),
    ('commission', 'hoa hồng'),
    ('deficit', 'thâm hụt'),
    ('expense', 'chi phí'),
    ('forecast', 'dự báo'),
    ('fund', 'quỹ; cấp vốn'),
    ('invoice', 'hóa đơn'),
    ('liability', 'khoản nợ; trách nhiệm'),
    ('margin', 'biên lợi nhuận'),
    ('overhead', 'chi phí chung'),
    ('payment', 'thanh toán'),
    ('profit', 'lợi nhuận'),
    ('reimburse', 'hoàn tiền'),
    ('revenue', 'doanh thu'),
    ('transaction', 'giao dịch'),
    ('affordable', 'giá phải chăng'),
    ('bargain', 'món hời; mặc cả'),
    ('catalog', 'danh mục'),
    ('complimentary', 'miễn phí'),
    ('consumer', 'người tiêu dùng'),
    ('discount', 'giảm giá'),
    ('inventory', 'hàng tồn kho'),
    ('merchandise', 'hàng hóa'),
    ('outlet', 'cửa hàng; điểm bán'),
    ('purchase', 'mua; việc mua hàng'),
    ('refund', 'hoàn tiền'),
    ('retailer', 'nhà bán lẻ'),
    ('shipment', 'lô hàng'),
    ('stock', 'hàng tồn; cổ phiếu'),
    ('supplier', 'nhà cung cấp'),
    ('warranty', 'bảo hành'),
    ('wholesale', 'bán buôn'),
    ('receipt', 'biên lai'),
    ('availability', 'tình trạng có sẵn'),
    ('substitute', 'thay thế'),
    ('advertise', 'quảng cáo'),
    ('campaign', 'chiến dịch'),
    ('client', 'khách hàng'),
    ('competitor', 'đối thủ'),
    ('demographic', 'nhóm nhân khẩu'),
    ('endorse', 'chứng thực; ủng hộ'),
    ('launch', 'ra mắt'),
    ('marketplace', 'thị trường'),
    ('publicity', 'sự quảng bá'),
    ('survey', 'khảo sát'),
    ('target', 'nhắm mục tiêu'),
    ('trend', 'xu hướng'),
    ('brand', 'thương hiệu'),
    ('brochure', 'tờ giới thiệu'),
    ('circulation', 'lượng phát hành'),
    ('feedback', 'phản hồi'),
    ('loyalty', 'lòng trung thành'),
    ('promotion', 'khuyến mãi'),
    ('prospective', 'tiềm năng'),
    ('sponsor', 'nhà tài trợ; tài trợ'),
    ('accommodation', 'chỗ ở'),
    ('amenity', 'tiện nghi'),
    ('boarding', 'việc lên máy bay'),
    ('cancellation', 'sự hủy'),
    ('destination', 'điểm đến'),
    ('fare', 'giá vé'),
    ('itinerary', 'lịch trình chuyến đi'),
    ('luggage', 'hành lý'),
    ('occupancy', 'tỷ lệ sử dụng phòng'),
    ('reservation', 'đặt chỗ'),
    ('shuttle', 'xe đưa đón'),
    ('departure', 'khởi hành'),
    ('arrival', 'đến nơi'),
    ('delay', 'sự trì hoãn'),
    ('check-in', 'thủ tục nhận phòng; làm thủ tục'),
    ('vacancy', 'phòng trống; vị trí trống'),
    ('hospitality', 'dịch vụ khách sạn'),
    ('reception', 'quầy lễ tân; sự tiếp đón'),
    ('route', 'tuyến đường'),
    ('transfer', 'chuyển; trung chuyển'),
    ('assemble', 'lắp ráp'),
    ('component', 'linh kiện'),
    ('defective', 'bị lỗi'),
    ('durable', 'bền'),
    ('equipment', 'thiết bị'),
    ('facility', 'cơ sở; nhà xưởng'),
    ('inspection', 'kiểm tra'),
    ('maintenance', 'bảo trì'),
    ('manufacture', 'sản xuất'),
    ('operate', 'vận hành'),
    ('output', 'sản lượng'),
    ('productivity', 'năng suất'),
    ('quality', 'chất lượng'),
    ('renovate', 'cải tạo'),
    ('repair', 'sửa chữa'),
    ('specification', 'thông số kỹ thuật'),
    ('warehouse', 'nhà kho'),
    ('malfunction', 'sự trục trặc'),
    ('installation', 'lắp đặt'),
    ('upgrade', 'nâng cấp'),
    ('access', 'truy cập'),
    ('attachment', 'tệp đính kèm'),
    ('compatible', 'tương thích'),
    ('database', 'cơ sở dữ liệu'),
    ('device', 'thiết bị'),
    ('install', 'cài đặt'),
    ('network', 'mạng'),
    ('password', 'mật khẩu'),
    ('retrieve', 'truy xuất'),
    ('software', 'phần mềm'),
    ('storage', 'lưu trữ'),
    ('update', 'cập nhật'),
    ('backup', 'bản sao lưu'),
    ('security', 'bảo mật'),
    ('technical', 'kỹ thuật'),
    ('wireless', 'không dây'),
    ('efficient', 'hiệu quả'),
    ('innovative', 'đổi mới'),
    ('reliable', 'đáng tin cậy'),
    ('automate', 'tự động hóa'),
    ('accomplish', 'hoàn thành'),
    ('accurate', 'chính xác'),
    ('adequate', 'đầy đủ; thích hợp'),
    ('anticipate', 'dự đoán'),
    ('approximately', 'xấp xỉ'),
    ('consecutive', 'liên tiếp'),
    ('considerable', 'đáng kể'),
    ('decline', 'giảm; từ chối'),
    ('demonstrate', 'chứng minh; trình bày'),
    ('distribute', 'phân phối'),
    ('estimate', 'ước tính'),
    ('exceed', 'vượt quá'),
    ('expand', 'mở rộng'),
    ('fluctuate', 'dao động'),
    ('improve', 'cải thiện'),
    ('maintain', 'duy trì'),
    ('obtain', 'đạt được'),
    ('permit', 'cho phép; giấy phép'),
    ('recommend', 'khuyến nghị'),
    ('resolve', 'giải quyết'),
]


def main() -> None:
    database = Database(BASE_DIR / 'data' / 'quizlet.db')
    create_tables(database)

    study_set_repository = StudySetRepository(database)
    flashcard_repository = FlashcardRepository(database)
    service = StudySetService(
        study_set_repository,
        flashcard_repository,
    )

    existing = [
        study_set
        for study_set in service.get_all_study_sets()
        if study_set.title.strip().casefold() == TITLE.casefold()
    ]

    if existing:
        print(f'Study Set "{TITLE}" đã tồn tại. Không tạo bản trùng.')
        return

    study_set = service.create_study_set_with_flashcards(
        title=TITLE,
        description=DESCRIPTION,
        cards=CARDS,
    )

    print(
        f'Đã tạo "{study_set.title}" với {len(CARDS)} flashcards '
        f'(Study Set ID: {study_set.id}).'
    )


if __name__ == '__main__':
    main()
