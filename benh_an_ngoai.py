import streamlit as st
import google.generativeai as genai
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Bệnh Án & Hội Chẩn", layout="wide")

# Khởi tạo bộ nhớ tạm để quản lý quyền và quy tắc
if 'role' not in st.session_state:
    st.session_state.role = 'Guest'
if 'admin_rules' not in st.session_state:
    st.session_state.admin_rules = "Không có quy tắc bắt buộc nào."

# Trích xuất API Key từ hệ thống bảo mật Secrets của Streamlit
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("LỖI BẢO MẬT: Chưa tìm thấy API Key trong mục Settings -> Secrets.")
    api_key = None

# Hàm tự động đọc phác đồ từ file văn bản cục bộ trên GitHub
def load_default_guideline():
    try:
        if os.path.exists("phac_do_ngoai_khoa.txt"):
            with open("phac_do_ngoai_khoa.txt", "r", encoding="utf-8") as file:
                return file.read()
        return "Không tìm thấy file phac_do_ngoai_khoa.txt. Hệ thống sẽ sử dụng kiến thức y văn chuẩn thế giới."
    except Exception as e:
        return f"Lỗi nạp phác đồ tham chiếu: {e}"

guideline_text = load_default_guideline()

# --- 2. THANH ĐIỀU HƯỚNG BÊN TRÁI ---
st.sidebar.title("Chế độ Hệ thống")
if st.session_state.role == 'Guest':
    mode = st.sidebar.radio("Tùy chọn:", ["Soạn Bệnh Án (Lâm sàng)", "Đăng nhập Quản trị (Admin)"])
else:
    mode = st.sidebar.radio("Tùy chọn:", ["Soạn Bệnh Án (Lâm sàng)", "Quản lý Quy tắc (Admin)", "Đăng xuất"])

if mode == "Đăng xuất":
    st.session_state.role = 'Guest'
    st.rerun()

# --- 3. KHU VỰC QUẢN TRỊ VIÊN (ADMIN) ---
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
    st.write("Các quy tắc tại đây mang tính áp đặt tối cao. AI buộc phải tuân thủ tuyệt đối trong quá trình biện luận.")
    new_rules = st.text_area("Cập nhật quy tắc hành nghề:", value=st.session_state.admin_rules, height=200)
    if st.button("Lưu Quy Tắc", type="primary"):
        st.session_state.admin_rules = new_rules
        st.success("Hệ thống đã cập nhật quy tắc thành công!")

# --- 4. KHU VỰC LÂM SÀNG CHÍNH ---
elif mode == "Soạn Bệnh Án (Lâm sàng)":
    st.title("BS. Nội Trú Trợ Lý: Hội chẩn & Soạn Bệnh Án")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.header("1. Dữ liệu thô (Giấy nháp)")
        ho_ten = st.text_input("Họ tên / Tuổi / Giới tính", placeholder="VD: Nguyễn Văn A, 45 tuổi, Nam")
        
        st.write("Nhập toàn bộ bệnh sử, tiền căn, khám, xét nghiệm vào đây:")
        ghi_chu_nhap = st.text_area(
            "Ghi chú lâm sàng", 
            height=400, 
            placeholder="Đau HSP 1 ngày, nôn. Khám: ấn đau HSP, Murphy (+). Tiền căn sỏi TM. SA: túi mật to, sỏi 12mm..."
        )
        
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
                    # Khởi động AI Engine
                    genai.configure(api_key=api_key)
                    # Thiết lập nhiệt độ = 0.1 để đảm bảo tính chính xác, không sáng tạo tùy tiện
                    model = genai.GenerativeModel(
                        model_name="gemini-3-flash-preview", 
                        generation_config={"temperature": 0.1}
                    )
                    
                    # PROMPT ZERO-HALLUCINATION BẮT BUỘC
                    system_prompt = f"""
                    Bạn là một Bác sĩ Nội trú Ngoại khoa đang hướng dẫn sinh viên. Nhiệm vụ của bạn là cấu trúc lại dữ liệu thô của sinh viên thành Bệnh án 16 phần và hướng dẫn biện luận.

                    ⚠️ NGUYÊN TẮC ZERO-HALLUCINATION (CẤM BỊA ĐẶT DỮ LIỆU):
                    1. BẢO TOÀN DỮ LIỆU THÔ: Bạn CHỈ ĐƯỢC PHÉP sử dụng các triệu chứng (âm tính/dương tính), chỉ số sinh hiệu, kết quả cận lâm sàng có xuất hiện trong phần "Dữ liệu từ sinh viên".
                    2. XỬ LÝ DỮ LIỆU TRỐNG: Đối với bất kỳ phần nào trong cấu trúc 16 phần (đặc biệt là Khám Lâm Sàng các hệ cơ quan, Tiền căn) mà sinh viên không ghi chú, BẮT BUỘC phải ghi chính xác cụm từ: "[Không có thông tin ghi nhận trong giấy nháp]". 
                    3. CẤM SUY DIỄN TRIỆU CHỨNG ÂM TÍNH: Tuyệt đối KHÔNG tự ý điền các cụm từ như "Bụng mềm", "Không sốt", "Tim đều", "Chưa ghi nhận bất thường" nếu sinh viên không trực tiếp viết ra. Việc tự ý kết luận bình thường khi chưa khám là vi phạm y đức.

                    THÁP ƯU TIÊN KIẾN THỨC BIỆN LUẬN:
                    1. Quy tắc bắt buộc từ Trưởng khoa: {st.session_state.admin_rules}
                    2. Phác đồ Bệnh viện (Ưu tiên tham chiếu): {guideline_text}
                    3. Y văn chuẩn: Harrison's Principles of Internal Medicine, Sabiston Textbook of Surgery, Tokyo Guidelines.

                    YÊU CẦU ĐẦU RA (CẤU TRÚC BẮT BUỘC):
                    
                    Phần A: NHẬN XÉT & CHỈNH SỬA CỦA BS. NỘI TRÚ
                    - Phê bình sự thiếu sót: Dựa vào Tiêu chuẩn chẩn đoán chuẩn, hãy chỉ rõ sinh viên ĐÃ QUÊN KHÁM hoặc QUÊN HỎI những triệu chứng/tiền căn/chỉ số nào quan trọng để củng cố chẩn đoán.

                    Phần B: BỆNH ÁN CẤU TRÚC 16 PHẦN
                    (Trình bày đủ 16 phần La Mã từ I đến XVI. Áp dụng nghiêm ngặt NGUYÊN TẮC ZERO-HALLUCINATION).
                    - Trong phần XI. BIỆN LUẬN LÂM SÀNG: Chỉ dùng logic y văn để giải thích các triệu chứng CÓ THẬT của bệnh nhân. Nếu dữ liệu quá ít, hãy kết luận: "Chưa đủ dữ kiện lâm sàng để chẩn đoán xác định, cần đề nghị khám thêm...".
                    - Trong phần XII. ĐỀ NGHỊ CLS: Liệt kê rõ các chỉ định cần làm thêm để bù đắp cho sự thiếu sót của sinh viên.

                    DỮ LIỆU TỪ SINH VIÊN:
                    - Hành chánh: {ho_ten}
                    - Ghi chú thô: {ghi_chu_nhap}
                    """
                    
                    with st.spinner("BS. Nội trú đang đọc nháp và biện luận..."):
                        response = model.generate_content(system_prompt)
                        st.markdown(response.text)
                
                except Exception as e:
                    st.error(f"Lỗi phản hồi từ máy chủ API: {e}")
