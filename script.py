import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

try:
    import pypdfium2 as pdfium
    PDFIUM_AVAILABLE = True
except ImportError:
    PDFIUM_AVAILABLE = False

st.set_page_config(page_title="ABIC STEM Lab Portal", page_icon="🔬", layout="wide")

UPLOAD_DIR = "stem_lab_records"
DATA_DIR = "portal_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

STUDENT_ATTENDANCE_FILE = os.path.join(DATA_DIR, "student_attendance.csv")
TEACHER_ATTENDANCE_FILE = os.path.join(DATA_DIR, "teacher_attendance.csv")
PRINCIPAL_MSG_FILE = os.path.join(DATA_DIR, "principal_message.txt")
SHEET_CONFIG_FILE = os.path.join(DATA_DIR, "gsheet_url.txt")
FORM_CONFIG_FILE = os.path.join(DATA_DIR, "gform_url.txt")

MONTHS = ["April", "May", "June", "July", "August", "September", "October", "November", "December", "January", "February", "March"]
WEEKS = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# ----------------- CURRENT REAL-TIME MONTH & WEEK -----------------
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
    "Mrs. Manju Bala Jindal",
    "Mrs. Dev Jyoti Choudhary",
    "Mrs. Monika Mishra",
    "Mr. Shiv Narayan Singh",
    "Mr. Shashank Verma",
    "Mr. Shashank Shekhar Tiwari",
    "Dr. Rakesh Singh",
    "Mr. Chandra Mohan Singh",
    "Mr. Harendra Dwivedi",
    "Mr. Praveen Kumar"
]

