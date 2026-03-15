import streamlit as st
import google.generativeai as genai
import pypdf

# --- 1. CẤU HÌNH & TRẠNG THÁI HỆ THỐNG ---
st.set_page_config(page_title="Hệ Sinh Thái Bệnh Án AI", layout="centered")

# Khởi tạo bộ nhớ tạm cho phiên làm việc
if 'role' not in st.session_state:
    st.session_state.role = 'Guest'
if 'admin_rules' not in st.session_state:
    st.session_state.admin_rules = "- Lý do nhập viện: Chỉ ghi triệu chứng chính ngắn gọn nhất, không ghi dài dòng chi tiết."

# Gọi chìa khóa API từ két sắt bảo mật
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("LỖI BẢO MẬT: Chưa tìm thấy API Key trong mục Settings -> Secrets của Streamlit.")
    api_key = None

# Hàm xử lý tài liệu PDF y khoa
def extract_text_from_pdf(uploaded_file):
    try:
        reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Không thể đọc file PDF. Vui lòng kiểm tra lại định dạng: {e}")
        return ""

# --- 2. HỆ THỐNG ĐIỀU HƯỚNG & PHÂN QUYỀN (SIDEBAR) ---
st.sidebar.title("Bảng Điều Khiển")
if st.session_state.role == 'Guest':
    loai_dang_nhap = st.sidebar.radio("Chọn chức năng:", ["Sử dụng Bệnh án", "Đăng nhập Quản trị (Admin)"])
elif st.session_state.role == 'Admin':
    loai_dang_nhap = st.sidebar.radio("Chọn chức năng:", ["Sử dụng Bệnh án", "Quản lý Quy tắc (Admin)", "Đăng xuất"])

if loai_dang_nhap == "Đăng xuất":
    st.session_state.role = 'Guest'
    st.rerun()

# --- 3. GIAO DIỆN QUẢN TRỊ VIÊN (ADMIN) ---
if loai_dang_nhap == "Đăng nhập Quản trị (Admin)":
    st.header("Cổng Đăng Nhập Quản Trị")
    mat_khau_admin = st.text_input("Nhập mã PIN (Gợi ý: 1234):", type="password")
    if st.button("Xác nhận"):
        if mat_khau_admin == "1234":
            st.session_state.role = 'Admin'
            st.rerun()
        else:
            st.error("Sai mã PIN.")

elif loai_dang_nhap == "Quản lý Quy tắc (Admin)":
    st.header("Thiết lập Quy tắc Lâm sàng Bắt buộc")
    st.info("Lưu ý: Các quy tắc nhập vào đây mang tính áp đặt tối cao. AI buộc phải tuân thủ tuyệt đối khi nội suy bệnh án.")
    quy_tac_moi = st.text_area("Cập nhật quy tắc hành nghề:", value=st.session_state.admin_rules, height=200)
    if st.button("Lưu Quy Tắc", type="primary"):
        st.session_state.admin_rules = quy_tac_moi
        st.success("Hệ thống đã cập nhật quy tắc thành công!")

