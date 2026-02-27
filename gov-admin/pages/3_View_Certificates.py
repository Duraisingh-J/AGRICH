import streamlit as st
from services.blockchain_service import BlockchainService
from services.hash_service import HashService

st.set_page_config(page_title="View Certificates - AGRICHain", page_icon="🔍")

st.title("🔍 View Certificate Status")

if 'blockchain_service' not in st.session_state:
    st.warning("Please start from the main app page.")
    st.stop()

bc_service: BlockchainService = st.session_state['blockchain_service']

if not bc_service.verify_admin_role():
    st.error("Access Denied.")
    st.stop()

aadhaar_number = st.text_input("Enter Farmer Aadhaar Number", type="password")

if st.button("Check Status"):
    if not aadhaar_number:
        st.error("Please enter the Aadhaar number.")
    elif len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
        st.error("Aadhaar number must be exactly 12 digits long.")
    else:
        with st.spinner("Querying Blockchain..."):
            try:
                aadhaar_hash = HashService.get_aadhaar_hash(aadhaar_number)
                
                is_approved = bc_service.is_approved(aadhaar_hash)
                
                if is_approved:
                    doc_hash = bc_service.get_document_hash(aadhaar_hash)
                    bound_wallet = bc_service.get_bound_wallet(aadhaar_hash)
                    ipfs_cid = bc_service.get_ipfs_cid(aadhaar_hash)
                    
                    st.success("✅ Certificate is Approved.")
                    st.write(f"**Aadhaar Hash Checksum:** `{aadhaar_hash}`")
                    st.write(f"**Document Hash:** `{doc_hash}`")
                    
                    if ipfs_cid:
                        st.write(f"**IPFS CID:** `{ipfs_cid}`")
                        # Construct a basic deterministic gateway URL
                        st.markdown(f"**IPFS Link:** [ipfs://{ipfs_cid}](http://localhost:8080/ipfs/{ipfs_cid})")
                    else:
                        st.write("**IPFS CID:** Not Available (Legacy Record)")
                    
                    if bound_wallet and bound_wallet != "0x0000000000000000000000000000000000000000":
                        st.info(f"**Bound Wallet Address:** `{bound_wallet}`")
                    else:
                        st.warning("Certificate is approved but not yet bound to a farmer's wallet.")
                else:
                    st.error("❌ Certificate is NOT Approved or does not exist.")
            except Exception as e:
                st.error(f"Error checking status: {str(e)}")
