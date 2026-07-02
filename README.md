# NORSU — Patient Record System

A web-based clinic management system for the NORSU Medical Dental Clinic.  
It streamlines patient registration, consultation queues, medical records, inventory, and certificate issuance.

---

## Features

- **Dashboard** – Overview of daily consultations, queue status, and clinic activity
- **Patient Management** – Register and update student/patient profiles (ID, college, age, sex, blood type, allergies, medical history, immunizations)
- **Consultation Queue** – Triage and track patient consultations from submission to completion
- **Medical Profiles** – Record and view allergies, blood type, medical history, and immunizations
- **Reports** – Generate clinic visit reports and summaries
- **Inventory Management** – Track clinic supplies and medicines
- **Staff Management** – Manage clinic staff accounts and roles
- **Account & Settings** – User profile, system preferences
- **Notifications & Feedback** – Alerts and user feedback collection
- **Admin Panel** – Full system administration via Django Admin

---

## Typical Clinic Workflow

### 1. Front Desk
- Patient arrives and states purpose (e.g., "Fit to Play" medical certificate)
- Front desk registers or retrieves patient record
- Creates a new **consultation** in the system
- Collects any required fees
- Patient enters the **queue**



### 3. Doctor Consultation
- Records vital signs and initial screening
- Notes reason for visit (sports clearance, medical exam, etc.)
- Doctor conducts physical examination and reviews medical history
- Determines fitness and documents findings
- Marks consultation as **Completed**

### 4. Certificate Issuance
- After doctor approval, the medical certificate is generated via the system
- Certificate is printed, signed/stamped, and released to the patient
- This step is typically handled by the front desk or the attending doctor

---

---

## Tech Stack

- **Backend:** Django (Python)
- **Frontend:** HTML, CSS, JavaScript (Bootstrap or similar)
- **Database:** SQLite/Mysql (development)
- **Development Server:** `http://127.0.0.1:8000`

---

## Installation (Local Development)

```bash
# Clone the repository
git clone https://github.com/usrss/clinic_patient_recorder.git
cd clinic-patient-recorder

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create a superuser (for admin access)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
