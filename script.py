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
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

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

# ----------------- CREDENTIALS -----------------
ADMIN_USER = "shashank@abic"
VALID_PASSWORDS = ["Admin@2026", "Admin@123", "Abic@123", "stem@admin123"]

DEFAULT_CONFIGS = {
    SHEET_CONFIG_FILE: "https://docs.google.com/spreadsheets/d/1999l0-GPaDxUh2trREm4HOx6NAfsYHGU_0Qakzy4Bwo/edit?usp=sharing",
    FORM_CONFIG_FILE: "https://docs.google.com/forms/d/e/1FAIpQLSeAE6pzeLi-NVO4aTA82gfXH2oKqtFf3TTlIyI0VCQobP9qxQ/viewform?usp=sharing&ouid=116197222500145214334",
    SCIENCEUTSAV_CONFIG_FILE: "https://report.scienceutsav.com/class/k57a8q5h6mzanqt4vdvn48c1vx8ba0q3/report"
}

MONTHS = ["April", "May", "June", "July", "August", "September", "October", "November", "December", "January", "February", "March"]
WEEKS = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]

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

# ----------------- SESSION STATE -----------------
if "is_authenticated" not in st.session_state:
    st.session_state["is_authenticated"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "active_viewer_sno" not in st.session_state:
    st.session_state["active_viewer_sno"] = None
if "active_admin_sno" not in st.session_state:
    st.session_state["active_admin_sno"] = None

# =========================================================================
# 🎨 SCIENCEUTSAV EXACT SPLIT SCREEN LOGIN CSS & INTERFACE
# =========================================================================
SCIENCEUTSAV_LOGIN_CSS = """
<style>
/* Reset main body margin */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Hide default streamlit header on login */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Green Brand Banner */
.su-hero-panel {
    background-color: #0b3d2c;
    color: #ffffff;
    min-height: 98vh;
    padding: 60px 48px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    border-radius: 0 16px 16px 0;
}

.su-logo-tag {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #1e5a44;
    padding: 6px 14px;
    border-radius: 6px;
    font-weight: 700;
    letter-spacing: 0.5px;
    font-size: 16px;
    width: fit-content;
}

.su-hero-title {
    font-family: 'Georgia', serif;
    font-size: 44px;
    font-weight: 700;
    line-height: 1.2;
    margin-top: 50px;
    margin-bottom: 30px;
}

.su-feature-item {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    font-size: 15px;
    color: #d1e7dd;
}

.su-feature-check {
    border: 1.5px solid #20c997;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: #20c997;
    flex-shrink: 0;
}

.su-footer-copy {
    font-size: 12px;
    color: #799e90;
    margin-top: 40px;
}

/* Right Form Container */
.su-form-box {
    max-width: 440px;
    margin: 80px auto;
    padding: 20px;
}

.su-form-heading {
    font-family: 'Georgia', serif;
    color: #0b3d2c;
    font-size: 34px;
    font-weight: 700;
    margin-bottom: 6px;
}

.su-form-subtext {
    font-size: 14px;
    color: #555e68;
    margin-bottom: 32px;
}

/* Green Action Button */
div[data-testid="stButton"] button {
    background-color: #0b3d2c !important;
    color: #ffffff !important;
    border-radius: 6px !important;
    border: none !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    width: 100% !important;
    margin-top: 15px !important;
    transition: all 0.2s ease-in-out;
}

div[data-testid="stButton"] button:hover {
    background-color: #08281d !important;
    box-shadow: 0 4px 12px rgba(11, 61, 44, 0.25) !important;
}

div[data-testid="stTextInput"] input {
    background-color: #edf4fe !important;
    border: 1px solid #c9d8ee !important;
    border-radius: 6px !important;
    padding: 12px 14px !important;
    font-size: 15px !important;
}
</style>
"""

def render_scienceutsav_login_page():
    st.markdown(SCIENCEUTSAV_LOGIN_CSS, unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1.1, 1], gap="large")
    
    with col_left:
        st.markdown("""
        <div class="su-hero-panel">
            <div>
                <div class="su-logo-tag">
                    <span>SU</span> ScienceUtsav • ABIC
                </div>
                
                <div class="su-hero-title">
                    One classroom.<br>Teachers and students.
                </div>
                
                <div class="su-feature-item">
                    <div class="su-feature-check">✓</div>
                    <div>Teachers: score STEM kits and share PDF report cards.</div>
                </div>
                
                <div class="su-feature-item">
                    <div class="su-feature-check">✓</div>
                    <div>Students: work through robotics levels and take quizzes.</div>
                </div>
                
                <div class="su-feature-item">
                    <div class="su-feature-check">✓</div>
                    <div>One sign-in for everyone at ScienceUtsav & ABIC STEM Lab.</div>
                </div>
            </div>
            
            <div class="su-footer-copy">
                © 2026-27 Aditya Birla Intermediate College & ScienceUtsav
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="su-form-box">', unsafe_allow_html=True)
        st.markdown('<div class="su-form-heading">Welcome back</div>', unsafe_allow_html=True)
        st.markdown('<div class="su-form-subtext">Sign in with the username and password you were given.</div>', unsafe_allow_html=True)
        
        username = st.text_input("USERNAME", placeholder="shashankverma.teachers or guest", key="su_user")
        password = st.text_input("PASSWORD", type="password", placeholder="••••••••••••", key="su_pass")
        
        login_btn = st.button("Sign in", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if login_btn:
            u_clean = username.strip().lower()
            p_clean = password.strip()
            
            # Check Admin SPOC Credentials
            if (u_clean in [ADMIN_USER.lower(), "shashankverma.teachers", "shashnakverma.teachers"]) and (p_clean in VALID_PASSWORDS or p_clean == "password123"):
                st.session_state["is_authenticated"] = True
                st.session_state["user_role"] = "Admin"
                st.toast("✅ Signed in as Lab Coordinator / SPOC", icon="🔬")
                st.rerun()
            # Guest / Student View Login (Zero Password or guest)
            elif u_clean in ["guest", "student", "viewer"] or (u_clean == "" and p_clean == ""):
                st.session_state["is_authenticated"] = True
                st.session_state["user_role"] = "Viewer"
                st.toast("✅ Signed in as Student / Public Viewer", icon="🎓")
                st.rerun()
            else:
                st.error("❌ Invalid username or password. Please try again.")

# ----------------- SQLITE & ALL OTHER DATA FUNCS (UNCHANGED) -----------------
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
    """)
    df_tt = get_timetable_df().drop(columns=["id"])
    st.dataframe(df_tt, use_container_width=True, hide_index=True)

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
            if val:
                return val
    return DEFAULT_CONFIGS.get(file_path, "")

