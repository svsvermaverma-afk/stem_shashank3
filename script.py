import streamlit as st
import pandas as pd
import os
import re
import sqlite3
from datetime import datetime
import streamlit.components.v1 as components

try:
    import pypdfium2 as pdfium
    PDFIUM_AVAILABLE = True
except ImportError:
    PDFIUM_AVAILABLE = False

st.set_page_config(page_title="ABIC STEM Lab Portal", page_icon="🔬", layout="wide", initial_sidebar_state="collapsed")

# ----------------- BASE DIRECTORIES & CONFIG -----------------
UPLOAD_DIR = "stem_lab_records"
DATA_DIR = "portal_data"

# Safe Directory Initialization to eliminate FileExistsError permanently
try:
    if os.path.exists(UPLOAD_DIR) and not os.path.isdir(UPLOAD_DIR):
        UPLOAD_DIR = "stem_lab_records_dir"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except Exception:
    pass

try:
    if os.path.exists(DATA_DIR) and not os.path.isdir(DATA_DIR):
        DATA_DIR = "portal_data_dir"
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    pass

TIMETABLE_DB_FILE = os.path.join(DATA_DIR, "timetable.db")
STUDENT_ATTENDANCE_FILE = os.path.join(DATA_DIR, "student_attendance.csv")
TEACHER_ATTENDANCE_FILE = os.path.join(DATA_DIR, "teacher_attendance.csv")
SAFETY_CHECKLIST_FILE = os.path.join(DATA_DIR, "safety_checklist.csv")
MAINTENANCE_DAILY_FILE = os.path.join(DATA_DIR, "maintenance_daily.csv")
MAINTENANCE_DEEP_FILE = os.path.join(DATA_DIR, "maintenance_deep.csv")
MAINTENANCE_BREAKDOWN_FILE = os.path.join(DATA_DIR, "maintenance_breakdown.csv")

PRINCIPAL_MSG_FILE = os.path.join(DATA_DIR, "principal_message.txt")
VICE_PRINCIPAL_MSG_FILE = os.path.join(DATA_DIR, "vice_principal_message.txt")
SHEET_CONFIG_FILE = os.path.join(DATA_DIR, "gsheet_url.txt")
FORM_CONFIG_FILE = os.path.join(DATA_DIR, "gform_url.txt")
SCIENCEUTSAV_CONFIG_FILE = os.path.join(DATA_DIR, "scienceutsav_url.txt")

# ----------------- ADMIN CREDENTIALS -----------------
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"

# PERMANENT HARDCODED LINKS
DEFAULT_CONFIGS = {
    SHEET_CONFIG_FILE: "https://docs.google.com/spreadsheets/d/1999l0-GPaDxUh2trREm4HOx6NAfsYHGU_0Qakzy4Bwo/edit?usp=sharing",
    FORM_CONFIG_FILE: "https://docs.google.com/forms/d/e/1FAIpQLSeAE6pzeLi-NVO4aTA82gfXH2oKqtFf3TTlIyI0VCQobP9qxQ/viewform?usp=sharing&ouid=116197222500145214334",
    SCIENCEUTSAV_CONFIG_FILE: "https://report.scienceutsav.com/class/k57a8q5h6mzanqt4vdvn48c1vx8ba0q3/report"
}

MONTHS = ["April", "May", "June", "July", "August", "September", "October", "November", "December", "January", "February", "March"]
WEEKS = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# EXACT SAFETY COMPLIANCE CHECKLIST: ELECTRONICS STEM LAB (#16)
DEFAULT_SAFETY_POINTS = [
    "Fire Extinguisher (CO₂ / Dry Powder): Ready and verified for electrical fire safety.",
    "Main Power Cut-off (Emergency Kill Switch): Functional to cut bench power instantly.",
    "Soldering Stations: Insulated stands, tip cleaners, and auto-shutoff enabled.",
    "Fume Ventilation: Solder smoke extractors/fans running properly.",
    "DC Power Supplies: Low-voltage limits set (3.3V–12V) and short-circuit protection checked.",
    "Multimeters & Probes: Intact insulation with functional internal fuses.",
    "Power Strips & Wiring: Securely mounted without loose or daisy-chained cords.",
    "Li-ion & Battery Storage: Dedicated fire-safe container for batteries and harvested cells.",
    "ESD & Component Storage: Anti-static protection for microcontrollers, ICs, and sensors.",
    "Hand Tools & Cutters: Insulated handles on pliers, strippers, and flush cutters.",
    "Eye Protection (Safety Glasses): Worn during wire snipping and soldering.",
    "First Aid Kit: Equipped with burn care dressings and minor cut treatments.",
    "E-Waste & Scrap Disposal: Separate bins for lead clippings, blown parts, and dead cells.",
    "Workstation Cleanliness: Benches free of loose wire snippets and solder residue."
]

DEFAULT_DAILY_AREAS = [
    "Student Workstations (Bench 1 to 5)",
    "Student Workstations (Bench 6 to 10)",
    "Component Storage & Racks",
    "Soldering & Desoldering Workbench",
    "Teacher Demonstration Bench",
    "3D Printer Prototyping Corner"
]

DEFAULT_DEEP_TASKS = [
    ("Benches & floors dry sweeping (No metal snips / Magnet roller used)", "Weekly"),
    ("Exhaust fans / Fume absorber carbon filters cleaning", "Weekly"),
    ("Multimeter probes, fuses & 9V battery voltage check", "Monthly"),
    ("Soldering iron tips cleaning, tinning & oxidation check", "Monthly"),
    ("Component drawers dusting & sensor/resistor box re-labeling", "Monthly"),
    ("Li-ion & Lithium battery health check (Discard swollen cells)", "Monthly"),
    ("Main MCB / Emergency Kill Switch trip test & Earthing check", "Monthly")
]

SECTIONS_LIST = [
    "Class VI - Section A", "Class VI - Section B", "Class VI - Section C", "Class VI - Section D",
    "Class VII - Section A", "Class VII - Section B", "Class VII - Section C", "Class VII - Section D",
    "Class VIII - Section A", "Class VIII - Section B", "Class VIII - Section C", "Class VIII - Section D",
    "Class IX - Section A", "Class IX - Section B", "Class IX - Section C", "Class IX - Section D",
    "Class IX - Section E", "Class IX - Section F", "Class IX - Section G", "Class IX - Section H"
]

TEACHERS_LIST = [
    "Mrs. Manju Bala Jindal", "Mrs. Dev Jyoti Choudhary", "Mrs. Monika Mishra",
    "Mr. Shiv Narayan Singh", "Mr. Shashank Verma", "Mr. Shashank Shekhar Tiwari",
    "Dr. Rakesh Singh", "Mr. Chandra Mohan Singh", "Mr. Harendra Dwivedi", "Mr. Praveen Kumar"
]

CATEGORIES = {
    "1. Administration & Planning": [
        (1, "STEM Lab Profile"), (2, "Lab Objectives & Guidelines"), (3, "Coordinator / SPOC Details"),
        (4, "Monthly / Annual STEM Activity Plan"), (5, "Class-wise Timetable"),
        (6, "Session / Lesson Plans"), (7, "Student List"), (8, "Student Attendance"), (9, "Teacher Attendance"),
    ],
    "2. Inventory & Safety": [
        (10, "Lab Inventory"), (11, "Equipment Details"), (12, "Equipment Photos"),
        (13, "Equipment Purchase Records"), (14, "Maintenance Records"), (15, "Lab Safety Rules"),
        (16, "Safety Checklist"),
    ],
    "3. Activities & Projects": [
        (17, "STEM Activities"), (18, "Activity Worksheets"), (19, "Activity Photos"),
        (20, "Activity Videos"), (21, "Student Projects"), (22, "Prototype Details"),
        (23, "Problem Statements"), (24, "Innovation Ideas"), (25, "Project Photos"), (26, "Project Videos"),
    ],
    "4. Assessment & Competitions": [
        (27, "Assessment Rubrics"), (28, "Student Assessment"), (29, "Student Performance"),
        (30, "STEM SPARK Registration"), (31, "STEM SPARK Team Details"), (32, "STEM SPARK Submissions"),
        (33, "VVM Records"), (34, "Other Competitions"),
    ],
    "5. Training & Communication": [
        (35, "Teacher Training Records"), (36, "Training Certificates"), (37, "Training Attendance"),
        (38, "Workshop Reports"), (39, "Workshop Photos"), (40, "Government Circulars"),
        (41, "School Circulars"), (42, "Official Emails"), (43, "Meeting Minutes"),
    ],
    "6. Reports & Achievements": [
        (44, "Monthly Reports"), (45, "Quarterly Reports"), (46, "Annual Report"),
        (47, "Student Certificates"), (48, "Student Achievements"), (49, "STEM Lab Event Photos"),
    ]
}

# ----------------- SESSION STATE TRACKERS -----------------
if "is_admin_logged_in" not in st.session_state:
    st.session_state["is_admin_logged_in"] = False
if "show_login_modal" not in st.session_state:
    st.session_state["show_login_modal"] = False
if "active_viewer_sno" not in st.session_state:
    st.session_state["active_viewer_sno"] = None
if "selected_category_filter" not in st.session_state:
    st.session_state["selected_category_filter"] = None

# ----------------- STYLING CSS (SWAYAM INTERFACE) -----------------
st.markdown("""
<style>
.main .block-container {
    padding-top: 15px !important;
    padding-bottom: 40px !important;
    max-width: 1250px !important;
}

div.cat-btn-container button {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    min-height: 95px !important;
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    transition: all 0.2s ease !important;
    padding: 10px 6px !important;
    width: 100% !important;
}

div.cat-btn-container button:hover {
    border-color: #004085 !important;
    background-color: #f0f7ff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
}

div.cat-btn-container button p {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #1f2937 !important;
    margin: 0 !important;
    text-align: center !important;
}

div[data-testid="stButton"] button {
    justify-content: flex-start !important;
    text-align: left !important;
    align-items: center !important;
    display: flex !important;
    width: 100% !important;
    padding: 9px 15px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    border: 1px solid #d0d7de !important;
    background-color: #f8fafc !important;
    color: #1f2328 !important;
    margin-bottom: 2px !important;
}

div[data-testid="stButton"] button:hover {
    background-color: #e2e8f0 !important;
    border-color: #004085 !important;
    color: #004085 !important;
}

.swayam-hero {
    text-align: center;
    margin: 20px auto 16px auto;
    max-width: 950px;
}
.swayam-tagline {
    font-size: 13px;
    letter-spacing: 2px;
    color: #e11d48;
    font-weight: 700;
    text-transform: uppercase;
}
.swayam-hero h1 {
    font-size: 36px;
    font-weight: 800;
    color: #0b2545;
    margin-top: 6px;
    margin-bottom: 6px;
}
.swayam-subheading {
    font-size: 17px;
    color: #0284c7;
    font-weight: 600;
    margin-bottom: 18px;
}
.swayam-metric-card {
    text-align: center;
    padding: 16px 10px;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}
.swayam-metric-title {
    font-size: 14px;
    color: #64748b;
    font-weight: 500;
    margin-bottom: 4px;
}
.swayam-metric-val {
    font-size: 30px;
    font-weight: 800;
    color: #003366;
}

.msg-container {
    background-color: #f0f7ff;
    border: 1px solid #cce3ff;
    border-left: 5px solid #0969da;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
}
.msg-container-vp {
    background-color: #f6f8fa;
    border: 1px solid #d0d7de;
    border-left: 5px solid #1f883d;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 14px;
}
</style>
""", unsafe_allow_html=True)