# ----------------- URL / SHEET SYNC HELPERS -----------------
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
                return None, "Invalid Google Sheet link. Ensure it has '/d/SHEET_ID/'."
            sheet_id = match.group(1)
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            
        df = pd.read_csv(csv_url, dtype=str).fillna("")
        return df, None
    except Exception as e:
        return None, f"Error fetching Sheet: {e}"

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
            month_name = dt.strftime("%B") if pd.notnull(dt) else "April"
            week_num = min(5, ((dt.day - 1) // 7) + 1) if pd.notnull(dt) else 1
            week_name = f"Week {week_num}"
            if not raw_day and pd.notnull(dt):
                raw_day = dt.strftime("%A")
        except Exception:
            month_name = "April"
            week_name = "Week 1"

        st_match_idx = df_st_all[
            (df_st_all["Month"] == month_name) & 
            (df_st_all["Week"] == week_name) & 
            (df_st_all["Class & Section"] == raw_class)
        ].index

        new_st_row = {
            "Month": month_name,
            "Week": week_name,
            "Date": raw_date.split(" ")[0],
            "Day": raw_day,
            "Class & Section": raw_class,
            "Total Students": raw_tot,
            "Period 1": raw_period,
            "Period 2": "",
            "Total Present": raw_pres,
            "Total Absent": raw_abs
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
            "Month": month_name,
            "Week": week_name,
            "Date": raw_date.split(" ")[0],
            "Day": raw_day,
            "S.No.": str(len(df_tc_all) + 1),
            "Teacher Name": raw_teacher,
            "Class & Section Taught": raw_class,
            "Period / Time Slot": raw_period,
            "Lab Activity / Topic Covered": raw_topic,
            "Total Present Students": raw_pres,
            "In-Time": raw_in,
            "Out-Time": raw_out,
            "Teacher Signature": "Verified"
        }

        if len(tc_match_idx) > 0:
            for k, v in new_tc_row.items():
                df_tc_all.loc[tc_match_idx[0], k] = v
        else:
            df_tc_all = pd.concat([df_tc_all, pd.DataFrame([new_tc_row])], ignore_index=True)

    df_st_all.to_csv(STUDENT_ATTENDANCE_FILE, index=False)
    df_tc_all.to_csv(TEACHER_ATTENDANCE_FILE, index=False)
    return True, f"Successfully synced {len(df_raw)} records from Google Sheet!"

# ----------------- COVER & PRINCIPAL -----------------
def render_cover_photo():
    possible_covers = [
        "cover photo.jpg", "cover photo.png", "cover photo.jpeg", "cover photo.webp",
        os.path.join(DATA_DIR, "cover photo.jpg"),
        os.path.join(DATA_DIR, "cover photo.png"),
        os.path.join(DATA_DIR, "cover photo.jpeg"),
        "cover.jpg", "cover.png", "cover.jpeg"
    ]
    found_cover = next((c for c in possible_covers if os.path.exists(c)), None)
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

# ----------------- ATTENDANCE INIT & DATA -----------------
def init_student_attendance():
    needs_init = True
    if os.path.exists(STUDENT_ATTENDANCE_FILE):
        try:
            temp_df = pd.read_csv(STUDENT_ATTENDANCE_FILE)
            required_cols = {"Month", "Week", "Date", "Day", "Class & Section", "Total Students", "Period 1", "Period 2", "Total Present", "Total Absent"}
            if required_cols.issubset(set(temp_df.columns)):
                needs_init = False
        except Exception:
            needs_init = True

    if needs_init:
        structure = {
            "Month": [], "Week": [], "Date": [], "Day": [], "Class & Section": [],
            "Total Students": [], "Period 1": [], "Period 2": [], "Total Present": [], "Total Absent": []
        }
        pd.DataFrame(structure).to_csv(STUDENT_ATTENDANCE_FILE, index=False)

def init_teacher_attendance():
    needs_init = True
    if os.path.exists(TEACHER_ATTENDANCE_FILE):
        try:
            temp_df = pd.read_csv(TEACHER_ATTENDANCE_FILE)
            required_cols = {"Month", "Week", "Date", "Day", "S.No.", "Teacher Name", "Class & Section Taught", "Period / Time Slot", "Lab Activity / Topic Covered", "Total Present Students", "In-Time", "Out-Time", "Teacher Signature"}
            if required_cols.issubset(set(temp_df.columns)):
                needs_init = False
        except Exception:
            needs_init = True

    if needs_init:
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
            cols_to_drop = [c for c in ["Month", "Week"] if c in filtered.columns]
            return filtered.drop(columns=cols_to_drop)
    
    return pd.DataFrame({
        "Date": ["" for _ in SECTIONS_LIST],
        "Day": ["" for _ in SECTIONS_LIST],
        "Class & Section": SECTIONS_LIST,
        "Total Students": ["" for _ in SECTIONS_LIST],
        "Period 1": ["" for _ in SECTIONS_LIST],
        "Period 2": ["" for _ in SECTIONS_LIST],
        "Total Present": ["" for _ in SECTIONS_LIST],
        "Total Absent": ["" for _ in SECTIONS_LIST]
    })

def save_student_attendance_slot(month, week, edited_df):
    df_all = get_student_attendance_all()
    edited_df = edited_df.copy()
    edited_df["Month"] = str(month)
    edited_df["Week"] = str(week)
    
    if df_all.empty:
        df_updated = edited_df
    else:
        df_remaining = df_all[~((df_all["Month"] == str(month)) & (df_all["Week"] == str(week)))]
        df_updated = pd.concat([df_remaining, edited_df], ignore_index=True)
        
    df_updated.to_csv(STUDENT_ATTENDANCE_FILE, index=False)

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
            cols_to_drop = [c for c in ["Month", "Week"] if c in filtered.columns]
            return filtered.drop(columns=cols_to_drop)
    
    return pd.DataFrame({
        "Date": ["" for _ in TEACHERS_LIST],
        "Day": ["" for _ in TEACHERS_LIST],
        "S.No.": list(range(1, len(TEACHERS_LIST) + 1)),
        "Teacher Name": TEACHERS_LIST,
        "Class & Section Taught": ["" for _ in TEACHERS_LIST],
        "Period / Time Slot": ["" for _ in TEACHERS_LIST],
        "Lab Activity / Topic Covered": ["" for _ in TEACHERS_LIST],
        "Total Present Students": ["" for _ in TEACHERS_LIST],
        "In-Time": ["" for _ in TEACHERS_LIST],
        "Out-Time": ["" for _ in TEACHERS_LIST],
        "Teacher Signature": ["" for _ in TEACHERS_LIST]
    })

def save_teacher_attendance_slot(month, week, edited_df):
    df_all = get_teacher_attendance_all()
    edited_df = edited_df.copy()
    edited_df["Month"] = str(month)
    edited_df["Week"] = str(week)
    
    if df_all.empty:
        df_updated = edited_df
    else:
        df_remaining = df_all[~((df_all["Month"] == str(month)) & (df_all["Week"] == str(week)))]
        df_updated = pd.concat([df_remaining, edited_df], ignore_index=True)
        
    df_updated.to_csv(TEACHER_ATTENDANCE_FILE, index=False)

# ----------------- UNIVERSAL FILE RENDERER -----------------
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
                    page = pdf[page_num]
                    image = page.render(scale=2).to_pil()
                    st.image(image, caption=f"Page {page_num + 1} of {len(pdf)}", use_container_width=True)
            except Exception:
                pass
        
        with open(file_path, "rb") as f:
            st.download_button(
                label=f"📥 Download / Open PDF ({file_name})",
                data=f.read(),
                file_name=file_name,
                mime="application/pdf",
                key=f"dl_pdf_{unique_key}"
            )

    elif ext in [".mp4", ".mov", ".avi", ".mkv"]:
        st.video(file_path)

    else:
        with open(file_path, "rb") as f:
            st.download_button(
                label=f"📥 Download File ({file_name})",
                data=f.read(),
                file_name=file_name,
                key=f"dl_doc_{unique_key}"
            )

# ----------------- STUDENT EXCEL VIEWER (PARAMETER #8) -----------------
def render_student_excel():
    possible_paths = [
        "LMS STUDENT DATA.xlsx", "LMS STUDENT DATA.xls", "LMS STUDENT DATA.csv",
        "lms student data.xlsx", "lms student data.xls", "lms student data.csv",
        os.path.join(DATA_DIR, "LMS STUDENT DATA.xlsx"),
        os.path.join(DATA_DIR, "lms student data.xlsx"),
        os.path.join(UPLOAD_DIR, "08_Student_List", "LMS STUDENT DATA.xlsx"),
        os.path.join(UPLOAD_DIR, "08_Student_List", "lms student data.xlsx"),
    ]
    
    upload_s8_dir = os.path.join(UPLOAD_DIR, "08_Student_List")
    if os.path.exists(upload_s8_dir):
        for f in os.listdir(upload_s8_dir):
            if f.lower().endswith((".xlsx", ".xls", ".csv")):
                possible_paths.append(os.path.join(upload_s8_dir, f))

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
        st.info("Aap ise Admin Workspace me **#8. Student List** me upload karein ya project folder me paste karein.")

# ----------------- ATTENDANCE VIEWER FUNCTIONS -----------------
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

# ----------------- COMPLETE EMBEDDED MASTER DATA -----------------
def render_profile():
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
    * Class VI
    * Class VII
    * Class VIII
    * Class IX

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
    10. To encourage participation in STEM competitions and innovation programmes.

    #### 4. Major Areas of STEM Learning
    * Science Experiments
    * Mathematics Applications
    * Electronics
    * Arduino and Microcontrollers
    * Robotics
    * Sensors and Actuators
    * Coding and Computational Thinking
    * IoT and Smart Systems
    * Design Thinking
    * 3D/Prototype Development
    * Environmental Innovation
    * E-waste Management
    * Problem Identification and Solution Development

    #### 5. Teaching-Learning Approach
    The STEM Lab follows an activity-oriented approach based on:
    > **Problem → Explore → Imagine Design → Build → Test → Improve → Present**

    Students are encouraged to work individually as well as in teams.

    #### 6. Major Activities
    The STEM Lab may conduct:
    * Hands-on STEM activities
    * Experiments and demonstrations
    * Design challenges
    * Innovation challenges
    * Project development
    * Prototype development
    * Robotics and electronics activities
    * Coding activities
    * STEM competitions
    * Workshops and training programmes
    * Exhibition and project presentations

    #### 7. Documentation
    The following records are maintained digitally:
    * Student records
    * Attendance
    * Inventory
    * Activity reports
    * Lesson/session plans
    * Project reports
    * Assessment records
    * Training records
    * Competition records
    * Photographs and videos
    * Circulars and official communication
    * Monthly and annual reports

    #### 8. Expected Learning Outcomes
    Students participating in STEM Lab activities are expected to develop:
    * Observation skills
    * Scientific reasoning
    * Problem-solving ability
    * Creativity
    * Computational thinking
    * Design and prototyping skills
    * Teamwork
    * Communication skills
    * Presentation skills
    * Innovation mindset

    #### 9. Evidence of STEM Lab Activities
    Evidence is maintained through:
    * Activity reports
    * Student worksheets
    * Project reports
    * Photographs
    * Videos
    * Assessment records
    * Certificates
    * Competition results
    * Student presentations
    """)

def render_guidelines():
    st.markdown("""
    ### 📋 STEM LAB OBJECTIVES & GUIDELINES

    * **School:** Aditya Birla Intermediate College, Renukoot
    * **Academic Session:** 2026-27
    * **STEM Coordinator / SPOC:** Shashank Verma

    ---

    #### A. Objectives of the STEM Lab

    1. **Experiential Learning:** To provide students with opportunities to learn through practical activities, experiments, and hands-on projects.
    2. **Problem Solving:** To encourage students to identify real-life problems, analyse them, and develop appropriate solutions.
    3. **Innovation:** To promote the ability of students to develop new ideas, designs, and prototypes.
    4. **Scientific Temper:** To develop the habits of observation, questioning, experimentation, evidence-based reasoning, and drawing logical conclusions.
    5. **Technology Skills:** To introduce students to coding, electronics, sensors, microcontrollers, robotics, and digital tools.
    6. **Collaboration:** To promote teamwork, peer learning, and collaborative problem solving.
    7. **Communication:** To provide students with opportunities to effectively explain and present their ideas, experiments, and projects.

    ---

    #### B. STEM Lab Guidelines

    ##### 1. General Rules
    * Students shall enter the STEM Lab only with the permission of the teacher/instructor.
    * Students shall use equipment only as instructed and for the designated activity.
    * Discipline and silence shall be maintained inside the lab.
    * No equipment shall be removed from the lab without permission.
    * After completing an activity, all materials shall be returned to their designated places.

    ##### 2. Safety Guidelines
    * Electrical equipment shall be handled carefully.
    * Damaged wires or equipment shall not be used.
    * Power supplies shall not be connected or disconnected without permission.
    * Water and electrical equipment shall be kept away from each other.
    * Any problem or malfunction in equipment shall be immediately reported to the teacher.
    * Running, pushing, or any form of unsafe behaviour inside the lab is strictly prohibited.
    * In case of an emergency, students shall follow the instructions of the teacher/instructor.

    ##### 3. Equipment Handling
    * Arduino boards, sensors, motors, and electronic components shall be handled carefully.
    * Components shall be stored in their designated boxes/containers after use.
    * Tools shall be used only for their intended purpose.
    * The condition of equipment shall be checked after every experiment/activity.
    * Any damaged equipment shall be reported and recorded in the Inventory/Maintenance Record.

    ##### 4. Student Responsibilities
    Students shall:
    * Follow all instructions given by the teacher/instructor.
    * Keep their workstation clean and organised.
    * Cooperate with other members of their team.
    * Record observations made during experiments and activities.
    * Properly document their projects and work.

    ##### 5. Documentation Guidelines
    For every major STEM activity/project, the following evidence should be maintained:
    > **Activity Name → Date → Class → Participants → Objective → Materials → Procedure → Outcome → Assessment → Photographs**

    ##### 6. Digital Record Management
    * STEM Lab records shall be systematically maintained in the designated Google Drive/School Digital Storage.
    * Important documents and records shall be backed up regularly to prevent data loss.

    ##### 7. Review
    * STEM Lab activities and records shall be reviewed periodically by the STEM Coordinator/SPOC to ensure proper implementation, documentation, safety, and record maintenance.
    """)

def render_spoc():
    st.markdown("""
    ### 👤 STEM LAB COORDINATOR / SPOC DETAILS

    **Academic Session:** 2026-27

    ---

    #### 1. School Details
    * **School Name:** Aditya Birla Intermediate College, Renukoot
    * **Location:** Renukoot, Sonbhadra, Uttar Pradesh

    #### 2. STEM Coordinator / SPOC
    * **Name:** Shashank Verma
    * **Designation:** PGT
    * **Academic Qualification:** M.Sc., B.Ed.
    * **Role:** STEM Coordinator / STEM Lab SPOC

    #### 3. Major Responsibilities
    The STEM Coordinator / SPOC is responsible for:
    1. Planning and coordinating STEM Lab activities.
    2. Preparing the annual and monthly STEM activity plan.
    3. Coordinating STEM Lab sessions for designated classes.
    4. Maintaining student participation and attendance records.
    5. Maintaining the STEM Lab inventory and equipment records.
    6. Coordinating maintenance and safe use of equipment.
    7. Supporting teachers in conducting STEM activities.
    8. Coordinating student projects and prototypes.
    9. Encouraging participation in STEM competitions and innovation programmes.
    10. Coordinating STEM SPARK and other STEM-related programmes.
    11. Maintaining activity photographs, videos and reports.
    12. Maintaining training and workshop records.
    13. Preparing monthly, quarterly and annual STEM Lab reports.
    14. Coordinating communication with school administration and programme authorities.
    15. Promoting a safe, innovative and collaborative learning environment in the STEM Lab.

    #### 4. Key Focus Areas
    * Experiential Learning | Project-Based Learning | Design Thinking | Innovation | Robotics | Electronics | Coding | Prototyping | Problem Solving | STEM Competitions

    #### 5. Record Maintenance
    The Coordinator/SPOC will ensure systematic maintenance of:
    * Lab Inventory | Attendance | Activity Records | Project Records | Assessment Records | Training Records | Competition Records | Safety Records | Circulars and Communication | Photo/Video Documentation | Monthly and Annual Reports

    #### 6. Contact Details
    * **Official School Email:** `shashank.verma@adityabirlaschools.in`
    * **Official Contact Number:** `9826594665`
    """)

BUILTIN_RECORDS = {
    1: {"title": "STEM Lab Profile", "render": render_profile},
    2: {"title": "Lab Objectives & Guidelines", "render": render_guidelines},
    3: {"title": "Coordinator / SPOC Details", "render": render_spoc},
    4: {"title": "Annual STEM Plan", "render": lambda: st.markdown("""
        ### 📅 Annual STEM Academic Roadmap (2026-27)
        * **Quarter 1 (Apr - Jul):** Fundamentals of Circuits, Electronic Components, Basic Sensor Interfacing.
        * **Quarter 2 (Aug - Oct):** Arduino Microcontroller Programming, Display Systems, STEM SPARK Ideation.
        * **Quarter 3 (Nov - Jan):** Robotics, Motor Drivers, 3D Design & 3D Printing Prototyping.
        * **Quarter 4 (Feb - Mar):** Capstone Project Exhibitions, Annual Lab Safety Audits, Student Portfolios.
    """)},
    6: {"title": "Class-wise Timetable", "render": lambda: st.markdown("""
        ### ⏰ Weekly STEM Lab Schedule
        * **Class VI:** Tuesday & Thursday (Period 4)
        * **Class VII:** Monday & Wednesday (Period 5)
        * **Class VIII:** Wednesday & Friday (Period 6)
        * **Class IX:** Saturday (Period 2 to 4)
    """)},
    8: {"title": "Student List (Class VI to IX)", "render": render_student_excel},
    9: {"title": "Student Attendance", "render": render_student_attendance_viewer},
    10: {"title": "Teacher Attendance", "render": render_teacher_attendance_viewer},
    11: {"title": "Lab Inventory (Teacher & Student Kits)", "render": lambda: st.markdown("""
        ### 📦 Verified STEM Lab Inventory
        * **Supplier / Source:** ScienceUtsav & ABPS Kit
        * **Controllers:** Arduino UNO DIP Microcontrollers, Custom Expansion Shields.
        * **Sensors:** DHT11 Temp/Humidity, Rain, Vibration, Ultrasonic, MQ2 Gas, Flame, Moisture, LDR, Touch.
        * **Actuators & 3D:** BO Motors, SG90 Servos, Water Pumps, Bambu Lab A1 Mini 3D Printer.
    """)},
    12: {"title": "Equipment Details", "render": lambda: st.markdown("""
        ### 🔬 Technical Equipment Details
        * **Microcontroller:** Arduino Uno (ATmega328P DIP), 16 MHz Clock, 5V.
        * **Connectors:** 3-Pin / 4-Pin RMC locking connectors.
        * **Prototyping:** Bambu Lab A1 Mini FDM 3D Printer.
    """)},
    16: {"title": "Lab Safety Rules", "render": lambda: st.markdown("""
        ### ⚠️ Mandatory STEM Lab Safety Rules
        1. Entry permitted only under teacher/instructor supervision.
        2. Never short circuit battery terminals; verify circuit polarity before turning on power.
        3. Zero food and liquid zone near equipment workbenches.
        4. In case of smoke or loose wiring, immediately switch off main bench supply.
    """)},
    17: {"title": "Safety Checklist", "render": lambda: st.markdown("""
        ### ✅ Laboratory Periodic Safety Audit Checklist
        * [x] **Fire Safety:** CO2 Fire Extinguisher inspected at lab entrance.
        * [x] **First Aid:** Fully-stocked medical kit accessible.
        * [x] **Power Infrastructure:** Surge protectors and MCB circuit breakers active.
        * [x] **Tool Storage:** Screwdrivers, strippers, and cutters organized in labeled toolboxes.
    """)},
    18: {"title": "STEM Activities", "render": lambda: st.markdown("""
        ### 💡 Core Laboratory Activity Modules
        1. Automatic Smart Street Light (LDR + Transistor)
        2. Smart Fire & Smoke Alert System (MQ2 + Flame Sensor)
        3. Obstacle Avoidance Robot (Ultrasonic + Servo + BO Motors)
        4. Weather Monitoring Station (DHT11 + 16x2 LCD)
        5. Automated Plant Watering System (Soil Moisture Probe + DC Pump)
    """)},
    28: {"title": "Assessment Rubrics", "render": lambda: st.markdown("""
        ### 📊 Student STEM Assessment Framework
        * **Problem Definition:** 20% | **Circuit Assembly:** 20% | **Coding Logic:** 20% | **Prototyping:** 20% | **Presentation:** 20%
    """)},
    36: {"title": "Teacher Training Records", "render": lambda: st.markdown("""
        ### 🧑‍🏫 STEM Capacity Building & Teacher Training
        * **Conducted by:** ScienceUtsav Technical Team & STEM SPOC
        * **Topics:** Arduino Programming, 3D Design/Printing, Sensor Interfacing & Pedagogy.
    """)},
    47: {"title": "Annual Report", "render": lambda: st.markdown("""
        ### 📑 Annual STEM Innovation Lab Report (2026-27 Executive Summary)
        * Over 400+ students actively trained from Classes VI to IX.
        * 15+ student working prototypes completed.
        * 100% equipment verified and active.
    """)}
}

CATEGORIES = {
    "1. Administration & Planning": [
        (1, "STEM Lab Profile"), (2, "Lab Objectives & Guidelines"), (3, "Coordinator / SPOC Details"),
        (4, "Annual STEM Plan"), (5, "Monthly Activity Plan"), (6, "Class-wise Timetable"),
        (7, "Session / Lesson Plans"), (8, "Student List"), (9, "Student Attendance"), (10, "Teacher Attendance"),
    ],
    "2. Inventory & Safety": [
        (11, "Lab Inventory"), (12, "Equipment Details"), (13, "Equipment Photos"),
        (14, "Equipment Purchase Records"), (15, "Maintenance Records"), (16, "Lab Safety Rules"), (17, "Safety Checklist"),
    ],
    "3. Activities & Projects": [
        (18, "STEM Activities"), (19, "Activity Worksheets"), (20, "Activity Photos"),
        (21, "Activity Videos"), (22, "Student Projects"), (23, "Prototype Details"),
        (24, "Problem Statements"), (25, "Innovation Ideas"), (26, "Project Photos"), (27, "Project Videos"),
    ],
    "4. Assessment & Competitions": [
        (28, "Assessment Rubrics"), (29, "Student Assessment"), (30, "Student Performance"),
        (31, "STEM SPARK Registration"), (32, "STEM SPARK Team Details"), (33, "STEM SPARK Submissions"),
        (34, "VVM Records"), (35, "Other Competitions"),
    ],
    "5. Training & Communication": [
        (36, "Teacher Training Records"), (37, "Training Certificates"), (38, "Training Attendance"),
        (39, "Workshop Reports"), (40, "Workshop Photos"), (41, "Government Circulars"),
        (42, "School Circulars"), (43, "Official Emails"), (44, "Meeting Minutes"),
    ],
    "6. Reports & Achievements": [
        (45, "Monthly Reports"), (46, "Quarterly Reports"), (47, "Annual Report"),
        (48, "Student Certificates"), (49, "Student Achievements"), (50, "STEM Lab Event Photos"),
    ]
}

def get_folder_name(sno, title):
    return f"{sno:02d}_{title.replace(' ', '_').replace('/', '_')}"

# ----------------- SIDEBAR NAVIGATION -----------------
st.sidebar.title("🔬 ABIC STEM Portal")
st.sidebar.caption("Aditya Birla Intermediate College, Renukoot")
access_mode = st.sidebar.radio("Navigation Mode", ["Public Viewer", "Admin Workspace"])

# ----------------- SESSION AUTH -----------------
if "is_admin_logged_in" not in st.session_state:
    st.session_state.is_admin_logged_in = False

# ----------------- ADMIN WORKSPACE -----------------
if access_mode == "Admin Workspace":
    st.sidebar.markdown("---")
    
    if not st.session_state.is_admin_logged_in:
        st.sidebar.subheader("Admin Login")
        password_input = st.sidebar.text_input("Enter Admin Password", type="password", key="login_pass_input")
        
        if password_input == "stem@admin123" or st.sidebar.button("Login", type="primary"):
            if password_input == "stem@admin123":
                st.session_state.is_admin_logged_in = True
                st.rerun()
            else:
                st.sidebar.error("Incorrect Password")
    else:
        st.sidebar.success("Authenticated as SPOC")
        if st.sidebar.button("🚪 Logout"):
            st.session_state.is_admin_logged_in = False
            st.rerun()

    if st.session_state.is_admin_logged_in:
        render_cover_photo()
        render_principal_message()
        st.title("⚙️ Admin Workspace: Manage Records & Live Attendance")

        # GOOGLE SYNC SETTINGS
        with st.expander("🔗 **Google Forms & Google Sheets Auto-Sync Settings**", expanded=False):
            st.markdown("##### 1. Connect Google Sheet (Responses)")
            current_sheet_url = get_saved_url(SHEET_CONFIG_FILE)
            sheet_input = st.text_input("Google Sheet Share Link (Anyone with link = Viewer):", value=current_sheet_url, placeholder="https://docs.google.com/spreadsheets/d/...")
            
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
            form_input = st.text_input("Google Form Link (For Teachers to Fill):", value=current_form_url, placeholder="https://forms.gle/...")
            if st.button("💾 Save Form Link"):
                save_url(FORM_CONFIG_FILE, form_input)
                st.success("Google Form link saved!")

        # COVER PHOTO & PRINCIPAL MESSAGE MANAGEMENT
        with st.expander("🖼️ **Update Cover Photo & Principal Message**", expanded=False):
            st.subheader("1. Update Cover Photo (Banner)")
            cover_file = st.file_uploader("Upload Cover Photo (JPG/PNG)", type=["jpg", "jpeg", "png", "webp"], key="upload_cover_banner")
            if cover_file:
                c_ext = os.path.splitext(cover_file.name)[1].lower()
                save_cover_path = os.path.join(DATA_DIR, f"cover photo{c_ext}")
                with open(save_cover_path, "wb") as f:
                    f.write(cover_file.getbuffer())
                st.success("Cover Photo successfully updated!")
                st.rerun()
            
            st.divider()
            st.subheader("2. Edit Principal's Message")
            current_p_msg = get_principal_message()
            edited_p_msg = st.text_area("Principal Message Text:", value=current_p_msg, height=120)
            if st.button("💾 Save Principal's Message", type="primary", key="save_p_msg_btn"):
                save_principal_message(edited_p_msg)
                st.success("Principal Message successfully saved!")
                st.rerun()

        # FAST LEFT-ALIGNED ADMIN SELECTOR
        selected_section = st.selectbox("Select Category to Manage", list(CATEGORIES.keys()))
        items = CATEGORIES[selected_section]
        
        param_options = {f"#{sno}. {title}": (sno, title) for sno, title in items}
        selected_param_label = st.selectbox("Select Parameter to Edit / Upload:", list(param_options.keys()))
        sno, title = param_options[selected_param_label]
        
        st.divider()
        st.markdown(f"### ⚙️ Managing: #{sno}. {title}")

        folder_name = get_folder_name(sno, title)
        record_dir = os.path.join(UPLOAD_DIR, folder_name)
        os.makedirs(record_dir, exist_ok=True)

        if sno == 9:
            st.markdown("#### 📝 Edit Student Attendance (Month & Week-wise)")
            cur_m_idx, cur_w_idx = get_current_indices()
            col_adm_st_m, col_adm_st_w = st.columns(2)
            admin_st_month = col_adm_st_m.selectbox("Select Month (Student):", MONTHS, index=cur_m_idx, key="admin_st_month")
            admin_st_week = col_adm_st_w.selectbox("Select Week (Student):", WEEKS, index=cur_w_idx, key="admin_st_week")
            
            st.caption(f"Editing Student Attendance: **{admin_st_month} | {admin_st_week}**")
            current_st_slot_df = get_student_attendance_for_slot(admin_st_month, admin_st_week)
            editor_st_slot_key = f"admin_st_editor_{admin_st_month}_{admin_st_week}"
            
            student_column_config = {
                "Date": st.column_config.TextColumn("Date (DD/MM/YYYY)"),
                "Day": st.column_config.SelectboxColumn("Day", options=DAYS, required=False)
            }
            
            edited_st_slot_df = st.data_editor(
                current_st_slot_df,
                column_config=student_column_config,
                num_rows="dynamic",
                use_container_width=True,
                key=editor_st_slot_key
            )
            
            if st.button(f"💾 Save Student Attendance for {admin_st_month} ({admin_st_week})", type="primary", key="save_st_slot_btn"):
                save_student_attendance_slot(admin_st_month, admin_st_week, edited_st_slot_df)
                st.success(f"Student Attendance for {admin_st_month} - {admin_st_week} saved!")
                st.rerun()

        elif sno == 10:
            st.markdown("#### 🧑‍🏫 Edit Teacher Attendance (Month & Week-wise)")
            cur_m_idx, cur_w_idx = get_current_indices()
            col_adm_tc_m, col_adm_tc_w = st.columns(2)
            admin_tc_month = col_adm_tc_m.selectbox("Select Month (Teacher):", MONTHS, index=cur_m_idx, key="admin_tc_month")
            admin_tc_week = col_adm_tc_w.selectbox("Select Week (Teacher):", WEEKS, index=cur_w_idx, key="admin_tc_week")
            
            st.caption(f"Editing Teacher Attendance: **{admin_tc_month} | {admin_tc_week}**")
            current_tc_slot_df = get_teacher_attendance_for_slot(admin_tc_month, admin_tc_week)
            editor_tc_slot_key = f"admin_tc_editor_{admin_tc_month}_{admin_tc_week}"
            
            teacher_column_config = {
                "Date": st.column_config.TextColumn("Date (DD/MM/YYYY)"),
                "Day": st.column_config.SelectboxColumn("Day", options=DAYS, required=False)
            }
            
            edited_tc_slot_df = st.data_editor(
                current_tc_slot_df,
                column_config=teacher_column_config,
                num_rows="dynamic",
                use_container_width=True,
                key=editor_tc_slot_key
            )
            
            if st.button(f"💾 Save Teacher Attendance for {admin_tc_month} ({admin_tc_week})", type="primary", key="save_tc_slot_btn"):
                save_teacher_attendance_slot(admin_tc_month, admin_tc_week, edited_tc_slot_df)
                st.success(f"Teacher Attendance for {admin_tc_month} - {admin_tc_week} saved!")
                st.rerun()

        else:
            uploaded_files = st.file_uploader(
                f"Upload files for #{sno} (All Formats Allowed)",
                type=None,
                accept_multiple_files=True,
                key=f"upload_{sno}"
            )

            if uploaded_files:
                for f in uploaded_files:
                    with open(os.path.join(record_dir, f.name), "wb") as buffer:
                                buffer.write(f.getbuffer())
                st.success(f"Saved {len(uploaded_files)} file(s).")
                st.rerun()

            existing_files = os.listdir(record_dir)
            if existing_files:
                st.markdown("**Manage Uploaded Files:**")
                for fname in existing_files:
                    col_a, col_b = st.columns([5, 1])
                    col_a.text(f"📄 {fname}")
                    if col_b.button("Delete", key=f"del_{sno}_{fname}"):
                        os.remove(os.path.join(record_dir, fname))
                        st.rerun()

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
        c_cat, c_param = st.columns([1, 2])
        selected_pub_cat = c_cat.selectbox("📑 Select Category:", list(CATEGORIES.keys()))
        
        cat_items = CATEGORIES[selected_pub_cat]
        pub_options = {f"#{sno}. {title}": (sno, title) for sno, title in cat_items}
        selected_pub_label = c_param.selectbox("🔍 Select Parameter to View:", list(pub_options.keys()))
        
        sel_sno, sel_title = pub_options[selected_pub_label]
        
        st.divider()
        st.subheader(f"📌 #{sel_sno}. {sel_title}")
        
        is_builtin = sel_sno in BUILTIN_RECORDS
        if is_builtin:
            BUILTIN_RECORDS[sel_sno]["render"]()

        folder_name = get_folder_name(sel_sno, sel_title)
        record_dir = os.path.join(UPLOAD_DIR, folder_name)
        files = os.listdir(record_dir) if os.path.exists(record_dir) else []

        if files:
            st.markdown("---")
            st.markdown("##### 📁 Uploaded Documents & Files:")
            for idx, fname in enumerate(files):
                fpath = os.path.join(record_dir, fname)
                render_file_preview(fpath, fname, f"{sel_sno}_{idx}")
                st.write("")
        elif not is_builtin:
            st.info("No document uploaded yet for this section.")

    with tab2:
        total = 50
        completed = 0
        summary_rows = []

        for section_name, items in CATEGORIES.items():
            for sno, title in items:
                folder_name = get_folder_name(sno, title)
                record_dir = os.path.join(UPLOAD_DIR, folder_name)
                file_count = len(os.listdir(record_dir)) if os.path.exists(record_dir) else 0

                if sno in BUILTIN_RECORDS or file_count > 0:
                    completed += 1
                    status = "✅ Active / Verified"
                else:
                    status = "⏳ Pending Upload"

                summary_rows.append({
                    "Index": sno,
                    "Parameter Name": title,
                    "Section": section_name,
                    "Status": status
                })

        col1, col2 = st.columns(2)
        col1.metric("Total Parameters", total)
        col2.metric("Completed / Active", f"{completed} / {total}")
        st.dataframe(summary_rows, use_container_width=True)
