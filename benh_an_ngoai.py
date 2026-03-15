import streamlit as st
import os
from services.ai_service import initialize_ai, process_medical_record
from services.rag_service import load_and_filter_guideline
from utils.text_processing import anonymize_name

# --- 1. CẤU HÌNH HỆ THỐNG & BẢO MẬT ---
st.set_page_config(page_title="AI Bác Sĩ Nội Trú - Ngoại Khoa", layout="wide")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    ADMIN_PIN_SECRET = st.secrets["ADMIN_PIN"]
    initialize_ai(api_key)
except KeyError as e:
    st.error(f"LỖI BẢO MẬT: Chưa tìm thấy {e} trong file secrets.toml.")
    st.stop()

# --- 2. CƠ CHẾ ĐỌC "SỔ TAY KINH NGHIỆM" TỪ GITHUB ---
def load_admin_rules():
    """Tự động tìm và đọc file quy_tac_kinh_nghiem.txt nếu có trên hệ thống"""
    file_path = "quy_tac_kinh_nghiem.txt"
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Lỗi đọc file quy tắc: {str(e)}"
    return "Không có quy tắc đặc biệt nào được thiết lập."

# Khởi tạo bộ nhớ tạm, lấy dữ liệu gốc từ Sổ tay kinh nghiệm
if 'admin_rules' not in st.session_state:
    st.session_state.admin_rules = load_admin_rules()

# --- 3. GIAO DIỆN QUẢN TRỊ (PHÒNG THÍ NGHIỆM TẠM THỜI) ---
st.sidebar.header("🔐 Quyền Quản Trị (Admin)")
st.sidebar.caption("Dùng để test tạm thời các quy tắc mới trước khi lưu vĩnh viễn lên GitHub.")

pin_input = st.sidebar.text_input("Nhập mã PIN:", type="password")

if pin_input == ADMIN_PIN_SECRET:
    st.sidebar.success("Đã xác thực quyền Admin!")
    # Ô nhập liệu này cho phép ghi đè tạm thời quy tắc đã đọc từ file
    st.session_state.admin_rules = st.sidebar.text_area(
        "Quy tắc Lâm sàng Tối thượng (Test Sandbox):", 
        value=st.session_state.admin_rules, 
        height=300
    )
    if st.sidebar.button("Tải lại quy tắc gốc từ Sổ tay"):
        st.session_state.admin_rules = load_admin_rules()
        st.rerun()
elif pin_input != "":
    st.sidebar.error("Mã PIN không chính xác!")

# --- 4. GIAO DIỆN NGƯỜI DÙNG CHÍNH ---
st.title("Hệ Thống Trợ Lý AI Ngoại Khoa")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Nhập liệu Lâm sàng")
    with st.form("clinical_input_form"):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: 
            ho_ten_input = st.text_input("Họ và tên:", placeholder="VD: Đinh Thị Kim Hồng")
        with c2: 
            tuoi_input = st.number_input("Tuổi:", min_value=0, max_value=120, value=30, step=1)
        with c3: 
            gioi_tinh_input = st.selectbox("Giới tính:", options=["Nam", "Nữ"])
            
        ghi_chu_nhap = st.text_area("Ghi chú nháp (Triệu chứng, tiền căn, khám, CLS...):", height=350)
        submit_btn = st.form_submit_button("Xử lý Bệnh án", type="primary", use_container_width=True)

# --- 5. LUỒNG XỬ LÝ DỮ LIỆU ---
if submit_btn:
    if not ghi_chu_nhap.strip():
        st.warning("Vui lòng nhập ghi chú nháp trước khi xử lý.")
    else:
        with st.spinner("Đang xử lý: Trích xuất tĩnh (Vùng 1) và Suy luận lâm sàng (Vùng 2)..."):
            # Tiền xử lý dữ liệu
            ho_ten_anonymized = anonymize_name(ho_ten_input)
            filtered_guideline = load_and_filter_guideline(ghi_chu_nhap)
            
            try:
                # Gọi Service AI (Truyền quy tắc Admin hiện tại vào)
                data = process_medical_record(ghi_chu_nhap, filtered_guideline, st.session_state.admin_rules)
                b = data.get("phan_b_benh_an", {})
                
                # Hàm map tĩnh cho Vùng 1 (Đảm bảo Zero-Hallucination)
                def get_val(key):
                    val = b.get(key, "").strip()
                    return val if val else "[Không có thông tin ghi nhận trong giấy nháp]"

                # Kết xuất giao diện bên phải
                with col2:
                    st.subheader("Kết quả Chuẩn hóa")
                    
                    st.markdown("### PHẦN A: NHẬN XÉT CỦA BS. NỘI TRÚ")
                    st.write(data.get("phan_a_nhan_xet", "Không có nhận xét."))
                    
                    st.markdown("### PHẦN B: BỆNH ÁN CẤU TRÚC 16 PHẦN")
                    st.markdown(f"**I. Hành chánh:** Tên: {ho_ten_anonymized} | Tuổi: {tuoi_input} | Giới tính: {gioi_tinh_input}")
                    st.markdown(f"**II. Lý do nhập viện:** {get_val('ly_do_nhap_vien')}")
                    st.markdown(f"**III. Bệnh sử:** {get_val('benh_su')}")
                    st.markdown(f"**IV. Tiền căn:** {get_val('tien_can')}")
                    st.markdown(f"**V. Lược qua các cơ quan:** {get_val('luoc_qua_cac_co_quan')}")
                    st.markdown(f"**VI. Khám lâm sàng:** {get_val('kham_lam_sang')}")
                    st.markdown(f"**VII. Tóm tắt bệnh án:** {get_val('tom_tat_benh_an')}")
                    st.markdown(f"**VIII. Đặt vấn đề:** {get_val('dat_van_de')}")
                    st.markdown(f"**IX. Chẩn đoán sơ bộ:** {get_val('chan_doan_so_bo')}")
                    st.markdown(f"**X. Chẩn đoán phân biệt:** {get_val('chan_doan_phan_biet')}")
                    st.markdown(f"**XI. Đề nghị cận lâm sàng:** {get_val('de_nghi_cls')}")
                    st.markdown(f"**XII. Kết quả cận lâm sàng:** {get_val('ket_qua_cls')}")
                    st.markdown(f"**XIII. Biện luận lâm sàng:** {get_val('bien_luan_lam_sang')}")
                    st.markdown(f"**XIV. Biện luận cận lâm sàng:** {get_val('bien_luan_cls')}")
                    st.markdown(f"**XV. Chẩn đoán:** {get_val('chan_doan_xac_dinh')}")
                    st.markdown(f"**XVI. Hướng điều trị và Tiên lượng:** {get_val('huong_dieu_tri')}")

                    st.markdown("### PHẦN C: TÓM TẮT BÀN GIAO (SOAP)")
                    soap = data.get("phan_c_soap", {})
                    st.markdown(f"- **S (Subjective):** {soap.get('s', '')}")
                    st.markdown(f"- **O (Objective):** {soap.get('o', '')}")
                    st.markdown(f"- **A (Assessment):** {soap.get('a', '')}")
                    st.markdown(f"- **P (Plan):** {soap.get('p', '')}")

            except Exception as e:
                st.error(f"Lỗi hệ thống: {str(e)}")
