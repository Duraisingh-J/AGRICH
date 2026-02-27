import streamlit as st
from services.blockchain_service import BlockchainService
from services.hash_service import HashService

st.set_page_config(page_title="Revoke Certificate - AGRICHain", page_icon="⛔")

st.title("⛔ Revoke Farmer Certificate")

if 'blockchain_service' not in st.session_state:
    st.warning("Please start from the main app.py page.")
    st.stop()

bc_service: BlockchainService = st.session_state['blockchain_service']

if not bc_service.verify_admin_role():
    st.error("Access Denied.")
    st.stop()

st.warning("Revoking a certificate will permanently invalidate it on the blockchain.")

aadhaar_number = st.text_input("Enter Farmer Aadhaar Number to Revoke", type="password")

if st.button("Revoke Certificate", type="primary"):
    if not aadhaar_number:
        st.error("Please enter the Aadhaar number.")
    elif len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
        st.error("Aadhaar number must be exactly 12 digits long.")
    else:
        with st.spinner("Processing Revocation..."):
            try:
                aadhaar_hash = HashService.get_aadhaar_hash(aadhaar_number)
                
                # Check if it was approved first
                if not bc_service.is_approved(aadhaar_hash):
                    st.error("Cannot revoke: This certificate is not currently approved.")
                    st.stop()
                    
                st.info("Broadcasting Transaction to Blockchain...")
                tx_hash = bc_service.revoke_certificate(aadhaar_hash)
                
                st.success(f"Certificate Revoked Successfully! **Transaction Hash:** `{tx_hash}`")
            except Exception as e:
                st.error(f"Error revoking certificate: {str(e)}")
