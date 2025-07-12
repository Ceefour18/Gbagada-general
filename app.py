import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import uuid # To generate unique referral IDs

st.set_page_config(layout="wide", page_title="Hospital Referral System 🏥")
# --- Configuration ---
# Make sure 'credentials.json' is in the same directory as your app.py
# For Streamlit Cloud deployment, you'd store this content in st.secrets
GOOGLE_SHEET_NAME = "KosofeReferral" # Your Google Sheet name
WORKSHEET_NAME = "Sheet1" # The specific worksheet name within your sheet

# --- Google Sheets Connection (Cached to avoid reconnecting on every rerun) ---
@st.cache_resource
def get_google_sheet_client():
    try:
        # This approach works for both local (with credentials.json) and Streamlit Cloud (with st.secrets)
        if st.secrets.get("gcp_service_account"): # Check if secrets are configured for cloud deployment
            gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        else: # Fallback to local file for development
            gc = gspread.service_account(filename="credentials.json")
        return gc
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        st.info("Please ensure 'credentials.json' (or st.secrets) is set up correctly and has the right permissions (Editor access to your Google Sheet).")
        st.stop() # Stop the app if connection fails

gc = get_google_sheet_client()

@st.cache_data(ttl=60) # Cache data for 60 seconds
def load_data():
    try:
        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        data = worksheet.get_all_records() # Get all data as a list of dictionaries
        df = pd.DataFrame(data)
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Google Sheet '{GOOGLE_SHEET_NAME}' not found. Please check the name and sharing permissions.")
        st.stop()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Worksheet '{WORKSHEET_NAME}' not found in '{GOOGLE_SHEET_NAME}'. Please check the name.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {e}")
        st.stop()

def append_data(row_data):
    try:
        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        worksheet.append_row(row_data)
        # Invalidate cache so the dashboard updates immediately after new data is added
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error appending data: {e}")
        return False

def update_cell_by_referral_id(referral_id, column_name, new_value):
    try:
        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        # Find the row index for the given Referral ID
        # gspread uses 1-based indexing for rows/columns; header is row 1
        # We search in 'Referral ID' column (which is assumed to be the first column)
        referral_ids = worksheet.col_values(1) # Column 1 is 'Referral ID'
        if referral_id not in referral_ids:
            st.error(f"Referral ID '{referral_id}' not found in the sheet. This might indicate a data sync issue or an invalid ID.")
            return False
        
        row_index = referral_ids.index(referral_id) + 1 # +1 because gspread is 1-indexed (headers are row 1)

        # Find the column index for the given column_name
        headers = worksheet.row_values(1) # Get the header row
        if column_name not in headers:
            st.error(f"Column '{column_name}' not found in sheet headers. Please check your Google Sheet headers.")
            return False
        
        col_index = headers.index(column_name) + 1 # +1 because gspread is 1-indexed

        worksheet.update_cell(row_index, col_index, new_value)
        # Invalidate cache so the dashboard updates immediately after data is updated
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error updating data: {e}")
        return False

# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Hospital Referral System 🏥")

st.title("🏥 PHC - Gbagada General Hospital Referral System")
st.markdown("---")

# --- User Role Selection in Sidebar (for non-authenticated version) ---
# This will be replaced by authentication logic if you re-introduce streamlit-authenticator
user_role = st.sidebar.radio(
    "Select Your Role:",
    ("Primary Health Care (PHC)", "Gbagada General Hospital"),
    help="Choose your role to access the relevant interface."
)

if user_role == "Primary Health Care (PHC)":
    st.header("📤 Refer a New Patient to Gbagada General Hospital")
    st.markdown("Please fill out the form below to refer a patient.")

    with st.form("phc_referral_form", clear_on_submit=True):
        st.subheader("Patient Details")
        col1, col2 = st.columns(2)
        with col1:
            patient_name = st.text_input("Patient Name:", help="Full name of the patient being referred.")
            patient_dob = st.date_input("Date of Birth:", value=None, help="Patient's date of birth.")
            patient_gender = st.selectbox("Gender:", ["Select", "Male", "Female", "Other"], help="Patient's gender.")
            patient_contact = st.text_input("Patient Contact Number:", help="Patient's phone number for contact.")
        with col2:
            referring_phc = st.text_input("Referring PHC Name:", help="The name of your Primary Health Care Center.")
            referring_doctor = st.text_input("Referring Doctor Name:", help="The name of the doctor making the referral.")
            diagnosis = st.text_area("Diagnosis / Reason for Referral:", height=150, help="Briefly describe the patient's diagnosis or the reason for referral to Gbagada General Hospital.")
            
            # Current time for referral (auto-generated and displayed)
            referral_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.info(f"📅 **Referral Time (Auto-generated):** {referral_datetime}")

        st.markdown("---")
        submitted = st.form_submit_button("🚀 Submit Referral")

        if submitted:
            # Basic validation
            if not all([patient_name, patient_dob, patient_gender != "Select", referring_phc, diagnosis, referring_doctor]):
                st.error("❗ Please fill in all **required fields** (Patient Name, Date of Birth, Gender, Referring PHC, Diagnosis, Referring Doctor).")
            else:
                # Generate a unique ID for the referral
                referral_id = str(uuid.uuid4()) 
                
                # Data must be in the same order as your Google Sheet headers
                row_data = [
                    referral_id,
                    patient_name,
                    patient_dob.strftime("%Y-%m-%d"), # Format date to YYYY-MM-DD
                    patient_gender,
                    patient_contact,
                    referring_phc,
                    referral_datetime,
                    diagnosis,
                    referring_doctor,
                    "No", # Gbagada Acknowledged (default to No)
                    "",   # Date/Time of Presentation (initially empty)
                    "",   # Acknowledged By (initially empty)
                    ""    # Gbagada Notes (initially empty)
                ]
                
                # Attempt to append data and provide immediate feedback
                with st.spinner("Submitting referral..."): # Show a spinner while submitting
                    if append_data(row_data):
                        st.success(f"✅ Referral for **{patient_name}** from **{referring_phc}** submitted successfully!")
                        st.info(f"Your Referral ID is: **{referral_id}**. Please note this for future reference.")
                        st.balloons() # Visual confirmation
                        # No need for st.rerun() here as clear_on_submit=True handles form clearing
                    else:
                        st.error("❌ Failed to submit referral. Please try again or contact support if the issue persists.")
                        
