import streamlit as st
from services.blockchain_service import BlockchainService
from services.hash_service import HashService
from services.ipfs_service import IPFSService
from utils.file_utils import process_uploaded_file

st.set_page_config(page_title="Approve Certificate - AGRICHain", page_icon="✅")

st.title("✅ Approve Farmer Certificate")

if 'blockchain_service' not in st.session_state:
    st.warning("Please start from the main app page.")
    st.stop()

bc_service: BlockchainService = st.session_state['blockchain_service']

if not bc_service.verify_admin_role():
    st.error("Access Denied.")
    st.stop()

st.markdown("Submit a new land certificate to IPFS and approve it on the AGRICHain network.")

aadhaar_number = st.text_input("Farmer Aadhaar Number", type="password", help="The Aadhaar number will be securely hashed with the server-side salt.")
uploaded_file = st.file_uploader("Upload Land Certificate (PDF/Image)", type=["pdf", "jpg", "png", "jpeg"])

if st.button("Approve Certificate"):
    if not aadhaar_number:
        st.error("Please enter the Aadhaar number.")
    elif len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
        st.error("Aadhaar number must be exactly 12 digits long.")
    elif not uploaded_file:
        st.error("Please upload the certificate file.")
    else:
        with st.spinner("Processing..."):
            try:
                # 1. Read file
                file_bytes = process_uploaded_file(uploaded_file)
                
                # 2. Compute Hashes
                st.info("Computing Secure Hashes...")
                aadhaar_hash = HashService.get_aadhaar_hash(aadhaar_number)
                document_hash = HashService.get_document_hash(file_bytes)
                
                st.write(f"**Aadhaar Hash:** `{aadhaar_hash}`")
                st.write(f"**Document Hash:** `{document_hash}`")
                
                # 3. Check if already approved
                if bc_service.is_approved(aadhaar_hash):
                    st.error("This Aadhaar number already has an approved certificate.")
                    st.stop()
                
                # 4. Upload to IPFS
                st.info("Uploading to local IPFS Node...")
                cid = IPFSService.upload_file(file_bytes)
                if not cid:
                    st.error("IPFS Upload Failed: Unable to retrieve CID.")
                    st.stop()
                    
                st.success(f"Uploaded to IPFS successfully! **CID:** `{cid}`")
                
                # 5. Broadcast Transaction
                st.info("Broadcasting Transaction to Blockchain...")
                tx_hash = bc_service.approve_certificate(aadhaar_hash, document_hash, cid)
                
                st.success(f"Certificate Approved on Blockchain! **Transaction Hash:** `{tx_hash}`")
                st.balloons()
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
