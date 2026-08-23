import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import streamlit.components.v1 as components

try:
    import pypdfium2 as pdfium
    PDFIUM_AVAILABLE = True
except ImportError:
    PDFIUM_AVAILABLE = False

st.set_page_config(page_title="ABIC STEM Lab Portal", page_icon="🔬", layout="wide")

# ----------------- STRICT INTERNAL BUTTON LEFT ALIGNMENT CSS -----------------
st.markdown("""
<style>
div[data-testid="stButton"] button {
    justify-content: flex-start !important;
    text-align: left !important;
    align-items: center !important;
    display: flex !important;
    width: 100% !important;
    padding: 10px 16px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    border: 1px solid #d0d7de !important;
    background-color: #f6f8fa !important;
    color: #1f2328 !important;
    margin-bottom: 2px !important;
}

div[data-testid="stButton"] button div,
div[data-testid="stButton"] button p,
div[data-testid="stButton"] button span,
div[data-testid="stButton"] button div[data-testid="stMarkdownContainer"] {
    text-align: left !important;
    justify-content: flex-start !important;
    align-items: center !important;
    display: flex !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="stButton"] button:hover {
    background-color: #eaeef2 !important;
    border-color: #0969da !important;
    color: #0969da !important;
}

div[data-testid="stButton"] button:focus {
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

UPLOAD_DIR = "stem_lab_records"
DATA_DIR = "portal_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

STUDENT_ATTENDANCE_FILE = os.path.join(DATA_DIR, "student_attendance.csv")
TEACHER_ATTENDANCE_FILE = os.path.join(DATA_DIR, "teacher_attendance.csv")
PRINCIPAL_MSG_FILE = os.path.join(DATA_DIR, "principal_message.txt")
SHEET_CONFIG_FILE = os.path.join(DATA_DIR, "gsheet_url.txt")
FORM_CONFIG_FILE = os.path.join(DATA_DIR, "gform_url.txt")
SCIENCEUTSAV_CONFIG_FILE = os.path.join(DATA_DIR, "scienceutsav_url.txt")

MONTHS = ["April", "May", "June", "July", "August", "September", "October", "November", "December", "January", "February", "March"]
WEEKS = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

if "active_viewer_sno" not in st.session_state:
    st.session_state["active_viewer_sno"] = 1

if "active_admin_sno" not in st.session_state:
    st.session_state["active_admin_sno"] = None

def get_current_indices():
    now = datetime.now()
    cur_month_name = now.strftime("%B")
    cur_week_num = min(5, ((now.day - 1) // 7) + 1)
    cur_week_name = f"Week {cur_week_num}"

    month_idx = MONTHS.index(cur_month_name) if cur_month_name in MONTHS else 0
    week_idx = WEEKS.index(cur_week_name) if cur_week_name in WEEKS else 0
    return month_idx, week_idx

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

def get_saved_url(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def save_url(file_path, url):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(url.strip())

def fetch_google_sheet_data(sheet_url):
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

def sync_data_from_google_sheet():
    sheet_url = get_saved_url(SHEET_CONFIG_FILE)
    if not sheet_url:
        return False, "Google Sheet URL not configured."
    df_raw, err = fetch_google_sheet_data(sheet_url)
    if err or df_raw is None or df_raw.empty:
        return False, err if err else "Google Sheet is empty."

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
            month_name = dt.strftime("%B") if pd.notnull(dt) else "August"
            week_num = min(5, ((dt.day - 1) // 7) + 1) if pd.notnull(dt) else 1
            week_name = f"Week {week_num}"
            if not raw_day and pd.notnull(dt):
                raw_day = dt.strftime("%A")
        except Exception:
            month_name = "August"
            week_name = "Week 1"

        st_match_idx = df_st_all[
            (df_st_all["Month"] == month_name) & 
            (df_st_all["Week"] == week_name) & 
            (df_st_all["Class & Section"] == raw_class)
        ].index

        new_st_row = {
            "Month": month_name, "Week": week_name, "Date": raw_date.split(" ")[0],
            "Day": raw_day, "Class & Section": raw_class, "Total Students": raw_tot,
            "Period 1": raw_period, "Period 2": "", "Total Present": raw_pres, "Total Absent": raw_abs
        }

        if len(st_match_idx) > 0:
            for k, v in new_st_row.items():
                df_st_all.loc[st_match_idx[0], k] = v
        else:
            df_st_all = pd.concat([df_st_all, pd.DataFrame([new_st_row])], ignore_index=True)

        tc_match_idx = df_tc_all[
            (df_tc_all["Month"] == month_name) & 
            (df_tc_all["Week"] == week_name) & 
            (df_tc_all["Teacher Name"] == raw_teacher)
        ].index

        new_tc_row = {
            "Month": month_name, "Week": week_name, "Date": raw_date.split(" ")[0],
            "Day": raw_day, "S.No.": str(len(df_tc_all) + 1), "Teacher Name": raw_teacher,
            "Class & Section Taught": raw_class, "Period / Time Slot": raw_period,
            "Lab Activity / Topic Covered": raw_topic, "Total Present Students": raw_pres,
            "In-Time": raw_in, "Out-Time": raw_out, "Teacher Signature": "Verified"
        }

        if len(tc_match_idx) > 0:
            for k, v in new_tc_row.items():
                df_tc_all.loc[tc_match_idx[0], k] = v
        else:
            df_tc_all = pd.concat([df_tc_all, pd.DataFrame([new_tc_row])], ignore_index=True)

    df_st_all.to_csv(STUDENT_ATTENDANCE_FILE, index=False)
    df_tc_all.to_csv(TEACHER_ATTENDANCE_FILE, index=False)
    return True, f"Successfully synced {len(df_raw)} records!"

def render_cover_photo():
    possible_covers = [
        "cover photo.jpg", "cover photo.png", "cover photo.jpeg", "cover photo.webp",
        os.path.join(DATA_DIR, "cover photo.jpg"), os.path.join(DATA_DIR, "cover photo.png")
    ]
    found = next((c for c in possible_covers if os.path.exists(c)), None)
    if found:
        st.image(found, use_container_width=True)

def get_principal_message():
    if os.path.exists(PRINCIPAL_MSG_FILE):
        with open(PRINCIPAL_MSG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return """**Principal's Desk:**
"Our STEM Innovation & Learning Laboratory is dedicated to nurturing scientific curiosity, critical problem-solving skills, and experiential innovation among our students. We encourage all learners to explore technology, build creative models, and lead the technical advancements of tomorrow."

— **Principal, Aditya Birla Intermediate College, Renukoot**"""

def save_principal_message(msg):
    with open(PRINCIPAL_MSG_FILE, "w", encoding="utf-8") as f:
        f.write(msg)

def render_principal_message():
    st.info(get_principal_message())

def init_student_attendance():
    if not os.path.exists(STUDENT_ATTENDANCE_FILE):
        structure = {
            "Month": [], "Week": [], "Date": [], "Day": [], "Class & Section": [],
            "Total Students": [], "Period 1": [], "Period 2": [], "Total Present": [], "Total Absent": []
        }
        pd.DataFrame(structure).to_csv(STUDENT_ATTENDANCE_FILE, index=False)

def init_teacher_attendance():
    if not os.path.exists(TEACHER_ATTENDANCE_FILE):
        structure = {
            "Month": [], "Week": [], "Date": [], "Day": [], "S.No.": [],
            "Teacher Name": [], "Class & Section Taught": [], "Period / Time Slot": [],
            "Lab Activity / Topic Covered": [], "Total Present Students": [],
            "In-Time": [], "Out-Time": [], "Teacher Signature": []
        }
        pd.DataFrame(structure).to_csv(TEACHER_ATTENDANCE_FILE, index=False)

init_student_attendance()
init_teacher_attendance()

def get_student_attendance_all():
    try:
        return pd.read_csv(STUDENT_ATTENDANCE_FILE, dtype=str).fillna("")
    except Exception:
        init_student_attendance()
        return pd.read_csv(STUDENT_ATTENDANCE_FILE, dtype=str).fillna("")

def get_student_attendance_for_slot(month, week):
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
        init_teacher_attendance()
        return pd.read_csv(TEACHER_ATTENDANCE_FILE, dtype=str).fillna("")

def get_teacher_attendance_for_slot(month, week):
    df_all = get_teacher_attendance_all()
    if not df_all.empty and {"Month", "Week", "Date", "Day"}.issubset(set(df_all.columns)):
        filtered = df_all[(df_all["Month"] == str(month)) & (df_all["Week"] == str(week))]
        if not filtered.empty:
            return filtered.drop(columns=[c for c in ["Month", "Week"] if c in filtered.columns])
    return pd.DataFrame({
        "Date": ["" for _ in TEACHERS_LIST], "Day": ["" for _ in TEACHERS_LIST],
        "S.No.": list(range(1, len(TEACHERS_LIST) + 1)), "Teacher Name": TEACHERS_LIST,
        "Class & Section Taught": ["" for _ in TEACHERS_LIST], "Period / Time Slot": ["" for _ in TEACHERS_LIST],
        "Lab Activity / Topic Covered": ["" for _ in TEACHERS_LIST], "Total Present Students": ["" for _ in TEACHERS_LIST],
        "In-Time": ["" for _ in TEACHERS_LIST], "Out-Time": ["" for _ in TEACHERS_LIST],
        "Teacher Signature": ["" for _ in TEACHERS_LIST]
    })

def save_teacher_attendance_slot(month, week, edited_df):
    df_all = get_teacher_attendance_all()
    edited_df = edited_df.copy()
    edited_df["Month"] = str(month)
    edited_df["Week"] = str(week)
    df_remaining = df_all[~((df_all["Month"] == str(month)) & (df_all["Week"] == str(week)))] if not df_all.empty else pd.DataFrame()
    pd.concat([df_remaining, edited_df], ignore_index=True).to_csv(TEACHER_ATTENDANCE_FILE, index=False)

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
                    st.image(pdf[page_num].render(scale=2).to_pil(), caption=f"Page {page_num + 1} of {len(pdf)}", use_container_width=True)
            except Exception:
                pass
        with open(file_path, "rb") as f:
            st.download_button(f"📥 Download / Open PDF ({file_name})", data=f.read(), file_name=file_name, mime="application/pdf", key=f"dl_pdf_{unique_key}")
    elif ext in [".mp4", ".mov", ".avi", ".mkv"]:
        st.video(file_path)
    else:
        with open(file_path, "rb") as f:
            st.download_button(f"📥 Download File ({file_name})", data=f.read(), file_name=file_name, key=f"dl_doc_{unique_key}")

def get_existing_files_for_parameter(sno, title):
    folder_candidates = [
        f"{sno:02d}_{title.replace(' ', '_').replace('/', '_')}",
        f"{(sno+1):02d}_{title.replace(' ', '_').replace('/', '_')}",
        f"{(sno-1):02d}_{title.replace(' ', '_').replace('/', '_')}",
        title.replace(' ', '_').replace('/', '_')
    ]
    all_files = []
    for cand in folder_candidates:
        cand_dir = os.path.join(UPLOAD_DIR, cand)
        if os.path.exists(cand_dir):
            for f in os.listdir(cand_dir):
                full_path = os.path.join(cand_dir, f)
                if os.path.isfile(full_path) and (full_path, f) not in all_files:
                    all_files.append((full_path, f))
    return all_files

# ----------------- 49 MASTER CATEGORIES CONFIGURATION -----------------
CATEGORIES = {
    "1. Administration & Planning": [
        (1, "STEM Lab Profile"), (2, "Lab Objectives & Guidelines"), (3, "Coordinator / SPOC Details"),
        (4, "Monthly / Annual STEM Activity Plan"), (5, "Class-wise Timetable"),
        (6, "Session / Lesson Plans"), (7, "Student List"), (8, "Student Attendance"), (9, "Teacher Attendance"),
    ],
    "2. Inventory & Safety": [
        (10, "Lab Inventory"), (11, "Equipment Details"), (12, "Equipment Photos"),
        (13, "Equipment Purchase Records"), (14, "Maintenance Records"), (15, "Lab Safety Rules"), (16, "Safety Checklist"),
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

def get_folder_name(sno, title):
    return f"{sno:02d}_{title.replace(' ', '_').replace('/', '_')}"

# ----------------- MASTER CONTENT DISPATCHER (ZERO DATA LOSS) -----------------
ANNUAL_PLAN_DATA = [
    {"Month": "July 2026", "Session #": "Session 1", "Class 6": "Intro to Robotics & Arduino IDE setup", "Class 7": "Microcontroller Recap & Sensor Safety", "Class 8": "Advanced Programming Architecture", "Class 9": "Multi-Sensor System Architecture & I/O", "Milestone": "Erehwon Phase 1: Team Formation (25+ Teams across Classes 6-9; 5-6 members each). Role allocation & Lab Logbooks initiated.", "Roles": "Team Lead & Problem Scout"},
    {"Month": "July 2026", "Session #": "Session 2", "Class 6": "Digital Pins & LED Blink Logic", "Class 7": "Tilt Switch Basics & Angle Alerts", "Class 8": "7-Segment / LCD Interface Basics", "Class 9": "Data Fusion & Complex Logic Loops", "Milestone": "Problem Discovery: Community, school campus & environmental pain point identification.", "Roles": "Problem Scout & QA Tester"},
    {"Month": "August 2026", "Session #": "Session 3", "Class 6": "Switches & Pull-up/Pull-down Logic", "Class 7": "Tilt Safety System Integration", "Class 8": "Digital Display Logic & Variables", "Class 9": "Capstone Planning & BOM Setup", "Milestone": "MILESTONE 1: Submission & approval of 25+ validated Problem Statements & Bill of Materials (BOM).", "Roles": "Team Lead & Circuit Engineer"},
    {"Month": "August 2026", "Session #": "Session 4", "Class 6": "Potentiometer & Analog Read Values", "Class 7": "Magnetic Detection & Hall Effect Intro", "Class 8": "Sensor-Driven Counting Algorithms", "Class 9": "Modular Subsystem Design & Pin Mapping", "Milestone": "Ideation & Architecture: System block diagrams, circuit schematics & hardware flowcharts.", "Roles": "Firmware Programmer & Casing Designer"},
    {"Month": "September 2026", "Session #": "Session 5", "Class 6": "Light Sensing (LDR) & Thresholds", "Class 7": "Hall Logic & Contactless Switches", "Class 8": "Touch Sensors & Capacitive Switching", "Class 9": "Interfacing Multi-Sensor Arrays", "Milestone": "Low-Fidelity Prototyping: Breadboard wiring & sensor threshold calibration.", "Roles": "Circuit Engineer & QA Tester"},
    {"Month": "September 2026", "Session #": "Session 6", "Class 6": "Auto Lighting System Integration", "Class 7": "IR Object Detection Fundamentals", "Class 8": "RGB Modulation via PWM Logic", "Class 9": "Multi-Actuator Output Orchestration", "Milestone": "MILESTONE 2: Low-Fidelity Prototype Walkthrough (Breadboards functional + cardboard mockups).", "Roles": "Casing Designer & Programmer"},
    {"Month": "October 2026", "Session #": "Session 7", "Class 6": "Sound Reactive System & Mic Modules", "Class 7": "IR Threshold Tuning & Alerts", "Class 8": "Laser Optical Transceivers & LDRs", "Class 9": "Code Integration & State Machine Coding", "Milestone": "Mid-Term Assembly: Combining sensors with actuators (servos, buzzers, multi-stage displays).", "Roles": "Firmware Programmer & Circuit Engineer"},
    {"Month": "October 2026", "Session #": "Session 8", "Class 6": "Acoustic Threshold Noise Alerts", "Class 7": "Servo Motor Motion & PWM (0°-180°)", "Class 8": "Multi-Trigger Security (AND/OR Logic)", "Class 9": "Smart System Capstone Integration (Pt 1)", "Milestone": "Logic Debugging: State machine loops, sensor conflict resolution & power distribution.", "Roles": "Programmer & QA Tester"},
    {"Month": "November 2026", "Session #": "Session 9", "Class 6": "Multi-LED Logic & Gated Alerts", "Class 7": "Automated IR + Servo Barrier System", "Class 8": "Subsystem Integration & Wire Looms", "Class 9": "Smart System Capstone Integration (Pt 2)", "Milestone": "High-Fidelity Packaging: Enclosure fabrication (acrylic/wood/cardboard) and cable looming.", "Roles": "Casing Designer & Circuit Engineer"},
    {"Month": "November 2026", "Session #": "Session 10", "Class 6": "System Testing & Breadboard Cleanup", "Class 7": "Enclosure Packaging & Assembly", "Class 8": "Edge Case Handling & Debounce Code", "Class 9": "Full System Field Testing & Telemetry", "Milestone": "MILESTONE 3: Alpha Working Prototype Demonstration in Lab under simulated operating conditions.", "Roles": "All 5-6 Team Members"},
    {"Month": "December 2026", "Session #": "Session 11", "Class 6": "Prototype Stress Testing & Debugging", "Class 7": "Mechanical Reliability & Power Checks", "Class 8": "System Stress Testing (100+ Cycles)", "Class 9": "Code Optimization & Fail-Safe Logic", "Milestone": "Stress Testing & Data Logging: 50-100 continuous test cycles, fail-safe verification & reliability audit.", "Roles": "QA Tester & Programmer"},
    {"Month": "December 2026", "Session #": "Session 12", "Class 6": "Presentation Skills & Pitch Deck Basics", "Class 7": "Project Report & Technical Schematics", "Class 8": "Pitch Scripting & Demo Storyboarding", "Class 9": "Comprehensive Engineering Dossier", "Milestone": "Documentation & Scripting: 1-Page Project Dossier, complete schematics, BOM and pitch script.", "Roles": "Pitch Lead & Team Lead"},
    {"Month": "January 2027", "Session #": "Session 13", "Class 6": "Internal Qualifying Pitch & Demo", "Class 7": "Internal Jury Evaluation & Feedback", "Class 8": "Pre-Competition Mock Presentation", "Class 9": "Grand Internal Capstone Defense", "Milestone": "School-Level Qualifying Round: 3-minute live pitch + 2-minute live hardware demonstration for all 25+ teams.", "Roles": "Pitch Lead & Full Team"},
    {"Month": "January 2027", "Session #": "Session 14", "Class 6": "Video Production & Competition Entry", "Class 7": "Final Video Shoot & Erehwon Upload", "Class 8": "Video Asset Rendering & Submission", "Class 9": "Final Portal Submission & Lab Archive", "Milestone": "MILESTONE 4: Final 2-Minute Demonstration Video Shoot & Official National Submission to Erehwon Competition Portal.", "Roles": "All 5-6 Team Members"}
]

LESSON_PLANS_DB = {
    "Class 6": [
        ("Session 1 (01-15 July 2026)", "Intro to Robotics & Arduino IDE setup with Sensor Shield", "Mount shield on Arduino Uno; flash BareMinimum sketch; setup 5-6 member teams and assign roles.", "1. Robotics anatomy, Arduino IDE, mounting Breakout Shield, G-V-S headers.\n2. Sensor Shield G-V-S pinout safety (Ground-Black, VCC-Red, Signal-Yellow).\n3. Code syntax: setup(), loop(), pinMode(), digitalRead/Write, analogRead().\n4. Erehwon Track: Campus problem discovery and functional prototyping.", "Arduino Uno, Sensor Shield V5.0, USB cables, PCs with Arduino IDE.", "Continuous Lab Evaluation (10M): Shield mounting & wiring hygiene (3M), Functional code execution (4M), Logbook documentation (3M)."),
        ("Session 2 (16-31 July 2026)", "LED, Digital Pins & Blink Logic on Shield", "Connect 3-pin LED module to Pin 13 of shield; modify blink delay; identify school energy waste issues.", "1. Digital output logic, LED module interfacing on Digital Pin 13 header.\n2. Sensor Shield G-V-S pinout safety.\n3. Delay modification and loop frequency.", "Arduino Uno, Sensor Shield, 3-pin LED module, 3-pin ribbon cables.", "Lab Evaluation (10M): Circuit wiring (3M), Code modification (4M), Logbook (3M)."),
        ("Session 3 (01-15 August 2026)", "Push Buttons & Digital Input Switching", "Plug 3-pin button module into Pin 2; code manual LED toggle; finalize 6-7 team Problem Statements.", "1. Digital inputs, pull-up vs pull-down, tactile button module on Pin 2.\n2. Software debouncing fundamentals.\n3. Erehwon Problem Statement validation.", "Arduino Uno, Sensor Shield, Push Button module, LED module.", "Lab Evaluation (10M): Input logic execution (4M), Wiring (3M), Logbook (3M)."),
        ("Session 4 (16-31 August 2026)", "Potentiometers & Analog Input Reading", "Connect Potentiometer to Analog Pin A0; read variable voltage on Serial Monitor; design variable brightness indicator.", "1. Analog signals, ADC (0-1023), 3-pin Potentiometer module on A0.\n2. Serial baud rate and data plotting.\n3. Mapping analog input to PWM output.", "Arduino Uno, Sensor Shield, Potentiometer module, LED module.", "Lab Evaluation (10M): Analog reading calibration (4M), Wiring (3M), Logbook (3M)."),
        ("Session 5 (01-15 September 2026)", "Light Sensing (LDR) & Threshold Calibration", "Calibrate LDR sensor module on Pin A0; log Lux values in bright/dark states; draft block diagram.", "1. Photoresistor physics, 3-pin LDR module on A0, ambient light thresholds.\n2. Calibrating sensory trigger points.\n3. Block diagram drafting.", "Arduino Uno, Sensor Shield, LDR module, Torch/Flashlight.", "Lab Evaluation (10M): Sensor calibration (4M), Wiring (3M), Logbook (3M)."),
        ("Session 6 (16-30 September 2026)", "Auto Lighting System & Miniature Post Assembly", "Build automated street lighting model; package Arduino+Shield inside cardboard post; test shadow activation.", "1. Automated night lighting logic, conditional IF/ELSE, relay/LED output.\n2. Enclosure assembly with cardboard chassis.\n3. Milestone 2: Low-Fidelity Prototype Walkthrough.", "Arduino Uno, Sensor Shield, LDR module, High-power LED, Cardboard chassis.", "Lab Evaluation (10M): Automated trigger (4M), Packaging (3M), Logbook (3M)."),
        ("Session 7 (01-15 October 2026)", "Sound Reactive System & Microphone Sensors", "Plug sound sensor into shield; code sound-reactive LED flash; observe classroom noise levels.", "1. Acoustic detection, sound sensor module on A1/D3, noise threshold tuning.\n2. Microphone comparator sensitivity adjustment.\n3. Classroom acoustic analysis.", "Arduino Uno, Sensor Shield, Sound Sensor module, LED module.", "Lab Evaluation (10M): Noise threshold tuning (4M), Wiring (3M), Logbook (3M)."),
        ("Session 8 (16-31 October 2026)", "Acoustic Alert & Smart Noise Warning Indicator", "Assemble Smart Noise Monitor (Sound module + RGB LED + Buzzer); test alert at loud decibel threshold.", "1. Sound threshold triggers, buzzer integration on Pin 8, noise alert logic.\n2. Audio-visual alarm sequencing.\n3. Enclosure integration.", "Arduino Uno, Sensor Shield, Sound module, RGB LED, Active Buzzer.", "Lab Evaluation (10M): Multi-actuator execution (4M), Wiring (3M), Logbook (3M)."),
        ("Session 9 (01-15 November 2026)", "Multi-LED Logic & Campus Security Triggers", "Wire 3-pin Red/Yellow/Green LED modules to pins 11, 12, 13 on shield; program automated status sequencing.", "1. Gated multi-output indicators, traffic/corridor status indicators.\n2. Multi-channel state sequencing.\n3. Erehwon High-Fidelity Packaging initiation.", "Arduino Uno, Sensor Shield, 3x LED modules (R/Y/G), Ribbon cables.", "Lab Evaluation (10M): Sequencing logic (4M), Wiring (3M), Logbook (3M)."),
        ("Session 10 (16-30 November 2026)", "System Enclosure & Alpha Prototype Assembly", "Alpha prototype demo: Install automated corridor light/noise monitor inside scale chassis; verify operation.", "1. Packaging Arduino + Shield inside rigid cardboard housing, cable looming.\n2. Milestone 3: Alpha Working Prototype Demonstration.\n3. System reliability check.", "Arduino Uno, Sensor Shield, Full Sensor Setup, Scale Cardboard Chassis.", "Lab Evaluation (10M): Alpha Prototype functioning (5M), Enclosure (3M), Logbook (2M)."),
        ("Session 11 (01-15 December 2026)", "Prototype Stress Testing & Data Logging", "Run 30 test cycles of automatic light/noise trigger; record response latency in QA Test Log.", "1. Reliability testing over 30 cycles, sensor drift check, loose wire inspection.\n2. QA logging and response time measurement.\n3. Failure mode analysis.", "Arduino Uno, Sensor Shield, Assembled Prototype, QA Test Sheets.", "Lab Evaluation (10M): Stress test consistency (4M), QA log (4M), Wiring (2M)."),
        ("Session 12 (16-31 December 2026)", "Presentation Skills & 1-Page Pitch Dossier", "Draft 1-page project brief; prepare slide deck with team photos, problem definition, and bill of materials.", "1. Drafting problem-solution narrative, circuit schematic sketching, slide design.\n2. 1-Page Project Dossier compiling.\n3. Pitch rehearsal.", "PCs, Projector, Engineering Logbooks, Slide templates.", "Lab Evaluation (10M): Project Dossier quality (5M), Slide deck (3M), Pitch trial (2M)."),
        ("Session 13 (01-15 January 2027)", "Internal Qualifying Pitch & Demo", "Live demonstration of all 6-7 Class 6 prototypes before school jury; receive feedback for final polishing.", "1. 3-minute live pitch, working hardware demo, answering faculty jury Q&A.\n2. Jury evaluation and live scoring.\n3. Post-pitch feedback implementation.", "Completed Prototypes, Projector, Jury Scorecards.", "Qualifying Pitch Score (10M): Hardware autonomy (4M), Oral defense (4M), Teamwork (2M)."),
        ("Session 14 (16-31 January 2027)", "Final Video Shoot & Erehwon Upload", "Record 2-minute project demo video; upload code, schematic, and report to Erehwon competition portal.", "1. Video recording, structured demonstration, uploading files to Erehwon portal.\n2. Final Lab repository archiving.\n3. Milestone 4 National Submission.", "Smartphones/Camera, Clean Demo Setup, Erehwon Portal Access.", "Lab Evaluation (10M): Video demo quality (5M), Portal submission compliance (5M).")
    ],
    "Class 7": [
        ("Session 1 (01-15 July 2026)", "Microcontroller Safety & Sensor Shield Architecture", "Inspect Arduino Uno + Shield; map 3-pin ports; form 5-6 member teams; scout public safety issues.", "1. Breakout Shield power distribution, 3-pin G-V-S bus, sensor protection.\n2. External power terminals for high-current actuators.\n3. Team charter setup.", "Arduino Uno, Sensor Shield, Multimeter, Power Supply.", "Lab Evaluation (10M): Shield mapping (3M), Safety compliance (4M), Logbook (3M)."),
        ("Session 2 (16-31 July 2026)", "Tilt Safety Sensors & Angular Threshold Logic", "Plug Tilt module into shield; write angle-deviation detection code; observe two-wheeler tilt hazards.", "1. Tilt switches, angular displacement detection, 3-pin Tilt module on D2.\n2. Digital state debounce for mechanical switches.\n3. Hazard alert logic.", "Arduino Uno, Sensor Shield, Tilt module, LED module.", "Lab Evaluation (10M): Tilt trigger logic (4M), Wiring (3M), Logbook (3M)."),
        ("Session 3 (01-15 August 2026)", "Tilt Safety System & Emergency Audio Alert", "Assemble Tilt Warning Rig (Tilt module + Buzzer on shield); test emergency trigger at 45° angle; finalize Problem Charters.", "1. Pulsed buzzer alarm logic, tilt stability integration, safety enclosures.\n2. Milestone 1: Problem Statement & BOM finalization.\n3. Audio pitch modulation.", "Arduino Uno, Sensor Shield, Tilt Sensor, Active Buzzer, LED.", "Lab Evaluation (10M): Alarm integration (4M), BOM setup (3M), Logbook (3M)."),
        ("Session 4 (16-31 August 2026)", "Magnetic Detection & Hall Effect Fundamentals", "Connect 3-pin Hall Sensor to Pin 3; test neodymium magnet approach; draft schematics for contactless safety latches.", "1. Lorentz force, A3144 Hall Effect module, magnetic proximity detection.\n2. Contactless switching physics.\n3. Schematics drafting.", "Arduino Uno, Sensor Shield, Hall Effect Sensor, Neodymium magnets.", "Lab Evaluation (10M): Hall sensor calibration (4M), Wiring (3M), Logbook (3M)."),
        ("Session 5 (01-15 September 2026)", "Hall Logic & Contactless Window/Door Security", "Build Contactless Door/Window Alarm using Hall module + LED/Buzzer on shield; verify trigger gap (2mm-15mm).", "1. Open-collector switching, pull-up logic, contactless door alarm.\n2. Air-gap calibration and false-trigger prevention.\n3. Security latch integration.", "Arduino Uno, Sensor Shield, Hall Sensor, Buzzer, Mock Door frame.", "Lab Evaluation (10M): Trigger gap precision (4M), Wiring (3M), Logbook (3M)."),
        ("Session 6 (16-30 September 2026)", "IR Proximity & Object Detection Principles", "Connect 3-pin IR Obstacle module to shield; calibrate detection distance (2cm-20cm); design gate mockups.", "1. IR emitter-receiver pair, onboard comparator potentiometer tuning, D4 input.\n2. Milestone 2: Low-Fidelity Prototype Walkthrough.\n3. Ambient IR noise rejection.", "Arduino Uno, Sensor Shield, IR Obstacle module, Cardboard gate mockup.", "Lab Evaluation (10M): Distance calibration (4M), Mockup (3M), Logbook (3M)."),
        ("Session 7 (01-15 October 2026)", "IR Threshold Tuning & Anti-Collision Alerts", "Wire IR module + multi-tone Buzzer; code anti-collision hallway alert; test with moving objects.", "1. Proximity alert logic, multi-stage distance warnings, buzzer frequencies.\n2. Dynamic response testing with moving obstacles.\n3. Hallway safety prototyping.", "Arduino Uno, Sensor Shield, IR Module, Multi-tone Buzzer, LEDs.", "Lab Evaluation (10M): Anti-collision logic (4M), Wiring (3M), Logbook (3M)."),
        ("Session 8 (16-31 October 2026)", "Servo Motor Motion & PWM Angular Control (0°-180°)", "Plug SG90 servo into dedicated Servo port on shield; write angular sweep code (0° to 90°); assemble cardboard linkage arm.", "1. TowerPro SG90 servo, 50Hz PWM signal, Servo.h library on PWM Pin 9.\n2. Mechanical linkage geometry.\n3. External 5V power stability.", "Arduino Uno, Sensor Shield, SG90 Servo, External battery box, Linkage arms.", "Lab Evaluation (10M): Servo sweep accuracy (4M), Linkage design (3M), Logbook (3M)."),
        ("Session 9 (01-15 November 2026)", "Automated IR + Servo Smart Barrier System", "Build Automated Barrier Gate: IR sensor triggers servo to lift barrier 90°, holds for 3s, and auto-closes; mount on base.", "1. Synchronized sensing and actuation, timed gate hold, auto-closure logic.\n2. Kinematic barrier balance.\n3. High-Fidelity packaging.", "Arduino Uno, Sensor Shield, IR Module, SG90 Servo, Gate Assembly.", "Lab Evaluation (10M): Automated gate loop (4M), Mechanical reliability (3M), Logbook (3M)."),
        ("Session 10 (16-30 November 2026)", "Enclosure Packaging & Alpha Model Assembly", "Alpha prototype demo: Complete mechanical casing for Smart Gate / Auto Dustbin; test stability.", "1. Mechanical housing, pivot stabilization, concealing shield and wires.\n2. Milestone 3: Alpha Working Prototype Demonstration.\n3. Structural rigidity.", "Arduino Uno, Sensor Shield, Full Rig, Rigid Cardboard/Acrylic housing.", "Lab Evaluation (10M): Alpha Prototype operation (5M), Housing (3M), Logbook (2M)."),
        ("Session 11 (01-15 December 2026)", "Mechanical Reliability & Power Surge Testing", "Execute 50 continuous automated cycles; verify servo does not cause board reset; log mechanical wear in QA sheet.", "1. Servo load testing, power decoupling, 50 continuous sweep cycles.\n2. Voltage dip check during servo stall.\n3. Mechanical wear logging.", "Arduino Uno, Sensor Shield, Automated Gate Rig, Multimeter, QA Sheet.", "Lab Evaluation (10M): 50-cycle reliability (4M), Power stability (4M), Logbook (2M)."),
        ("Session 12 (16-31 December 2026)", "Technical Schematics & Project Pitch Preparation", "Draft technical report and circuit diagrams; storyboard 2-minute video pitch narrative with team roles.", "1. Full circuit schematics, bill of materials, slide deck layout.\n2. Engineering dossier completion.\n3. Pitch presentation script.", "PCs, Schematics software/Paper, Presentation slides.", "Lab Evaluation (10M): Schematics accuracy (4M), Dossier completeness (4M), Pitch (2M)."),
        ("Session 13 (01-15 January 2027)", "Internal Qualifying Evaluation & Jury Defense", "Present working hardware prototype before school evaluation committee; implement jury feedback.", "1. 3-minute pitch, live automated gate demo, fault injection test by jury.\n2. Technical oral defense.\n3. Post-eval optimization.", "Completed Prototypes, Projector, Evaluation scorecards.", "Qualifying Defense Score (10M): Mechanism reliability (4M), Defense (4M), Teamwork (2M)."),
        ("Session 14 (16-31 January 2027)", "Final Video Production & Erehwon Portal Upload", "Record 2-minute demonstration video showing IR trigger and servo actuation; submit entry on Erehwon portal.", "1. HD video recording, voiceover narration, digital portfolio upload.\n2. Milestone 4 Final National Submission.\n3. Lab repository handover.", "Smartphones/Camera, Assembled Gate Rig, Erehwon Portal.", "Lab Evaluation (10M): Video clarity (5M), Portal submission verified (5M).")
    ],
    "Class 8": [
        ("Session 1 (01-15 July 2026)", "Advanced Programming Architecture & Shield I/O Banks", "Setup Arduino Uno + Shield; map analog/digital/I2C channels; form 5-6 member teams; scout access tracking problems.", "1. Arrays, state machines, shield I2C/UART ports, pin budgeting.\n2. I2C bus addressing.\n3. Team allocation for advanced security tracks.", "Arduino Uno, Sensor Shield, I2C scanner tools, PC.", "Lab Evaluation (10M): Shield mapping (3M), Architecture planning (4M), Logbook (3M)."),
        ("Session 2 (16-31 July 2026)", "7-Segment Display Architecture & Segment Mapping", "Connect 7-segment display module to digital pins 2-8; display digits 0-9 sequentially; draft project scope.", "1. Common cathode/anode pinouts, segment truth tables (a-g), 220Ω resistor protection.\n2. Bitwise display mapping.\n3. Project charter drafting.", "Arduino Uno, Sensor Shield, 7-Segment display module, Resistors.", "Lab Evaluation (10M): Segment code accuracy (4M), Wiring (3M), Logbook (3M)."),
        ("Session 3 (01-15 August 2026)", "Digital Counting Logic & Software Switch Debounce", "Build Digital Counter with 2 pushbuttons (Entry/Exit) and 7-segment display on shield; finalize Milestone 1 Problem Charter.", "1. Counter variables, debounce timing with millis(), increment/decrement.\n2. Milestone 1: Problem Statement & BOM approval.\n3. Edge detection logic.", "Arduino Uno, Sensor Shield, 7-Segment Display, 2x Push Buttons.", "Lab Evaluation (10M): Counter debouncing (4M), BOM setup (3M), Logbook (3M)."),
        ("Session 4 (16-31 August 2026)", "I2C LCD 16x2 Interface & Dedicated Shield I2C Port", "Plug I2C LCD directly into 4-pin I2C port on shield; initialize display at address 0x27; print live visitor count strings.", "1. I2C bus (SDA/SCL on A4/A5), LiquidCrystal_I2C library, LCD cursor control.\n2. Memory optimization on Uno.\n3. String formatting on LCD.", "Arduino Uno, Sensor Shield, 16x2 I2C LCD module, 4-pin cable.", "Lab Evaluation (10M): I2C communication (4M), Display logic (3M), Logbook (3M)."),
        ("Session 5 (01-15 September 2026)", "Capacitive Touch Sensing & Variable Switching", "Connect 3-pin Touch Sensor to Pin 4 and RGB LED to PWM Pins 9, 10, 11 on shield; program 3-stage touch-controlled dimmer.", "1. TTP223 Capacitive Touch module, digital touch states, PWM LED dimming.\n2. Touch state latching vs momentary.\n3. Dimming curves.", "Arduino Uno, Sensor Shield, TTP223 Touch module, RGB LED module.", "Lab Evaluation (10M): Touch dimming loop (4M), Wiring (3M), Logbook (3M)."),
        ("Session 6 (16-30 September 2026)", "RGB Color Modulation via PWM Logic", "Code multi-color warning beacon on shield (Green=Normal, Amber=Caution, Red=Alert); interface with touch button.", "1. AnalogWrite() duty cycles (0-255), RGB additive color mixing, visual status modes.\n2. Milestone 2: Low-Fidelity Prototype Walkthrough.\n3. State beacon coding.", "Arduino Uno, Sensor Shield, RGB LED, Touch module.", "Lab Evaluation (10M): Color mixing accuracy (4M), Wiring (3M), Logbook (3M)."),
        ("Session 7 (01-15 October 2026)", "Laser Optical Transceivers & Narrow-Beam Alignment", "Mount Laser Module on Pin 8 and LDR on Pin A0 of shield; align optical beam inside shrouded tube; log breach thresholds.", "1. 650nm Laser Diode module, shielded LDR receiver module, optical tripwire physics.\n2. Optical collimation and shroud alignment.\n3. Optical breach detection.", "Arduino Uno, Sensor Shield, 5V Laser Diode, Shrouded LDR module.", "Lab Evaluation (10M): Optical alignment (4M), Threshold calibration (3M), Logbook (3M)."),
        ("Session 8 (16-31 October 2026)", "Multi-Trigger Security System (AND/OR Conditional Logic)", "Build Dual-Factor Security Grid: Laser breach + Touch perimeter trigger multi-tone siren and latch Red LED; test reset logic.", "1. Compound boolean logic (laserTripped && touchAlert), software alarm latching.\n2. Keypad/Touch disarm logic.\n3. Multi-sensor security rules.", "Arduino Uno, Sensor Shield, Laser, LDR, Touch Sensor, Buzzer, RGB LED.", "Lab Evaluation (10M): Dual-factor logic (4M), Alarm latching (3M), Logbook (3M)."),
        ("Session 9 (01-15 November 2026)", "Subsystem Integration & Wire Looming inside Casing", "Assemble full system on shield; route cables into rigid acrylic/wood casing; test live LCD status updates.", "1. Combining I2C LCD, Laser tripwire, Touch sensor, and Siren into single shield setup.\n2. Cable management & looming.\n3. Casing fabrication.", "Arduino Uno, Sensor Shield, Full Sensor Suite, Acrylic/Wood housing.", "Lab Evaluation (10M): Integration hygiene (4M), LCD readout (3M), Logbook (3M)."),
        ("Session 10 (16-30 November 2026)", "Edge Case Handling & Debounce Code Hardening", "Alpha Prototype Review: Test laser security grid under changing ambient room lights; optimize threshold code.", "1. Eliminating false optical triggers, ambient light compensation, code hardening.\n2. Milestone 3: Alpha Working Prototype Demonstration.\n3. Noise filtering.", "Arduino Uno, Sensor Shield, Integrated Security Rig, Variable Room Lighting.", "Lab Evaluation (10M): False-alarm rejection (5M), Stability (3M), Logbook (2M)."),
        ("Session 11 (01-15 December 2026)", "System Stress Testing (100+ Cycles) & QA Logging", "Execute 100 continuous intrusion tests; record trigger reliability in QA Test Sheet; verify zero false alarms.", "1. Automated 100-cycle tripwire testing, alarm latency measurement, power stability.\n2. Quantitative QA logging.\n3. Thermal stability check.", "Arduino Uno, Sensor Shield, Security Rig, QA Test Log.", "Lab Evaluation (10M): 100-test zero fault (4M), QA log (4M), Wiring (2M)."),
        ("Session 12 (16-31 December 2026)", "Pitch Deck Creation & Video Storyboarding", "Compile technical dossier, wiring schematic, and BOM; storyboard 2-minute pitch video with designated student speakers.", "1. Value proposition, technical architecture slide, video scriptwriting.\n2. Complete engineering schematic generation.\n3. Oral presentation run-through.", "PCs, Fritzing/Schematic tool, Presentation templates.", "Lab Evaluation (10M): Dossier completeness (4M), Video storyboard (4M), Pitch (2M)."),
        ("Session 13 (01-15 January 2027)", "Pre-Competition Mock Defense & Jury Evaluation", "Full dress rehearsal: Present working laser/display security prototype before senior faculty panel; refine pitch.", "1. 3-minute presentation, live laser breach demonstration, faculty technical Q&A.\n2. Rigorous jury defense.\n3. Feedback implementation.", "Complete Integrated Prototype, Projector, Jury Scorecards.", "Mock Defense Score (10M): Technical depth (4M), Live demonstration (4M), Team (2M)."),
        ("Session 14 (16-31 January 2027)", "Final Video Rendering & Erehwon Dossier Upload", "Record final 2-minute demonstration video; upload code (.ino), schematic, and documentation to Erehwon portal.", "1. HD video recording, schematic export, complete project submission.\n2. Milestone 4 National Competition Submission.\n3. Lab archive deployment.", "Camera, Completed System, Erehwon Portal.", "Lab Evaluation (10M): Video demo quality (5M), Portal submission verified (5M).")
    ],
    "Class 9": [
        ("Session 1 (01-15 July 2026)", "Multi-Sensor System Architecture & Shield Bus Management", "Analyze Uno+Shield pin allocation; map 4+ simultaneous sensor channels; form 5-6 member teams; scout Agritech/Industry problems.", "1. Heterogeneous sensor bus, pinout budgeting, non-blocking millis() timing.\n2. Power rails decoupling on shield.\n3. Capstone team charter.", "Arduino Uno, Sensor Shield, Multi-sensor array, Multimeter.", "Lab Evaluation (10M): Bus allocation (3M), Architecture design (4M), Logbook (3M)."),
        ("Session 2 (16-31 July 2026)", "Data Fusion & Multi-Variable Logic Loops", "Connect LDR + Tilt + Sound modules simultaneously to shield; write synchronized telemetry code; draft Capstone Charters.", "1. Sensor fusion principles, combining analog environmental data with digital triggers.\n2. Multi-channel telemetry over Serial.\n3. Capstone Charter drafting.", "Arduino Uno, Sensor Shield, LDR, Tilt, Sound Sensor modules.", "Lab Evaluation (10M): Sensor fusion code (4M), Wiring (3M), Logbook (3M)."),
        ("Session 3 (01-15 August 2026)", "Capstone System Planning & BOM Optimization", "Finalize Capstone BOM (Sensors, actuators, displays, battery); submit Erehwon Milestone 1 Project Charter for sign-off.", "1. System architecture diagrams, component specifications, power budgeting (500mA limit).\n2. Milestone 1: Validated Problem Statement & BOM.\n3. Power distribution planning.", "Arduino Uno, Sensor Shield, Components catalog, BOM Spreadsheet.", "Lab Evaluation (10M): BOM optimization (4M), Architecture rigor (3M), Logbook (3M)."),
        ("Session 4 (16-31 August 2026)", "Modular Subsystem Prototyping (Sensing vs Actuation)", "Build Sensing Subsystem (Analog inputs on shield) and Actuation Subsystem (Servos/Relays) on separate benches; verify signals.", "1. Decoupling hardware layers: Input sensing subsystem vs Output actuator subsystem.\n2. Signal integrity and power isolation.\n3. Independent subsystem testing.", "Arduino Uno, Sensor Shield, Relay module, High-torque Servo, Sensors.", "Lab Evaluation (10M): Subsystem isolation (4M), Signal integrity (3M), Logbook (3M)."),
        ("Session 5 (01-15 September 2026)", "Interfacing Multi-Sensor Arrays on Breakout Shield", "Integrate full sensor array onto shield; verify zero signal crosstalk; write unified sensor sampling routine.", "1. Simultaneous wiring of IR, Hall, Tilt, and LDR modules on shield headers.\n2. Non-blocking sensor polling.\n3. Crosstalk prevention.", "Arduino Uno, Sensor Shield, IR, Hall, Tilt, LDR sensors.", "Lab Evaluation (10M): Polling routine (4M), High-density wiring (3M), Logbook (3M)."),
        ("Session 6 (16-30 September 2026)", "Multi-Actuator Orchestration & Power Isolation", "Connect SG90 servo + 5V Relay module + I2C LCD to shield; supply external 5V power to terminal block; test concurrent actuation.", "1. Driving multiple servos, relays, and buzzers via shield external power terminals.\n2. Milestone 2: Low-Fidelity Prototype Walkthrough.\n3. Inductive kickback protection.", "Arduino Uno, Sensor Shield, Servo, Relay, I2C LCD, External DC Supply.", "Lab Evaluation (10M): Concurrent actuation (4M), Power isolation (3M), Logbook (3M)."),
        ("Session 7 (01-15 October 2026)", "Non-Blocking State Machine Code Integration", "Merge sensor sampling and actuator routines into a non-blocking master sketch; eliminate code blocking; test real-time response.", "1. Replacing delay() with millis() timers, interrupt service routines (ISR), state enums.\n2. State machine architecture.\n3. Real-time responsiveness.", "Arduino Uno, Sensor Shield, Full Hardware Setup, PC IDE.", "Lab Evaluation (10M): State machine logic (4M), Zero-blocking verified (3M), Logbook (3M)."),
        ("Session 8 (16-31 October 2026)", "Smart System Capstone Integration (Part 1: Core Logic)", "Assemble integrated Capstone build (Sensors + Actuators + Display on shield); code automated feedback control loop.", "1. Automated greenhouse / industrial safety interlocking logic, multi-stage thresholds.\n2. Closed-loop feedback control.\n3. Telemetry streaming.", "Arduino Uno, Sensor Shield, Full Capstone Sensors & Actuators, Chassis.", "Lab Evaluation (10M): Closed-loop execution (4M), Assembly (3M), Logbook (3M)."),
        ("Session 9 (01-15 November 2026)", "Smart System Capstone Integration (Part 2: Casing & Looms)", "Mount Arduino+Shield assembly into durable modular chassis; bundle cables with spiral wrap; test standalone battery operation.", "1. Industrial-grade enclosure fabrication, heat-shrink wire looms, power switch.\n2. Mechanical stress relief on cables.\n3. Standalone battery integration.", "Arduino Uno, Sensor Shield, Industrial Modular Chassis, Spiral wrap, Battery pack.", "Lab Evaluation (10M): Industrial casing (4M), Cable looming (3M), Logbook (3M)."),
        ("Session 10 (16-30 November 2026)", "Full System Field Testing & Telemetry Logging", "Milestone 3 Alpha Review: Subject capstone build to 50 continuous operational cycles; log performance metrics in QA dossier.", "1. Field stress testing over 50 continuous cycles, sensor drift and latency logging.\n2. Milestone 3: Alpha Working Prototype Demonstration.\n3. Telemetry recording.", "Complete Capstone Unit, Test Environment, QA Telemetry Sheet.", "Lab Evaluation (10M): 50-cycle stability (5M), Telemetry log (3M), Logbook (2M)."),
        ("Session 11 (01-15 December 2026)", "Code Hardening, Fail-Safes & Auto-Recovery", "Implement fail-safe routines (auto-shutdown on sensor fault); optimize code execution speed; finalize firmware repository.", "1. Watchdog timers, error-handling routines, sensor disconnection auto-recovery.\n2. Firmware code hardening.\n3. Safe state default routines.", "Arduino Uno, Sensor Shield, Capstone Rig, PC IDE.", "Lab Evaluation (10M): Fail-safe recovery (4M), Firmware optimization (4M), Logbook (2M)."),
        ("Session 12 (16-31 December 2026)", "Comprehensive Engineering Dossier & Schematics", "Compile comprehensive engineering dossier (Problem statement, block diagram, schematics, source code, test analytics).", "1. IEEE-style project documentation, full circuit schematics, test data graphs.\n2. Bill of Materials reconciliation.\n3. Pitch scriptwriting.", "PCs, Schematics CAD tools, Engineering Dossier Template.", "Lab Evaluation (10M): Dossier depth (4M), Schematics accuracy (4M), Script (2M)."),
        ("Session 13 (01-15 January 2027)", "Grand Internal Capstone Defense & Jury Review", "Formal Capstone defense before school leadership and external technical jury; demonstrate full system autonomy.", "1. 5-minute technical defense, live autonomous operation demo, rigorous panel Q&A.\n2. Technical committee evaluation.\n3. Defense rubric scoring.", "Completed Capstone System, Projector, Jury Evaluation Dossiers.", "Capstone Defense Score (10M): Autonomy & rigor (4M), Defense (4M), Teamwork (2M)."),
        ("Session 14 (16-31 January 2027)", "National Submission & Lab Archive Deployment", "Milestone 4: Record broadcast-quality 2-min demo video; complete final submission on Erehwon portal; archive code in lab repo.", "1. Final 2-minute video production, Erehwon portal upload, lab repository handover.\n2. Milestone 4 National Competition Submission.\n3. STEM Lab permanent archiving.", "Camera Rig, Finished Capstone, Erehwon Portal.", "Lab Evaluation (10M): Broadcast demo video (5M), Portal submission verified (5M).")
    ]
}

def render_master_content(sno, title):
    if title == "STEM Lab Profile":
        st.markdown("""
        ### 🏫 STEM LAB PROFILE
        * **School Name:** Aditya Birla Intermediate College, Renukoot
        * **Academic Session:** 2026-27
        * **STEM Lab:** School STEM Innovation & Learning Laboratory
        * **STEM Coordinator / SPOC:** Shashank Verma
        ---
        #### 1. Introduction
        The STEM Lab of Aditya Birla Intermediate College, Renukoot is a dedicated space for promoting Science, Technology, Engineering and Mathematics (STEM) learning through hands-on activities, experimentation, problem-solving, innovation and project-based learning. The laboratory provides students with opportunities to connect classroom concepts with real-life situations and develop practical skills through designing, making, testing and improving solutions.
        #### 2. Classes Covered
        The STEM Lab activities are primarily conducted for: Class VI, VII, VIII, IX.
        #### 3. Major Objectives
        1. To develop scientific thinking and curiosity among students.
        2. To promote hands-on and experiential learning.
        3. To develop problem-solving and critical-thinking skills.
        4. To encourage students to identify real-life problems and develop solutions.
        5. To promote creativity, innovation and design thinking.
        6. To provide exposure to technology, electronics, coding, robotics and prototyping.
        7. To encourage teamwork and collaborative learning.
        8. To develop communication, presentation and documentation skills.
        9. To connect STEM concepts with real-life applications.
        10. To encourage participation in STEM competitions and innovation programmes.
        #### 4. Major Areas of STEM Learning
        Science Experiments, Mathematics Applications, Electronics, Arduino & Microcontrollers, Robotics, Sensors & Actuators, Coding & Computational Thinking, IoT & Smart Systems, Design Thinking, 3D Prototyping (Bambu Lab A1 Mini), Environmental Innovation.
        """)
        return True

    elif title == "Lab Objectives & Guidelines":
        st.markdown("""
        ### 📋 STEM LAB OBJECTIVES & GUIDELINES
        * **School:** Aditya Birla Intermediate College, Renukoot | **Session:** 2026-27 | **SPOC:** Shashank Verma
        ---
        #### A. Core Objectives
        1. **Experiential Learning:** Hands-on projects & experiments.
        2. **Problem Solving:** Develop appropriate real-life solutions.
        3. **Innovation:** Design & prototype new ideas.
        4. **Scientific Temper:** Evidence-based logical reasoning.
        5. **Technology Skills:** Coding, electronics, sensors, robotics.
        ---
        #### B. Mandatory Safety Guidelines
        1. Entry permitted only under teacher/instructor supervision.
        2. Electrical equipment shall be handled carefully. Polarity must be verified before powering Arduino/Shield.
        3. Never short circuit battery terminals; keep water away from equipment workbenches.
        4. In case of smoke or emergency, hit the master power cutoff switch immediately.
        """)
        return True

    elif title == "Coordinator / SPOC Details":
        st.markdown("""
        ### 👤 STEM LAB COORDINATOR / SPOC DETAILS
        * **Name:** Shashank Verma | **Designation:** PGT | **Qualification:** M.Sc., B.Ed.
        * **Role:** STEM Coordinator / STEM Lab SPOC
        * **Official Email:** `shashank.verma@adityabirlaschools.in` | **Contact:** `9826594665`
        ---
        #### Major Responsibilities
        1. Planning and coordinating weekly STEM Lab sessions and annual activities.
        2. Enforcing 56 Master Lesson Plans and National Erehwon Innovation competition milestones[cite: 1].
        3. Maintaining student attendance, teacher lab records, and digital cloud synchronizations.
        4. Overseeing equipment safety, tool inventories, and 3D printing workflows.
        """)
        return True

    elif title == "Monthly / Annual STEM Activity Plan":
        render_annual_plan()
        return True

    elif title == "Class-wise Timetable":
        st.markdown("""
        ### ⏰ Weekly STEM Lab Schedule (2026-27)
        * **Class VI (Sections A, B, C, D):** Tuesday & Thursday (Period 4)
        * **Class VII (Sections A, B, C, D):** Monday & Wednesday (Period 5)
        * **Class VIII (Sections A, B, C, D):** Wednesday & Friday (Period 6)
        * **Class IX (Sections A to H):** Saturday (Period 2 to 4 - 3 Period Capstone Block)
        """)
        return True

    elif title == "Session / Lesson Plans":
        st.markdown("""
        ### 📖 ANNUAL STEM LAB & ROBOTICS MASTER LESSON PLANS (JULY 2026 – JANUARY 2027)
        * **Platform:** ScienceUtsav LMS (Robo Scientist Level 2: Sensational Sensors)[cite: 1]
        * **Hardware Kit:** Arduino Uno R3 + Sensor Breakout Shield (3-Pin G-V-S Plug-and-Play)[cite: 1]
        * **Innovation Track:** Erehwon National Competition (25+ Teams across Classes 6–9)[cite: 1]
        * **Scope:** 56 Detailed Session Plans (14 Sessions / Class)[cite: 1]
        ---
        """)
        col_c, col_s = st.columns([1, 2])
        selected_class = col_c.selectbox("🎓 Select Class:", list(LESSON_PLANS_DB.keys()), key="lp_class_select")
        sessions_list = LESSON_PLANS_DB[selected_class]
        session_titles = [f"{s[0]} — {s[1]}" for s in sessions_list]
        selected_session_idx = col_s.selectbox("📑 Select Session:", range(len(session_titles)), format_func=lambda i: session_titles[i], key="lp_session_select")
        plan_data = sessions_list[selected_session_idx]
        st.markdown("---")
        st.subheader(f"📌 {selected_class}: {plan_data[0]}")
        st.markdown(f"#### 🔬 Unit / Module: `{plan_data[1]}`")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("##### 🎯 Learning Objectives & Outcomes")
            st.info(f"**Objectives:** Master the working principles of {plan_data[1]} on Arduino Uno with 3-pin Breakout Shield. Advance team deliverables on the Erehwon Track.")
            st.success(f"**Expected Outcome:** Securely wire modules without breadboards, calibrate sensor thresholds via Serial Monitor, and fulfill designated team roles.")
            st.markdown("##### 🛠️ Hands-on Experimental Activity")
            st.warning(f"**Activity:** {plan_data[2]}")
        with col_r:
            st.markdown("##### 📚 Content & Teaching Points")
            st.code(plan_data[3], language="text")
            st.markdown("##### 📦 Teaching Aids & Resources")
            st.write(f"• **Hardware:** {plan_data[4]}")
            st.write(f"• **Digital Resource:** ScienceUtsav LMS (report.scienceutsav.com/lms) | Arduino Reference")
            st.markdown("##### 📊 Periodic Assessment")
            st.write(f"• **Criteria:** {plan_data[5]}")
        return True

    elif title == "Student List":
        render_student_excel()
        return True

    elif title == "Student Attendance":
        render_student_attendance_viewer()
        return True

    elif title == "Teacher Attendance":
        render_teacher_attendance_viewer()
        return True

    elif title == "Lab Inventory":
        st.markdown("""
        ### 📦 Verified STEM Lab Inventory (ScienceUtsav & ABPS Kit)
        * **Microcontrollers:** 25x Arduino Uno R3 (ATmega328P DIP), 25x Sensor Breakout Shields V5.0 (3-Pin G-V-S).
        * **Sensor Modules:** LDR Light, DHT11 Temp/Humidity, MQ2 Smoke/Gas, Flame, Soil Moisture, Ultrasonic HC-SR04, IR Obstacle, Hall Effect A3144, Tilt SW-520D, TTP223 Touch, Sound Mic.
        * **Actuators & Displays:** SG90 Micro Servos (0°-180°), BO Geared Motors + Wheels, 5V Relays, 16x2 I2C Character LCDs, 7-Segment Displays, Active/Passive Buzzers, RGB LEDs.
        * **3D & Prototyping:** Bambu Lab A1 Mini 3D Printer (PLA Filament), 5V DC Bench Power Adapters, Battery Cases, 3-Pin / 4-Pin RMC Ribbon Jumpers.
        """)
        return True

    elif title == "Equipment Details":
        st.markdown("""
        ### 🔬 Technical Hardware Specifications
        * **Processing Unit:** Arduino Uno R3 (16 MHz Crystal, 5V Logic, 14 Digital I/O, 6 Analog Inputs).
        * **Shield Architecture:** Dedicated external servo power terminal block, I2C port (A4/A5), UART (TX/RX).
        * **Rapid Prototyping:** Bambu Lab A1 Mini FDM 3D Printer (0.4mm Nozzle, Auto-bed Leveling, 180x180x180mm Build Volume).
        """)
        return True

    elif title == "Lab Safety Rules":
        st.markdown("""
        ### ⚠️ Mandatory STEM Lab Safety Protocol
        1. Always inspect wiring for short-circuits before plugging the USB / 5V DC barrel jack into the Arduino Uno.
        2. Never draw high current for servos or motors directly from Uno 5V pin; always utilize the shield's dedicated external power terminal block.
        3. Soldering and hot glue work must be performed at designated thermal workstations wearing protective safety glasses.
        4. Any component malfunction or heating issue must be immediately reported to the SPOC.
        """)
        return True

    elif title == "Safety Checklist":
        st.markdown("""
        ### ✅ Periodic Laboratory Safety Audit Checklist
        * [x] **Power Breakers:** Master MCB cutoff switch and bench surge protectors fully operational.
        * [x] **Fire Suppression:** CO2 Fire Extinguisher inspected, tagged, and unobstructed at main entrance.
        * [x] **First Aid Medical Kit:** Stocked with burn cream, antiseptic, bandages, and eye-wash solution.
        * [x] **Cable Hygiene:** Anti-trip cable routing and color-coded modular storage boxes labeled.
        """)
        return True

    elif title == "STEM Activities":
        st.markdown("""
        ### 💡 Core Laboratory Project Modules
        1. Smart Street Lighting with LDR Sensor and Transistor/Relay Switching.
        2. Acoustic Decibel Warning Station using Sound Sensor, RGB LED, and Buzzer.
        3. Automated Touchless Boom Barrier Gate with IR Proximity Sensor and SG90 Micro Servo.
        4. Multi-Factor Laser Optical Tripwire Security System with Capacitive Touch Disarm.
        5. Smart Agricultural Greenhouse Monitor with Soil Moisture, DHT11, and I2C LCD Readout.
        """)
        return True

    elif title == "Assessment Rubrics":
        st.markdown("""
        ### 📊 Student STEM Assessment Rubric (100 Marks Distribution)
        * **Problem Identification & Research (20 Marks):** Campus problem statement clarity and engineering logbook documentation.
        * **Circuit Assembly & Hardware Hygiene (20 Marks):** Modular shield wiring, secure pin mapping, and power stability.
        * **Firmware Coding Logic (20 Marks):** Non-blocking millis() loops, conditional thresholds, and bug-free syntax.
        * **Enclosure & Packaging (20 Marks):** Mechanical chassis stability, 3D printed / cardboard casing, and cable looming.
        * **Oral Defense & Live Demonstration (20 Marks):** 3-minute pitch, prototype autonomy, and jury Q&A handling.
        """)
        return True

    elif title == "Student Assessment":
        render_scienceutsav_assessment()
        return True

    elif title == "Teacher Training Records":
        st.markdown("""
        ### 🧑‍🏫 Teacher STEM Capacity Building & Training Record
        * **Conducted By:** ScienceUtsav Technical Expert Team & ABIC STEM Coordinator.
        * **Core Modules Covered:** Sensor Breakout Shield Architecture, Modular C++ Embedded Coding, Bambu Lab 3D Slicing & Printing, Student Mentorship Pedagogy.
        * **Participating Faculty:** 10 Designated Science & STEM Faculty Members.
        """)
        return True

    elif title == "Annual Report":
        st.markdown("""
        ### 📑 Annual STEM Innovation Lab Report (2026-27 Executive Summary)
        * Over 400+ students from Classes VI to IX actively enrolled in weekly hands-on maker curricula.
        * 56 structured lesson plans executed across sensor and robotics modules[cite: 1].
        * 25+ student teams successfully completed Alpha working prototypes for the National Erehwon Innovation Competition.
        * 100% equipment audit verified with zero electrical safety incidents.
        """)
        return True

    return False

# ----------------- SIDEBAR NAVIGATION -----------------
st.sidebar.title("🔬 ABIC STEM Portal")
st.sidebar.caption("Aditya Birla Intermediate College, Renukoot")
access_mode = st.sidebar.radio("Navigation Mode", ["Public Viewer", "Admin Workspace"])

if "is_admin_logged_in" not in st.session_state:
    st.session_state["is_admin_logged_in"] = False

# ----------------- ADMIN WORKSPACE -----------------
if access_mode == "Admin Workspace":
    st.sidebar.markdown("---")
    if not st.session_state["is_admin_logged_in"]:
        st.sidebar.subheader("Admin Login")
        password_input = st.sidebar.text_input("Enter Admin Password", type="password", key="login_pass_input")
        if password_input == "stem@admin123" or st.sidebar.button("Login", type="primary"):
            if password_input == "stem@admin123":
                st.session_state["is_admin_logged_in"] = True
                st.rerun()
            else:
                st.sidebar.error("Incorrect Password")
    else:
        st.sidebar.success("Authenticated as SPOC")
        if st.sidebar.button("🚪 Logout"):
            st.session_state["is_admin_logged_in"] = False
            st.rerun()

    if st.session_state["is_admin_logged_in"]:
        render_cover_photo()
        render_principal_message()
        st.title("⚙️ Admin Workspace: Manage Records & Live Attendance")

        with st.expander("🔗 **Google Forms, Sheets & ScienceUtsav Integration**", expanded=False):
            st.markdown("##### 1. Connect Google Sheet (Responses)")
            current_sheet_url = get_saved_url(SHEET_CONFIG_FILE)
            sheet_input = st.text_input("Google Sheet Share Link (Viewer):", value=current_sheet_url)
            c_save_s, c_sync = st.columns(2)
            if c_save_s.button("💾 Save Sheet Link"):
                save_url(SHEET_CONFIG_FILE, sheet_input)
                st.success("Google Sheet link saved!")
            if c_sync.button("🔄 Sync Now from Google Sheet", type="primary"):
                if sheet_input:
                    save_url(SHEET_CONFIG_FILE, sheet_input)
                success, msg = sync_data_from_google_sheet()
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

            st.divider()
            st.markdown("##### 2. Connect Google Form (Teacher Link)")
            current_form_url = get_saved_url(FORM_CONFIG_FILE)
            form_input = st.text_input("Google Form Link:", value=current_form_url)
            if st.button("💾 Save Form Link"):
                save_url(FORM_CONFIG_FILE, form_input)
                st.success("Google Form link saved!")

            st.divider()
            st.markdown("##### 3. ScienceUtsav Classroom Report Link")
            current_su_url = get_saved_url(SCIENCEUTSAV_CONFIG_FILE)
            if not current_su_url:
                current_su_url = "https://report.scienceutsav.com/class/k57a8q5h6mzanqt4vdvn48c1vx8ba0q3/report"
            su_input = st.text_input("ScienceUtsav URL:", value=current_su_url)
            if st.button("💾 Save ScienceUtsav Link"):
                save_url(SCIENCEUTSAV_CONFIG_FILE, su_input)
                st.success("ScienceUtsav URL saved!")

        with st.expander("🖼️ **Update Cover Photo & Principal Message**", expanded=False):
            cover_file = st.file_uploader("Upload Banner Photo", type=["jpg", "jpeg", "png", "webp"], key="upload_cover_banner")
            if cover_file:
                c_ext = os.path.splitext(cover_file.name)[1].lower()
                with open(os.path.join(DATA_DIR, f"cover photo{c_ext}"), "wb") as f:
                    f.write(cover_file.getbuffer())
                st.success("Banner updated!")
                st.rerun()
            st.divider()
            current_p_msg = get_principal_message()
            edited_p_msg = st.text_area("Principal Message:", value=current_p_msg, height=120)
            if st.button("💾 Save Message", type="primary"):
                save_principal_message(edited_p_msg)
                st.success("Saved!")
                st.rerun()

        st.divider()
        st.subheader("📁 Manage All 49 Parameters")

        for section_name, items in CATEGORIES.items():
            st.markdown(f"#### 📑 {section_name}")
            for sno, title in items:
                folder_name = get_folder_name(sno, title)
                record_dir = os.path.join(UPLOAD_DIR, folder_name)
                os.makedirs(record_dir, exist_ok=True)

                is_active = (st.session_state.get("active_admin_sno") == sno)
                btn_label = f"▼ #{sno}. {title}" if is_active else f"▶ #{sno}. {title}"

                if st.button(btn_label, key=f"admin_btn_{sno}", use_container_width=True):
                    st.session_state["active_admin_sno"] = None if is_active else sno
                    st.rerun()

                if is_active:
                    st.markdown(f"### ⚙️ Managing: #{sno}. {title}")
                    if title == "Student Attendance":
                        cur_m_idx, cur_w_idx = get_current_indices()
                        c_m, c_w = st.columns(2)
                        admin_st_month = c_m.selectbox("Select Month:", MONTHS, index=cur_m_idx, key=f"adm_st_m_{sno}")
                        admin_st_week = c_w.selectbox("Select Week:", WEEKS, index=cur_w_idx, key=f"adm_st_w_{sno}")
                        current_st_slot_df = get_student_attendance_for_slot(admin_st_month, admin_st_week)
                        edited_st_slot_df = st.data_editor(current_st_slot_df, num_rows="dynamic", use_container_width=True, key=f"adm_ed_st_{sno}")
                        if st.button(f"💾 Save Student Attendance ({admin_st_month})", type="primary", key=f"btn_st_s_{sno}"):
                            save_student_attendance_slot(admin_st_month, admin_st_week, edited_st_slot_df)
                            st.success("Saved!")
                            st.rerun()
                    elif title == "Teacher Attendance":
                        cur_m_idx, cur_w_idx = get_current_indices()
                        c_m, c_w = st.columns(2)
                        admin_tc_month = c_m.selectbox("Select Month:", MONTHS, index=cur_m_idx, key=f"adm_tc_m_{sno}")
                        admin_tc_week = c_w.selectbox("Select Week:", WEEKS, index=cur_w_idx, key=f"adm_tc_w_{sno}")
                        current_tc_slot_df = get_teacher_attendance_for_slot(admin_tc_month, admin_tc_week)
                        edited_tc_slot_df = st.data_editor(current_tc_slot_df, num_rows="dynamic", use_container_width=True, key=f"adm_ed_tc_{sno}")
                        if st.button(f"💾 Save Teacher Attendance ({admin_tc_month})", type="primary", key=f"btn_tc_s_{sno}"):
                            save_teacher_attendance_slot(admin_tc_month, admin_tc_week, edited_tc_slot_df)
                            st.success("Saved!")
                            st.rerun()
                    else:
                        uploaded_files = st.file_uploader(f"Upload files for #{sno} ({title})", type=None, accept_multiple_files=True, key=f"upload_{sno}")
                        if uploaded_files:
                            for f in uploaded_files:
                                with open(os.path.join(record_dir, f.name), "wb") as buffer:
                                    buffer.write(f.getbuffer())
                            st.success(f"Saved {len(uploaded_files)} file(s).")
                            st.rerun()
                        existing_file_tuples = get_existing_files_for_parameter(sno, title)
                        if existing_file_tuples:
                            for fpath, fname in existing_file_tuples:
                                c_a, c_b = st.columns([5, 1])
                                c_a.text(f"📄 {fname}")
                                if c_b.button("Delete", key=f"del_{sno}_{fname}"):
                                    if os.path.exists(fpath):
                                        os.remove(fpath)
                                    st.rerun()
                    st.divider()
    else:
        st.title("🔒 Restricted Access")
        st.info("Enter admin password in the sidebar to access Admin Workspace.")

# ----------------- PUBLIC VIEWER -----------------
else:
    render_cover_photo()
    render_principal_message()
    st.title("🔬 STEM Innovation & Learning Laboratory")
    st.caption("Aditya Birla Intermediate College, Renukoot | Academic Session 2026-27")

    tab1, tab2 = st.tabs(["📁 Explore Records", "📊 Repository Status"])

    with tab1:
        for section_name, items in CATEGORIES.items():
            st.subheader(f"📑 {section_name}")
            for sno, title in items:
                files_found = get_existing_files_for_parameter(sno, title)
                is_active = (st.session_state.get("active_viewer_sno") == sno)
                toggle_btn_label = f"▼ #{sno}. {title}" if is_active else f"▶ #{sno}. {title}"

                if st.button(toggle_btn_label, key=f"viewer_btn_{sno}", use_container_width=True):
                    st.session_state["active_viewer_sno"] = None if is_active else sno
                    st.rerun()

                if is_active:
                    st.markdown(f"#### 📌 #{sno}. {title}")
                    has_builtin_content = render_master_content(sno, title)
                    
                    if files_found:
                        st.markdown("---")
                        st.markdown("##### 📁 Uploaded Documents & Files:")
                        for idx, (fpath, fname) in enumerate(files_found):
                            render_file_preview(fpath, fname, f"{sno}_{idx}")
                            st.write("")
                    elif not has_builtin_content:
                        st.info("No document uploaded yet for this section.")
                    st.markdown("---")

    with tab2:
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
                    "Equipment Details", "Lab Safety Rules", "Safety Checklist", "STEM Activities",
                    "Assessment Rubrics", "Student Assessment", "Teacher Training Records", "Annual Report"
                ]
                if has_builtin or len(files_found) > 0:
                    completed += 1
                    status = "✅ Active / Verified"
                else:
                    status = "⏳ Pending Upload"
                summary_rows.append({"Index": sno, "Parameter Name": title, "Section": section_name, "Status": status})

        c1, c2 = st.columns(2)
        c1.metric("Total Parameters", total)
        c2.metric("Completed / Active", f"{completed} / {total}")
        st.dataframe(summary_rows, use_container_width=True)
