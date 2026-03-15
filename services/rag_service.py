import os
import re

def load_and_filter_guideline(draft_notes):
    """Lọc đoạn phác đồ có chứa từ khóa liên quan đến ghi chú lâm sàng"""
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
