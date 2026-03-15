import streamlit as st
import google.generativeai as genai
import PyPDF2

# 1. CẤU HÌNH & TRẠNG THÁI
st.set_page_config(page_title="Hệ Sinh Thái Bệnh Án AI", layout="centered")

if 'role' not in st.session_state:
    st.session_state.role = 'Guest'
if 'admin_rules' not in st.session_state:
    st.session_state.admin_rules = "- Lý do nhập viện: Chỉ ghi triệu chứng chính ngắn gọn."

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("Chưa tìm thấy API Key trong Secrets.")
    api_key = None

def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# 2. THANH SIDEBAR PHÂN QUYỀN
st.sidebar.title("Hệ Thống")
if st.session_state.role == 'Guest':
    loai_dang_nhap = st.sidebar.radio("Tùy chọn:", ["Sử dụng Bệnh án", "Đăng nhập Admin"])
elif st.session_state.role == 'Admin':
    loai_dang_nhap = st.sidebar.radio("Tùy chọn:", ["Sử dụng Bệnh án", "Quản lý Quy tắc (Admin)", "Đăng xuất"])

if loai_dang_nhap == "Đăng xuất":
    st.session_state.role = 'Guest'
    st.rerun()

# 3. QUẢN TRỊ ADMIN
if loai_dang_nhap == "Đăng nhập Admin":
    mat_khau_admin = st.text_input("Nhập mã PIN:", type="password")
    if st.button("Xác nhận"):
        if mat_khau_admin == "1234":
            st.session_state.role = 'Admin'
            st.rerun()
        else:
            st.error("Sai mã PIN.")

elif loai_dang_nhap == "Quản lý Quy tắc (Admin)":
    st.header("Thiết lập Quy tắc Lâm sàng")
    quy_tac_moi = st.text_area("Cập nhật quy tắc:", value=st.session_state.admin_rules, height=200)
    if st.button("Lưu Quy Tắc", type="primary"):
        st.session_state.admin_rules = quy_tac_moi
        st.success("Đã lưu quy tắc!")

# 4. GIAO DIỆN SỬ DỤNG CHÍNH
elif loai_dang_nhap == "Sử dụng Bệnh án":
    st.title("Trợ lý AI Soạn Bệnh Án Ngoại Khoa")
    
    st.header("Thông tin đầu vào")
    col1, col2 = st.columns(2)
    with col1:
        ho_ten = st.text_input("Họ và tên")
        ly_do_nv = st.text_input("Lý do nhập viện")
    with col2:
        tuoi = st.number_input("Tuổi", 0, 120)
        gioi_tinh = st.selectbox("Giới tính", ["Nam", "Nữ"])
    
    uploaded_file = st.file_uploader("Tải lên Phác đồ (PDF) để tham chiếu", type=['pdf'])
    file_content = ""
    if uploaded_file is not None:
        file_content = extract_text_from_pdf(uploaded_file)
        st.success("Đã nạp tài liệu.")

    thong_tin_nhap = st.text_area("Nhập Ghi chú Lâm sàng (Triệu chứng, Khám, CLS)...", height=150)

    if st.button("Tạo Bệnh Án Hoàn Chỉnh", type="primary", use_container_width=True):
        if not thong_tin_nhap or not ho_ten:
            st.warning("Vui lòng điền Họ tên và Ghi chú.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config={"temperature": 0.1})

                # PROMPT ÉP KHUNG 16 PHẦN
                system_prompt = f"""
                Bạn là một Bác sĩ Ngoại khoa. Nhiệm vụ của bạn là tổng hợp dữ liệu thành một Bệnh án Ngoại khoa ĐÚNG 16 PHẦN.
                
                QUY TẮC TỐI CAO:
                1. {st.session_state.admin_rules}
                2. Tham chiếu tài liệu này nếu có: {file_content}
                3. BẮT BUỘC trình bày theo ĐÚNG 16 tiêu đề La Mã dưới đây. Không được thiếu mục nào. Nếu dữ liệu đầu vào không có thông tin cho một mục cụ thể, hãy điền "Chưa ghi nhận bất thường" hoặc "Đề nghị bổ sung".
                
                CẤU TRÚC BẮT BUỘC:
                I. HÀNH CHÁNH
                II. LÝ DO NHẬP VIỆN
                III. BỆNH SỬ
                IV. TIỀN CĂN (Chia rõ 1. Bản thân, 2. Gia đình)
                V. LƯỢC QUA CÁC CƠ QUAN
                VI. KHÁM LÂM SÀNG (Chia rõ A. Tổng trạng, B. Khám cơ quan)
                VII. TÓM TẮT BỆNH ÁN
                VIII. ĐẶT VẤN ĐỀ
                IX. CHẨN ĐOÁN SƠ BỘ
                X. CHẨN ĐOÁN PHÂN BIỆT
                XI. BIỆN LUẬN LÂM SÀNG
                XII. ĐỀ NGHỊ CLS
                XIII. KẾT QUẢ CẬN LÂM SÀNG
                XIV. BIỆN LUẬN CẬN LÂM SÀNG
                XV. CHẨN ĐOÁN XÁC ĐỊNH
                XVI. HƯỚNG ĐIỀU TRỊ

                DỮ LIỆU BỆNH NHÂN:
                - Hành chánh: {ho_ten}, {tuoi} tuổi, {gioi_tinh}.
                - Lý do nhập viện: {ly_do_nv}
                - Ghi chú: {thong_tin_nhap}
                """
                
                with st.spinner('Đang nội suy theo khung 16 phần...'):
                    response = model.generate_content(system_prompt)
                    
                st.markdown("### BỆNH ÁN CHI TIẾT")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Lỗi hệ thống: {e}")
