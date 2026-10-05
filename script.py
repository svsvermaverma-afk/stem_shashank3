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

# ----------------- ADMIN CREDENTIALS (EXACT RESET TO ADMIN / ADMIN) -----------------
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"

DEFAULT_CONFIGS = {
    SHEET_CONFIG_FILE: "https://docs.google.com/spreadsheets/d/1999l0-GPaDxUh2trREm4HOx6NAfsYHGU_0Qakzy4Bwo/edit?usp=sharing",
    FORM_CONFIG_FILE: "https://docs.google.com/forms/d/e/1FAIpQLSeAE6pzeLi-NVO4aTA82gfXH2oKqtFf3TTlIyI0VCQobP9qxQ/viewform?usp=sharing&ouid=116197222500145214334",
    SCIENCEUTSAV_CONFIG_FILE: "https://report.scienceutsav.com/class/k57a8q5h6mzanqt4vdvn48c1vx8ba0q3/report"
}

MONTHS = ["April", "May", "June", "July", "August", "September", "October", "November", "December", "January", "February", "March"]
WEEKS = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]

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
if "is_admin_logged_in" not in st.session_state:
    st.session_state["is_admin_logged_in"] = False
if "show_login_modal" not in st.session_state:
    st.session_state["show_login_modal"] = False

# ----------------- SWAYAM STYLING CSS -----------------
st.markdown("""
<style>
.main .block-container {
    padding-top: 15px !important;
    padding-bottom: 40px !important;
    max-width: 1250px !important;
}
.swayam-hero {
    text-align: center;
    margin: 30px auto 20px auto;
    max-width: 900px;
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
    margin-bottom: 20px;
}
.swayam-metric-card {
    text-align: center;
    padding: 18px 10px;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}
.swayam-metric-title {
    font-size: 14px;
    color: #64748b;
    font-weight: 500;
    margin-bottom: 6px;
}
.swayam-metric-val {
    font-size: 32px;
    font-weight: 800;
    color: #003366;
}
</style>
""", unsafe_allow_html=True)

