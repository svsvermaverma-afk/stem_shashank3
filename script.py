import streamlit as st
import pandas as pd
import os

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

MONTHS = ["April", "May", "June", "July", "August", "September", "October", "November", "December", "January", "February", "March"]
WEEKS = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]

# Detailed Section-wise breakdown (Class 6th to 9th)
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

# ----------------- ATTENDANCE INITIALIZATION (AUTO-MIGRATING) -----------------
def init_student_attendance():
    needs_init = True
    if os.path.exists(STUDENT_ATTENDANCE_FILE):
        try:
            temp_df = pd.read_csv(STUDENT_ATTENDANCE_FILE)
            if "Month" in temp_df.columns and "Week" in temp_df.columns:
                needs_init = False
        except Exception:
            needs_init = True

    if needs_init:
        structure = {
            "Month": [],
            "Week": [],
            "Class & Section": [],
            "Total Registered Students": [],
            "Total Working Days": [],
            "Sessions Planned": [],
            "Sessions Conducted": [],
            "Total Present Count": [],
            "Total Absent Count": [],
            "Average Attendance %": [],
            "Remarks": []
        }
        pd.DataFrame(structure).to_csv(STUDENT_ATTENDANCE_FILE, index=False)

def init_teacher_attendance():
    needs_init = True
    if os.path.exists(TEACHER_ATTENDANCE_FILE):
        try:
            temp_df = pd.read_csv(TEACHER_ATTENDANCE_FILE)
            if "Month" in temp_df.columns and "Week" in temp_df.columns:
                needs_init = False
        except Exception:
            needs_init = True

    if needs_init:
        structure = {
            "Month": [],
            "Week": [],
            "S.No.": [],
            "Teacher Name": [],
            "Class & Section Taught": [],
            "Period / Time Slot": [],
            "Lab Activity / Topic Covered": [],
            "Total Present Students": [],
            "In-Time": [],
            "Out-Time": [],
            "Teacher Signature": []
        }
        pd.DataFrame(structure).to_csv(TEACHER_ATTENDANCE_FILE, index=False)

init_student_attendance()
init_teacher_attendance()

# ----------------- STUDENT ATTENDANCE HELPERS -----------------
def get_student_attendance_all():
    try:
        df = pd.read_csv(STUDENT_ATTENDANCE_FILE, dtype=str).fillna("")
        if "Month" not in df.columns or "Week" not in df.columns:
            init_student_attendance()
            df = pd.read_csv(STUDENT_ATTENDANCE_FILE, dtype=str).fillna("")
        return df
    except Exception:
        init_student_attendance()
        return pd.read_csv(STUDENT_ATTENDANCE_FILE, dtype=str).fillna("")

