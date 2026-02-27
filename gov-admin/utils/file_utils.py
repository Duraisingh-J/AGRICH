def process_uploaded_file(uploaded_file) -> bytes:
    """Reads stream from Streamlit's UploadedFile object and returns bytes"""
    if uploaded_file is not None:
        return uploaded_file.read()
    return b""
