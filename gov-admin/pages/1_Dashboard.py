import streamlit as st
from services.blockchain_service import BlockchainService

st.set_page_config(page_title="Dashboard - AGRICHain", page_icon="📊")

st.title("📊 Government Dashboard")

if 'blockchain_service' not in st.session_state:
    st.warning("Please start from the main app.py page.")
    st.stop()

bc_service: BlockchainService = st.session_state['blockchain_service']

if not bc_service.verify_admin_role():
    st.error("Access Denied.")
    st.stop()

try:
    with st.spinner("Fetching blockchain events..."):
        events = bc_service.get_approval_events()
        total_approved = len(events)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    total_approved = "Error"
    events = []

st.metric("Total Approved Certificates", total_approved)

st.subheader("Recent Approvals (from Blockchain Logs)")
if events:
    # Only show last 20
    recent = list(events[-20:])
    recent.reverse()
    for e in recent:
        aadhaar_hash = e.args.get('aadhaarHash', b'').hex()
        doc_hash = e.args.get('documentHash', b'').hex()
        st.write(f"**Aadhaar Hash:** `0x{aadhaar_hash}` | **Doc Hash:** `0x{doc_hash}` | **Block:** {e.blockNumber}")
else:
    st.info("No approval events found.")