def get_student_attendance_for_slot(month, week):
    df_all = get_student_attendance_all()
    if not df_all.empty and "Month" in df_all.columns and "Week" in df_all.columns:
        filtered = df_all[(df_all["Month"] == str(month)) & (df_all["Week"] == str(week))]
        if not filtered.empty:
            cols_to_drop = [c for c in ["Month", "Week"] if c in filtered.columns]
            return filtered.drop(columns=cols_to_drop)
    
    return pd.DataFrame({
        "Class & Section": SECTIONS_LIST,
        "Total Registered Students": ["" for _ in SECTIONS_LIST],
        "Total Working Days": ["" for _ in SECTIONS_LIST],
        "Sessions Planned": ["" for _ in SECTIONS_LIST],
        "Sessions Conducted": ["" for _ in SECTIONS_LIST],
        "Total Present Count": ["" for _ in SECTIONS_LIST],
        "Total Absent Count": ["" for _ in SECTIONS_LIST],
        "Average Attendance %": ["" for _ in SECTIONS_LIST],
        "Remarks": ["" for _ in SECTIONS_LIST]
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

# ----------------- TEACHER ATTENDANCE HELPERS -----------------
def get_teacher_attendance_all():
    try:
        df = pd.read_csv(TEACHER_ATTENDANCE_FILE, dtype=str).fillna("")
        if "Month" not in df.columns or "Week" not in df.columns:
            init_teacher_attendance()
            df = pd.read_csv(TEACHER_ATTENDANCE_FILE, dtype=str).fillna("")
        return df
    except Exception:
        init_teacher_attendance()
        return pd.read_csv(TEACHER_ATTENDANCE_FILE, dtype=str).fillna("")

def get_teacher_attendance_for_slot(month, week):
    df_all = get_teacher_attendance_all()
    if not df_all.empty and "Month" in df_all.columns and "Week" in df_all.columns:
        filtered = df_all[(df_all["Month"] == str(month)) & (df_all["Week"] == str(week))]
        if not filtered.empty:
            cols_to_drop = [c for c in ["Month", "Week"] if c in filtered.columns]
            return filtered.drop(columns=cols_to_drop)
    
    return pd.DataFrame({
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

# ----------------- IN-LINE FILE PREVIEW RENDERER -----------------
def render_file_preview(file_path, file_name, unique_key):
    ext = os.path.splitext(file_name)[1].lower()

    if ext in [".jpg", ".jpeg", ".png"]:
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

    elif ext in [".mp4", ".mov", ".avi"]:
        st.video(file_path)

    else:
        with open(file_path, "rb") as f:
            st.download_button(
                label=f"📥 Download {file_name}",
                data=f.read(),
                file_name=file_name,
                key=f"dl_doc_{unique_key}"
            )

# ----------------- STUDENT EXCEL VIEWER HELPER -----------------
def render_student_excel():
    possible_names = ["LMS STUDENT DATA.xlsx", "LMS STUDENT DATA.xls"]
    found_file = next((name for name in possible_names if os.path.exists(name)), None)

    if found_file:
        try:
            df = pd.read_excel(found_file)
            st.markdown("### 👨‍🎓 Registered Student Database (Classes VI – IX)")
            
            class_col = next((c for c in df.columns if c.strip().lower() == "class"), None)
            if class_col:
                unique_classes = ["All Classes"] + sorted([str(x) for x in df[class_col].dropna().unique()])
                selected_class = st.selectbox("Filter by Class:", unique_classes)
                df_display = df[df[class_col].astype(str) == selected_class] if selected_class != "All Classes" else df
            else:
                df_display = df

            st.write(f"**Total Students Displayed:** {len(df_display)}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error reading {found_file}: {e}")
    else:
        st.info("ℹ️ LMS STUDENT DATA.xlsx file project folder me rakhein.")

# ----------------- ATTENDANCE VIEWER FUNCTIONS -----------------
def render_student_attendance_viewer():
    st.markdown("### 📊 Section-wise Student STEM Attendance Record")
    col_m, col_w = st.columns(2)
    sel_month = col_m.selectbox("Select Month to View (Student):", MONTHS, key="view_st_month")
    sel_week = col_w.selectbox("Select Week to View (Student):", WEEKS, key="view_st_week")
    
    df_slot = get_student_attendance_for_slot(sel_month, sel_week)
    st.caption(f"Showing Student Attendance for: **{sel_month} - {sel_week}**")
    st.dataframe(df_slot, use_container_width=True, hide_index=True)

def render_teacher_attendance_viewer():
    st.markdown("### 🧑‍🏫 STEM Teacher Lab Duty & Activity Attendance")
    col_m, col_w = st.columns(2)
    sel_month = col_m.selectbox("Select Month to View (Teacher):", MONTHS, key="view_tc_month")
    sel_week = col_w.selectbox("Select Week to View (Teacher):", WEEKS, key="view_tc_week")
    
    df_slot = get_teacher_attendance_for_slot(sel_month, sel_week)
    st.caption(f"Showing Teacher Attendance for: **{sel_month} - {sel_week}**")
    st.dataframe(df_slot, use_container_width=True, hide_index=True)

# ----------------- EMBEDDED MASTER DATA -----------------
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

    1. **Experiential Learning**
    To provide students with opportunities to learn through practical activities, experiments, and hands-on projects.

    2. **Problem Solving**
    To encourage students to identify real-life problems, analyse them, and develop appropriate solutions.

    3. **Innovation**
    To promote the ability of students to develop new ideas, designs, and prototypes.

    4. **Scientific Temper**
    To develop the habits of observation, questioning, experimentation, evidence-based reasoning, and drawing logical conclusions.

    5. **Technology Skills**
    To introduce students to coding, electronics, sensors, microcontrollers, robotics, and digital tools.

    6. **Collaboration**
    To promote teamwork, peer learning, and collaborative problem solving.

    7. **Communication**
    To provide students with opportunities to effectively explain and present their ideas, experiments, and projects.

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
    * Power supplies shall not be connected or disconnected without the permission of the teacher/instructor.
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
    * Experiential Learning
    * Project-Based Learning
    * Design Thinking
    * Innovation
    * Robotics
    * Electronics
    * Coding
    * Prototyping
    * Problem Solving
    * STEM Competitions

    #### 5. Record Maintenance
    The Coordinator/SPOC will ensure systematic maintenance of:
    * Lab Inventory
    * Attendance
    * Activity Records
    * Project Records
    * Assessment Records
    * Training Records
    * Competition Records
    * Safety Records
    * Circulars and Communication
    * Photo/Video Documentation
    * Monthly and Annual Reports

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
        (1, "STEM Lab Profile", ["pdf", "docx"]),
        (2, "Lab Objectives & Guidelines", ["pdf"]),
        (3, "Coordinator / SPOC Details", ["pdf", "docx"]),
        (4, "Annual STEM Plan", ["xlsx", "xls", "pdf"]),
        (5, "Monthly Activity Plan", ["xlsx", "xls"]),
        (6, "Class-wise Timetable", ["xlsx", "xls", "pdf"]),
        (7, "Session / Lesson Plans", ["pdf", "docx"]),
        (8, "Student List", ["xlsx", "xls"]),
        (9, "Student Attendance", ["xlsx", "xls", "csv"]),
        (10, "Teacher Attendance", ["xlsx", "xls", "csv"]),
    ],
    "2. Inventory & Safety": [
        (11, "Lab Inventory", ["xlsx", "xls", "csv"]),
        (12, "Equipment Details", ["xlsx", "xls"]),
        (13, "Equipment Photos", ["jpg", "png", "jpeg"]),
        (14, "Equipment Purchase Records", ["pdf"]),
        (15, "Maintenance Records", ["xlsx", "xls", "pdf"]),
        (16, "Lab Safety Rules", ["pdf"]),
        (17, "Safety Checklist", ["xlsx", "xls", "pdf"]),
    ],
    "3. Activities & Projects": [
        (18, "STEM Activities", ["pdf", "docx"]),
        (19, "Activity Worksheets", ["pdf"]),
        (20, "Activity Photos", ["jpg", "png", "jpeg"]),
        (21, "Activity Videos", ["mp4", "mov", "avi"]),
        (22, "Student Projects", ["pdf", "docx"]),
        (23, "Prototype Details", ["pdf"]),
        (24, "Problem Statements", ["docx", "xlsx"]),
        (25, "Innovation Ideas", ["xlsx", "xls"]),
        (26, "Project Photos", ["jpg", "png", "jpeg"]),
        (27, "Project Videos", ["mp4", "mov"]),
    ],
    "4. Assessment & Competitions": [
        (28, "Assessment Rubrics", ["xlsx", "xls", "pdf"]),
        (29, "Student Assessment", ["xlsx", "xls"]),
        (30, "Student Performance", ["xlsx", "xls", "csv"]),
        (31, "STEM SPARK Registration", ["pdf", "xlsx"]),
        (32, "STEM SPARK Team Details", ["xlsx", "xls"]),
        (33, "STEM SPARK Submissions", ["pdf"]),
        (34, "VVM Records", ["pdf", "xlsx"]),
        (35, "Other Competitions", ["pdf", "xlsx"]),
    ],
    "5. Training & Communication": [
        (36, "Teacher Training Records", ["xlsx", "xls", "pdf"]),
        (37, "Training Certificates", ["pdf", "jpg", "png"]),
        (38, "Training Attendance", ["xlsx", "xls"]),
        (39, "Workshop Reports", ["docx", "pdf"]),
        (40, "Workshop Photos", ["jpg", "png"]),
        (41, "Government Circulars", ["pdf"]),
        (42, "School Circulars", ["pdf"]),
        (43, "Official Emails", ["pdf", "jpg", "png"]),
        (44, "Meeting Minutes", ["docx", "pdf"]),
    ],
    "6. Reports & Achievements": [
        (45, "Monthly Reports", ["pdf"]),
        (46, "Quarterly Reports", ["pdf"]),
        (47, "Annual Report", ["pdf"]),
        (48, "Student Certificates", ["pdf", "jpg", "png"]),
        (49, "Student Achievements", ["xlsx", "xls", "pdf"]),
        (50, "STEM Lab Event Photos", ["jpg", "png"]),
    ]
}

def get_folder_name(sno, title):
    return f"{sno:02d}_{title.replace(' ', '_').replace('/', '_')}"

# ----------------- SIDEBAR NAVIGATION -----------------
st.sidebar.title("🔬 ABIC STEM Portal")
st.sidebar.caption("Aditya Birla Intermediate College, Renukoot")
access_mode = st.sidebar.radio("Navigation Mode", ["Public Viewer", "Admin Workspace"])

# ----------------- ADMIN WORKSPACE -----------------
if access_mode == "Admin Workspace":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Admin Login")
    password = st.sidebar.text_input("Enter Admin Password", type="password")

    if password == "stem@admin123":
        st.sidebar.success("Authenticated as SPOC")
        st.title("⚙️ Admin Workspace: Manage Records & Live Attendance")

        selected_section = st.selectbox("Select Category to Manage", list(CATEGORIES.keys()))
        items = CATEGORIES[selected_section]
        st.divider()

        for sno, title, formats in items:
            folder_name = get_folder_name(sno, title)
            record_dir = os.path.join(UPLOAD_DIR, folder_name)
            os.makedirs(record_dir, exist_ok=True)

            with st.expander(f"**#{sno}. {title}**", expanded=False):
                # SPECIAL HANDLER FOR #9 STUDENT ATTENDANCE (MONTH & WEEK WISE SELECTION & SEPARATE SECTIONS)
                if sno == 9:
                    st.markdown("#### 📝 Edit Student Attendance (Month & Week-wise)")
                    col_adm_st_m, col_adm_st_w = st.columns(2)
                    admin_sel_st_month = col_adm_st_m.selectbox("Select Month (Student):", MONTHS, key="admin_st_month")
                    admin_sel_st_week = col_adm_st_w.selectbox("Select Week (Student):", WEEKS, key="admin_st_week")
                    
                    st.caption(f"Currently Editing Student Attendance: **{admin_sel_st_month} - {admin_sel_st_week}**")
                    
                    current_st_slot_df = get_student_attendance_for_slot(admin_sel_st_month, admin_sel_st_week)
                    editor_st_slot_key = f"admin_st_editor_{admin_sel_st_month}_{admin_sel_st_week}"
                    edited_st_slot_df = st.data_editor(current_st_slot_df, num_rows="dynamic", use_container_width=True, key=editor_st_slot_key)
                    
                    if st.button(f"💾 Save Student Attendance for {admin_sel_st_month} - {admin_sel_st_week}", type="primary", key="save_st_slot_btn"):
                        save_student_attendance_slot(admin_sel_st_month, admin_sel_st_week, edited_st_slot_df)
                        st.success(f"Student Attendance for {admin_sel_st_month} ({admin_sel_st_week}) successfully saved!")
                        st.rerun()

                # SPECIAL HANDLER FOR #10 TEACHER ATTENDANCE (MONTH & WEEK WISE SELECTION & PERSISTENCE)
                elif sno == 10:
                    st.markdown("#### 🧑‍🏫 Edit Teacher Attendance (Month & Week-wise)")
                    col_adm_m, col_adm_w = st.columns(2)
                    admin_sel_month = col_adm_m.selectbox("Select Month (Teacher):", MONTHS, key="admin_tc_month")
                    admin_sel_week = col_adm_w.selectbox("Select Week (Teacher):", WEEKS, key="admin_tc_week")
                    
                    st.caption(f"Currently Editing Teacher Attendance: **{admin_sel_month} - {admin_sel_week}**")
                    
                    current_slot_df = get_teacher_attendance_for_slot(admin_sel_month, admin_sel_week)
                    editor_slot_key = f"admin_tc_editor_{admin_sel_month}_{admin_sel_week}"
                    edited_slot_df = st.data_editor(current_slot_df, num_rows="dynamic", use_container_width=True, key=editor_slot_key)
                    
                    if st.button(f"💾 Save Teacher Attendance for {admin_sel_month} - {admin_sel_week}", type="primary", key="save_tc_slot_btn"):
                        save_teacher_attendance_slot(admin_sel_month, admin_sel_week, edited_slot_df)
                        st.success(f"Teacher Attendance for {admin_sel_month} ({admin_sel_week}) successfully saved!")
                        st.rerun()

                # REGULAR FILE UPLOADER FOR OTHER PARAMETERS
                else:
                    uploaded_files = st.file_uploader(
                        f"Upload files for #{sno} ({', '.join(formats)})",
                        type=formats,
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
        st.info("Enter admin password to upload and modify records.")

# ----------------- PUBLIC VIEWER -----------------
else:
    st.title("🔬 STEM Innovation & Learning Laboratory")
    st.caption("Aditya Birla Intermediate College, Renukoot | Academic Session 2026-27")

    tab1, tab2 = st.tabs(["📁 Explore Records", "📊 Repository Status"])

    with tab1:
        for section_name, items in CATEGORIES.items():
            st.subheader(f"📑 {section_name}")
            for sno, title, formats in items:
                folder_name = get_folder_name(sno, title)
                record_dir = os.path.join(UPLOAD_DIR, folder_name)
                files = os.listdir(record_dir) if os.path.exists(record_dir) else []
                is_builtin = sno in BUILTIN_RECORDS

                with st.expander(f"#{sno}. {title}"):
                    if is_builtin:
                        BUILTIN_RECORDS[sno]["render"]()
                    
                    if files:
                        st.markdown("---")
                        for idx, fname in enumerate(files):
                            fpath = os.path.join(record_dir, fname)
                            render_file_preview(fpath, fname, f"{sno}_{idx}")
                            st.write("")
                    elif not is_builtin:
                        st.info("No document uploaded yet for this section.")

    with tab2:
        total = 50
        completed = 0
        summary_rows = []

        for section_name, items in CATEGORIES.items():
            for sno, title, formats in items:
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