# ----------------- SQLITE TIME TABLE ENGINE -----------------
def init_timetable_db():
    conn = sqlite3.connect(TIMETABLE_DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_name TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            monday TEXT,
            tuesday TEXT,
            wednesday TEXT,
            thursday TEXT,
            friday TEXT,
            saturday TEXT
        )
    ''')
    conn.commit()

    c.execute("SELECT COUNT(*) FROM timetable")
    if c.fetchone()[0] == 0:
        official_slots = [
            ("Zero Period", "8:05 AM - 8:50 AM", "-", "-", "-", "-", "-", "-"),
            ("Period I", "9:15 AM - 9:55 AM", "-", "-", "VIII - C (SST)", "-", "-", "IX G (HD)"),
            ("Period II", "9:55 AM - 10:30 AM", "-", "-", "-", "-", "-", "VII C (SNS)"),
            ("Period III", "10:30 AM - 11:05 AM", "VI - A (SV)", "VII - A (RKS)", "VII B (MBJ)", "VIII-A (SV) / VIII B (MM)", "-", "-"),
            ("Period IV", "11:05 AM - 11:40 AM", "-", "-", "-", "-", "-", "-"),
            ("INTERVAL / RECESS", "11:40 AM - 12:05 PM", "I N T E R V A L", "I N T E R V A L", "I N T E R V A L", "I N T E R V A L", "I N T E R V A L", "I N T E R V A L"),
            ("Period V", "12:05 PM - 12:45 PM", "-", "-", "-", "-", "VI C", "-"),
            ("Period VI", "12:45 PM - 1:20 PM", "-", "-", "-", "-", "-", "-"),
            ("Period VII", "1:20 PM - 1:55 PM", "VI - D (DJ) / IX - A (RKS)\nIX - E (CM) / IX - H (PK)", "IX - F (CM)", "IX C (SNS)", "VI - B (MM) / VIII D (PK)", "IX D / IX B / VII D", "-"),
            ("Period VIII", "1:55 PM - 2:30 PM", "-", "-", "-", "-", "-", "-"),
        ]
        c.executemany('''
            INSERT INTO timetable (period_name, time_slot, monday, tuesday, wednesday, thursday, friday, saturday)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', official_slots)
        conn.commit()
    conn.close()

init_timetable_db()

def get_timetable_df():
    conn = sqlite3.connect(TIMETABLE_DB_FILE)
    df = pd.read_sql_query("SELECT id, period_name AS [Period], time_slot AS [Timing], monday AS [Monday], tuesday AS [Tuesday], wednesday AS [Wednesday], thursday AS [Thursday], friday AS [Friday], saturday AS [Saturday] FROM timetable ORDER BY id ASC", conn)
    conn.close()
    return df