# ----------------- DATABASE HELPERS -----------------
def init_timetable_db():
    conn = sqlite3.connect(TIMETABLE_DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_name TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            monday TEXT, tuesday TEXT, wednesday TEXT, thursday TEXT, friday TEXT, saturday TEXT
        )
    ''')
    conn.commit()
    c.execute("SELECT COUNT(*) FROM timetable")
    if c.fetchone()[0] == 0:
        slots = [
            ("Zero Period", "8:05 AM - 8:50 AM", "-", "-", "-", "-", "-", "-"),
            ("Period I", "9:15 AM - 9:55 AM", "-", "-", "VIII - C (SST)", "-", "-", "IX G (HD)"),
            ("Period II", "9:55 AM - 10:30 AM", "-", "-", "-", "-", "-", "VII C (SNS)"),
            ("Period III", "10:30 AM - 11:05 AM", "VI - A (SV)", "VII - A (RKS)", "VII B (MBJ)", "VIII-A (SV) / VIII B (MM)", "-", "-"),
            ("Period IV", "11:05 AM - 11:40 AM", "-", "-", "-", "-", "-", "-"),
            ("INTERVAL", "11:40 AM - 12:05 PM", "RECESS", "RECESS", "RECESS", "RECESS", "RECESS", "RECESS"),
            ("Period V", "12:05 PM - 12:45 PM", "-", "-", "-", "-", "VI C", "-"),
            ("Period VI", "12:45 PM - 1:20 PM", "-", "-", "-", "-", "-", "-"),
            ("Period VII", "1:20 PM - 1:55 PM", "VI - D (DJ) / IX - A (RKS)", "IX - F (CM)", "IX C (SNS)", "VI - B (MM)", "IX D", "-"),
            ("Period VIII", "1:55 PM - 2:30 PM", "-", "-", "-", "-", "-", "-"),
        ]
        c.executemany('INSERT INTO timetable (period_name, time_slot, monday, tuesday, wednesday, thursday, friday, saturday) VALUES (?,?,?,?,?,?,?,?)', slots)
        conn.commit()
    conn.close()

init_timetable_db()

def get_timetable_df():
    conn = sqlite3.connect(TIMETABLE_DB_FILE)
    df = pd.read_sql_query("SELECT period_name AS [Period], time_slot AS [Timing], monday AS [Monday], tuesday AS [Tuesday], wednesday AS [Wednesday], thursday AS [Thursday], friday AS [Friday], saturday AS [Saturday] FROM timetable", conn)
    conn.close()
    return df

def get_saved_url(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            val = f.read().strip()
            if val:
                return val
    return DEFAULT_CONFIGS.get(file_path, "")

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
            st.markdown(f"#### 👨‍🎓 Registered Student Database (Total Records: {len(df)})")
            class_col = next((c for c in df.columns if "class" in str(c).lower()), None)
            if class_col:
                unique_classes = ["All Classes"] + sorted([str(x) for x in df[class_col].dropna().unique()])
                sel_class = st.selectbox("Filter by Class:", unique_classes, key="st_class_filter")
                df_disp = df[df[class_col].astype(str) == sel_class] if sel_class != "All Classes" else df
            else:
                df_disp = df
            st.dataframe(df_disp, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error loading student database: {e}")
    else:
        st.info("ℹ️ Student database safe. 'LMS STUDENT DATA.xlsx' folder me rakhein.")

# ----------------- TOP NAVBAR (SWAYAM STYLE) -----------------
nav1, nav2, nav3 = st.columns([3.5, 6.5, 2])

with nav1:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px;">
        <div style="background:#004085; color:white; font-weight:800; font-size:20px; padding:4px 10px; border-radius:4px;">ABIC</div>
        <span style="font-weight:700; color:#1f2937; font-size:16px;">STEM Lab Portal</span>
    </div>
    """, unsafe_allow_html=True)

with nav2:
    st.markdown("""
    <div style="display:flex; gap:18px; align-items:center; height:100%; font-size:14px; color:#4b5563; font-weight:500;">
        <span>About STEM Lab</span>
        <span>All 49 Parameters</span>
        <span>Student Records</span>
        <span>Robotics & IoT</span>
        <span>Safety Rules</span>
    </div>
    """, unsafe_allow_html=True)

with nav3:
    if not st.session_state["is_admin_logged_in"]:
        if st.button("Login / Sign up", type="primary", use_container_width=True):
            st.session_state["show_login_modal"] = not st.session_state["show_login_modal"]
    else:
        if st.button("Admin Logout 🚪", use_container_width=True):
            st.session_state["is_admin_logged_in"] = False
            st.rerun()

# ----------------- ADMIN LOGIN POPUP (RESET TO ADMIN / ADMIN) -----------------
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
            # Dono case-insensitive check honge (Admin, admin, ADMIN sab chalega)
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

# ----------------- MAIN HEADING & SWAYAM HERO -----------------
st.markdown("""
<div class="swayam-hero">
    <div class="swayam-tagline">INNOVATION • EXPERIMENTATION • RESEARCH</div>
    <h1>Aditya Birla Inter College Renukoot STEM Lab</h1>
    <div class="swayam-subheading">Science, Technology, Engineering & Mathematics Laboratory (Session 2026-27)</div>
</div>
""", unsafe_allow_html=True)

# ----------------- SEARCH BAR -----------------
search_cols = st.columns([2, 8, 2])
with search_cols[1]:
    search_text = st.text_input("🔍 Search STEM Lab Parameters, Projects, or Timetable...", placeholder="Search SWAYAM Courses / STEM Modules...", label_visibility="collapsed")

# ----------------- 6 MAIN CATEGORY ICONS -----------------
st.markdown("<br>", unsafe_allow_html=True)
cat_cols = st.columns(6)
cat_keys = list(CATEGORIES.keys())
cat_icons = ["📋", "🛡️", "🚀", "📊", "🧑‍🏫", "🏆"]

for i, col in enumerate(cat_cols):
    with col:
        cat_short = cat_keys[i].split(". ")[1]
        st.markdown(f"""
        <div style="text-align:center; padding:12px; border-radius:8px; border:1px solid #e5e7eb; background:#f9fafb; margin-bottom:10px;">
            <div style="font-size:24px; margin-bottom:4px;">{cat_icons[i]}</div>
            <div style="font-size:12px; font-weight:600; color:#1f2937;">{cat_short}</div>
        </div>
        """, unsafe_allow_html=True)

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

# ----------------- REPOSITORY SECTION & TABS -----------------
st.subheader("📚 Explore All 49 STEM Lab Modules")

tab_records, tab_students, tab_tt, tab_su = st.tabs([
    "📁 49 Parameters & Files", "👨‍🎓 2000+ Students Data", "⏰ Master Timetable", "🌐 ScienceUtsav Live"
])

with tab_records:
    if st.session_state["is_admin_logged_in"]:
        st.info("🔓 Admin Mode Active: Aap files upload aur manage kar sakte hain.")

    for cat_title, items in CATEGORIES.items():
        with st.expander(cat_title, expanded=False):
            for sno, title in items:
                if search_text and search_text.lower() not in title.lower() and search_text.lower() not in cat_title.lower():
                    continue
                
                c_item1, c_item2 = st.columns([9, 2])
                with c_item1:
                    st.write(f"**#{sno}. {title}**")
                with c_item2:
                    st.caption("Active Module")

                if st.session_state["is_admin_logged_in"]:
                    folder_name = f"{sno:02d}_{title.replace(' ', '_').replace('/', '_')}"
                    rec_dir = os.path.join(UPLOAD_DIR, folder_name)
                    os.makedirs(rec_dir, exist_ok=True)
                    u_file = st.file_uploader(f"Upload document for #{sno}", key=f"up_{sno}")
                    if u_file:
                        with open(os.path.join(rec_dir, u_file.name), "wb") as bf:
                            bf.write(u_file.getbuffer())
                        st.success(f"Saved {u_file.name}")

with tab_students:
    render_student_excel()

with tab_tt:
    st.markdown("### ⏰ Master Lab Schedule")
    df_tt = get_timetable_df()
    st.dataframe(df_tt, use_container_width=True)

with tab_su:
    su_url = get_saved_url(SCIENCEUTSAV_CONFIG_FILE)
    st.link_button("🌐 Open Live ScienceUtsav LMS", su_url)
    components.iframe(su_url, height=750, scrolling=True)

# ----------------- FOOTER -----------------
st.markdown("""
<div style="text-align:center; padding:30px 0 10px 0; color:#6b7280; font-size:13px; border-top:1px solid #e5e7eb; margin-top:50px;">
    Aditya Birla Intermediate College, Renukoot, Sonbhadra (U.P.) • STEM Innovation & Learning Laboratory<br>
    © 2026-27 Government / Corporate STEM Educational Framework
</div>
""", unsafe_allow_html=True)
