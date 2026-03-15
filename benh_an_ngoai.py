import streamlit as st
import google.generativeai as genai
import os
import re

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Bác Sĩ Nội Trú - Chuẩn Hóa Bệnh Án", layout="wide")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("LỖI BẢO MẬT: Chưa tìm thấy API Key trong mục Settings -> Secrets.")
    st.stop()

# --- 2. CÁC HÀM TIỀN XỬ LÝ (PRE-PROCESSING) ---

def anonymize_name(full_name):
    """Ẩn danh hóa tên bệnh nhân (Ví dụ: Nguyễn Văn A -> N.V.A)"""
    if not full_name:
        return ""
    words = full_name.strip().split()
    return ".".join([word[0].upper() for word in words])

def load_and_filter_guideline(draft_notes):
    """Thuật toán RAG cục bộ: Lọc phác đồ dựa trên từ khóa trong ghi chú nháp"""
    guideline_path = "phac_do_ngoai_khoa.txt"
    if not os.path.exists(guideline_path):
        return "Không tìm thấy file phac_do_ngoai_khoa.txt. Áp dụng y văn chuẩn thế giới."
    
    try:
        with open(guideline_path, "r", encoding="utf-8") as file:
            full_text = file.read()
            
        # Trích xuất từ khóa có ý nghĩa từ ghi chú nháp (độ dài > 3 ký tự)
        keywords = set([w.lower() for w in re.findall(r'\b\w+\b', draft_notes) if len(w) > 3])
        
        # Chia nhỏ phác đồ thành các đoạn và lọc đoạn có chứa từ khóa
        paragraphs = full_text.split('\n\n')
        relevant_chunks = []
        for p in paragraphs:
            if any(kw in p.lower() for kw in keywords):
                relevant_chunks.append(p)
                
        # Nếu tìm thấy, ghép tối đa 10 đoạn liên quan nhất để tiết kiệm Token
        if relevant_chunks:
            return "\n\n".join(relevant_chunks[:10])
        else:
            return "Không tìm thấy nội dung phác đồ khớp với từ khóa. Áp dụng y văn chuẩn thế giới."
            
    except Exception as e:
        return f"Lỗi đọc phác đồ: {str(e)}"

# --- 3. GIAO DIỆN NGƯỜI DÙNG (UI) ---

st.title("Hệ Thống Trợ Lý AI Ngoại Khoa")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Nhập liệu Lâm sàng")
    ho_ten_input = st.text_input("Họ và tên bệnh nhân (Hệ thống sẽ tự động ẩn danh):", placeholder="VD: Đinh Thị Kim Hồng")
    ghi_chu_nhap = st.text_area("Ghi chú nháp (Triệu chứng, tiền căn, khám, CLS...):", height=400, placeholder="Nhập mọi thông tin bạn ghi nhận được tại đây...")
    submit_btn = st.button("Xử lý Bệnh án", type="primary", use_container_width=True)

# --- 4. LUỒNG XỬ LÝ AI ---

if submit_btn:
    if not ghi_chu_nhap.strip():
        st.warning("Vui lòng nhập ghi chú nháp trước khi xử lý.")
    else:
        with st.spinner("Hệ thống đang tiền xử lý dữ liệu và phân tích y văn..."):
            
            # Bước 1 & 2: Ẩn danh và Lọc RAG
            ho_ten_anonymized = anonymize_name(ho_ten_input)
            filtered_guideline = load_and_filter_guideline(ghi_chu_nhap)
            
            # Bước 3: Đóng gói System Prompt
            system_prompt = f"""
            Bạn là một Bác sĩ Nội trú Ngoại khoa xuất sắc. Nhiệm vụ của bạn là chuẩn hóa ghi chú nháp lộn xộn của sinh viên thành một Bệnh án Ngoại khoa chuẩn học thuật, đánh giá thiếu sót và lập báo cáo bàn giao ca trực.

            NGUYÊN TẮC TỐI THƯỢNG (ZERO-HALLUCINATION PROTOCOL):
            - Tuyệt đối không tự suy diễn, bịa đặt thêm triệu chứng, tiền căn hay kết quả khám nếu giấy nháp không đề cập.
            - Mọi mục trong 16 phần bệnh án nếu KHÔNG CÓ dữ kiện, BẮT BUỘC ghi chính xác chuỗi sau: "[Không có thông tin ghi nhận trong giấy nháp]".

            DỮ LIỆU ĐẦU VÀO:
            - Họ tên BN (đã ẩn danh): {ho_ten_anonymized}
            - Ghi chú nháp từ sinh viên: {ghi_chu_nhap}
            - Phác đồ tham khảo (đã lọc theo keyword): {filtered_guideline}

            YÊU CẦU ĐẦU RA (Trình bày rõ 3 phần):

            ### PHẦN A: NHẬN XÉT & CHỈNH SỬA CỦA BS. NỘI TRÚ
            Đối chiếu Ghi chú nháp với Phác đồ tham khảo (hoặc y văn), chỉ ra sinh viên đã quên khám/hỏi những triệu chứng cơ năng, thực thể hoặc cận lâm sàng quan trọng nào để củng cố chẩn đoán.

            ### PHẦN B: BỆNH ÁN CẤU TRÚC 16 PHẦN
            I. Hành chánh (Ghi nhận tên ẩn danh: {ho_ten_anonymized})
            II. Lý do nhập viện
            III. Bệnh sử
            IV. Tiền căn bản thân
            V. Tiền căn gia đình
            VI. Lược qua các cơ quan
            VII. Khám lâm sàng toàn thân
            VIII. Khám lâm sàng cơ quan bệnh lý
            IX. Tóm tắt bệnh án
            X. Đặt vấn đề
            XI. Chẩn đoán sơ bộ & Phân biệt
            XII. Đề nghị cận lâm sàng
            XIII. Kết quả cận lâm sàng (nếu có)
            XIV. Biện luận lâm sàng và cận lâm sàng
            XV. Chẩn đoán xác định
            XVI. Hướng điều trị và Tiên lượng

            ### PHẦN C: TÓM TẮT BÀN GIAO (SOAP)
            Trích xuất thông tin gọn gàng từ Phần B để bàn giao:
            - S (Subjective): Lời khai, cơ năng chính.
            - O (Objective): Sinh hiệu, thực thể dương tính, CLS hiện có.
            - A (Assessment): Chẩn đoán sơ bộ/xác định, đánh giá mức độ.
            - P (Plan): Hướng xử trí, CLS cần làm gấp, theo dõi.
            """

            try:
                # Gọi mô hình theo đúng chỉ định
                model = genai.GenerativeModel("gemini-3-flash-preview")
                response = model.generate_content(system_prompt)
                
                with col2:
                    st.subheader("Kết quả Chuẩn hóa")
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"Lỗi khi kết nối với AI: {str(e)}")
