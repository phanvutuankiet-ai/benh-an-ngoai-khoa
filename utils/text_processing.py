def anonymize_name(full_name):
    """Ẩn danh hóa tên bệnh nhân (VD: Đinh Thị Kim Hồng -> Đ.T.K.H)"""
    if not full_name:
        return ""
    words = full_name.strip().split()
    return ".".join([word[0].upper() for word in words])
