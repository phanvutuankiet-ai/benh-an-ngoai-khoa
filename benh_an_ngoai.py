import streamlit as st
import datetime

# 1. Cấu hình trang web
st.set_page_config(page_title="Bệnh Án Ngoại Khoa", layout="wide")

# 2. Khởi tạo bộ nhớ tạm (Session State) để giữ dữ liệu khi chuyển trang
if 'ba_data' not in st.session_state:
    st.session_state.ba_data = {
        "ho_ten": "", "tuoi": 0, "gioi_tinh": "Nam", "dia_chi": "",
        "ly_do_nv": "", "benh_su": "",
        "wbc": 0.0, "neu": 0.0
    }

# Hàm cập nhật dữ liệu
def update_data(key, value):
    st.session_state.ba_data[key] = value

# 3. Thiết kế Menu Thanh bên (Sidebar)
st.sidebar.title("Mục lục Bệnh Án")
menu = st.sidebar.radio("Chọn phần cần nhập:", 
                        ["I. Hành chánh & Lý do NV", 
                         "II. Bệnh sử & Tiền căn", 
                         "III. Khám lâm sàng", 
                         "IV. Cận lâm sàng", 
                         "V. Tổng hợp & Xuất PDF"])

# --- PHẦN I: HÀNH CHÁNH ---
if menu == "I. Hành chánh & Lý do NV":
    st.header("I. Phần Hành Chánh")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ho_ten = st.text_input("Họ và tên", value=st.session_state.ba_data["ho_ten"])
        update_data("ho_ten", ho_ten)
    with col2:
        tuoi = st.number_input("Tuổi", min_value=0, max_value=120, value=st.session_state.ba_data["tuoi"])
        update_data("tuoi", tuoi)
    with col3:
        gioi_tinh = st.selectbox("Giới tính", ["Nam", "Nữ"], index=["Nam", "Nữ"].index(st.session_state.ba_data["gioi_tinh"]))
        update_data("gioi_tinh", gioi_tinh)
        
    dia_chi = st.text_input("Địa chỉ", value=st.session_state.ba_data["dia_chi"])
    update_data("dia_chi", dia_chi)
    
    st.markdown("---")
    st.header("II. Lý do nhập viện")
    ly_do_nv = st.text_area("Bệnh nhân nhập viện vì...", value=st.session_state.ba_data["ly_do_nv"])
    update_data("ly_do_nv", ly_do_nv)

# --- PHẦN II: BỆNH SỬ ---
elif menu == "II. Bệnh sử & Tiền căn":
    st.header("III. Bệnh sử")
    benh_su = st.text_area("Mô tả diễn tiến bệnh lý (Cách nhập viện...)", value=st.session_state.ba_data["benh_su"], height=200)
    update_data("benh_su", benh_su)

# --- PHẦN III: KHÁM LÂM SÀNG (Mẫu rút gọn) ---
elif menu == "III. Khám lâm sàng":
    st.header("Khám Lâm Sàng")
    st.info("Phần này có thể mở rộng thêm các trường như Tim, Phổi, Bụng (Murphy, phản ứng thành bụng...) tùy theo nhu cầu thực tế.")

# --- PHẦN IV: CẬN LÂM SÀNG (Tích hợp Clinical Flag) ---
elif menu == "IV. Cận lâm sàng":
    st.header("Kết quả Cận Lâm Sàng")
    st.write("Nhập các chỉ số huyết học/sinh hóa. Hệ thống sẽ tự động đối chiếu với khoảng tham chiếu.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Huyết đồ")
        wbc = st.number_input("WBC (K/uL) [TC: 4.6 - 10]", value=st.session_state.ba_data["wbc"], format="%.2f")
        update_data("wbc", wbc)
        # Logic Cờ Lâm Sàng (Clinical Flag)
        if wbc > 10.0:
            st.error(f"🚩 WBC {wbc} tăng cao: Cảnh báo đáp ứng viêm/nhiễm trùng hệ thống.")
        elif wbc > 0 and wbc < 4.6:
            st.warning(f"🚩 WBC {wbc} giảm.")
            
    with col2:
        st.subheader("Sinh hóa máu")
        st.write("(Có thể tiếp tục thêm các chỉ số Amylase, Bilirubin tại đây)")

# --- PHẦN V: TỔNG HỢP VÀ XUẤT PDF ---
elif menu == "V. Tổng hợp & Xuất PDF":
    st.header("Bệnh Án Hoàn Chỉnh")
    st.write("Kiểm tra lại thông tin. Nhấn **Ctrl + P** (hoặc Cmd + P trên Mac) để lưu dưới dạng PDF.")
    
    st.markdown("---")
    st.markdown(f"""
    ### I. HÀNH CHÁNH
    - **Họ và tên:** {st.session_state.ba_data['ho_ten']} | **Giới tính:** {st.session_state.ba_data['gioi_tinh']} | **Tuổi:** {st.session_state.ba_data['tuoi']}
    - **Địa chỉ:** {st.session_state.ba_data['dia_chi']}
    
    ### II. LÝ DO NHẬP VIỆN
    {st.session_state.ba_data['ly_do_nv']}
    
    ### III. BỆNH SỬ
    {st.session_state.ba_data['benh_su']}
    
    ### IV. CẬN LÂM SÀNG NỔI BẬT
    - **WBC:** {st.session_state.ba_data['wbc']} K/uL
    """)