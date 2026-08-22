import streamlit as st
import pandas as pd
import os
import base64

st.set_page_config(page_title="ABIC STEM Lab Portal", page_icon="🔬", layout="wide")

UPLOAD_DIR = "stem_lab_records"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------- IN-LINE FILE PREVIEW RENDERER -----------------
def render_file_preview(file_path, file_name):
    ext = os.path.splitext(file_name)[1].lower()

    # 1. Images Preview
    if ext in [".jpg", ".jpeg", ".png"]:
        st.image(file_path, caption=file_name, use_container_width=True)

    # 2. Excel & CSV Preview (Direct Interactive Table)
    elif ext in [".xlsx", ".xls", ".csv"]:
        try:
            if ext == ".csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            st.markdown(f"📊 **Data Table: {file_name}** ({len(df)} rows)")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error previewing spreadsheet: {e}")

    # 3. PDF Preview (Embedded Viewer)
    elif ext == ".pdf":
        try:
            with open(file_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf" style="border: 1px solid #ddd; border-radius: 8px;"></iframe>'
            st.markdown(f"📄 **PDF Document: {file_name}**", unsafe_allow_html=True)
            st.markdown(pdf_display, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error previewing PDF: {e}")

    # 4. Video Player Preview
    elif ext in [".mp4", ".mov", ".avi"]:
        st.video(file_path)

    # 5. Other Documents / Plain Text
    else:
        st.info(f"📄 {file_name} (Preview not supported for this extension)")

# ----------------- STUDENT EXCEL VIEWER HELPER -----------------
def render_student_excel():
    possible_names = ["LMS STUDENT DATA.xlsx", "LMS STUDENT DATA.xls"]
    found_file = None
    for name in possible_names:
        if os.path.exists(name):
            found_file = name
            break

    if found_file:
        try:
            df = pd.read_excel(found_file)
            st.markdown("### 👨‍🎓 Registered Student Database (Classes VI – IX)")
            
            class_col = next((c for c in df.columns if c.strip().lower() == "class"), None)
            if class_col:
                unique_classes = ["All Classes"] + sorted([str(x) for x in df[class_col].dropna().unique()])
                selected_class = st.selectbox("Filter by Class:", unique_classes)
                if selected_class != "All Classes":
                    df_display = df[df[class_col].astype(str) == selected_class]
                else:
                    df_display = df
            else:
                df_display = df

            st.write(f"**Total Students Displayed:** {len(df_display)}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error reading {found_file}: {e}")
    else:
        st.warning("⚠️ LMS STUDENT DATA.xlsx file project folder me nahi mili. File ko project folder me paste karein.")

# ----------------- EMBEDDED MASTER DATA -----------------
BUILTIN_RECORDS = {
    1: {
        "title": "STEM Lab Profile",
        "type": "embed",
        "render": lambda: st.markdown("""
        ### 🏫 STEM Lab Profile
        * **School Name:** Aditya Birla Intermediate College, Renukoot[cite: 1]
        * **Academic Session:** 2026-27[cite: 1]
        * **STEM Lab Name:** School STEM Innovation & Learning Laboratory[cite: 1]
        * **STEM Coordinator / SPOC:** Shashank Verma[cite: 1]
        
        #### 1. Introduction
        The STEM Lab of Aditya Birla Intermediate College, Renukoot is a dedicated space for promoting Science, Technology, Engineering and Mathematics (STEM) learning through hands-on activities, experimentation, problem-solving, innovation and project-based learning.[cite: 1]
        
        #### 2. Classes Covered
        * Class VI[cite: 1]
        * Class VII[cite: 1]
        * Class VIII[cite: 1]
        * Class IX[cite: 1]
        *(Activities are also organized for other classes for special competitions & projects)*[cite: 1]
        
        #### 3. Major Objectives
        * Develop scientific thinking and curiosity.[cite: 1]
        * Promote hands-on and experiential learning.[cite: 1]
        * Encourage problem-solving, critical thinking, design thinking & prototyping.[cite: 1]
        * Provide exposure to electronics, Arduino, coding, sensors, robotics & IoT.[cite: 1]
        * Connect STEM concepts with real-life applications and competitions.[cite: 1]
        
        #### 4. Learning Approach
        `Problem → Explore → Imagine Design → Build → Test → Improve → Present`[cite: 1]
        """)
    },
    2: {
        "title": "Lab Objectives & Guidelines",
        "type": "embed",
        "render": lambda: st.markdown("""
        ### 📋 Lab Objectives & Guidelines (Session 2026-27)
        #### A. Key Objectives
        1. **Experiential Learning:** Practical activities, experiments, and hands-on projects.[cite: 2]
        2. **Problem Solving:** Identify real-life problems and engineer appropriate solutions.[cite: 2]
        3. **Innovation & Prototyping:** Build functional models, circuits, and prototypes.[cite: 2]
        4. **Scientific Temper & Tech Skills:** Coding, electronics, microcontrollers, and digital tools.[cite: 2]
        5. **Collaboration & Presentation:** Team-based problem solving and project pitching.[cite: 2]

        #### B. Laboratory Guidelines & Safety Rules
        * Entry permitted only under teacher/instructor supervision.[cite: 2]
        * Equipment must be used only for designated activities and returned to original boxes.[cite: 2]
        * Keep liquids away from electrical equipment and microcontrollers.[cite: 2]
        * Report any damaged components immediately in the Maintenance/Inventory record.[cite: 2]
        * Maintain documentation for every activity: `Activity → Date → Class → Objective → Procedure → Outcome → Photos`.[cite: 2]
        """)
    },
    3: {
        "title": "Coordinator / SPOC Details",
        "type": "embed",
        "render": lambda: st.markdown("""
        ### 👤 STEM Coordinator / SPOC Details
        * **Institution:** Aditya Birla Intermediate College, Renukoot (Sonbhadra, UP)[cite: 3]
        * **Name:** Shashank Verma[cite: 3]
        * **Designation:** TGT
        * **Academic Qualification:** M.Sc., B.Ed.[cite: 3]
        * **Role:** STEM Coordinator / STEM Lab SPOC[cite: 3]
        * **Official Email:** `shashank.verma@adityabirlaschools.in`[cite: 3]
        * **Official Contact:** `9826594665`[cite: 3]
        
        #### Key Responsibilities:
        * Planning and coordinating annual/monthly STEM activity calendars.[cite: 3]
        * Maintaining student lists, attendance, digital inventories, and lab equipment.[cite: 3]
        * Mentoring student prototypes, competitions (STEM SPARK, VVM, exhibitions).[cite: 3]
        * Documentation, workshop reporting, and periodic digital backups.[cite: 3]
        """)
    },
    8: {
        "title": "Student List (Class VI to IX)",
        "type": "excel_view",
        "render": render_student_excel
    },
    11: {
        "title": "Lab Inventory (Teacher & Student Kits)",
        "type": "embed",
        "render": lambda: st.markdown("""
        ### 📦 Complete STEM Lab Inventory
        * **Supplier / Source:** ScienceUtsav & ABPS Kit[cite: 4, 5]
        * **Status:** Verified & Working[cite: 5]
        * **Key Categories:**
          * **Controllers:** Arduino UNO DIP Type, Custom Shields, Bluetooth HC-05, IR Remotes & Receivers.[cite: 4, 5]
          * **Sensors:** DHT11 Temp/Humidity, Rain, Vibration, Ultrasonic, MQ2 Smoke, Flame, Moisture, LDR, Hall Effect, Touch sensors.[cite: 4, 5]
          * **Actuators & Motors:** BO Motors (60 RPM), SG90 Micro Servo Motors, 3-6V Mini Submersible Water Pumps, CD Motors.[cite: 4, 5]
          * **Electronics & Displays:** 16x2 I2C LCD Displays, 7-Segment Displays, WS2812B RGB Addressable LED Strips, 1W LED PCBs, DPDT modules.[cite: 4, 5]
          * **Tools & Hardware:** 3D Printer (Bambu Lab A1 Mini), Peg Boards, Screwdrivers, Li-Ion 18650 Batteries, Multi-pin RMC cables.[cite: 4, 5]
        """)
    },
    12: {
        "title": "Equipment Details",
        "type": "embed",
        "render": lambda: st.markdown("""
        ### 🔬 Detailed Equipment Specifications
        * **Core Microcontroller:** Arduino UNO (Atmega328P DIP) with custom expansion shield.[cite: 4, 5]
        * **Rapid Prototyping:** Bambu Lab A1 Mini 3D Printer for student structural components.[cite: 4]
        * **Sensor Integration:** 3-Pin / 4-Pin standard RMC locking connectors for plug-and-play prototyping.[cite: 4, 5]
        * **Power Management:** 5V DC adapters and dual 18650 Li-Ion rechargeable battery packs with DC barrel jacks.[cite: 4, 5]
        """)
    }
}

# Full 50 STEM Record categories
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

# ----------------- SIDEBAR CONTROLS -----------------
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
        st.title("⚙️ Admin Workspace: Upload & Manage Records")
        st.info("💡 Files uploaded here will automatically open inside the browser for viewers.")

        selected_section = st.selectbox("Select Category to Manage", list(CATEGORIES.keys()))
        items = CATEGORIES[selected_section]
        st.divider()

        for sno, title, formats in items:
            folder_name = get_folder_name(sno, title)
            record_dir = os.path.join(UPLOAD_DIR, folder_name)
            os.makedirs(record_dir, exist_ok=True)

            is_builtin = sno in BUILTIN_RECORDS

            with st.expander(f"**#{sno}. {title}** {'(Integrated Master Data)' if is_builtin else ''}", expanded=False):
                if is_builtin:
                    st.success("✅ Integrated system record.")
                
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

# ----------------- PUBLIC VIEWER (DIRECT VIEW) -----------------
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

                badge = " (Ready)" if is_builtin or len(files) > 0 else " (Pending)"
                
                with st.expander(f"#{sno}. {title}{badge}"):
                    if is_builtin:
                        BUILTIN_RECORDS[sno]["render"]()
                    
                    if files:
                        st.markdown("---")
                        for fname in files:
                            fpath = os.path.join(record_dir, fname)
                            # Direct in-browser display without download necessity
                            render_file_preview(fpath, fname)
                            st.write("")
                    elif not is_builtin:
                        st.info("No documents uploaded yet for this parameter.")

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
                    status = "✅ Verified / Ready"
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