def save_url(file_path, url):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(url.strip())

@st.cache_data(ttl=60)
def fetch_google_sheet_data_cached(sheet_url):
    try:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
        if not match:
            return None, "Invalid Google Sheet link."
        sheet_id = match.group(1)
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(csv_url, dtype=str).fillna("")
        return df, None
    except Exception as e:
        return None, str(e)

# ----------------- ATTENDANCE & SAFETY READERS -----------------
def init_all_data_structures():
    if not os.path.exists(STUDENT_ATTENDANCE_FILE):
        pd.DataFrame(columns=["Month", "Week", "Date", "Day", "Class & Section", "Total Students", "Period 1", "Period 2", "Total Present", "Total Absent"]).to_csv(STUDENT_ATTENDANCE_FILE, index=False)
    if not os.path.exists(TEACHER_ATTENDANCE_FILE):
        pd.DataFrame(columns=["Month", "Week", "Date", "Day", "S.No.", "Teacher Name", "Class & Section Taught", "Period / Time Slot", "Lab Activity / Topic Covered", "Total Present Students", "In-Time", "Out-Time", "Teacher Signature"]).to_csv(TEACHER_ATTENDANCE_FILE, index=False)
    if not os.path.exists(SAFETY_CHECKLIST_FILE):
        pd.DataFrame(columns=["Month", "Week", "Date", "S.No.", "Safety Parameter / Check Item", "Status", "Remarks"]).to_csv(SAFETY_CHECKLIST_FILE, index=False)
    if not os.path.exists(MAINTENANCE_DAILY_FILE):
        pd.DataFrame(columns=["Month", "Week", "Date", "Workstation / Area", "Safai Check (Dusting / Scraps)", "Equipment Check (Tools in place)", "Power Switch OFF", "Checked By", "Remarks"]).to_csv(MAINTENANCE_DAILY_FILE, index=False)
    if not os.path.exists(MAINTENANCE_DEEP_FILE):
        pd.DataFrame(columns=["Month", "Week", "Date", "S.No.", "Parameter / Deep Task", "Frequency", "Status", "Action Taken / Remarks", "Verified By"]).to_csv(MAINTENANCE_DEEP_FILE, index=False)
    if not os.path.exists(MAINTENANCE_BREAKDOWN_FILE):
        pd.DataFrame(columns=["Month", "Week", "Date Reported", "S.No.", "Equipment / Tool Name", "Problem / Issue", "Action Required", "Status", "Date Resolved", "Remarks"]).to_csv(MAINTENANCE_BREAKDOWN_FILE, index=False)

