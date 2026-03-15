import streamlit as st
import google.generativeai as genai

# 1. Cấu hình trang
st.set_page_config(page_title="Bệnh Án Ngoại Khoa", layout="centered")

st.title("Trợ lý AI Soạn Bệnh Án Ngoại Khoa")
st.write("Điền thông tin theo thứ tự từ trên xuống. Nhấn nút ở cuối trang để hệ thống tự động tổng hợp và cấu trúc bệnh án.")

# Gọi API Key từ Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("Chưa tìm thấy API Key. Vui lòng cài đặt trong mục Settings -> Secrets của Streamlit.")
    api_key = None

# --- KHỐI 1: THÔNG TIN HÀNH CHÁNH ---
st.header("I. Phần Hành Chánh")
col1, col2, col3 = st.columns(3)
with col1:
    ho_ten = st.text_input("Họ và tên")
with col2:
    tuoi = st.number_input("Tuổi", min_value=0, max_value=120, step=1)
with col3:
    gioi_tinh = st.selectbox("Giới tính", ["Nam", "Nữ"])
dia_chi = st.text_input("Địa chỉ")

st.markdown("---")

# --- KHỐI 2: LÝ DO NHẬP VIỆN ---
st.header("II. Lý do nhập viện")
ly_do_nv = st.text_input("Bệnh nhân nhập viện vì...")

st.markdown("---")

# --- KHỐI 3: GHI CHÚ LÂM SÀNG (AI XỬ LÝ) ---
st.header("III. Ghi chú Lâm sàng & Cận lâm sàng")
st.info("💡 Mẹo: Bạn chỉ cần gõ vắn tắt, dùng từ viết tắt. AI sẽ tự động chuẩn hóa văn phong và phân bổ vào các mục Bệnh sử, Tiền căn, Khám, Tóm tắt và Biện luận.")
thong_tin_nhap = st.text_area(
    "Nhập triệu chứng, chỉ số khám, xét nghiệm...", 
    height=200,
    placeholder="VD: Đau HSP 10h sau ăn, âm ỉ, nôn 1 lần ra thức ăn cũ. Khám: M 80, HA 160/90, ấn đau HSP, Murphy (+). Tiền căn: Sỏi túi mật 5 năm. CLS: WBC 22.23 (Neu 87.6%), SA: túi mật 38mm, sỏi 12mm..."
)

st.markdown("---")

# --- KHỐI 4: NÚT TẠO BỆNH ÁN & KẾT QUẢ ---
st.header("IV. Hoàn thiện Bệnh Án")
btn_tao_benh_an = st.button("Tạo Bệnh Án Hoàn Chỉnh", type="primary", use_container_width=True)

if btn_tao_benh_an:
    if not api_key:
        st.warning("Hệ thống bị khóa vì thiếu API Key.")
    elif not thong_tin_nhap or not ho_ten:
        st.warning("Vui lòng điền tối thiểu Họ tên và Ghi chú lâm sàng.")
    else:
        try:
            genai.configure(api_key=api_key)
            generation_config = {
              "temperature": 0.1, 
              "top_p": 0.9,
              "top_k": 40,
              "max_output_tokens": 4096,
            }
            model = genai.GenerativeModel(model_name="gemini-1.5-pro", generation_config=generation_config)

            # Tổng hợp dữ liệu đầu vào cho AI
            du_lieu_tong_hop = f"""
            - Họ tên: {ho_ten} | Tuổi: {tuoi} | Giới tính: {gioi_tinh}
            - Địa chỉ: {dia_chi}
            - Lý do nhập viện: {ly_do_nv}
            - Ghi chú lâm sàng, tiền căn, cận lâm sàng: {thong_tin_nhap}
            """

            system_prompt = """
            Bạn là một Bác sĩ Ngoại khoa dạn dày kinh nghiệm. Dựa trên dữ liệu tổng hợp được cung cấp, hãy biên soạn một "Bệnh án Ngoại khoa" hoàn chỉnh.
            TUYỆT ĐỐI TUÂN THỦ:
            1. Trung thực tuyệt đối: KHÔNG sáng tác thêm triệu chứng, chỉ số cận lâm sàng, hay tiền căn không có trong dữ liệu. Nếu thiếu thông tin để biện luận, hãy ghi chú cần đề nghị thêm cận lâm sàng gì.
            2. Cấu trúc chuẩn 10 phần: I. Hành chánh, II. Lý do nhập viện, III. Bệnh sử, IV. Tiền căn, V. Khám lâm sàng, VI. Tóm tắt bệnh án, VII. Đặt vấn đề, VIII. Biện luận lâm sàng, IX. Chẩn đoán sơ bộ/xác định, X. Hướng điều trị.
            3. Văn phong y khoa: Khách quan, khoa học. Biện luận logic đi từ triệu chứng đến chẩn đoán, tuân thủ các guideline cập nhật.
            """
            
            full_prompt = f"{system_prompt}\n\nDữ liệu tổng hợp:\n{du_lieu_tong_hop}\n\nHãy viết bệnh án:"
            
            with st.spinner('Hệ thống đang cấu trúc bệnh án...'):
                response = model.generate_content(full_prompt)
                
            st.success("Tạo bệnh án thành công! Nhấn Ctrl + P để lưu dưới dạng PDF.")
            st.markdown("### KẾT QUẢ BỆNH ÁN")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"Lỗi hệ thống: {e}")
