import streamlit as st

st.set_page_config(page_title="Bệnh Án Ngoại Khoa", layout="wide")

if 'ba_data' not in st.session_state:
    st.session_state.ba_data = {
        "ho_ten": "", "tuoi": 0, "gioi_tinh": "Nam", "dia_chi": "",
        "ly_do_nv": "", "benh_su": "",
        "wbc": 0.0, "amylase_normal": False,
        "xquang_liem_hoi": False, "sa_gan_bt": False,
        "sa_duong_mat_gian": False, "sa_tui_mat_soi": False
    }

def update_data(key, value):
    st.session_state.ba_data[key] = value

st.sidebar.title("Mục lục Bệnh Án")
menu = st.sidebar.radio("Chọn phần cần nhập:", 
                        ["I. Hành chánh & Lý do NV", 
                         "II. Bệnh sử", 
                         "III. Cận lâm sàng",
                         "IV. Biện luận & Xuất Bệnh án"])

# --- PHẦN I: HÀNH CHÁNH ---
if menu == "I. Hành chánh & Lý do NV":
    st.header("I. Phần Hành Chánh")
    col1, col2, col3 = st.columns(3)
    with col1:
        update_data("ho_ten", st.text_input("Họ và tên", value=st.session_state.ba_data["ho_ten"]))
    with col2:
        update_data("tuoi", st.number_input("Tuổi", min_value=0, max_value=120, value=st.session_state.ba_data["tuoi"]))
    with col3:
        update_data("gioi_tinh", st.selectbox("Giới tính", ["Nam", "Nữ"], index=["Nam", "Nữ"].index(st.session_state.ba_data["gioi_tinh"])))
    update_data("dia_chi", st.text_input("Địa chỉ", value=st.session_state.ba_data["dia_chi"]))
    
    st.markdown("---")
    st.header("II. Lý do nhập viện")
    update_data("ly_do_nv", st.text_area("Bệnh nhân nhập viện vì...", value=st.session_state.ba_data["ly_do_nv"]))

# --- PHẦN II: BỆNH SỬ ---
elif menu == "II. Bệnh sử":
    st.header("III. Bệnh sử")
    update_data("benh_su", st.text_area("Mô tả diễn tiến bệnh lý", value=st.session_state.ba_data["benh_su"], height=200))

# --- PHẦN III: CẬN LÂM SÀNG ---
elif menu == "III. Cận lâm sàng":
    st.header("Kết quả & Ghi nhận Cận Lâm Sàng")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Xét nghiệm máu")
        wbc = st.number_input("WBC (K/uL) [TC: 4.6 - 10]", value=st.session_state.ba_data["wbc"], format="%.2f")
        update_data("wbc", wbc)
        if wbc > 10.0:
            st.error("🚩 WBC tăng cao: Thỏa tiêu chuẩn B (Viêm túi mật cấp).")
            
        update_data("amylase_normal", st.checkbox("Amylase máu trong giới hạn bình thường", value=st.session_state.ba_data["amylase_normal"]))
        
    with col2:
        st.subheader("2. Hình ảnh học (SA, X-Quang, CT)")
        update_data("xquang_liem_hoi", st.checkbox("Ghi nhận liềm hơi/bóng khí tự do", value=st.session_state.ba_data["xquang_liem_hoi"]))
        update_data("sa_gan_bt", st.checkbox("Siêu âm Gan: Chưa ghi nhận bất thường", value=st.session_state.ba_data["sa_gan_bt"]))
        update_data("sa_duong_mat_gian", st.checkbox("Siêu âm: Đường mật dãn, tắc mật", value=st.session_state.ba_data["sa_duong_mat_gian"]))
        update_data("sa_tui_mat_soi", st.checkbox("Siêu âm: Túi mật căng, có sỏi", value=st.session_state.ba_data["sa_tui_mat_soi"]))

# --- PHẦN IV: BIỆN LUẬN & XUẤT ---
elif menu == "IV. Biện luận & Xuất Bệnh án":
    st.header("Khung Biện Luận Cận Lâm Sàng Tự Động")
    
    bien_luan_text = ""
    # Xây dựng các câu biện luận dựa trên input
    if st.session_state.ba_data["wbc"] > 10:
        bien_luan_text += f"- Công thức máu có bạch cầu tăng ({st.session_state.ba_data['wbc']} K/uL) => Thỏa tiêu chuẩn B Viêm túi mật cấp.\n"
    if st.session_state.ba_data["amylase_normal"]:
        bien_luan_text += "- Amylase máu trong khoảng tham chiếu => Không phù hợp, loại trừ chẩn đoán viêm tụy cấp.\n"
    if not st.session_state.ba_data["xquang_liem_hoi"]:
        bien_luan_text += "- Hình ảnh học không ghi nhận liềm hơi/bóng khí => Loại trừ thủng bít dạ dày tá tràng.\n"
    if st.session_state.ba_data["sa_gan_bt"]:
        bien_luan_text += "- Siêu âm gan chưa ghi nhận bất thường => Loại trừ áp xe gan.\n"
    if not st.session_state.ba_data["sa_duong_mat_gian"]:
        bien_luan_text += "- Đường mật trong ngoài gan không dãn => Không có tình trạng tắc mật, không gợi ý viêm đường mật cấp.\n"
    if st.session_state.ba_data["sa_tui_mat_soi"]:
        bien_luan_text += "- Siêu âm túi mật căng, có sỏi => Thỏa tiêu chuẩn C (Hình ảnh học) của Viêm túi mật cấp.\n"

    st.text_area("Văn bản biện luận (Có thể chỉnh sửa thêm trước khi in):", value=bien_luan_text, height=200)

    st.markdown("---")
    st.header("Bệnh Án Hoàn Chỉnh (Nhấn Ctrl + P để lưu PDF)")
    st.markdown(f"""
    ### I. HÀNH CHÁNH
    - **Họ và tên:** {st.session_state.ba_data['ho_ten']} | **Giới tính:** {st.session_state.ba_data['gioi_tinh']} | **Tuổi:** {st.session_state.ba_data['tuoi']}
    
    ### II. LÝ DO NHẬP VIỆN & BỆNH SỬ
    - **Lý do:** {st.session_state.ba_data['ly_do_nv']}
    - **Bệnh sử:** {st.session_state.ba_data['benh_su']}
    
    ### III. BIỆN LUẬN CẬN LÂM SÀNG
    {bien_luan_text}
    """)
