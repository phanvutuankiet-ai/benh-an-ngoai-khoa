import streamlit as st
import google.generativeai as genai
import os
import re

# --- 1. CẤU HÌNH HỆ THỐNG & BẢO MẬT ---
st.set_page_config(page_title="AI Bác Sĩ Nội Trú - Chuẩn Hóa Bệnh Án", layout="wide")

# Lấy API Key và Mã PIN từ Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    ADMIN_PIN_SECRET = st.secrets["ADMIN_PIN"]
    genai.configure(api_key=api_key)
except KeyError as e:
    st.error(f"LỖI BẢO MẬT: Chưa tìm thấy {e} trong file secrets.toml.")
    st.stop()

# Khởi tạo Session State cho Admin Rules
if 'admin_rules' not in st.session_state:
    st.session_state.admin_rules = "Không có quy tắc đặc biệt nào được thiết lập."

# --- 2. GIAO DIỆN QUẢN TRỊ VIÊN (SIDEBAR) ---
st.sidebar.header("🔐 Quyền Quản Trị (Admin)")
st.sidebar.caption("Sử dụng mã PIN nội bộ. Tích hợp Firebase sẽ thực hiện ở giai đoạn sau.")

pin_input = st.sidebar.text_input("Nhập mã PIN:", type="password")

if pin_input == ADMIN_PIN_SECRET:
    st.sidebar.success("Đã xác thực quyền Admin!")
    st.session_state.admin_rules = st.sidebar.text_area(
        "Thiết lập Quy tắc Lâm sàng Tối thượng (Ưu tiên 1):", 
        value=st.session_state.admin_rules, 
        height=200,
        help="Ví dụ: Bắt buộc dùng thang điểm Alvarado cho viêm ruột thừa."
    )
elif pin_input != "":
    st.sidebar.error("Mã PIN không chính xác!")

# --- 3. CÁC HÀM TIỀN XỬ LÝ (PRE-PROCESSING) ---
def anonymize_name(full_name):
    """Ẩn danh hóa tên (VD: Đinh Thị Kim Hồng -> Đ.T.K.H)"""
    if not full_name:
        return ""
    words = full_name.strip().split()
    return ".".join([word[0].upper() for word in words])

def load_and_filter_guideline(draft_notes):
    """Thuật toán RAG cục bộ: Lọc phác đồ theo từ khóa"""
    guideline_path = "phac_do_ngoai_khoa.txt"
    if not os.path.exists(guideline_path):
        return "[HỆ THỐNG] Không tìm thấy file phac_do_ngoai_khoa.txt."
    
    try:
        with open(guideline_path, "r", encoding="utf-8") as file:
            full_text = file.read()
            
        keywords = set([w.lower() for w in re.findall(r'\b\w+\b', draft_notes) if len(w) > 3])
        paragraphs = full_text.split('\n\n')
        relevant_chunks = [p for p in paragraphs if any(kw in p.lower() for kw in keywords)]
                
        if relevant_chunks:
            return "\n\n".join(relevant_chunks[:10])
        else:
            return "[HỆ THỐNG] Phác đồ cục bộ không có nội dung khớp với ca bệnh này."
            
    except Exception as e:
        return f"[LỖI RAG]: {str(e)}"

# --- 4. GIAO DIỆN NGƯỜI DÙNG (UI) CHÍNH ---
st.title("Hệ Thống Trợ Lý AI Ngoại Khoa")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Nhập liệu Lâm sàng")
    
    # Sử dụng st.form để đóng gói luồng dữ liệu, khắc phục lỗi State Sync
    with st.form("clinical_input_form"):
        # Chia cột cho phần Hành chánh
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            ho_ten_input = st.text_input("Họ và tên:", placeholder="VD: Đinh Thị Kim Hồng")
        with c2:
            tuoi_input = st.number_input("Tuổi:", min_value=0, max_value=120, value=30, step=1)
        with c3:
            gioi_tinh_input = st.selectbox("Giới tính:", options=["Nam", "Nữ"])
            
        ghi_chu_nhap = st.text_area("Ghi chú nháp (Triệu chứng, tiền căn, khám, CLS...):", height=350)
        
        # Nút Submit của Form
        submit_btn = st.form_submit_button("Xử lý Bệnh án", type="primary", use_container_width=True)

