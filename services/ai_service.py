import google.generativeai as genai
import json

def initialize_ai(api_key):
    """Khởi tạo cấu hình API Gemini"""
    genai.configure(api_key=api_key)

def process_medical_record(ghi_chu_nhap, filtered_guideline, admin_rules):
    """Gửi Prompt đa tầng và trả về JSON thuần túy"""
    system_prompt = f"""
    Bạn là Bác sĩ Nội trú Ngoại khoa. Nhiệm vụ của bạn là đọc ghi chú và xuất JSON. KHÔNG XUẤT BẤT KỲ VĂN BẢN NÀO BÊN NGOÀI KHỐI JSON.

    THÁP ƯU TIÊN BIỆN LUẬN:
    1. Admin Rules: {admin_rules}
    2. Ghi chú của sinh viên: "{ghi_chu_nhap}"
    3. Phác đồ RAG: "{filtered_guideline}"

    PHÂN TÁCH 2 VÙNG NHẬN THỨC (QUY TẮC TỐI THƯỢNG):
    
    VÙNG 1: TRÍCH XUẤT TĨNH (Nghiêm ngặt Zero-Hallucination)
    - Áp dụng cho: Lý do nhập viện, Bệnh sử, Tiền căn, Lược qua các cơ quan, Khám lâm sàng, Kết quả cận lâm sàng.
    - Lệnh: Chỉ trích xuất sự thật từ ghi chú. Cấm tự suy diễn triệu chứng. Nếu thiếu, trả về chuỗi rỗng "".

    VÙNG 2: TƯ DUY ĐỘNG (Bác sĩ Nội trú Biện luận)
    - Áp dụng cho: Tóm tắt bệnh án, Đặt vấn đề, Chẩn đoán sơ bộ/phân biệt, Đề nghị cận lâm sàng, Biện luận lâm sàng/Cận lâm sàng, Chẩn đoán xác định, Hướng điều trị.
    - Lệnh: Giải phóng giới hạn trích xuất. BẮT BUỘC sử dụng dữ liệu từ Vùng 1 kết hợp với Phác đồ RAG và Y văn để SUY LUẬN LOGIC. Tự động lập luận, đưa ra chẩn đoán chính xác nhất và đề xuất kế hoạch điều trị hoàn chỉnh.

    CẤU TRÚC JSON BẮT BUỘC TRẢ VỀ:
    {{
        "phan_a_nhan_xet": "Nhận xét thiếu sót...",
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
        model = genai.GenerativeModel("gemini-3-flash-preview")
        response = model.generate_content(
            system_prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        return json.loads(response.text)
    except Exception as e:
        raise Exception(f"Lỗi truy xuất AI: {str(e)}")
