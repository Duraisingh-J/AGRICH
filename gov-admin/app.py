import streamlit as st
from utils.config import Config
from services.blockchain_service import BlockchainService

st.set_page_config(
    page_title="AGRICHain Government Portal",
    page_icon="🏛️",
    layout="wide"
)

# Validate config at startup
try:
    Config.validate()
except ValueError as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

st.title("🏛️ AGRICHain Government Admin Portal")

# Initialize blockchain service
try:
    blockchain_service = BlockchainService()
    # Cache in session state
    st.session_state['blockchain_service'] = blockchain_service
except Exception as e:
    st.error(f"Failed to initialize blockchain connection: {str(e)}")
    st.info("Please ensure Besu node is running and DeployedAddresses.json exists.")
    st.stop()

# Role Verification check before allowing access to the tools
if not blockchain_service.verify_admin_role():
    st.error(f"Access Denied: The configured account ({blockchain_service.get_account_address()}) does NOT have the Government role on AGRICHain.")
    st.stop()

st.success(f"Connected to AGRICHain. Authorized as Government Admin.")

st.markdown("""
### Welcome to the AGRICHain Government Portal
Use the sidebar to navigate:
- **Dashboard**: View system statistics and recent blockchain approval events.
- **Approve Certificate**: Register and approve new farmer land certificates.
- **View Certificates**: Check the on-chain status of a certificate.
- **Revoke Certificate**: Revoke a compromised or invalid certificate.

*All private keys and system salts are managed securely by the backend service.*
""")