def save_timetable_from_df(edited_df):
    conn = sqlite3.connect(TIMETABLE_DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM timetable")
    for _, row in edited_df.iterrows():
        c.execute('''
            INSERT INTO timetable (period_name, time_slot, monday, tuesday, wednesday, thursday, friday, saturday)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(row['Period']), str(row['Timing']), str(row['Monday']), str(row['Tuesday']), str(row['Wednesday']), str(row['Thursday']), str(row['Friday']), str(row['Saturday'])))
    conn.commit()
    conn.close()

def render_timetable_view():
    st.markdown("""
    ### ⏰ STEM INNOVATION LAB - MASTER TIME TABLE (SESSION 2026-27)
    **Aditya Birla Intermediate College, Renukoot, Sonebhadra (U.P.)**
    * **Lab In-charge / SPOC:** Shashank Verma | **Effective Date:** 01 July 2026
    * **Assembly / Prayer:** 9:00 AM - 9:15 AM (Warning Bell: 8:50 AM)
    * **Final Bell:** Class 11-12: 2:25 PM | Class 6-10: 2:30 PM
    """)
    df_tt = get_timetable_df().drop(columns=["id"])
    st.dataframe(df_tt, use_container_width=True, hide_index=True)
    
    with st.expander("ℹ️ Faculty Teacher Code Index"):
        st.markdown("""
        * **SV:** Mr. Shashank Verma (Physics / SPOC)
        * **RKS:** Dr. Rakesh Singh
        * **MBJ:** Mrs. Manju Bala Jindal
        * **MM:** Mrs. Monika Mishra
        * **DJ:** Mrs. Dev Jyoti Choudhary
        * **SNS:** Mr. Shiv Narayan Singh
        * **SST:** Mr. Shashank Shekhar Tiwari
        * **CM:** Mr. Chandra Mohan Singh
        * **HD:** Mr. Harendra Dwivedi
        * **PK:** Mr. Praveen Kumar
        """)

# ----------------- URL ACCESS & GOOGLE ENGINE -----------------
def get_current_indices():
    now = datetime.now()
    cur_month_name = now.strftime("%B")
    cur_week_num = min(5, ((now.day - 1) // 7) + 1)
    cur_week_name = f"Week {cur_week_num}"
    month_idx = MONTHS.index(cur_month_name) if cur_month_name in MONTHS else 0
    week_idx = WEEKS.index(cur_week_name) if cur_week_name in WEEKS else 0
    return month_idx, week_idx

def get_folder_name(sno, title):
    return f"{sno:02d}_{title.replace(' ', '_').replace('/', '_')}"

def get_saved_url(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            val = f.read().strip()
            if "gsheet" in file_path and "spreadsheets" in val:
                return val
            elif "gform" in file_path and "forms" in val:
                return val
            elif "scienceutsav" in file_path and val:
                return val

    if "gsheet" in file_path and "GSHEET_URL" in st.secrets:
        return st.secrets["GSHEET_URL"]
    if "gform" in file_path and "GFORM_URL" in st.secrets:
        return st.secrets["GFORM_URL"]
    if "scienceutsav" in file_path and "SCIENCEUTSAV_URL" in st.secrets:
        return st.secrets["SCIENCEUTSAV_URL"]

    return DEFAULT_CONFIGS.get(file_path, "")

def save_url(file_path, url):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(url.strip())

@st.cache_data(ttl=60)
def fetch_google_sheet_data_cached(sheet_url):
    try:
        if "pub?output=csv" in sheet_url or "pubhtml" in sheet_url:
            csv_url = sheet_url.replace("pubhtml", "pub?output=csv")
        else:
            match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
            if not match:
                return None, "Invalid Google Sheet link."
            sheet_id = match.group(1)
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(csv_url, dtype=str).fillna("")
        return df, None
    except Exception as e:
        return None, str(e)

# ----------------- EXECUTIVE MESSAGES HANDLER -----------------
def get_principal_message():
    if os.path.exists(PRINCIPAL_MSG_FILE):
        with open(PRINCIPAL_MSG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return """"Our STEM Innovation & Learning Laboratory is dedicated to nurturing scientific curiosity, critical problem-solving skills, and experiential innovation among our students. We encourage all learners to explore technology, build creative models, and lead the technical advancements of tomorrow."

— **Principal, Aditya Birla Intermediate College, Renukoot**"""

def save_principal_message(msg):
    with open(PRINCIPAL_MSG_FILE, "w", encoding="utf-8") as f:
        f.write(msg)

def get_vice_principal_message():
    if os.path.exists(VICE_PRINCIPAL_MSG_FILE):
        with open(VICE_PRINCIPAL_MSG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return """"Practical hands-on exploration in our STEM lab bridges the gap between textbook concepts and real-world execution. We emphasize regular project mentoring, rigorous inquiry, and national innovation participation for every student."

— **Vice Principal, Aditya Birla Intermediate College, Renukoot**"""

def save_vice_principal_message(msg):
    with open(VICE_PRINCIPAL_MSG_FILE, "w", encoding="utf-8") as f:
        f.write(msg)

def get_profile_photo(role):
    valid_exts = [".jpg", ".jpeg", ".png", ".webp"]
    for ext in valid_exts:
        candidate = os.path.join(DATA_DIR, f"{role}{ext}")
        if os.path.exists(candidate):
            return candidate
    return None

def render_executive_messages():
    principal_img = get_profile_photo("principal_photo")
    vp_img = get_profile_photo("vice_principal_photo")

    with st.container():
        st.markdown('<div class="msg-container">', unsafe_allow_html=True)
        if principal_img:
            cp1, cp2 = st.columns([1.1, 8.9])
            with cp1:
                st.image(principal_img, width=100)
            with cp2:
                st.markdown("**🏛️ Principal's Desk**")
                st.markdown(get_principal_message())
        else:
            st.markdown("**🏛️ Principal's Desk**")
            st.markdown(get_principal_message())
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="msg-container-vp">', unsafe_allow_html=True)
        if vp_img:
            cvp1, cvp2 = st.columns([1.1, 8.9])
            with cvp1:
                st.image(vp_img, width=100)
            with cvp2:
                st.markdown("**📘 Vice Principal's Desk**")
                st.markdown(get_vice_principal_message())
        else:
            st.markdown("**📘 Vice Principal's Desk**")
            st.markdown(get_vice_principal_message())
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- ATTENDANCE, SAFETY & MAINTENANCE INIT -----------------
def init_all_data_structures():
    if not os.path.exists(STUDENT_ATTENDANCE_FILE):
        structure = {
            "Month": [], "Week": [], "Date": [], "Day": [], "Class & Section": [],
            "Total Students": [], "Period 1": [], "Period 2": [], "Total Present": [], "Total Absent": []
        }
        pd.DataFrame(structure).to_csv(STUDENT_ATTENDANCE_FILE, index=False)

    if not os.path.exists(TEACHER_ATTENDANCE_FILE):
        structure = {
            "Month": [], "Week": [], "Date": [], "Day": [], "S.No.": [],
            "Teacher Name": [], "Class & Section Taught": [], "Period / Time Slot": [],
            "Lab Activity / Topic Covered": [], "Total Present Students": [],
            "In-Time": [], "Out-Time": [], "Teacher Signature": []
        }
        pd.DataFrame(structure).to_csv(TEACHER_ATTENDANCE_FILE, index=False)

    if not os.path.exists(SAFETY_CHECKLIST_FILE):
        structure = {
            "Month": [], "Week": [], "Date": [], "S.No.": [],
            "Safety Parameter / Check Item": [], "Status": [], "Remarks": []
        }
        pd.DataFrame(structure).to_csv(SAFETY_CHECKLIST_FILE, index=False)

    if not os.path.exists(MAINTENANCE_DAILY_FILE):
        structure = {
            "Month": [], "Week": [], "Date": [], "Workstation / Area": [],
            "Safai Check (Dusting / Scraps)": [], "Equipment Check (Tools in place)": [],
            "Power Switch OFF": [], "Checked By": [], "Remarks": []
        }
        pd.DataFrame(structure).to_csv(MAINTENANCE_DAILY_FILE, index=False)

    if not os.path.exists(MAINTENANCE_DEEP_FILE):
        structure = {
            "Month": [], "Week": [], "Date": [], "S.No.": [],
            "Parameter / Deep Task": [], "Frequency": [], "Status": [],
            "Action Taken / Remarks": [], "Verified By": []
        }
        pd.DataFrame(structure).to_csv(MAINTENANCE_DEEP_FILE, index=False)

    if not os.path.exists(MAINTENANCE_BREAKDOWN_FILE):
        structure = {
            "Month": [], "Week": [], "Date Reported": [], "S.No.": [],
            "Equipment / Tool Name": [], "Problem / Issue": [], "Action Required": [],
            "Status": [], "Date Resolved": [], "Remarks": []
        }
        pd.DataFrame(structure).to_csv(MAINTENANCE_BREAKDOWN_FILE, index=False)

init_all_data_structures()

# ----------------- ATTENDANCE & SAFETY LOGIC -----------------
def get_student_attendance_all():
    try:
        return pd.read_csv(STUDENT_ATTENDANCE_FILE, dtype=str).fillna("")
    except Exception:
        init_all_data_structures()
        return pd.read_csv(STUDENT_ATTENDANCE_FILE, dtype=str).fillna("")

def save_student_attendance_slot(month, week, edited_df):
    df_all = get_student_attendance_all()
    edited_df = edited_df.copy()
    edited_df["Month"] = str(month)
    edited_df["Week"] = str(week)
    df_remaining = df_all[~((df_all["Month"] == str(month)) & (df_all["Week"] == str(week)))] if not df_all.empty else pd.DataFrame()
    pd.concat([df_remaining, edited_df], ignore_index=True).to_csv(STUDENT_ATTENDANCE_FILE, index=False)

def get_teacher_attendance_all():
    try:
        return pd.read_csv(TEACHER_ATTENDANCE_FILE, dtype=str).fillna("")
    except Exception:
        init_all_data_structures()
        return pd.read_csv(TEACHER_ATTENDANCE_FILE, dtype=str).fillna("")

def save_teacher_attendance_slot(month, week, edited_df):
    df_all = get_teacher_attendance_all()
    edited_df = edited_df.copy()
    edited_df["Month"] = str(month)
    edited_df["Week"] = str(week)
    df_remaining = df_all[~((df_all["Month"] == str(month)) & (df_all["Week"] == str(week)))] if not df_all.empty else pd.DataFrame()
    pd.concat([df_remaining, edited_df], ignore_index=True).to_csv(TEACHER_ATTENDANCE_FILE, index=False)

def get_safety_checklist_all():
    try:
        return pd.read_csv(SAFETY_CHECKLIST_FILE, dtype=str).fillna("")
    except Exception:
        init_all_data_structures()
        return pd.read_csv(SAFETY_CHECKLIST_FILE, dtype=str).fillna("")

def get_safety_checklist_for_slot(month, week, default_date_str=None):
    df_all = get_safety_checklist_all()
    if not default_date_str:
        default_date_str = datetime.now().strftime("%Y-%m-%d")

    if not df_all.empty and {"Month", "Week", "Safety Parameter / Check Item"}.issubset(set(df_all.columns)):
        filtered = df_all[(df_all["Month"] == str(month)) & (df_all["Week"] == str(week))]
        if not filtered.empty:
            df_slot = filtered.drop(columns=[c for c in ["Month", "Week"] if c in filtered.columns]).copy()
            df_slot["Status"] = df_slot["Status"].apply(
                lambda x: True if str(x).lower() in ["true", "1", "yes", "passed"] else False)
            if "Date" not in df_slot.columns or df_slot["Date"].dropna().empty or (df_slot["Date"] == "").all():
                df_slot["Date"] = default_date_str
            return df_slot

    return pd.DataFrame({
        "Date": [default_date_str for _ in DEFAULT_SAFETY_POINTS],
        "S.No.": list(range(1, len(DEFAULT_SAFETY_POINTS) + 1)),
        "Safety Parameter / Check Item": DEFAULT_SAFETY_POINTS,
        "Status": [False for _ in DEFAULT_SAFETY_POINTS],
        "Remarks": ["Verified Compliant" for _ in DEFAULT_SAFETY_POINTS]
    })

def save_safety_checklist_slot(month, week, edited_df, chosen_date=None):
    df_all = get_safety_checklist_all()
    edited_df = edited_df.copy()
    edited_df["Month"] = str(month)
    edited_df["Week"] = str(week)
    if chosen_date:
        edited_df["Date"] = str(chosen_date)
    edited_df["Status"] = edited_df["Status"].apply(lambda x: "Passed" if x is True else "Failed")
    df_remaining = df_all[~((df_all["Month"] == str(month)) & (df_all["Week"] == str(week)))] if not df_all.empty else pd.DataFrame()
    pd.concat([df_remaining, edited_df], ignore_index=True).to_csv(SAFETY_CHECKLIST_FILE, index=False)

# ----------------- MAINTENANCE ACCESSORS (#14) -----------------
def get_daily_maint_for_slot(month, week, default_date_str=None):
    try:
        df_all = pd.read_csv(MAINTENANCE_DAILY_FILE, dtype=str).fillna("")
    except Exception:
        init_all_data_structures()
        df_all = pd.read_csv(MAINTENANCE_DAILY_FILE, dtype=str).fillna("")

    if not default_date_str:
        default_date_str = datetime.now().strftime("%Y-%m-%d")

    if not df_all.empty and {"Month", "Week", "Workstation / Area"}.issubset(set(df_all.columns)):
        filtered = df_all[(df_all["Month"] == str(month)) & (df_all["Week"] == str(week))]
        if not filtered.empty:
            df_slot = filtered.drop(columns=[c for c in ["Month", "Week"] if c in filtered.columns]).copy()
            for col in ["Safai Check (Dusting / Scraps)", "Equipment Check (Tools in place)", "Power Switch OFF"]:
                if col in df_slot.columns:
                    df_slot[col] = df_slot[col].apply(
                        lambda x: True if str(x).lower() in ["true", "1", "yes", "done"] else False)
            return df_slot

    return pd.DataFrame({
        "Date": [default_date_str for _ in DEFAULT_DAILY_AREAS],
        "Workstation / Area": DEFAULT_DAILY_AREAS,
        "Safai Check (Dusting / Scraps)": [False for _ in DEFAULT_DAILY_AREAS],
        "Equipment Check (Tools in place)": [False for _ in DEFAULT_DAILY_AREAS],
        "Power Switch OFF": [False for _ in DEFAULT_DAILY_AREAS],
        "Checked By": ["Lab Attendant / Teacher" for _ in DEFAULT_DAILY_AREAS],
        "Remarks": ["Wire scraps & benches cleared" for _ in DEFAULT_DAILY_AREAS]
    })

def save_daily_maint_slot(month, week, edited_df, chosen_date=None):
    try:
        df_all = pd.read_csv(MAINTENANCE_DAILY_FILE, dtype=str).fillna("")
    except Exception:
        df_all = pd.DataFrame()
    edited_df = edited_df.copy()
    edited_df["Month"] = str(month)
    edited_df["Week"] = str(week)
    if chosen_date:
        edited_df["Date"] = str(chosen_date)
    for col in ["Safai Check (Dusting / Scraps)", "Equipment Check (Tools in place)", "Power Switch OFF"]:
        if col in edited_df.columns:
            edited_df[col] = edited_df[col].apply(lambda x: "Done" if x is True else "Pending")

    df_rem = df_all[~((df_all["Month"] == str(month)) & (df_all["Week"] == str(week)))] if not df_all.empty else pd.DataFrame()
    pd.concat([df_rem, edited_df], ignore_index=True).to_csv(MAINTENANCE_DAILY_FILE, index=False)

def get_deep_maint_for_slot(month, week, default_date_str=None):
    try:
        df_all = pd.read_csv(MAINTENANCE_DEEP_FILE, dtype=str).fillna("")
    except Exception:
        init_all_data_structures()
        df_all = pd.read_csv(MAINTENANCE_DEEP_FILE, dtype=str).fillna("")

    if not default_date_str:
        default_date_str = datetime.now().strftime("%Y-%m-%d")

    if not df_all.empty and {"Month", "Week", "Parameter / Deep Task"}.issubset(set(df_all.columns)):
        filtered = df_all[(df_all["Month"] == str(month)) & (df_all["Week"] == str(week))]
        if not filtered.empty:
            df_slot = filtered.drop(columns=[c for c in ["Month", "Week"] if c in filtered.columns]).copy()
            df_slot["Status"] = df_slot["Status"].apply(
                lambda x: True if str(x).lower() in ["true", "1", "yes", "ok"] else False)
            return df_slot

    return pd.DataFrame({
        "Date": [default_date_str for _ in DEFAULT_DEEP_TASKS],
        "S.No.": list(range(1, len(DEFAULT_DEEP_TASKS) + 1)),
        "Parameter / Deep Task": [t[0] for t in DEFAULT_DEEP_TASKS],
        "Frequency": [t[1] for t in DEFAULT_DEEP_TASKS],
        "Status": [False for _ in DEFAULT_DEEP_TASKS],
        "Action Taken / Remarks": ["Inspection Completed / Cleaned" for _ in DEFAULT_DEEP_TASKS],
        "Verified By": ["SPOC / Coordinator" for _ in DEFAULT_DEEP_TASKS]
    })

def save_deep_maint_slot(month, week, edited_df, chosen_date=None):
    try:
        df_all = pd.read_csv(MAINTENANCE_DEEP_FILE, dtype=str).fillna("")
    except Exception:
        df_all = pd.DataFrame()
    edited_df = edited_df.copy()
    edited_df["Month"] = str(month)
    edited_df["Week"] = str(week)
    if chosen_date:
        edited_df["Date"] = str(chosen_date)
    edited_df["Status"] = edited_df["Status"].apply(lambda x: "OK" if x is True else "Pending")
    df_rem = df_all[~((df_all["Month"] == str(month)) & (df_all["Week"] == str(week)))] if not df_all.empty else pd.DataFrame()
    pd.concat([df_rem, edited_df], ignore_index=True).to_csv(MAINTENANCE_DEEP_FILE, index=False)

def get_breakdown_maint_for_slot(month, week):
    try:
        df_all = pd.read_csv(MAINTENANCE_BREAKDOWN_FILE, dtype=str).fillna("")
    except Exception:
        init_all_data_structures()
        df_all = pd.read_csv(MAINTENANCE_BREAKDOWN_FILE, dtype=str).fillna("")

    if not df_all.empty and {"Month", "Week", "Equipment / Tool Name"}.issubset(set(df_all.columns)):
        filtered = df_all[(df_all["Month"] == str(month)) & (df_all["Week"] == str(week))]
        if not filtered.empty:
            return filtered.drop(columns=[c for c in ["Month", "Week"] if c in filtered.columns]).copy()

    return pd.DataFrame({
        "Date Reported": [datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")],
        "S.No.": ["1", "2"],
        "Equipment / Tool Name": ["Soldering Station 3", "DC Bench Power Supply"],
        "Problem / Issue": ["Tip not heating / loose connector", "Voltage display fluctuation"],
        "Action Required": ["Heating element replaced & tested", "Recalibrated / Sent for repair"],
        "Status": ["Repaired", "Pending"],
        "Date Resolved": [datetime.now().strftime("%Y-%m-%d"), ""],
        "Remarks": ["Ready for students", "Tagged Red: Under Maintenance"]
    })

def save_breakdown_maint_slot(month, week, edited_df):
    try:
        df_all = pd.read_csv(MAINTENANCE_BREAKDOWN_FILE, dtype=str).fillna("")
    except Exception:
        df_all = pd.DataFrame()
    edited_df = edited_df.copy()
    edited_df["Month"] = str(month)
    edited_df["Week"] = str(week)
    df_rem = df_all[~((df_all["Month"] == str(month)) & (df_all["Week"] == str(week)))] if not df_all.empty else pd.DataFrame()
    pd.concat([df_rem, edited_df], ignore_index=True).to_csv(MAINTENANCE_BREAKDOWN_FILE, index=False)

# ----------------- REAL-TIME GOOGLE SHEET SYNC ENGINE -----------------
def sync_data_from_google_sheet():
    sheet_url = get_saved_url(SHEET_CONFIG_FILE)
    if not sheet_url:
        return False, "Google Sheet URL not configured."
    df_raw, err = fetch_google_sheet_data_cached(sheet_url)
    if err or df_raw is None or df_raw.empty:
        return False, err if err else "Google Sheet is empty or not accessible."

    def find_col(keywords):
        for col in df_raw.columns:
            if any(k.lower() in str(col).lower() for k in keywords):
                return col
        return None

    col_date = find_col(["date", "timestamp"])
    col_day = find_col(["day"])
    col_teacher = find_col(["teacher", "name"])
    col_class = find_col(["class", "section"])
    col_period = find_col(["period", "slot", "time slot"])
    col_topic = find_col(["activity", "topic", "covered"])
    col_tot_st = find_col(["total student", "registered", "strength"])
    col_present = find_col(["present"])
    col_absent = find_col(["absent"])
    col_in = find_col(["in-time", "in time", "intime"])
    col_out = find_col(["out-time", "out time", "outtime"])

    df_st_all = get_student_attendance_all()
    df_tc_all = get_teacher_attendance_all()

    now = datetime.now()

    for _, row in df_raw.iterrows():
        raw_date = str(row[col_date]) if col_date else ""
        raw_day = str(row[col_day]) if col_day else ""
        raw_teacher = str(row[col_teacher]) if col_teacher else ""
        raw_class = str(row[col_class]) if col_class else ""
        raw_period = str(row[col_period]) if col_period else ""
        raw_topic = str(row[col_topic]) if col_topic else ""
        raw_tot = str(row[col_tot_st]) if col_tot_st else ""
        raw_pres = str(row[col_present]) if col_present else ""
        raw_abs = str(row[col_absent]) if col_absent else ""
        raw_in = str(row[col_in]) if col_in else ""
        raw_out = str(row[col_out]) if col_out else ""

        try:
            dt = pd.to_datetime(raw_date, errors="coerce")
            month_name = dt.strftime("%B") if pd.notnull(dt) else now.strftime("%B")
            week_num = min(5, ((dt.day - 1) // 7) + 1) if pd.notnull(dt) else min(5, ((now.day - 1) // 7) + 1)
            week_name = f"Week {week_num}"
            if not raw_day and pd.notnull(dt):
                raw_day = dt.strftime("%A")
        except Exception:
            month_name = now.strftime("%B")
            week_name = "Week 1"

        if raw_class:
            st_match_idx = df_st_all[(df_st_all["Month"] == month_name) & (df_st_all["Week"] == week_name) & (
                    df_st_all["Class & Section"] == raw_class)].index
            new_st_row = {
                "Month": month_name, "Week": week_name, "Date": raw_date.split(" ")[0], "Day": raw_day,
                "Class & Section": raw_class, "Total Students": raw_tot, "Period 1": raw_period, "Period 2": "",
                "Total Present": raw_pres, "Total Absent": raw_abs
            }
            if len(st_match_idx) > 0:
                for k, v in new_st_row.items():
                    df_st_all.loc[st_match_idx[0], k] = v
            else:
                df_st_all = pd.concat([df_st_all, pd.DataFrame([new_st_row])], ignore_index=True)

        if raw_teacher:
            tc_match_idx = df_tc_all[(df_tc_all["Month"] == month_name) & (df_tc_all["Week"] == week_name) & (
                    df_tc_all["Teacher Name"] == raw_teacher)].index
            new_tc_row = {
                "Month": month_name, "Week": week_name, "Date": raw_date.split(" ")[0], "Day": raw_day,
                "S.No.": str(len(df_tc_all) + 1), "Teacher Name": raw_teacher, "Class & Section Taught": raw_class,
                "Period / Time Slot": raw_period, "Lab Activity / Topic Covered": raw_topic,
                "Total Present Students": raw_pres, "In-Time": raw_in, "Out-Time": raw_out,
                "Teacher Signature": "Verified"
            }
            if len(tc_match_idx) > 0:
                for k, v in new_tc_row.items():
                    df_tc_all.loc[tc_match_idx[0], k] = v
            else:
                df_tc_all = pd.concat([df_tc_all, pd.DataFrame([new_tc_row])], ignore_index=True)

    df_st_all.to_csv(STUDENT_ATTENDANCE_FILE, index=False)
    df_tc_all.to_csv(TEACHER_ATTENDANCE_FILE, index=False)
    return True, f"Synced {len(df_raw)} records automatically."

def get_student_attendance_for_slot(month, week):
    sync_data_from_google_sheet()
    df_all = get_student_attendance_all()
    if not df_all.empty and {"Month", "Week", "Date", "Day"}.issubset(set(df_all.columns)):
        filtered = df_all[(df_all["Month"] == str(month)) & (df_all["Week"] == str(week))]
        if not filtered.empty:
            return filtered.drop(columns=[c for c in ["Month", "Week"] if c in filtered.columns])
    return pd.DataFrame({
        "Date": ["" for _ in SECTIONS_LIST], "Day": ["" for _ in SECTIONS_LIST],
        "Class & Section": SECTIONS_LIST, "Total Students": ["" for _ in SECTIONS_LIST],
        "Period 1": ["" for _ in SECTIONS_LIST], "Period 2": ["" for _ in SECTIONS_LIST],
        "Total Present": ["" for _ in SECTIONS_LIST], "Total Absent": ["" for _ in SECTIONS_LIST]
    })

def get_teacher_attendance_for_slot(month, week):
    sync_data_from_google_sheet()
    df_all = get_teacher_attendance_all()
    if not df_all.empty and {"Month", "Week", "Date", "Day"}.issubset(set(df_all.columns)):
        filtered = df_all[(df_all["Month"] == str(month)) & (df_all["Week"] == str(week))]
        if not filtered.empty:
            return filtered.drop(columns=[c for c in ["Month", "Week"] if c in filtered.columns])
    return pd.DataFrame({
        "Date": ["" for _ in TEACHERS_LIST], "Day": ["" for _ in TEACHERS_LIST],
        "S.No.": list(range(1, len(TEACHERS_LIST) + 1)), "Teacher Name": TEACHERS_LIST,
        "Class & Section Taught": ["" for _ in TEACHERS_LIST], "Period / Time Slot": ["" for _ in TEACHERS_LIST],
        "Lab Activity / Topic Covered": ["" for _ in TEACHERS_LIST],
        "Total Present Students": ["" for _ in TEACHERS_LIST],
        "In-Time": ["" for _ in TEACHERS_LIST], "Out-Time": ["" for _ in TEACHERS_LIST],
        "Teacher Signature": ["" for _ in TEACHERS_LIST]
    })

# ----------------- UNIVERSAL FILE RENDERER & PREVIEW -----------------
def render_file_preview(file_path, file_name, unique_key):
    ext = os.path.splitext(file_name)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        st.image(file_path, caption=file_name, use_container_width=True)
    elif ext in [".xlsx", ".xls", ".csv"]:
        try:
            df = pd.read_csv(file_path) if ext == ".csv" else pd.read_excel(file_path)
            st.markdown(f"📊 **Data Table: {file_name}** ({len(df)} rows)")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading spreadsheet: {e}")
    elif ext == ".pdf":
        st.markdown(f"📄 **PDF Document:** {file_name}")
        if PDFIUM_AVAILABLE:
            try:
                pdf = pdfium.PdfDocument(file_path)
                for page_num in range(len(pdf)):
                    st.image(pdf[page_num].render(scale=2).to_pil(), caption=f"Page {page_num + 1} of {len(pdf)}",
                             use_container_width=True)
            except Exception:
                pass
        with open(file_path, "rb") as f:
            st.download_button(f"📥 Download PDF ({file_name})", data=f.read(), file_name=file_name,
                               mime="application/pdf", key=f"dl_pdf_{unique_key}")
    elif ext in [".mp4", ".mov", ".avi", ".mkv"]:
        st.video(file_path)
    else:
        with open(file_path, "rb") as f:
            st.download_button(f"📥 Download File ({file_name})", data=f.read(), file_name=file_name,
                               key=f"dl_doc_{unique_key}")

def get_existing_files_for_parameter(sno, title):
    folder_candidates = [
        f"{sno:02d}_{title.replace(' ', '_').replace('/', '_')}",
        f"{(sno + 1):02d}_{title.replace(' ', '_').replace('/', '_')}",
        f"{(sno - 1):02d}_{title.replace(' ', '_').replace('/', '_')}",
        title.replace(' ', '_').replace('/', '_')
    ]
    all_files = []
    seen = set()

    for cand in folder_candidates:
        cand_dir = os.path.join(UPLOAD_DIR, cand)
        if os.path.isdir(cand_dir):
            for f in sorted(os.listdir(cand_dir)):
                full_path = os.path.join(cand_dir, f)
                if os.path.isfile(full_path) and f not in seen:
                    seen.add(f)
                    all_files.append((full_path, f))

    try:
        root_files = [f for f in os.listdir(".") if os.path.isfile(f)]
        for rf in root_files:
            rf_lower = rf.lower()
            if sno in [10, 11] and any(k in rf_lower for k in ["inventory", "materials", "equipment"]) and rf not in seen:
                if rf.endswith((".pdf", ".xlsx", ".xls", ".csv")):
                    seen.add(rf)
                    all_files.append((rf, rf))
            elif sno == 5 and "time" in rf_lower and "table" in rf_lower and rf not in seen:
                if rf.endswith((".pdf", ".xlsx", ".xls", ".csv")):
                    seen.add(rf)
                    all_files.append((rf, rf))
    except Exception:
        pass

    return all_files

def render_parameter_file_manager(sno, title):
    folder_name = get_folder_name(sno, title)
    record_dir = os.path.join(UPLOAD_DIR, folder_name)
    if os.path.exists(record_dir) and not os.path.isdir(record_dir):
        record_dir = record_dir + "_uploads"
    os.makedirs(record_dir, exist_ok=True)

    st.markdown("---")
    st.markdown(f"##### 📂 Upload & Manage Files for #{sno} ({title})")
    
    uploaded_files = st.file_uploader(
        f"Upload documents/photos/videos for #{sno}:",
        accept_multiple_files=True,
        key=f"mgr_uploader_{sno}"
    )

    if uploaded_files:
        for f in uploaded_files:
            with open(os.path.join(record_dir, f.name), "wb") as buffer:
                buffer.write(f.getbuffer())
        st.success(f"✅ Successfully saved {len(uploaded_files)} file(s).")
        st.rerun()

    existing_files = get_existing_files_for_parameter(sno, title)
    if existing_files:
        st.markdown(f"**📑 Uploaded Files ({len(existing_files)}):**")
        for idx, (fpath, fname) in enumerate(existing_files):
            c_a, c_b = st.columns([5, 1])
            c_a.markdown(f"📄 **{fname}**")
            if c_b.button("🗑️ Delete", key=f"del_btn_{sno}_{idx}_{fname}"):
                if os.path.exists(fpath):
                    os.remove(fpath)
                st.warning(f"Deleted {fname}")
                st.rerun()
    else:
        st.caption("No files uploaded for this section yet.")

# ----------------- REPOSITORY VIEWERS -----------------
def render_student_attendance_viewer():
    st.markdown("### 📊 Section-wise Student STEM Attendance Record")
    gform_link = get_saved_url(FORM_CONFIG_FILE)
    if gform_link:
        st.link_button("📝 Open Teacher Daily STEM Entry Form", gform_link)
        st.write("")
    cur_m_idx, cur_w_idx = get_current_indices()
    c1, c2 = st.columns(2)
    sel_month = c1.selectbox("Select Month (Student):", MONTHS, index=cur_m_idx, key="view_st_month")
    sel_week = c2.selectbox("Select Week (Student):", WEEKS, index=cur_w_idx, key="view_st_week")
    df_slot = get_student_attendance_for_slot(sel_month, sel_week)
    st.caption(f"Showing Student Attendance for: **{sel_month} | {sel_week}** (Auto-Synced with Google Sheet)")
    st.dataframe(df_slot, use_container_width=True, hide_index=True)

def render_teacher_attendance_viewer():
    st.markdown("### 🧑‍🏫 STEM Teacher Lab Duty & Activity Attendance")
    gform_link = get_saved_url(FORM_CONFIG_FILE)
    if gform_link:
        st.link_button("📝 Open Teacher Daily STEM Entry Form", gform_link)
        st.write("")
    cur_m_idx, cur_w_idx = get_current_indices()
    c1, c2 = st.columns(2)
    sel_month = c1.selectbox("Select Month (Teacher):", MONTHS, index=cur_m_idx, key="view_tc_month")
    sel_week = c2.selectbox("Select Week (Teacher):", WEEKS, index=cur_w_idx, key="view_tc_week")
    df_slot = get_teacher_attendance_for_slot(sel_month, sel_week)
    st.caption(f"Showing Teacher Attendance for: **{sel_month} | {sel_week}** (Auto-Synced with Google Sheet)")
    st.dataframe(df_slot, use_container_width=True, hide_index=True)

def render_maintenance_viewer():
    st.markdown("### 🛠️ Electronics STEM Lab Maintenance & Cleaning System")
    cur_m_idx, cur_w_idx = get_current_indices()
    c1, c2, c3 = st.columns([1.2, 1.2, 1.2])
    sel_month = c1.selectbox("Select Month (Maintenance):", MONTHS, index=cur_m_idx, key="view_maint_month")
    sel_week = c2.selectbox("Select Week (Maintenance):", WEEKS, index=cur_w_idx, key="view_maint_week")
    sel_date = c3.date_input("Audit / Log Date:", value=datetime.now(), key="view_maint_date")

    tab_m1, tab_m2, tab_m3 = st.tabs(["🧹 1. Daily Cleaning & Workstation Log", "🔍 2. Deep Maintenance & Hygiene",
                                      "⚠ 3. Equipment Breakdown Register"])

    with tab_m1:
        st.markdown(f"##### 📅 Daily Log for: `{sel_month} | {sel_week} | {sel_date}`")
        df_daily = get_daily_maint_for_slot(sel_month, sel_week, default_date_str=str(sel_date))
        disp_daily = df_daily.copy()
        for col in ["Safai Check (Dusting / Scraps)", "Equipment Check (Tools in place)", "Power Switch OFF"]:
            if col in disp_daily.columns:
                disp_daily[col] = disp_daily[col].apply(lambda x: "✅ Done" if x is True else "⏳ Pending")
        st.dataframe(disp_daily, use_container_width=True, hide_index=True)

    with tab_m2:
        st.markdown(f"##### 🛡️ Deep Hardware & Hygiene Audit: `{sel_month} | {sel_week}`")
        df_deep = get_deep_maint_for_slot(sel_month, sel_week, default_date_str=str(sel_date))
        disp_deep = df_deep.copy()
        disp_deep["Status"] = disp_deep["Status"].apply(
            lambda x: "✅ OK / Cleaned" if x is True else "⚠️ Action Required")
        st.dataframe(disp_deep, use_container_width=True, hide_index=True)

    with tab_m3:
        st.markdown(f"##### 🏷️ Equipment Breakdown & Red-Tag Repair Tracking")
        df_bd = get_breakdown_maint_for_slot(sel_month, sel_week)
        st.dataframe(df_bd, use_container_width=True, hide_index=True)

def render_safety_checklist_viewer():
    st.markdown("### 🛡️️ Safety Compliance Checklist: Electronics STEM Lab")
    cur_m_idx, cur_w_idx = get_current_indices()

    c1, c2, c3 = st.columns([1.2, 1.2, 1.2])
    sel_month = c1.selectbox("Select Month (Safety Audit):", MONTHS, index=cur_m_idx, key="view_safe_month")
    sel_week = c2.selectbox("Select Week (Safety Audit):", WEEKS, index=cur_w_idx, key="view_safe_week")
    sel_date = c3.date_input("Inspection Date:", value=datetime.now(), key="view_safe_date")

    df_slot = get_safety_checklist_for_slot(sel_month, sel_week, default_date_str=str(sel_date))
    display_df = df_slot.copy()
    display_df["Inspection Status"] = display_df["Status"].apply(
        lambda x: "✅ Verified / Compliant" if x is True else "❌ Attention Needed")
    display_df = display_df.drop(columns=["Status"])
    st.dataframe(display_df, use_container_width=True, hide_index=True)

def render_student_excel():
    possible_paths = [
        "LMS STUDENT DATA.xlsx", "LMS STUDENT DATA.xls", "LMS STUDENT DATA.csv",
        os.path.join(DATA_DIR, "LMS STUDENT DATA.xlsx"),
    ]
    for folder in os.listdir(UPLOAD_DIR):
        if "student_list" in folder.lower() or "student list" in folder.lower():
            u_dir = os.path.join(UPLOAD_DIR, folder)
            if os.path.isdir(u_dir):
                for f in os.listdir(u_dir):
                    if f.lower().endswith((".xlsx", ".xls", ".csv")):
                        possible_paths.append(os.path.join(u_dir, f))

    found_file = next((p for p in possible_paths if os.path.exists(p)), None)
    if found_file:
        try:
            ext = os.path.splitext(found_file)[1].lower()
            df = pd.read_csv(found_file) if ext == ".csv" else pd.read_excel(found_file)
            st.markdown(f"### 👨‍🎓 Registered Student Database (Total Records: {len(df)})")
            class_col = next((c for c in df.columns if "class" in str(c).lower()), None)
            if class_col:
                unique_classes = ["All Classes"] + sorted([str(x) for x in df[class_col].dropna().unique()])
                selected_class = st.selectbox("Filter by Class:", unique_classes, key="st_excel_filter")
                df_display = df[df[class_col].astype(str) == selected_class] if selected_class != "All Classes" else df
            else:
                df_display = df
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error reading student dataset: {e}")
    else:
        st.info("ℹ️ 'LMS STUDENT DATA.xlsx' file portal me surakshit load hone ke liye ready hai.")

def render_scienceutsav_assessment():
    st.markdown("### 📊 ScienceUtsav Classroom Assessment & Performance Portal")
    saved_su_url = get_saved_url(SCIENCEUTSAV_CONFIG_FILE)
    if not saved_su_url:
        saved_su_url = "https://report.scienceutsav.com/class/k57a8q5h6mzanqt4vdvn48c1vx8ba0q3/report"
    st.link_button("🌐 Open ScienceUtsav Portal in New Tab", saved_su_url)
    components.iframe(saved_su_url, height=750, scrolling=True)

# ----------------- ANNUAL INNOVATION ROADMAP DATA -----------------
ANNUAL_PLAN_DATA = [
    {"Month": "July 2026", "Session #": "Session 1", "Class 6": "Intro to Robotics & Arduino IDE setup",
     "Class 7": "Microcontroller Recap & Sensor Safety", "Class 8": "Advanced Programming Architecture",
     "Class 9": "Multi-Sensor System Architecture & I/O",
     "Milestone": "Erehwon Phase 1: Team Formation (25+ Teams across Classes 6-9; 5-6 members each).",
     "Roles": "Team Lead & Problem Scout"},
    {"Month": "July 2026", "Session #": "Session 2", "Class 6": "Digital Pins & LED Blink Logic",
     "Class 7": "Tilt Switch Basics & Angle Alerts", "Class 8": "7-Segment / LCD Interface Basics",
     "Class 9": "Data Fusion & Complex Logic Loops",
     "Milestone": "Problem Discovery: Community, school campus & environmental pain point identification.",
     "Roles": "Problem Scout & QA Tester"},
    {"Month": "August 2026", "Session #": "Session 3", "Class 6": "Switches & Pull-up/Pull-down Logic",
     "Class 7": "Tilt Safety System Integration", "Class 8": "Digital Display Logic & Variables",
     "Class 9": "Capstone Planning & BOM Setup",
     "Milestone": "MILESTONE 1: Submission & approval of 25+ validated Problem Statements & BOM.",
     "Roles": "Team Lead & Circuit Engineer"},
    {"Month": "August 2026", "Session #": "Session 4", "Class 6": "Potentiometer & Analog Read Values",
     "Class 7": "Magnetic Detection & Hall Effect Intro", "Class 8": "Sensor-Driven Counting Algorithms",
     "Class 9": "Modular Subsystem Design & Pin Mapping",
     "Milestone": "Ideation & Architecture: System block diagrams, circuit schematics & hardware flowcharts.",
     "Roles": "Firmware Programmer & Casing Designer"},
    {"Month": "September 2026", "Session #": "Session 5", "Class 6": "Light Sensing (LDR) & Thresholds",
     "Class 7": "Hall Logic & Contactless Switches", "Class 8": "Touch Sensors & Capacitive Switching",
     "Class 9": "Interfacing Multi-Sensor Arrays",
     "Milestone": "Low-Fidelity Prototyping: Breadboard wiring & sensor threshold calibration.",
     "Roles": "Circuit Engineer & QA Tester"},
    {"Month": "September 2026", "Session #": "Session 6", "Class 6": "Auto Lighting System Integration",
     "Class 7": "IR Object Detection Fundamentals", "Class 8": "RGB Modulation via PWM Logic",
     "Class 9": "Multi-Actuator Output Orchestration",
     "Milestone": "MILESTONE 2: Low-Fidelity Prototype Walkthrough (Breadboards functional + cardboard mockups).",
     "Roles": "Casing Designer & Programmer"},
    {"Month": "October 2026", "Session #": "Session 7", "Class 6": "Sound Reactive System & Mic Modules",
     "Class 7": "IR Threshold Tuning & Alerts", "Class 8": "Laser Optical Transceivers & LDRs",
     "Class 9": "Code Integration & State Machine Coding",
     "Milestone": "Mid-Term Assembly: Combining sensors with actuators (servos, buzzers, multi-stage displays).",
     "Roles": "Firmware Programmer & Circuit Engineer"},
    {"Month": "October 2026", "Session #": "Session 8", "Class 6": "Acoustic Threshold Noise Alerts",
     "Class 7": "Servo Motor Motion & PWM (0°-180°)", "Class 8": "Multi-Trigger Security (AND/OR Logic)",
     "Class 9": "Smart System Capstone Integration (Pt 1)",
     "Milestone": "Logic Debugging: State machine loops, sensor conflict resolution & power distribution.",
     "Roles": "Programmer & QA Tester"},
    {"Month": "November 2026", "Session #": "Session 9", "Class 6": "Multi-LED Logic & Gated Alerts",
     "Class 7": "Automated IR + Servo Barrier System", "Class 8": "Subsystem Integration & Wire Looms",
     "Class 9": "Smart System Capstone Integration (Pt 2)",
     "Milestone": "High-Fidelity Packaging: Enclosure fabrication and cable looming.",
     "Roles": "Casing Designer & Circuit Engineer"},
    {"Month": "November 2026", "Session #": "Session 10", "Class 6": "System Testing & Breadboard Cleanup",
     "Class 7": "Enclosure Packaging & Assembly", "Class 8": "Edge Case Handling & Debounce Code",
     "Class 9": "Full System Field Testing & Telemetry",
     "Milestone": "MILESTONE 3: Alpha Working Prototype Demonstration in Lab under operating conditions.",
     "Roles": "All 5-6 Team Members"},
    {"Month": "December 2026", "Session #": "Session 11", "Class 6": "Prototype Stress Testing & Debugging",
     "Class 7": "Mechanical Reliability & Power Checks", "Class 8": "System Stress Testing (100+ Cycles)",
     "Class 9": "Code Optimization & Fail-Safe Logic",
     "Milestone": "Stress Testing & Data Logging: 50-100 continuous test cycles, fail-safe verification.",
     "Roles": "QA Tester & Programmer"},
    {"Month": "December 2026", "Session #": "Session 12", "Class 6": "Presentation Skills & Pitch Deck Basics",
     "Class 7": "Project Report & Technical Schematics", "Class 8": "Pitch Scripting & Demo Storyboarding",
     "Class 9": "Comprehensive Engineering Dossier",
     "Milestone": "Documentation & Scripting: 1-Page Project Dossier, complete schematics, BOM and pitch script.",
     "Roles": "Pitch Lead & Team Lead"},
    {"Month": "January 2027", "Session #": "Session 13", "Class 6": "Internal Qualifying Pitch & Demo",
     "Class 7": "Internal Jury Evaluation & Feedback", "Class 8": "Pre-Competition Mock Presentation",
     "Class 9": "Grand Internal Capstone Defense",
     "Milestone": "School-Level Qualifying Round: 3-minute live pitch + 2-minute live hardware demonstration.",
     "Roles": "Pitch Lead & Full Team"},
    {"Month": "January 2027", "Session #": "Session 14", "Class 6": "Video Production & Competition Entry",
     "Class 7": "Final Video Shoot & Erehwon Upload", "Class 8": "Video Asset Rendering & Submission",
     "Class 9": "Final Portal Submission & Lab Archive",
     "Milestone": "MILESTONE 4: Final 2-Minute Demo Video Shoot & Submission to National Portal.",
     "Roles": "All 5-6 Team Members"}
]

def render_annual_plan():
    st.markdown("""
    ### 📅 MONTHLY / ANNUAL STEM ACTIVITY PLAN (JULY 2026 – JANUARY 2027)
    > **Schedule:** 2 Sessions / Month (14 Total Sessions) | **Target:** 25+ Innovation Teams (Classes 6–9)
    """)
    df_plan = pd.DataFrame(ANNUAL_PLAN_DATA)
    st.dataframe(df_plan, use_container_width=True, hide_index=True)

# ----------------- 56 MASTER LESSON PLANS -----------------
LESSON_PLANS_DB = {
    "Class 6": [
        ("Session 1 (01-15 July 2026)", "Intro to Robotics & Arduino IDE setup with Sensor Shield",
         "Mount shield on Arduino Uno; flash BareMinimum sketch; setup 5-6 member teams.",
         "1. Robotics anatomy, Arduino IDE, mounting Breakout Shield.\n2. Pinout safety (GND-VCC-Signal).\n3. Code syntax: setup(), loop(), pinMode().",
         "Arduino Uno, Sensor Shield V5.0, USB cables, PCs.", "Continuous Lab Evaluation (10M)."),
        ("Session 2 (16-31 July 2026)", "LED, Digital Pins & Blink Logic on Shield",
         "Connect 3-pin LED module to Pin 13; modify blink delay; analyze energy waste.",
         "1. Digital output logic on Pin 13.\n2. Delay modification and loop frequency.",
         "Arduino Uno, Sensor Shield, 3-pin LED module.", "Lab Evaluation (10M)."),
        ("Session 3 (01-15 August 2026)", "Push Buttons & Digital Input Switching",
         "Plug 3-pin button module into Pin 2; code manual LED toggle.",
         "1. Digital inputs, pull-up logic, tactile button on Pin 2.\n2. Software debouncing.",
         "Arduino Uno, Sensor Shield, Button module, LED.", "Lab Evaluation (10M)."),
        ("Session 4 (16-31 August 2026)", "Potentiometers & Analog Input Reading",
         "Connect Potentiometer to Analog Pin A0; read voltage on Serial Monitor.",
         "1. Analog signals, ADC (0-1023) on Pin A0.\n2. Mapping analog input to PWM.",
         "Arduino Uno, Sensor Shield, Potentiometer module.", "Lab Evaluation (10M)."),
        ("Session 5 (01-15 September 2026)", "Light Sensing (LDR) & Threshold Calibration",
         "Calibrate LDR module on Pin A0; log Lux values in bright/dark states.",
         "1. Photoresistor physics, 3-pin LDR on A0.\n2. Calibrating sensory trigger points.",
         "Arduino Uno, Sensor Shield, LDR module.", "Lab Evaluation (10M)."),
        ("Session 6 (16-30 September 2026)", "Auto Lighting System & Miniature Post Assembly",
         "Build automated street lighting model inside cardboard chassis.",
         "1. Conditional IF/ELSE logic for night lighting.\n2. Milestone 2: Prototype walkthrough.",
         "Arduino Uno, Sensor Shield, LDR module, High-power LED.", "Lab Evaluation (10M)."),
        ("Session 7 (01-15 October 2026)", "Sound Reactive System & Microphone Sensors",
         "Plug sound sensor into shield; code sound-reactive LED flash.",
         "1. Acoustic detection, noise threshold tuning on A1/D3.\n2. Microphone sensitivity tuning.",
         "Arduino Uno, Sensor Shield, Sound Sensor, LED.", "Lab Evaluation (10M)."),
        ("Session 8 (16-31 October 2026)", "Acoustic Alert & Smart Noise Warning Indicator",
         "Assemble Smart Noise Monitor (Sound module + RGB LED + Buzzer).",
         "1. Sound threshold triggers, active buzzer integration on Pin 8.\n2. Alarm sequencing.",
         "Arduino Uno, Sensor Shield, Sound module, RGB LED, Buzzer.", "Lab Evaluation (10M)."),
        ("Session 9 (01-15 November 2026)", "Multi-LED Logic & Campus Security Triggers",
         "Wire Red/Yellow/Green LED modules to pins 11, 12, 13; program status sequencing.",
         "1. Multi-output corridor status indicators.\n2. Multi-channel state sequencing.",
         "Arduino Uno, Sensor Shield, 3x LED modules.", "Lab Evaluation (10M)."),
        ("Session 10 (16-30 November 2026)", "System Enclosure & Alpha Prototype Assembly",
         "Alpha demo: Install automated corridor light inside scale chassis.",
         "1. Packaging hardware inside rigid housing.\n2. Milestone 3: Alpha Prototype.",
         "Arduino Uno, Sensor Shield, Full Sensor Setup, Chassis.", "Lab Evaluation (10M)."),
        ("Session 11 (01-15 December 2026)", "Prototype Stress Testing & Data Logging",
         "Run 30 test cycles of automatic light/noise trigger; record latency.",
         "1. Reliability testing, sensor drift check, loose wire inspection.\n2. QA logging.",
         "Arduino Uno, Sensor Shield, Assembled Prototype.", "Lab Evaluation (10M)."),
        ("Session 12 (16-31 December 2026)", "Presentation Skills & 1-Page Pitch Dossier",
         "Draft 1-page project brief; prepare slide deck with team photos and BOM.",
         "1. Problem-solution narrative, circuit schematic sketching.\n2. 1-Page Project Dossier.",
         "PCs, Logbooks, Slide templates.", "Lab Evaluation (10M)."),
        ("Session 13 (01-15 January 2027)", "Internal Qualifying Pitch & Demo",
         "Live demonstration of prototypes before school jury.",
         "1. 3-minute pitch, working hardware demo, answering jury Q&A.\n2. Jury evaluation.",
         "Completed Prototypes, Projector, Jury Scorecards.", "Qualifying Pitch Score (10M)."),
        ("Session 14 (16-31 January 2027)", "Final Video Shoot & Erehwon Upload",
         "Record 2-minute project demo video; upload code and report to portal.",
         "1. Video recording, structured demonstration, portal submission.\n2. Lab archiving.",
         "Camera, Demo Setup, Portal Access.", "Lab Evaluation (10M).")
    ],
    "Class 7": [
        ("Session 1 (01-15 July 2026)", "Microcontroller Safety & Sensor Shield Architecture",
         "Inspect Arduino Uno + Shield; map 3-pin ports; form 5-6 member teams.",
         "1. Breakout Shield power distribution, 3-pin G-V-S bus.\n2. Actuator power safety.",
         "Arduino Uno, Sensor Shield, Multimeter.", "Lab Evaluation (10M)."),
        ("Session 2 (16-31 July 2026)", "Tilt Safety Sensors & Angular Threshold Logic",
         "Plug Tilt module into shield; write angle-deviation detection code.",
         "1. Tilt switches, angular displacement detection on D2.\n2. Digital debounce logic.",
         "Arduino Uno, Sensor Shield, Tilt module, LED.", "Lab Evaluation (10M)."),
        ("Session 3 (01-15 August 2026)", "Tilt Safety System & Emergency Audio Alert",
         "Assemble Tilt Warning Rig (Tilt module + Buzzer on shield); test at 45° angle.",
         "1. Pulsed buzzer alarm logic, tilt stability.\n2. Milestone 1: Problem Statement approval.",
         "Arduino Uno, Sensor Shield, Tilt Sensor, Buzzer.", "Lab Evaluation (10M)."),
        ("Session 4 (16-31 August 2026)", "Magnetic Detection & Hall Effect Fundamentals",
         "Connect Hall Sensor to Pin 3; test neodymium magnet approach.",
         "1. Lorentz force, A3144 Hall Effect module, proximity detection.\n2. Contactless switching.",
         "Arduino Uno, Sensor Shield, Hall Sensor, Magnets.", "Lab Evaluation (10M)."),
        ("Session 5 (01-15 September 2026)", "Hall Logic & Contactless Window/Door Security",
         "Build Contactless Door/Window Alarm using Hall module + Buzzer on shield.",
         "1. Open-collector switching, pull-up logic.\n2. Air-gap calibration (2mm-15mm).",
         "Arduino Uno, Sensor Shield, Hall Sensor, Buzzer.", "Lab Evaluation (10M)."),
        ("Session 6 (16-30 September 2026)", "IR Proximity & Object Detection Principles",
         "Connect IR Obstacle module to shield; calibrate detection distance (2cm-20cm).",
         "1. IR emitter-receiver pair, onboard potentiometer tuning.\n2. Milestone 2: Walkthrough.",
         "Arduino Uno, Sensor Shield, IR Obstacle module.", "Lab Evaluation (10M)."),
        ("Session 7 (01-15 October 2026)", "IR Threshold Tuning & Anti-Collision Alerts",
         "Wire IR module + multi-tone Buzzer; code anti-collision hallway alert.",
         "1. Proximity alert logic, multi-stage distance warnings.\n2. Dynamic response testing.",
         "Arduino Uno, Sensor Shield, IR Module, Buzzer.", "Lab Evaluation (10M)."),
        ("Session 8 (16-31 October 2026)", "Servo Motor Motion & PWM Angular Control (0°-180°)",
         "Plug SG90 servo into dedicated Servo port; write angular sweep code (0° to 90°).",
         "1. SG90 servo, 50Hz PWM signal, Servo.h library on PWM Pin 9.\n2. Mechanical linkage.",
         "Arduino Uno, Sensor Shield, SG90 Servo.", "Lab Evaluation (10M)."),
        ("Session 9 (01-15 November 2026)", "Automated IR + Servo Smart Barrier System",
         "Build Automated Barrier Gate: IR sensor triggers servo to lift barrier 90°.",
         "1. Synchronized sensing and actuation, auto-closure logic.\n2. High-Fidelity packaging.",
         "Arduino Uno, Sensor Shield, IR Module, SG90 Servo, Gate Assembly.", "Lab Evaluation (10M)."),
        ("Session 10 (16-30 November 2026)", "Enclosure Packaging & Alpha Model Assembly",
         "Alpha demo: Complete mechanical casing for Smart Gate / Auto Dustbin.",
         "1. Mechanical housing, pivot stabilization, concealing shield.\n2. Milestone 3: Alpha Review.",
         "Arduino Uno, Sensor Shield, Chassis housing.", "Lab Evaluation (10M)."),
        ("Session 11 (01-15 December 2026)", "Mechanical Reliability & Power Surge Testing",
         "Execute 50 continuous automated cycles; verify servo does not reset board.",
         "1. Servo load testing, 50 continuous sweep cycles.\n2. Voltage dip check.",
         "Arduino Uno, Sensor Shield, Automated Gate Rig, Multimeter.", "Lab Evaluation (10M)."),
        ("Session 12 (16-31 December 2026)", "Technical Schematics & Project Pitch Preparation",
         "Draft technical report and circuit diagrams; storyboard 2-minute pitch.",
         "1. Full circuit schematics, BOM reconciliation.\n2. Pitch presentation script.",
         "PCs, Schematics CAD tools.", "Lab Evaluation (10M)."),
        ("Session 13 (01-15 January 2027)", "Internal Qualifying Evaluation & Jury Defense",
         "Present working hardware prototype before school evaluation committee.",
         "1. 3-minute pitch, live automated gate demo.\n2. Technical oral defense.",
         "Completed Prototypes, Projector, Evaluation scorecards.", "Qualifying Defense Score (10M)."),
        ("Session 14 (16-31 January 2027)", "Final Video Production & Erehwon Portal Upload",
         "Record 2-minute demonstration video; submit entry on portal.",
         "1. HD video recording, voiceover narration.\n2. Milestone 4 Submission.",
         "Camera, Finished Rig, Portal Access.", "Lab Evaluation (10M).")
    ],
    "Class 8": [
        ("Session 1 (01-15 July 2026)", "Advanced Programming Architecture & Shield I/O Banks",
         "Setup Arduino Uno + Shield; map analog/digital/I2C channels; form teams.",
         "1. Arrays, state machines, shield I2C/UART ports.\n2. Pin budgeting.",
         "Arduino Uno, Sensor Shield, PC.", "Lab Evaluation (10M)."),
        ("Session 2 (16-31 July 2026)", "7-Segment Display Architecture & Segment Mapping",
         "Connect 7-segment display to pins 2-8; display digits 0-9 sequentially.",
         "1. Common cathode/anode pinouts, segment truth tables (a-g).\n2. Bitwise mapping.",
         "Arduino Uno, Sensor Shield, 7-Segment display.", "Lab Evaluation (10M)."),
        ("Session 3 (01-15 August 2026)", "Digital Counting Logic & Software Switch Debounce",
         "Build Digital Counter with 2 pushbuttons and 7-segment display on shield.",
         "1. Counter variables, debounce timing with millis().\n2. Milestone 1 approval.",
         "Arduino Uno, Sensor Shield, 7-Segment, 2x Buttons.", "Lab Evaluation (10M)."),
        ("Session 4 (16-31 August 2026)", "I2C LCD 16x2 Interface & Dedicated Shield Port",
         "Plug I2C LCD into 4-pin I2C port on shield; print live visitor count strings.",
         "1. I2C bus (SDA/SCL on A4/A5), LiquidCrystal_I2C library.\n2. String formatting.",
         "Arduino Uno, Sensor Shield, 16x2 I2C LCD.", "Lab Evaluation (10M)."),
        ("Session 5 (01-15 September 2026)", "Capacitive Touch Sensing & Variable Switching",
         "Connect Touch Sensor to Pin 4 and RGB LED to PWM Pins 9, 10, 11 on shield.",
         "1. TTP223 Capacitive Touch module, PWM LED dimming.\n2. Touch latching.",
         "Arduino Uno, Sensor Shield, TTP223 Touch, RGB LED.", "Lab Evaluation (10M)."),
        ("Session 6 (16-30 September 2026)", "RGB Color Modulation via PWM Logic",
         "Code multi-color warning beacon on shield (Green=Normal, Amber=Caution, Red=Alert).",
         "1. AnalogWrite() duty cycles (0-255), RGB additive mixing.\n2. Milestone 2 Walkthrough.",
         "Arduino Uno, Sensor Shield, RGB LED.", "Lab Evaluation (10M)."),
        ("Session 7 (01-15 October 2026)", "Laser Optical Transceivers & Narrow-Beam Alignment",
         "Mount Laser on Pin 8 and LDR on Pin A0; align optical beam inside shrouded tube.",
         "1. 650nm Laser Diode, optical tripwire physics.\n2. Optical breach detection.",
         "Arduino Uno, Sensor Shield, 5V Laser Diode, LDR module.", "Lab Evaluation (10M)."),
        ("Session 8 (16-31 October 2026)", "Multi-Trigger Security System (AND/OR Logic)",
         "Build Dual-Factor Security Grid: Laser breach + Touch perimeter triggers siren.",
         "1. Compound boolean logic, software alarm latching.\n2. Disarm logic.",
         "Arduino Uno, Sensor Shield, Laser, LDR, Touch, Buzzer.", "Lab Evaluation (10M)."),
        ("Session 9 (01-15 November 2026)", "Subsystem Integration & Wire Looming inside Casing",
         "Assemble full system on shield; route cables into rigid casing.",
         "1. Combining LCD, Laser, Touch, and Siren into single shield setup.\n2. Cable looming.",
         "Arduino Uno, Sensor Shield, Full Sensor Suite, Casing.", "Lab Evaluation (10M)."),
        ("Session 10 (16-30 November 2026)", "Edge Case Handling & Debounce Code Hardening",
         "Test laser security grid under changing ambient room lights; optimize code.",
         "1. Eliminating false optical triggers, ambient compensation.\n2. Milestone 3: Alpha Review.",
         "Arduino Uno, Sensor Shield, Integrated Security Rig.", "Lab Evaluation (10M)."),
        ("Session 11 (01-15 December 2026)", "System Stress Testing (100+ Cycles) & QA Logging",
         "Execute 100 continuous intrusion tests; record trigger reliability in QA Sheet.",
         "1. Automated 100-cycle tripwire testing, alarm latency measurement.\n2. QA logging.",
         "Arduino Uno, Sensor Shield, Security Rig, QA Sheet.", "Lab Evaluation (10M)."),
        ("Session 12 (16-31 December 2026)", "Pitch Deck Creation & Video Storyboarding",
         "Compile technical dossier and BOM; storyboard 2-minute pitch video.",
         "1. Technical architecture slide, video scriptwriting.\n2. Engineering schematics.",
         "PCs, Schematics software.", "Lab Evaluation (10M)."),
        ("Session 13 (01-15 January 2027)", "Pre-Competition Mock Defense & Jury Evaluation",
         "Full dress rehearsal: Present security prototype before senior faculty panel.",
         "1. 3-minute presentation, live laser breach demo.\n2. Jury defense.",
         "Complete Integrated Prototype, Projector.", "Mock Defense Score (10M)."),
        ("Session 14 (16-31 January 2027)", "Final Video Rendering & Erehwon Dossier Upload",
         "Record final 2-minute demonstration video; upload code and dossier.",
         "1. HD video recording, schematic export.\n2. Milestone 4 Submission.",
         "Camera, Completed System, Portal.", "Lab Evaluation (10M).")
    ],
    "Class 9": [
        ("Session 1 (01-15 July 2026)", "Multi-Sensor System Architecture & Shield Bus Management",
         "Analyze Uno+Shield pin allocation; map 4+ simultaneous sensor channels.",
         "1. Heterogeneous sensor bus, non-blocking millis() timing.\n2. Power rails decoupling.",
         "Arduino Uno, Sensor Shield, Multi-sensor array.", "Lab Evaluation (10M)."),
        ("Session 2 (16-31 July 2026)", "Data Fusion & Multi-Variable Logic Loops",
         "Connect LDR + Tilt + Sound modules simultaneously; write synchronized telemetry.",
         "1. Sensor fusion principles, combining analog and digital triggers.\n2. Serial telemetry.",
         "Arduino Uno, Sensor Shield, LDR, Tilt, Sound modules.", "Lab Evaluation (10M)."),
        ("Session 3 (01-15 August 2026)", "Capstone System Planning & BOM Optimization",
         "Finalize Capstone BOM; submit Milestone 1 Project Charter for sign-off.",
         "1. System architecture diagrams, power budgeting.\n2. Milestone 1 approval.",
         "Arduino Uno, Sensor Shield, BOM Spreadsheet.", "Lab Evaluation (10M)."),
        ("Session 4 (16-31 August 2026)", "Modular Subsystem Prototyping (Sensing vs Actuation)",
         "Build Sensing Subsystem and Actuation Subsystem on separate benches; verify signals.",
         "1. Decoupling hardware layers: Input sensing vs Output actuation.\n2. Signal integrity.",
         "Arduino Uno, Sensor Shield, Relays, Servos.", "Lab Evaluation (10M)."),
        ("Session 5 (01-15 September 2026)", "Interfacing Multi-Sensor Arrays on Breakout Shield",
         "Integrate full sensor array onto shield; write unified sensor sampling routine.",
         "1. Simultaneous wiring of IR, Hall, Tilt, and LDR modules.\n2. Non-blocking polling.",
         "Arduino Uno, Sensor Shield, IR, Hall, Tilt, LDR sensors.", "Lab Evaluation (10M)."),
        ("Session 6 (16-30 September 2026)", "Multi-Actuator Orchestration & Power Isolation",
         "Connect SG90 servo + 5V Relay + I2C LCD to shield; supply external 5V power.",
         "1. Driving multiple servos, relays via external power terminals.\n2. Milestone 2 Walkthrough.",
         "Arduino Uno, Sensor Shield, Servo, Relay, I2C LCD, DC Supply.", "Lab Evaluation (10M)."),
        ("Session 7 (01-15 October 2026)", "Non-Blocking State Machine Code Integration",
         "Merge sensor sampling and actuator routines into non-blocking master sketch.",
         "1. Replacing delay() with millis() timers, state enums.\n2. Real-time response.",
         "Arduino Uno, Sensor Shield, Full Hardware Setup.", "Lab Evaluation (10M)."),
        ("Session 8 (16-31 October 2026)", "Smart System Capstone Integration (Part 1: Core Logic)",
         "Assemble integrated Capstone build; code automated feedback control loop.",
         "1. Industrial safety interlocking logic, multi-stage thresholds.\n2. Feedback control.",
         "Arduino Uno, Sensor Shield, Capstone Sensors & Actuators.", "Lab Evaluation (10M)."),
        ("Session 9 (01-15 November 2026)", "Smart System Capstone Integration (Part 2: Casing & Looms)",
         "Mount assembly into durable modular chassis; bundle cables with spiral wrap.",
         "1. Enclosure fabrication, heat-shrink wire looms, power switch.\n2. Battery integration.",
         "Arduino Uno, Sensor Shield, Chassis, Spiral wrap, Battery pack.", "Lab Evaluation (10M)."),
        ("Session 10 (16-30 November 2026)", "Full System Field Testing & Telemetry Logging",
         "Subject capstone build to 50 continuous operational cycles; log metrics.",
         "1. Field stress testing, sensor drift and latency logging.\n2. Milestone 3: Alpha Review.",
         "Complete Capstone Unit, QA Sheet.", "Lab Evaluation (10M)."),
        ("Session 11 (01-15 December 2026)", "Code Hardening, Fail-Safes & Auto-Recovery",
         "Implement fail-safe routines (auto-shutdown on sensor fault); optimize firmware.",
         "1. Error-handling routines, sensor disconnection auto-recovery.\n2. Firmware hardening.",
         "Arduino Uno, Sensor Shield, Capstone Rig.", "Lab Evaluation (10M)."),
        ("Session 12 (16-31 December 2026)", "Comprehensive Engineering Dossier & Schematics",
         "Compile engineering dossier (Problem statement, block diagram, schematics, source code).",
         "1. Project documentation, full circuit schematics, test data graphs.\n2. Pitch script.",
         "PCs, Schematics CAD tools.", "Lab Evaluation (10M)."),
        ("Session 13 (01-15 January 2027)", "Grand Internal Capstone Defense & Jury Review",
         "Formal Capstone defense before school leadership and external jury.",
         "1. 5-minute technical defense, live autonomous operation demo.\n2. Committee evaluation.",
         "Completed Capstone System, Projector.", "Capstone Defense Score (10M)."),
        ("Session 14 (16-31 January 2027)", "National Submission & Lab Archive Deployment",
         "Record 2-min demo video; complete final submission on portal; archive in lab repo.",
         "1. Video production, portal upload, lab repository handover.\n2. Milestone 4 Submission.",
         "Camera Rig, Finished Capstone, Portal.", "Lab Evaluation (10M).")
    ]
}

# ----------------- MASTER CONTENT ROUTER -----------------
def render_master_content(sno, title):
    if title == "STEM Lab Profile" or sno == 1:
        st.markdown("""
        ### 🏫 STEM LAB PROFILE
        * **School Name:** Aditya Birla Intermediate College, Renukoot
        * **Academic Session:** 2026-27
        * **STEM Lab:** School STEM Innovation & Learning Laboratory
        * **STEM Coordinator / SPOC:** Shashank Verma

        ---
        #### 1. Introduction
        The STEM Lab of Aditya Birla Intermediate College, Renukoot is a dedicated space for promoting Science, Technology, Engineering and Mathematics (STEM) learning through hands-on activities, experimentation, problem-solving, innovation and project-based learning.

        #### 2. Classes Covered
        * **Class VI** (Beginner Tier) | **Class VII** (Intermediate Tier) | **Class VIII** (Advanced Tier) | **Class IX** (Expert Capstone Tier)

        #### 3. Major Objectives
        1. To develop scientific thinking and curiosity among students.
        2. To promote hands-on and experiential learning.
        3. To encourage real-life problem solving and design thinking.
        4. To master embedded coding, robotics and 3D printing.
        5. To mentor student innovation for national platforms (Erehwon, STEM SPARK, VVM).
        """)
        return True

    elif title == "Lab Objectives & Guidelines" or sno == 2:
        st.markdown("""
        ### 📋 STEM LAB OBJECTIVES & GUIDELINES
        * **School:** Aditya Birla Intermediate College, Renukoot | **Session:** 2026-27
        ---
        #### Safety & Handling Guidelines
        1. **Supervision:** Students may work in the lab only in the presence of the STEM Teacher or SPOC.
        2. **Electrical Safety:** Always verify power polarity before connecting headers to the Breakout Shield. Short circuits are strictly prohibited.
        3. **Emergency Cutoff:** In the event of smoke or sparking, hit the emergency master bench cutoff switch immediately.
        """)
        return True

    elif title == "Coordinator / SPOC Details" or sno == 3:
        st.markdown("""
        ### 👤 STEM LAB COORDINATOR / SPOC DETAILS
        * **Name:** Shashank Verma
        * **Designation:** PGT
        * **Role:** STEM Coordinator / School STEM SPOC
        * **School:** Aditya Birla Intermediate College, Renukoot, Sonbhadra (U.P.)
        * **Official Email:** `shashank.verma@adityabirlaschools.in`
        * **Official Contact:** `9826594665`
        """)
        return True

    elif title == "Monthly / Annual STEM Activity Plan" or sno == 4:
        render_annual_plan()
        return True

    elif title == "Class-wise Timetable" or sno == 5:
        render_timetable_view()
        return True

    elif title == "Session / Lesson Plans" or sno == 6:
        st.markdown("### 📖 ANNUAL STEM LAB MASTER LESSON PLANS (56 SESSIONS)")
        col_c, col_s = st.columns([1, 2])
        selected_class = col_c.selectbox("🎓 Select Class:", list(LESSON_PLANS_DB.keys()), key="lp_cls_sel")
        sessions_list = LESSON_PLANS_DB[selected_class]
        session_titles = [f"{s[0]} — {s[1]}" for s in sessions_list]
        selected_session_idx = col_s.selectbox("📑 Select Session:", range(len(session_titles)),
                                               format_func=lambda i: session_titles[i], key="lp_ses_sel")
        plan = sessions_list[selected_session_idx]
        st.markdown("---")
        st.subheader(f"📌 {selected_class}: {plan[0]}")
        st.markdown(f"#### 🔬 Unit / Module: `{plan[1]}`")
        cl, cr = st.columns(2)
        with cl:
            st.info(f"**Activity:** {plan[2]}")
            st.success(f"**Teaching Aid:** {plan[4]}")
        with cr:
            st.code(plan[3], language="text")
            st.caption(f"Assessment: {plan[5]}")
        return True

    elif title == "Student List" or sno == 7:
        render_student_excel()
        return True

    elif title == "Student Attendance" or sno == 8:
        render_student_attendance_viewer()
        return True

    elif title == "Teacher Attendance" or sno == 9:
        render_teacher_attendance_viewer()
        return True

    elif title == "Lab Inventory" or sno == 10:
        st.markdown("""
        ### 📦 Verified STEM Lab Inventory
        * **Microcontrollers:** 25x Arduino Uno R3, 25x Sensor Breakout Shields V5.0.
        * **Sensor Suite:** LDR, DHT11, MQ2, Soil Moisture, Ultrasonic HC-SR04, IR Obstacle, Hall Effect, Tilt, Touch, Sound.
        * **Actuators:** SG90 Servos, BO Geared Motors, 5V Relays, 16x2 I2C LCDs, 7-Segment Displays, Buzzers, RGB LEDs.
        * **Prototyping:** Bambu Lab A1 Mini 3D Printer, DC Power Supplies, Component Racks.
        """)
        return True

    elif title == "Maintenance Records" or sno == 14:
        render_maintenance_viewer()
        return True

    elif title == "Lab Safety Rules" or sno == 15:
        st.markdown("""
        ### 🛡️ STEM LAB SAFETY RULES
        > **BE SAFE • BE RESPONSIBLE • BE INNOVATIVE**
        * Enter the lab only with permission.
        * Check all circuit wiring before powering on.
        * Wear safety glasses during soldering and wire snipping.
        * Keep water and beverages strictly away from electrical benches.
        * Report loose connections or damaged tools immediately.
        """)
        return True

    elif title == "Safety Checklist" or sno == 16:
        render_safety_checklist_viewer()
        return True

    elif title == "Assessment Rubrics" or sno == 27:
        st.markdown("""
        ### 📊 Student STEM Assessment Rubric (100 Marks Distribution)
        * **Problem Identification & Logbook (20M)**
        * **Hardware Circuit & Wiring Hygiene (20M)**
        * **Firmware Coding & Logic (20M)**
        * **Enclosure, Packaging & Casing (20M)**
        * **Live Demonstration & Oral Defense (20M)**
        """)
        return True

    elif title == "Student Assessment" or sno == 28:
        render_scienceutsav_assessment()
        return True

    return False

# =========================================================================
# 🧭 TOP NAVBAR (SWAYAM STYLE LAYOUT)
# =========================================================================
nav_col1, nav_col2, nav_col3 = st.columns([3.5, 6.5, 2])

with nav_col1:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px;">
        <div style="background:#004085; color:white; font-weight:800; font-size:20px; padding:4px 10px; border-radius:4px;">ABIC</div>
        <span style="font-weight:700; color:#1f2937; font-size:16px;">STEM Lab Portal</span>
    </div>
    """, unsafe_allow_html=True)

with nav_col2:
    st.markdown("""
    <div style="display:flex; gap:16px; align-items:center; height:100%; font-size:13px; color:#4b5563; font-weight:500;">
        <span>About STEM Lab</span>
        <span>49 Parameters</span>
        <span>Student Records</span>
        <span>Robotics & IoT</span>
        <span>Safety Rules</span>
    </div>
    """, unsafe_allow_html=True)

with nav_col3:
    if not st.session_state["is_admin_logged_in"]:
        if st.button("Login / Sign up", type="primary", use_container_width=True):
            st.session_state["show_login_modal"] = not st.session_state["show_login_modal"]
    else:
        if st.button("Admin Logout 🚪", use_container_width=True):
            st.session_state["is_admin_logged_in"] = False
            st.rerun()

# ----------------- ADMIN LOGIN POPUP (ADMIN / ADMIN) -----------------
if st.session_state["show_login_modal"] and not st.session_state["is_admin_logged_in"]:
    with st.container():
        st.markdown("---")
        st.markdown("#### 🔐 Admin Portal Sign In")
        col_log1, col_log2 = st.columns([1, 1])
        with col_log1:
            u_in = st.text_input("Admin ID", placeholder="Admin", key="adm_id_input")
        with col_log2:
            p_in = st.text_input("Password", type="password", placeholder="Admin", key="adm_pass_input")
        
        btn_c1, btn_c2 = st.columns([2, 8])
        if btn_c1.button("Sign In as Admin", type="primary"):
            if u_in.strip().lower() == ADMIN_USER and p_in.strip().lower() == ADMIN_PASSWORD:
                st.session_state["is_admin_logged_in"] = True
                st.session_state["show_login_modal"] = False
                st.success("✅ Logged in successfully as Admin!")
                st.rerun()
            else:
                st.error("Invalid credentials! ID wa Password dono 'Admin' dalein.")
        if btn_c2.button("Cancel"):
            st.session_state["show_login_modal"] = False
            st.rerun()
        st.markdown("---")

# =========================================================================
# 🏛️ MAIN SWAYAM HERO BANNER & HEADING
# =========================================================================
st.markdown("""
<div class="swayam-hero">
    <div class="swayam-tagline">INNOVATION • EXPERIMENTATION • RESEARCH</div>
    <h1>Aditya Birla Inter College Renukoot STEM Lab</h1>
    <div class="swayam-subheading">Science, Technology, Engineering & Mathematics Laboratory (Session 2026-27)</div>
</div>
""", unsafe_allow_html=True)

# Executive Messages Cards
render_executive_messages()

# Center Search Bar
search_cols = st.columns([2, 8, 2])
with search_cols[1]:
    search_text = st.text_input("🔍 Search STEM Lab Parameters, Projects, or Timetable...", placeholder="Search STEM Modules / Parameters...", label_visibility="collapsed")

# =========================================================================
# 🔘 6 CLICKABLE CATEGORY ICONS
# =========================================================================
st.markdown("<br>", unsafe_allow_html=True)

cat_cols = st.columns(6)
cat_keys = list(CATEGORIES.keys())
cat_icons = ["📋", "🛡️", "🚀", "📊", "🧑‍🏫", "🏆"]
cat_titles = [
    "Administration & Planning",
    "Inventory & Safety",
    "Activities & Projects",
    "Assessment & Competitions",
    "Training & Communication",
    "Reports & Achievements"
]

for i, col in enumerate(cat_cols):
    with col:
        st.markdown('<div class="cat-btn-container">', unsafe_allow_html=True)
        btn_caption = f"{cat_icons[i]}\n\n**{cat_titles[i]}**"
        
        if st.button(btn_caption, key=f"cat_tile_{i}", use_container_width=True):
            if st.session_state["selected_category_filter"] == cat_keys[i]:
                st.session_state["selected_category_filter"] = None
            else:
                st.session_state["selected_category_filter"] = cat_keys[i]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- 3 METRICS COUNTER -----------------
met1, met2, met3 = st.columns(3)
with met1:
    st.markdown("""
    <div class="swayam-metric-card">
        <div class="swayam-metric-title">Total Registered Students</div>
        <div class="swayam-metric-val">2000 +</div>
    </div>
    """, unsafe_allow_html=True)

with met2:
    st.markdown("""
    <div class="swayam-metric-card">
        <div class="swayam-metric-title">Lab Compliance Parameters</div>
        <div class="swayam-metric-val">49 Active</div>
    </div>
    """, unsafe_allow_html=True)

with met3:
    st.markdown("""
    <div class="swayam-metric-card">
        <div class="swayam-metric-title">Innovation Teams</div>
        <div class="swayam-metric-val">25 + Teams</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================================
# 📁 REPOSITORY TABS & DATA VIEWERS
# =========================================================================
st.subheader("📚 Explore STEM Laboratory Records & Systems")

if st.session_state["selected_category_filter"]:
    c_banner1, c_banner2 = st.columns([8, 2])
    c_banner1.info(f"📂 **Showing Options for:** `{st.session_state['selected_category_filter']}`")
    if c_banner2.button("✖ Clear Filter (Show All)", key="clear_cat_filter"):
        st.session_state["selected_category_filter"] = None
        st.rerun()

tab_records, tab_students, tab_tt, tab_su, tab_summary = st.tabs([
    "📁 49 Parameters & Files", "👨‍🎓 2000+ Students Data", "⏰ Master Timetable", "🌐 ScienceUtsav Live", "📊 Repository Status"
])

with tab_records:
    if st.session_state["is_admin_logged_in"]:
        st.info("🔓 Admin Mode Active: Aap sabhi parameters me files upload wa manage kar sakte hain.")

    categories_to_show = CATEGORIES.items()
    if st.session_state["selected_category_filter"]:
        categories_to_show = [(st.session_state["selected_category_filter"], CATEGORIES[st.session_state["selected_category_filter"]])]

    for cat_title, items in categories_to_show:
        is_expanded = True if st.session_state["selected_category_filter"] else False
        with st.expander(cat_title, expanded=is_expanded):
            for sno, title in items:
                if search_text and search_text.lower() not in title.lower() and search_text.lower() not in cat_title.lower():
                    continue

                is_active = (st.session_state.get("active_viewer_sno") == sno)
                toggle_btn_label = f"▼ #{sno}. {title}" if is_active else f"▶ #{sno}. {title}"

                if st.button(toggle_btn_label, key=f"view_btn_{sno}"):
                    st.session_state["active_viewer_sno"] = None if is_active else sno
                    st.rerun()

                if is_active:
                    st.markdown(f"#### 📌 #{sno}. {title}")
                    has_builtin = render_master_content(sno, title)
                    files_found = get_existing_files_for_parameter(sno, title)

                    if files_found:
                        st.markdown("---")
                        st.markdown("##### 📁 Uploaded Documents & Files:")
                        for idx, (fpath, fname) in enumerate(files_found):
                            render_file_preview(fpath, fname, f"{sno}_{idx}")
                    elif not has_builtin:
                        st.caption("No document uploaded yet for this parameter.")

                    if st.session_state["is_admin_logged_in"]:
                        render_parameter_file_manager(sno, title)
                    st.markdown("---")

with tab_students:
    render_student_excel()

with tab_tt:
    render_timetable_view()

with tab_su:
    render_scienceutsav_assessment()

with tab_summary:
    total = 49
    completed = 0
    summary_rows = []
    for section_name, items in CATEGORIES.items():
        for sno, title in items:
            files_found = get_existing_files_for_parameter(sno, title)
            has_builtin = title in [
                "STEM Lab Profile", "Lab Objectives & Guidelines", "Coordinator / SPOC Details",
                "Monthly / Annual STEM Activity Plan", "Class-wise Timetable", "Session / Lesson Plans",
                "Student List", "Student Attendance", "Teacher Attendance", "Lab Inventory",
                "Equipment Details", "Maintenance Records", "Lab Safety Rules", "Safety Checklist",
                "Assessment Rubrics", "Student Assessment"
            ]
            if has_builtin or len(files_found) > 0:
                completed += 1
                status = "✅ Active / Verified"
            else:
                status = "⏳ Pending Upload"
            summary_rows.append({"Index": sno, "Parameter Name": title, "Section": section_name, "Status": status})

    c_s1, c_s2 = st.columns(2)
    c_s1.metric("Total Parameters", total)
    c_s2.metric("Active & Verified", f"{completed} / {total}")
    st.dataframe(summary_rows, use_container_width=True)

# ----------------- FOOTER -----------------
st.markdown("""
<div style="text-align:center; padding:30px 0 10px 0; color:#6b7280; font-size:13px; border-top:1px solid #e5e7eb; margin-top:50px;">
    Aditya Birla Intermediate College, Renukoot, Sonbhadra (U.P.) • STEM Innovation & Learning Laboratory<br>
    © 2026-27 Government / Corporate STEM Educational Framework
</div>
""", unsafe_allow_html=True)