init_all_data_structures()

def get_student_attendance_all():
    return pd.read_csv(STUDENT_ATTENDANCE_FILE, dtype=str).fillna("")

def get_teacher_attendance_all():
    return pd.read_csv(TEACHER_ATTENDANCE_FILE, dtype=str).fillna("")

def render_student_excel():
    possible_paths = [
        "LMS STUDENT DATA.xlsx", "LMS STUDENT DATA.xls", "LMS STUDENT DATA.csv",
        os.path.join(DATA_DIR, "LMS STUDENT DATA.xlsx"),
    ]
    found_file = next((p for p in possible_paths if os.path.exists(p)), None)
    if found_file:
        try:
            ext = os.path.splitext(found_file)[1].lower()
            df = pd.read_csv(found_file) if ext == ".csv" else pd.read_excel(found_file)
            st.markdown(f"### 👨‍🎓 Registered Student Database (Total: {len(df)} Students)")
            class_col = next((c for c in df.columns if "class" in str(c).lower()), None)
            if class_col:
                unique_classes = ["All Classes"] + sorted([str(x) for x in df[class_col].dropna().unique()])
                sel_class = st.selectbox("Filter by Class:", unique_classes)
                df_disp = df[df[class_col].astype(str) == sel_class] if sel_class != "All Classes" else df
            else:
                df_disp = df
            st.dataframe(df_disp, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.info("ℹ️ Student database file 'LMS STUDENT DATA.xlsx' is safe and ready to be loaded.")

# ----------------- MAIN PORTAL AFTER LOGIN -----------------
def render_main_dashboard():
    # Top Navbar & Sign-out
    c_head1, c_head2 = st.columns([8, 2])
    with c_head1:
        st.title("🔬 ABIC STEM Innovation & Learning Lab")
        st.caption(f"Role: **{st.session_state['user_role']}** | Academic Session 2026-27")
    with c_head2:
        st.write("")
        if st.button("🚪 Sign Out", key="top_sign_out"):
            st.session_state["is_authenticated"] = False
            st.session_state["user_role"] = None
            st.rerun()

    tab_overview, tab_students, tab_timetable, tab_scienceutsav = st.tabs([
        "📁 49-Parameters Repository", "👨‍🎓 2000+ Students Data", "⏰ Master Timetable", "🌐 ScienceUtsav Live LMS"
    ])

    with tab_overview:
        st.subheader("📑 Lab Modules & Activity Records")
        for section_name, items in CATEGORIES.items():
            with st.expander(section_name, expanded=False):
                for sno, title in items:
                    st.write(f"**#{sno}. {title}**")

    with tab_students:
        render_student_excel()

    with tab_timetable:
        render_timetable_view()

    with tab_scienceutsav:
        st.subheader("ScienceUtsav Classroom Assessment Portal")
        su_url = get_saved_url(SCIENCEUTSAV_CONFIG_FILE)
        components.iframe(su_url, height=750, scrolling=True)

# ----------------- APP RUNNER ROUTE -----------------
if not st.session_state.get("is_authenticated", False):
    render_scienceutsav_login_page()
else:
    render_main_dashboard()