# --- 5. LUỒNG XỬ LÝ AI ---
if submit_btn:
    if not ghi_chu_nhap.strip():
        st.warning("Vui lòng nhập ghi chú nháp trước khi xử lý.")
    else:
        with st.spinner("Đang phân tích Tháp ưu tiên và xử lý dữ liệu..."):
            ho_ten_anonymized = anonymize_name(ho_ten_input)
            filtered_guideline = load_and_filter_guideline(ghi_chu_nhap)
            admin_rules_current = st.session_state.admin_rules
            
            system_prompt = f"""
            Bạn là một Bác sĩ Nội trú Ngoại khoa. Nhiệm vụ của bạn là chuẩn hóa bệnh án và lập báo cáo bàn giao.

            ### THÁP ƯU TIÊN TRI THỨC (BẮT BUỘC TUÂN THỦ NGHIÊM NGẶT TỪ TRÊN XUỐNG):
            1. ƯU TIÊN 1 - QUY TẮC QUẢN TRỊ (ADMIN RULES): {admin_rules_current}
               -> Đây là mệnh lệnh tối cao. Bắt buộc áp dụng vào nhận xét và biện luận.
            2. ƯU TIÊN 2 - SỰ THẬT LÂM SÀNG (ZERO-HALLUCINATION):
               -> Ghi chú của sinh viên: "{ghi_chu_nhap}"
               -> Tuyệt đối không tự bịa thêm triệu chứng âm tính hay dương tính nếu sinh viên không ghi. Thiếu dữ liệu thì ghi: "[Không có thông tin ghi nhận trong giấy nháp]".
            3. ƯU TIÊN 3 - PHÁC ĐỒ CỤC BỘ (RAG):
               -> Trích xuất từ kho dữ liệu: "{filtered_guideline}"
               -> Dùng phác đồ này để đối chiếu xem sinh viên chẩn đoán đúng chưa, thiếu sót gì.
            4. ƯU TIÊN 4 - Y VĂN THẾ GIỚI:
               -> Chỉ sử dụng trí tuệ AI có sẵn NẾU Phác đồ cục bộ (Ưu tiên 3) không có thông tin về bệnh lý này. Nếu có xung đột, phải nghe theo Phác đồ cục bộ.

            ### YÊU CẦU ĐẦU RA (Trình bày 3 phần rõ rệt):

            **PHẦN A: NHẬN XÉT CỦA BS. NỘI TRÚ**
            Dựa vào Tháp ưu tiên, chỉ ra sinh viên đã thiếu sót gì trong việc hỏi bệnh, khám lâm sàng hoặc đề nghị cận lâm sàng.

            **PHẦN B: BỆNH ÁN CẤU TRÚC 16 PHẦN (Tuyệt đối tuân thủ khung sau)**
            I. Hành chánh (Tên: {ho_ten_anonymized}, Tuổi: {tuoi_input}, Giới tính: {gioi_tinh_input})
            II. Lý do nhập viện
            III. Bệnh sử
            IV. Tiền căn (Bản thân và Gia đình)
            V. Lược qua các cơ quan
            VI. Khám lâm sàng
            VII. Tóm tắt bệnh án
            VIII. Đặt vấn đề
            IX. Chẩn đoán sơ bộ
            X. Chẩn đoán phân biệt
            XI. Đề nghị cận lâm sàng
            XII. Kết quả cận lâm sàng
            XIII. Biện luận lâm sàng
            XIV. Biện luận cận lâm sàng
            XV. Chẩn đoán
            XVI. Hướng điều trị và Tiên lượng

            **PHẦN C: TÓM TẮT BÀN GIAO (SOAP)**
            - S (Subjective): Lời khai, cơ năng.
            - O (Objective): Sinh hiệu, thực thể, CLS.
            - A (Assessment): Chẩn đoán, mức độ nặng.
            - P (Plan): Hướng xử trí.
            """

            try:
                model = genai.GenerativeModel("gemini-3-flash-preview")
                response = model.generate_content(system_prompt)
                
                with col2:
                    st.subheader("Kết quả Chuẩn hóa")
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"Lỗi kết nối AI: {str(e)}")
