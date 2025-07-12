This project is a Streamlit-based web application designed to manage patient referrals between Primary Health Care Centers (PHCs) and Gbagada General Hospital.

✅ Core Functionality:
PHC Referral Submission:
Primary Health Care Centers can submit referral details for patients being sent to Gbagada General Hospital, including:
Patient Name, Age, Gender, Phone Number (optional)
Diagnosis
Referring PHC Name
Time of Referral
Hospital Acknowledgment:
Gbagada General Hospital staff can:
View incoming referral notifications.
Acknowledge patient arrival.
Record the time of presentation/arrival.
Centralized Record Keeping:
All referral records are automatically stored in a connected Google Sheet for easy access, updates, and download in CSV format.

⚙️ Technologies Used:
Python
Streamlit
Google Sheets API (via gspread and oauth2client)
Pandas
💡 Why This App?
The app provides a simple, user-friendly interface for seamless two-way communication between health facilities. It ensures accountability, improves patient tracking, and supports data-driven decisions for healthcare administrators.