# --- 4. GIAO DIỆN LÂM SÀNG CHÍNH (SOẠN BỆNH ÁN) ---
elif loai_dang_nhap == "Sử dụng Bệnh án":
    st.title("Trợ lý AI Soạn Bệnh Án Ngoại Khoa")
    st.write("Hệ thống tự động chuẩn hóa dữ liệu thô thành Bệnh án Ngoại khoa 16 phần theo chuẩn học thuật.")
    
    st.markdown("---")
    st.header("I. Dữ liệu Hành chánh")
    col1, col2 = st.columns(2)
    with col1:
        ho_ten = st.text_input("Họ và tên bệnh nhân")
        ly_do_nv = st.text_input("Lý do nhập viện (Ghi chú thô)")
    with col2:
        tuoi = st.number_input("Tuổi", min_value=0, max_value=120, step=1)
        gioi_tinh = st.selectbox("Giới tính", ["Nam", "Nữ"])
    
    st.markdown("---")
    st.header("II. Nạp Phác đồ Tham chiếu (Tùy chọn)")
    uploaded_file = st.file_uploader("Tải lên file Guideline/Phác đồ (PDF) để AI ưu tiên biện luận theo:", type=['pdf'])
    file_content = ""
    if uploaded_file is not None:
        file_content = extract_text_from_pdf(uploaded_file)
        if file_content:
            st.success("Đã trích xuất dữ liệu từ tài liệu thành công.")

    st.markdown("---")
    st.header("III. Dữ liệu Lâm sàng & Cận lâm sàng")
    thong_tin_nhap = st.text_area("Nhập các mảnh thông tin (Bệnh sử, Tiền căn, Khám, Chỉ số xét nghiệm, Siêu âm...)", height=200, placeholder="Ví dụ: Đau HSP 10h sau ăn, nôn 1 lần. Khám: M 80, HA 160/90, ấn đau HSP, Murphy (+). Tiền căn: Sỏi túi mật 5 năm. CLS: WBC 22.23, SA: túi mật 38mm, sỏi 12mm...")

    st.markdown("---")
    if st.button("Tiến hành Cấu trúc Bệnh Án", type="primary", use_container_width=True):
        if not api_key:
            st.warning("Hệ thống đang bị khóa do thiếu API Key.")
        elif not thong_tin_nhap or not ho_ten:
            st.warning("Vui lòng cung cấp ít nhất Họ tên và Dữ liệu Lâm sàng để hệ thống hoạt động.")
        else:
            try:
                # Khởi động AI Engine
                genai.configure(api_key=api_key)
                
                # Cấu hình tính logic cao, giảm tính sáng tạo để tránh bịa đặt thông tin y khoa
                generation_config = {
                  "temperature": 0.1, 
                  "top_p": 0.9,
                  "top_k": 40,
                  "max_output_tokens": 8192,
                }
                model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

                # KIẾN TRÚC PROMPT: THÁP ƯU TIÊN VÀ KHUNG 16 PHẦN
                system_prompt = f"""
                Bạn là một Bác sĩ Ngoại khoa cấp cao. Nhiệm vụ của bạn là phân tích dữ liệu lâm sàng thô và cấu trúc thành một Bệnh án Ngoại khoa hoàn chỉnh, logic và mang tính học thuật cao.
                
                🔥 THÁP ƯU TIÊN KIẾN THỨC BẮT BUỘC TUÂN THỦ:
                [Ưu tiên 1 - Lệnh Tối Cao từ Trưởng Khoa]: Bạn PHẢI tuân thủ tuyệt đối các quy tắc sau khi định dạng văn bản:
                {st.session_state.admin_rules}
                
                [Ưu tiên 2 - Guideline Cục bộ]: Sử dụng tài liệu dưới đây làm cơ sở chính để biện luận chẩn đoán và hướng điều trị (Nếu có):
                {file_content if file_content else "Không có tài liệu đính kèm."}
                
                [Ưu tiên 3 - Y văn Thế giới]: Đối chiếu các dữ liệu còn thiếu với Harrison's Principles of Internal Medicine, Sabiston Textbook of Surgery, và các phác đồ quốc tế (VD: Tokyo Guidelines) để củng cố lập luận. Không tự ý bịa đặt số liệu.

                📋 CẤU TRÚC BỆNH ÁN BẮT BUỘC (Trình bày đúng 16 tiêu đề La Mã sau. Nếu thiếu thông tin để biện luận, hãy điền "Chưa ghi nhận bất thường" hoặc "Đề nghị khảo sát thêm"):
                I. HÀNH CHÁNH
                II. LÝ DO NHẬP VIỆN
                III. BỆNH SỬ
                IV. TIỀN CĂN (1. Bản thân, 2. Gia đình)
                V. LƯỢC QUA CÁC CƠ QUAN
                VI. KHÁM LÂM SÀNG (A. Tổng trạng, B. Khám cơ quan)
                VII. TÓM TẮT BỆNH ÁN
                VIII. ĐẶT VẤN ĐỀ
                IX. CHẨN ĐOÁN SƠ BỘ
                X. CHẨN ĐOÁN PHÂN BIỆT
                XI. BIỆN LUẬN LÂM SÀNG (Lập luận logic để loại trừ các bệnh ở phần X)
                XII. ĐỀ NGHỊ CLS
                XIII. KẾT QUẢ CẬN LÂM SÀNG
                XIV. BIỆN LUẬN CẬN LÂM SÀNG
                XV. CHẨN ĐOÁN XÁC ĐỊNH
                XVI. HƯỚNG ĐIỀU TRỊ (Nội khoa & Ngoại khoa)

                DỮ LIỆU BỆNH NHÂN:
                - Hành chánh: {ho_ten}, {tuoi} tuổi, Giới tính: {gioi_tinh}.
                - Lý do nhập viện ban đầu: {ly_do_nv} (Hãy áp dụng [Ưu tiên 1] để chỉnh sửa lại phần này).
                - Dữ liệu Lâm sàng/Cận lâm sàng: {thong_tin_nhap}
                """
                
                with st.spinner('Hệ thống đang nội suy và áp dụng các tiêu chuẩn y khoa...'):
                    response = model.generate_content(system_prompt)
                    
                st.success("Tạo bệnh án thành công! Nhấn Ctrl + P để lưu báo cáo dưới dạng PDF.")
                st.markdown("### KẾT QUẢ BỆNH ÁN CHÍNH THỨC")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Lỗi phản hồi từ máy chủ AI: {e}")
