import streamlit as st
import google.generativeai as genai
import os
import re
import json

# --- 1. CẤU HÌNH HỆ THỐNG & BẢO MẬT ---
st.set_page_config(page_title="AI Bác Sĩ Nội Trú - Chuẩn Hóa Bệnh Án", layout="wide")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    ADMIN_PIN_SECRET = st.secrets["ADMIN_PIN"]
    genai.configure(api_key=api_key)
except KeyError as e:
    st.error(f"LỖI BẢO MẬT: Chưa tìm thấy {e} trong file secrets.toml.")
    st.stop()

if 'admin_rules' not in st.session_state:
    st.session_state.admin_rules = "Không có quy tắc đặc biệt nào được thiết lập."

# --- 2. GIAO DIỆN QUẢN TRỊ VIÊN ---
st.sidebar.header("Quyền Quản Trị (Admin)")
st.sidebar.caption("Sử dụng mã PIN nội bộ.")

pin_input = st.sidebar.text_input("Nhập mã PIN:", type="password")

if pin_input == ADMIN_PIN_SECRET:
    st.sidebar.success("Đã xác thực quyền Admin!")
    st.session_state.admin_rules = st.sidebar.text_area(
        "Thiết lập Quy tắc Lâm sàng Tối thượng:", 
        value=st.session_state.admin_rules, 
        height=200
    )
elif pin_input != "":
    st.sidebar.error("Mã PIN không chính xác!")

# --- 3. CÁC HÀM TIỀN XỬ LÝ ---
def anonymize_name(full_name):
    if not full_name: return ""
    return ".".join([word[0].upper() for word in full_name.strip().split()])

def load_and_filter_guideline(draft_notes):
    guideline_path = "phac_do_ngoai_khoa.txt"
    if not os.path.exists(guideline_path):
        return "[HỆ THỐNG] Không tìm thấy phác đồ cục bộ."
    try:
        with open(guideline_path, "r", encoding="utf-8") as file:
            full_text = file.read()
        keywords = set([w.lower() for w in re.findall(r'\b\w+\b', draft_notes) if len(w) > 3])
        paragraphs = full_text.split('\n\n')
        relevant_chunks = [p for p in paragraphs if any(kw in p.lower() for kw in keywords)]
        return "\n\n".join(relevant_chunks[:10]) if relevant_chunks else "[HỆ THỐNG] Không có phác đồ khớp."
    except Exception as e:
        return f"[LỖI RAG]: {str(e)}"

# --- 4. GIAO DIỆN NGƯỜI DÙNG CHÍNH ---
st.title("Hệ Thống Trợ Lý AI Ngoại Khoa")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Nhập liệu Lâm sàng")
    with st.form("clinical_input_form"):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: ho_ten_input = st.text_input("Họ và tên:")
        with c2: tuoi_input = st.number_input("Tuổi:", min_value=0, max_value=120, value=30, step=1)
        with c3: gioi_tinh_input = st.selectbox("Giới tính:", options=["Nam", "Nữ"])
        ghi_chu_nhap = st.text_area("Ghi chú nháp:", height=350)
        submit_btn = st.form_submit_button("Xử lý Bệnh án", type="primary", use_container_width=True)

# --- 5. LUỒNG XỬ LÝ AI ÉP KIỂU JSON ---
if submit_btn:
    if not ghi_chu_nhap.strip():
        st.warning("Vui lòng nhập ghi chú nháp trước khi xử lý.")
    else:
        with st.spinner("Đang trích xuất dữ liệu đa tầng..."):
            ho_ten_anonymized = anonymize_name(ho_ten_input)
            filtered_guideline = load_and_filter_guideline(ghi_chu_nhap)
            admin_rules = st.session_state.admin_rules
            
            system_prompt = f"""
            Bạn là một hệ thống trích xuất dữ liệu y khoa. Nhiệm vụ của bạn là đọc ghi chú nháp và xuất ra ĐÚNG định dạng JSON được yêu cầu, KHÔNG KÈM BẤT KỲ VĂN BẢN NÀO KHÁC.

            THÁP ƯU TIÊN BIỆN LUẬN:
            1. Admin Rules: {admin_rules}
            2. Ghi chú của sinh viên: "{ghi_chu_nhap}"
            3. Phác đồ RAG: "{filtered_guideline}"

            NGUYÊN TẮC ZERO-HALLUCINATION:
            - Chỉ trích xuất thông tin có thật trong "Ghi chú của sinh viên".
            - Nếu một mục không có thông tin trong ghi chú, hãy để giá trị là chuỗi rỗng "". Tuyệt đối không tự bịa triệu chứng.

            CẤU TRÚC JSON BẮT BUỘC PHẢI TRẢ VỀ:
            {{
                "phan_a_nhan_xet": "Dựa vào phác đồ và ghi chú, nhận xét sinh viên thiếu sót gì...",
                "phan_b_benh_an": {{
                    "ly_do_nhap_vien": "...",
                    "benh_su": "...",
                    "tien_can": "...",
                    "luoc_qua_cac_co_quan": "...",
                    "kham_lam_sang": "...",
                    "tom_tat_benh_an": "...",
                    "dat_van_de": "...",
                    "chan_doan_so_bo": "...",
                    "chan_doan_phan_biet": "...",
                    "de_nghi_cls": "...",
                    "ket_qua_cls": "...",
                    "bien_luan_lam_sang": "...",
                    "bien_luan_cls": "...",
                    "chan_doan_xac_dinh": "...",
                    "huong_dieu_tri": "..."
                }},
                "phan_c_soap": {{
                    "s": "...",
                    "o": "...",
                    "a": "...",
                    "p": "..."
                }}
            }}
            """

            try:
                # Ép mô hình trả về chuẩn JSON
                model = genai.GenerativeModel("gemini-3-flash-preview")
                response = model.generate_content(
                    system_prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                    )
                )
                
                # Python phân tích JSON và tự động map dữ liệu
                data = json.loads(response.text)
                b = data.get("phan_b_benh_an", {})
                
                def get_val(key):
                    val = b.get(key, "").strip()
                    return val if val else "[Không có thông tin ghi nhận trong giấy nháp]"

                # Kết xuất giao diện Markdown
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

            except json.JSONDecodeError:
                st.error("Lỗi: AI không trả về đúng định dạng dữ liệu chuẩn. Vui lòng thử lại.")
            except Exception as e:
                st.error(f"Lỗi hệ thống: {str(e)}")