elif user_role == "Gbagada General Hospital":
    st.header("📥 Incoming Patient Referrals (Gbagada General Hospital)")
    st.markdown("View pending referrals and acknowledge patient arrivals.")
    
    data_df = load_data()

    if data_df.empty:
        st.info("ℹ️ No referrals found yet.")
    else:
        # Separate acknowledged from unacknowledged
        unacknowledged_df = data_df[data_df["Gbagada Acknowledged"] == "No"].copy()
        acknowledged_df = data_df[data_df["Gbagada Acknowledged"] == "Yes"].copy()

        st.subheader("❗ Pending Referrals")
        if unacknowledged_df.empty:
            st.success("🎉 All referrals have been acknowledged! No pending actions.")
        else:
            st.dataframe(
                unacknowledged_df.sort_values(by="Date/Time of Referral", ascending=False)
                                 .set_index("Referral ID"), 
                use_container_width=True,
                height=300 # Set a fixed height for better scroll experience if many entries
            )

            st.subheader("Acknowledge Patient Arrival")
            st.markdown("Select a pending referral ID below to mark the patient as arrived.")
            
            referral_to_ack = st.selectbox(
                "Select Referral ID to Acknowledge:",
                options=["Select a Referral"] + unacknowledged_df["Referral ID"].tolist(),
                help="Choose the unique ID of the patient who has presented at Gbagada General Hospital."
            )

            if referral_to_ack != "Select a Referral":
                # Display details of the selected referral for confirmation
                selected_referral_details = unacknowledged_df[unacknowledged_df["Referral ID"] == referral_to_ack].iloc[0]
                
                st.write(f"---")
                st.write(f"**Patient Name:** {selected_referral_details['Patient Name']}")
                st.write(f"**Referring PHC:** {selected_referral_details['Referring PHC']}")
                st.write(f"**Diagnosis:** {selected_referral_details['Diagnosis/Reason for Referral']}")
                st.write(f"---")

                with st.form("acknowledge_form"):
                    time_of_presentation = st.text_input(
                        "Time of Presentation (YYYY-MM-DD HH:MM:SS):", 
                        value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        help="Enter the exact date and time the patient presented at Gbagada Hospital. Auto-filled with current time."
                    )
                    acknowledged_by = st.text_input(
                        "Acknowledged By (Your Name/ID):",
                        help="Your name or staff ID for accountability."
                    )
                    gbagada_notes = st.text_area(
                        "Gbagada Hospital Notes (Optional):", 
                        help="Add any relevant notes about the patient's arrival or initial assessment."
                    )

                    ack_submitted = st.form_submit_button("✅ Acknowledge Arrival")

                    if ack_submitted:
                        if not all([time_of_presentation, acknowledged_by]):
                            st.warning("Please fill in **Time of Presentation** and **Acknowledged By** fields.")
                        else:
                            # Update the relevant cells in the Google Sheet
                            with st.spinner("Updating referral status..."):
                                success1 = update_cell_by_referral_id(referral_to_ack, "Gbagada Acknowledged", "Yes")
                                success2 = update_cell_by_referral_id(referral_to_ack, "Date/Time of Presentation", time_of_presentation)
                                success3 = update_cell_by_referral_id(referral_to_ack, "Acknowledged By", acknowledged_by)
                                success4 = update_cell_by_referral_id(referral_to_ack, "Gbagada Notes", gbagada_notes)

                                if success1 and success2 and success3 and success4:
                                    st.success(f"✅ Referral for **{selected_referral_details['Patient Name']}** acknowledged successfully!")
                                    st.rerun() # Refresh the page to update the dashboard immediately
                                else:
                                    st.error("❌ Failed to acknowledge referral. Please check logs.")
            else:
                st.info("Select a pending referral from the dropdown above to acknowledge its arrival.")


        st.markdown("---")
        st.subheader("✅ Acknowledged Referrals")
        if acknowledged_df.empty:
            st.info("No referrals have been acknowledged yet.")
        else:
            st.dataframe(
                acknowledged_df.sort_values(by="Date/Time of Presentation", ascending=False)
                               .set_index("Referral ID"), 
                use_container_width=True,
                height=300 # Set a fixed height
            )