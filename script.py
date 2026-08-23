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

# ----------------- UNIVERSAL COVER PHOTO LOADER -----------------
def render_cover_photo():
    search_dirs = [".", DATA_DIR, os.path.join(UPLOAD_DIR, "00_Cover"), os.path.join(UPLOAD_DIR, "cover")]
    valid_exts = [".jpg", ".jpeg", ".png", ".webp"]
    
    found_cover = None
    for s_dir in search_dirs:
        if os.path.exists(s_dir):
            for file_name in os.listdir(s_dir):
                name_lower = file_name.lower()
                if any(k in name_lower for k in ["cover", "banner", "header"]) and any(name_lower.endswith(ext) for ext in valid_exts):
                    found_cover = os.path.join(s_dir, file_name)
                    break
        if found_cover:
            break
            
    if found_cover:
        st.image(found_cover, use_container_width=True)

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
    st.caption(f"Showing Student Attendance for: **{sel_month} | {sel_week}**")
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
    st.caption(f"Showing Teacher Attendance for: **{sel_month} | {sel_week}**")
    st.dataframe(df_slot, use_container_width=True, hide_index=True)

def render_student_excel():
    possible_paths = [
        "LMS STUDENT DATA.xlsx", "LMS STUDENT DATA.xls", "LMS STUDENT DATA.csv",
        "lms student data.xlsx", "lms student data.xls", "lms student data.csv",
        os.path.join(DATA_DIR, "LMS STUDENT DATA.xlsx"),
        os.path.join(DATA_DIR, "lms student data.xlsx"),
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
            st.markdown("### 👨‍🎓 Registered Student Database (Classes VI – IX)")
            class_col = next((c for c in df.columns if "class" in str(c).lower()), None)
            if class_col:
                unique_classes = ["All Classes"] + sorted([str(x) for x in df[class_col].dropna().unique()])
                selected_class = st.selectbox("Filter by Class:", unique_classes, key="st_excel_filter")
                df_display = df[df[class_col].astype(str) == selected_class] if selected_class != "All Classes" else df
            else:
                df_display = df
            st.write(f"**Total Students Displayed:** {len(df_display)}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error reading {found_file}: {e}")
    else:
        st.warning("⚠️ `LMS STUDENT DATA.xlsx` file nahi mili.")
        st.info("Aap ise Admin Workspace me **Student List** me upload karein ya project folder me paste karein.")

def render_scienceutsav_assessment():
    st.markdown("### 📊 ScienceUtsav Classroom Assessment & Performance Portal")
    saved_su_url = get_saved_url(SCIENCEUTSAV_CONFIG_FILE)
    if not saved_su_url:
        saved_su_url = "https://report.scienceutsav.com/class/k57a8q5h6mzanqt4vdvn48c1vx8ba0q3/report"
    col_l1, col_l2 = st.columns([1, 1])
    col_l1.link_button("🌐 Open ScienceUtsav Portal in New Tab", saved_su_url)
    st.info("💡 Neeche live dashboard load ho raha hai. Aap upar diye gaye link se bhi direct access kar sakte hain ya Admin panel se downloaded 'Combined PDF' upload kar sakte hain.")
    components.iframe(saved_su_url, height=750, scrolling=True)

def render_annual_plan():
    st.markdown("""
    ### 📅 MONTHLY / ANNUAL STEM ACTIVITY PLAN (JULY 2026 – JANUARY 2027)
    > **Schedule:** 2 Sessions / Month (14 Total Sessions) | **Target:** 25+ Innovation Teams (Classes 6–9 | 5–6 Students Per Team)
    """)
    df_plan = pd.DataFrame(ANNUAL_PLAN_DATA)
    plan_months = ["All Months"] + sorted(list(df_plan["Month"].unique()), key=lambda x: datetime.strptime(x, "%B %Y"))
    class_options = ["All Classes", "Class 6 (Beginner Tier)", "Class 7 (Intermediate Tier)", "Class 8 (Advanced Tier)", "Class 9 (Expert Tier)"]
    
    now_dt = datetime.now()
    cur_month_str = now_dt.strftime("%B %Y")
    default_month_idx = plan_months.index(cur_month_str) if cur_month_str in plan_months else 0
    
    col_m, col_c = st.columns([1, 1])
    selected_plan_month = col_m.selectbox("📅 Filter by Month (Auto-Selected Present Month):", plan_months, index=default_month_idx, key="filter_plan_month")
    selected_plan_class = col_c.selectbox("🎓 Filter by Class:", class_options, key="filter_plan_class")
    
    filtered_df = df_plan if selected_plan_month == "All Months" else df_plan[df_plan["Month"] == selected_plan_month]
    
    if selected_plan_class == "Class 6 (Beginner Tier)":
        display_cols = ["Month", "Session #", "Class 6", "Milestone", "Roles"]
    elif selected_plan_class == "Class 7 (Intermediate Tier)":
        display_cols = ["Month", "Session #", "Class 7", "Milestone", "Roles"]
    elif selected_plan_class == "Class 8 (Advanced Tier)":
        display_cols = ["Month", "Session #", "Class 8", "Milestone", "Roles"]
    elif selected_plan_class == "Class 9 (Expert Tier)":
        display_cols = ["Month", "Session #", "Class 9", "Milestone", "Roles"]
    else:
        display_cols = ["Month", "Session #", "Class 6", "Class 7", "Class 8", "Class 9", "Milestone", "Roles"]

    st.markdown(f"**Showing Activity Plan for:** `{selected_plan_month}` | `{selected_plan_class}` ({len(filtered_df)} Sessions)")
    st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)

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
        The STEM Lab of Aditya Birla Intermediate College, Renukoot is a dedicated space for promoting Science, Technology, Engineering and Mathematics (STEM) learning through hands-on activities, experimentation, problem-solving, innovation and project-based learning. The laboratory provides students with opportunities to connect classroom concepts with real-life situations and develop practical skills through designing, making, testing and improving solutions.

        #### 2. Classes Covered
        The STEM Lab activities are primarily conducted for:
        * **Class VI** (Beginner Tier)
        * **Class VII** (Intermediate Tier)
        * **Class VIII** (Advanced Tier)
        * **Class IX** (Expert Capstone Tier)

        *Activities may also be organized for other classes as required under school programmes, competitions and special projects.*

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
        10. To encourage participation in STEM competitions and innovation programmes (Erehwon, STEM SPARK, VVM).

        #### 4. Major Areas of STEM Learning
        * **Science Experiments:** Physics, Chemistry & Biology inquiry setups.
        * **Mathematics Applications:** Data plotting, statistics & logic graphs.
        * **Electronics & Sensors:** Resistors, capacitors, LDR, DHT11, MQ2, Touch, Ultrasonic, IR, Hall.
        * **Microcontrollers & Robotics:** Arduino Uno R3, Breakout Shields, Motor Drivers, SG90 Servos, BO Motors.
        * **Coding & Computational Thinking:** C++ embedded programming, non-blocking state engines, algorithms.
        * **IoT & Smart Systems:** Sensor fusion, digital telemetry, automated controls.
        * **3D Prototyping & Design Thinking:** Bambu Lab A1 Mini 3D printer, CAD modeling, enclosure packaging.
        * **Environmental Innovation & E-waste:** Upcycling phone parts, clean water solutions, smart farming.

        #### 5. Teaching-Learning Approach
        The STEM Lab strictly follows an inquiry and maker-oriented engineering cycle:
        > **Problem Identification → Explore Science → Imagine Design → Build Prototype → Test Hardware → Code & Improve → Present to Jury**

        #### 6. Documentation System
        The following records are maintained digitally in the school portal:
        * 49-Parameter Master Repository
        * Class & Section-wise Student & Teacher Attendance CSVs
        * 56 Structured Master Lesson Plans[cite: 1]
        * Real-time ScienceUtsav Assessment LMS Linkage
        * Complete Lab Inventory and Safety Audit Records

        #### 7. Expected Learning Outcomes
        Students are trained to achieve modular prototyping hygiene, logical problem decomposition, code debugging, 3D casing assembly, team leadership, and empirical test documentation.
        """)
        return True

    elif title == "Lab Objectives & Guidelines" or sno == 2:
        st.markdown("""
        ### 📋 STEM LAB OBJECTIVES & GUIDELINES

        * **School:** Aditya Birla Intermediate College, Renukoot
        * **Academic Session:** 2026-27
        * **STEM Coordinator / SPOC:** Shashank Verma

        ---

        #### A. Objectives of the STEM Lab
        1. **Experiential Learning:** To provide students with direct hands-on modular kits, sensors, and microcontrollers.
        2. **Problem Solving:** To identify school campus and community pain points and design functional engineering solutions.
        3. **Innovation:** To build functional proof-of-concepts, alpha prototypes, and capstone demonstration models.
        4. **Scientific Temper:** To encourage hypothesis testing, sensor data calibration, and empirical trial logging.
        5. **Technology Mastery:** To develop coding proficiency in Arduino IDE, serial telemetry, and 3D printing design.

        ---

        #### B. STEM Lab Safety & Handling Guidelines
        1. **Supervision:** Students may enter and work in the lab only in the presence of the STEM Teacher or SPOC.
        2. **Electrical Safety:**
           * Verify battery/power polarity before connecting headers to the Breakout Shield.
           * Short-circuiting battery terminals or connecting 5V directly to Ground without a load is strictly prohibited.
           * Water, beverages, and food items are 100% prohibited on equipment workbenches.
        3. **Tool & Shield Maintenance:**
           * Always use 3-pin RMC ribbon cables with correct G-V-S pinout (Ground=Black, VCC=Red, Signal=Yellow).
           * Never force microcontroller pins; report bent pins or loose solder joints immediately.
           * Return all sensor modules, tools, multimeters, and jumpers to designated labeled bins after every period.
        4. **Emergency Protocol:**
           * In the event of smoke, burning smell, or electrical sparking, immediately hit the master bench power cutoff switch.
           * CO2 Fire Extinguisher and First Aid Medical Kit are stationed at the main entrance door.
        """)
        return True

    elif title == "Coordinator / SPOC Details" or sno == 3:
        st.markdown("""
        ### 👤 STEM LAB COORDINATOR / SPOC DETAILS

        **Academic Session:** 2026-27

        ---

        #### 1. School Details
        * **School Name:** Aditya Birla Intermediate College, Renukoot
        * **Location:** Renukoot, Sonbhadra, Uttar Pradesh (Pin: 231217)

        #### 2. Coordinator Information
        * **Name:** Shashank Verma
        * **Designation:** PGT
        * **Academic Qualification:** M.Sc., B.Ed.
        * **Official Role:** STEM Coordinator / School STEM SPOC
        * **Official School Email:** `shashank.verma@adityabirlaschools.in`
        * **Official Contact Number:** `9826594665`

        #### 3. Core Responsibilities
        1. Structuring and enforcing the 14-session Annual STEM Roadmap and 56 Master Lesson Plans across Classes 6–9[cite: 1].
        2. Managing digital data synchronization with Google Sheets, Google Forms, and ScienceUtsav LMS.
        3. Coordinating weekly lab timetables, section-wise student attendance, and teacher duty allocations.
        4. Overseeing equipment safety, tool inventories, Bambu Lab 3D printer maintenance, and component procurement.
        5. Mentoring 25+ student innovation teams for the National Erehwon Competition, STEM SPARK, and VVM.
        6. Preparing monthly, quarterly, and annual STEM laboratory progress reports for school management.
        """)
        return True

    elif title == "Monthly / Annual STEM Activity Plan" or sno == 4:
        render_annual_plan()
        return True

    elif title == "Class-wise Timetable" or sno == 5:
        st.markdown("""
        ### ⏰ Weekly STEM Lab Schedule (2026-27)
        * **Class VI (Sections A, B, C, D):** Tuesday & Thursday (Period 4)
        * **Class VII (Sections A, B, C, D):** Monday & Wednesday (Period 5)
        * **Class VIII (Sections A, B, C, D):** Wednesday & Friday (Period 6)
        * **Class IX (Sections A to H):** Saturday (Period 2 to 4 - 3 Period Capstone Block)
        """)
        return True

    elif title == "Session / Lesson Plans" or sno == 6:
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
        ### 📦 Verified STEM Lab Inventory (ScienceUtsav & ABPS Kit)
        * **Microcontrollers:** 25x Arduino Uno R3 (ATmega328P DIP), 25x Sensor Breakout Shields V5.0 (3-Pin G-V-S).
        * **Sensor Modules:** LDR Light, DHT11 Temp/Humidity, MQ2 Smoke/Gas, Flame, Soil Moisture, Ultrasonic HC-SR04, IR Obstacle, Hall Effect A3144, Tilt SW-520D, TTP223 Touch, Sound Mic.
        * **Actuators & Displays:** SG90 Micro Servos (0°-180°), BO Geared Motors + Wheels, 5V Relays, 16x2 I2C Character LCDs, 7-Segment Displays, Active/Passive Buzzers, RGB LEDs.
        * **3D & Prototyping:** Bambu Lab A1 Mini 3D Printer (PLA Filament), 5V DC Bench Power Adapters, Battery Cases, 3-Pin / 4-Pin RMC Ribbon Jumpers.
        """)
        return True

    elif title == "Equipment Details" or sno == 11:
        st.markdown("""
        ### 🔬 Technical Hardware Specifications
        * **Processing Unit:** Arduino Uno R3 (16 MHz Crystal, 5V Logic, 14 Digital I/O, 6 Analog Inputs).
        * **Shield Architecture:** Dedicated external servo power terminal block, I2C port (A4/A5), UART (TX/RX).
        * **Rapid Prototyping:** Bambu Lab A1 Mini FDM 3D Printer (0.4mm Nozzle, Auto-bed Leveling, 180x180x180mm Build Volume).
        """)
        return True

    elif title == "Lab Safety Rules" or sno == 15:
        st.markdown("""
        ### ⚠️ Mandatory STEM Lab Safety Protocol
        1. Always inspect wiring for short-circuits before plugging the USB / 5V DC barrel jack into the Arduino Uno.
        2. Never draw high current for servos or motors directly from Uno 5V pin; always utilize the shield's dedicated external power terminal block.
        3. Soldering and hot glue work must be performed at designated thermal workstations wearing protective safety glasses.
        4. Any component malfunction or heating issue must be immediately reported to the SPOC.
        """)
        return True

    elif title == "Safety Checklist" or sno == 16:
        st.markdown("""
        ### ✅ Periodic Laboratory Safety Audit Checklist
        * [x] **Power Breakers:** Master MCB cutoff switch and bench surge protectors fully operational.
        * [x] **Fire Suppression:** CO2 Fire Extinguisher inspected, tagged, and unobstructed at main entrance.
        * [x] **First Aid Medical Kit:** Stocked with burn cream, antiseptic, bandages, and eye-wash solution.
        * [x] **Cable Hygiene:** Anti-trip cable routing and color-coded modular storage boxes labeled.
        """)
        return True

    elif title == "STEM Activities" or sno == 17:
        st.markdown("""
        ### 💡 Core Laboratory Project Modules
        1. Smart Street Lighting with LDR Sensor and Transistor/Relay Switching.
        2. Acoustic Decibel Warning Station using Sound Sensor, RGB LED, and Buzzer.
        3. Automated Touchless Boom Barrier Gate with IR Proximity Sensor and SG90 Micro Servo.
        4. Multi-Factor Laser Optical Tripwire Security System with Capacitive Touch Disarm.
        5. Smart Agricultural Greenhouse Monitor with Soil Moisture, DHT11, and I2C LCD Readout.
        """)
        return True

    elif title == "Assessment Rubrics" or sno == 27:
        st.markdown("""
        ### 📊 Student STEM Assessment Rubric (100 Marks Distribution)
        * **Problem Identification & Research (20 Marks):** Campus problem statement clarity and engineering logbook documentation.
        * **Circuit Assembly & Hardware Hygiene (20 Marks):** Modular shield wiring, secure pin mapping, and power stability.
        * **Firmware Coding Logic (20 Marks):** Non-blocking millis() loops, conditional thresholds, and bug-free syntax.
        * **Enclosure & Packaging (20 Marks):** Mechanical chassis stability, 3D printed / cardboard casing, and cable looming.
        * **Oral Defense & Live Demonstration (20 Marks):** 3-minute pitch, prototype autonomy, and jury Q&A handling.
        """)
        return True

    elif title == "Student Assessment" or sno == 28:
        render_scienceutsav_assessment()
        return True

    elif title == "Teacher Training Records" or sno == 35:
        st.markdown("""
        ### 🧑‍🏫 Teacher STEM Capacity Building & Training Record
        * **Conducted By:** ScienceUtsav Technical Expert Team & ABIC STEM Coordinator.
        * **Core Modules Covered:** Sensor Breakout Shield Architecture, Modular C++ Embedded Coding, Bambu Lab 3D Slicing & Printing, Student Mentorship Pedagogy.
        * **Participating Faculty:** 10 Designated Science & STEM Faculty Members.
        """)
        return True

    elif title == "Annual Report" or sno == 46:
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
