import streamlit as st
import google.generativeai as genai
import os

# 1. CẤU HÌNH HỆ THỐNG
st.set_page_config(page_title="Hệ Sinh Thái Bệnh Án AI", layout="wide")

if 'role' not in st.session_state:
    st.session_state.role = 'Guest'
if 'admin_rules' not in st.session_state:
    st.session_state.admin_rules = "Không có quy tắc bắt buộc nào."

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("LỖI: Chưa tìm thấy API Key trong Secrets.")
    api_key = None

# Hàm tự động đọc phác đồ từ file txt trên GitHub
def load_default_guideline():
    try:
        if os.path.exists("phac_do_ngoai_khoa.txt"):
            with open("phac_do_ngoai_khoa.txt", "r", encoding="utf-8") as file:
                return file.read()
        return "Không tìm thấy file phac_do_ngoai_khoa.txt. AI sẽ sử dụng kiến thức y văn chuẩn thế giới."
    except Exception as e:
        return f"Lỗi nạp phác đồ: {e}"

guideline_text = load_default_guideline()

# 2. ĐIỀU HƯỚNG BÊN TRÁI
st.sidebar.title("Chế độ Hệ thống")
if st.session_state.role == 'Guest':
    mode = st.sidebar.radio("Tùy chọn:", ["Soạn Bệnh Án (Lâm sàng)", "Đăng nhập Quản trị (Admin)"])
else:
    mode = st.sidebar.radio("Tùy chọn:", ["Soạn Bệnh Án (Lâm sàng)", "Quản lý Quy tắc (Admin)", "Đăng xuất"])

if mode == "Đăng xuất":
    st.session_state.role = 'Guest'
    st.rerun()

# 3. CHẾ ĐỘ QUẢN TRỊ (ADMIN)
if mode == "Đăng nhập Quản trị (Admin)":
    st.header("Cổng Đăng Nhập Quản Trị")
    pin = st.text_input("Nhập mã PIN (Gợi ý: 1234):", type="password")
    if st.button("Xác nhận"):
        if pin == "1234":
            st.session_state.role = 'Admin'
            st.rerun()
        else:
            st.error("Sai mã PIN.")

elif mode == "Quản lý Quy tắc (Admin)":
    st.header("Thiết lập Quy tắc Lâm sàng Bắt buộc")
    st.write("Các quy tắc tại đây mang tính áp đặt tối cao. AI buộc phải tuân thủ tuyệt đối.")
    new_rules = st.text_area("Cập nhật quy tắc:", value=st.session_state.admin_rules, height=200)
    if st.button("Lưu Quy Tắc", type="primary"):
        st.session_state.admin_rules = new_rules
        st.success("Hệ thống đã cập nhật quy tắc thành công!")

# 4. CHẾ ĐỘ LÂM SÀNG
elif mode == "Soạn Bệnh Án (Lâm sàng)":
    st.title("BS. Nội Trú Trợ Lý: Hội chẩn & Soạn Bệnh Án")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.header("1. Dữ liệu thô (Giấy nháp)")
        ho_ten = st.text_input("Họ tên / Tuổi / Giới tính", placeholder="VD: Nguyễn Văn A, 45 tuổi, Nam")
        
        st.write("Nhập toàn bộ bệnh sử, tiền căn, khám, xét nghiệm vào đây:")
        ghi_chu_nhap = st.text_area("Ghi chú lâm sàng", height=400, placeholder="Đau HSP 1 ngày, nôn. Khám: ấn đau HSP, Murphy (+). Tiền căn sỏi TM. SA: túi mật to, sỏi 12mm...")
        
        btn_submit = st.button("Tiến hành Hội chẩn & Cấu trúc", type="primary", use_container_width=True)

    with col2:
        st.header("2. Kết quả Biện luận & Bệnh án")
        
        if btn_submit:
            if not api_key:
                st.warning("Hệ thống đang bị khóa do thiếu API Key.")
            elif not ghi_chu_nhap:
                st.warning("Vui lòng cung cấp Dữ liệu Lâm sàng.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config={"temperature": 0.1})
                    
                    system_prompt = f"""
                    Bạn là một Bác sĩ Nội trú Ngoại khoa xuất sắc. Nhiệm vụ của bạn là hướng dẫn sinh viên bằng cách cấu trúc lại dữ liệu lộn xộn thành Bệnh án chuẩn 16 phần, đồng thời chỉ ra các thiếu sót trong quá trình khám của sinh viên.

                    THÁP ƯU TIÊN KIẾN THỨC:
                    1. Quy tắc bắt buộc từ Trưởng khoa: {st.session_state.admin_rules}
                    2. Phác đồ Bệnh viện (Ưu tiên tham chiếu để biện luận): {guideline_text}
                    3. Y văn chuẩn: Nếu 2 mục trên không có, đối chiếu với Harrison, Sabiston, Tokyo Guidelines.

                    YÊU CẦU ĐẦU RA BẮT BUỘC:
                    Phần A: NHẬN XÉT CỦA BS. NỘI TRÚ
                    - Phân tích ngắn gọn dữ liệu sinh viên cung cấp.
                    - CHỈ RA ĐIỂM THIẾU SÓT: Liệt kê rõ các triệu chứng cơ năng/thực thể hoặc tiền căn mà sinh viên đã quên khám để có thể loại trừ các chẩn đoán phân biệt.
                    
                    Phần B: BỆNH ÁN CẤU TRÚC 16 PHẦN
                    Trình bày đúng 16 tiêu đề La Mã sau. Nếu thiếu thông tin, ghi "Chưa ghi nhận bất thường" hoặc "Đề nghị khảo sát thêm".
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
                    XI. BIỆN LUẬN LÂM SÀNG
                    XII. ĐỀ NGHỊ CLS
                    XIII. KẾT QUẢ CẬN LÂM SÀNG
                    XIV. BIỆN LUẬN CẬN LÂM SÀNG
                    XV. CHẨN ĐOÁN XÁC ĐỊNH
                    XVI. HƯỚNG ĐIỀU TRỊ

                    DỮ LIỆU TỪ SINH VIÊN:
                    - Hành chánh: {ho_ten}
                    - Ghi chú thô: {ghi_chu_nhap}
                    """
                    
                    with st.spinner("BS. Nội trú đang đọc nháp và biện luận..."):
                        response = model.generate_content(system_prompt)
                        st.markdown(response.text)
                
                except Exception as e:
                    st.error(f"Lỗi phản hồi từ máy chủ: {e}")
