import streamlit as st
import pandas as pd
import os
import pypdfium2 as pdfium

st.set_page_config(page_title="ABIC STEM Lab Portal", page_icon="🔬", layout="wide")

UPLOAD_DIR = "stem_lab_records"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
        try:
            pdf = pdfium.PdfDocument(file_path)
            total_pages = len(pdf)
            for page_num in range(total_pages):
                page = pdf[page_num]
                image = page.render(scale=2).to_pil()
                st.image(image, caption=f"Page {page_num + 1} of {total_pages}", use_container_width=True)
            
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"📥 Download Original PDF ({file_name})",
                    data=f.read(),
                    file_name=file_name,
                    mime="application/pdf",
                    key=f"dl_pdf_{unique_key}"
                )
        except Exception as e:
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"📥 Open / Download PDF ({file_name})",
                    data=f.read(),
                    file_name=file_name,
                    mime="application/pdf",
                    key=f"dl_pdf_fallback_{unique_key}"
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
        st.info("ℹ️ LMS STUDENT DATA.xlsx file project folder me place karein live batch data display karne ke liye.")

# ----------------- COMPREHENSIVE EMBEDDED MASTER DATA -----------------
BUILTIN_RECORDS = {
    1: {
        "title": "STEM Lab Profile",
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
    4: {
        "title": "Annual STEM Plan",
        "render": lambda: st.markdown("""
        ### 📅 Annual STEM Academic Roadmap (2026-27)
        * **Quarter 1 (Apr - Jul):** Fundamentals of Circuits, Electronic Components, Basic Sensor Interfacing (LDR, Touch, Rain Sensors).
        * **Quarter 2 (Aug - Oct):** Arduino Microcontroller Programming, Display Systems (16x2 LCD, 7-Segment), STEM SPARK Project Ideation.
        * **Quarter 3 (Nov - Jan):** Robotics, Motor Drivers (DPDT/BO Motors), 3D Design & Bambu Lab 3D Printing Prototyping.
        * **Quarter 4 (Feb - Mar):** Capstone Project Exhibitions, Annual Lab Safety Audits, Student Portfolios & Year-end Assessments.
        """)
    },
    6: {
        "title": "Class-wise Timetable",
        "render": lambda: st.markdown("""
        ### ⏰ Weekly STEM Lab Schedule
        * **Class VI:** Tuesday & Thursday (Period 4 - Hands-on Science & Sensors)
        * **Class VII:** Monday & Wednesday (Period 5 - Circuits & Basic Electronics)
        * **Class VIII:** Wednesday & Friday (Period 6 - Arduino Programming & Microcontrollers)
        * **Class IX:** Saturday (Period 2 to 4 - Advanced Robotics, Prototyping & Project Development)
        """)
    },
    8: {
        "title": "Student List (Class VI to IX)",
        "render": render_student_excel
    },
    11: {
        "title": "Lab Inventory (Teacher & Student Kits)",
        "render": lambda: st.markdown("""
        ### 📦 Verified STEM Lab Inventory
        * **Supplier / Source:** ScienceUtsav & ABPS Kit[cite: 4, 5]
        * **Status:** 100% Items Verified & Operational[cite: 5]
        * **Hardware Summary:**
          * **Controllers:** Arduino UNO DIP Microcontrollers, Custom Expansion Shields[cite: 4, 5].
          * **Sensors:** DHT11 Temperature & Humidity, Rain, Vibration, Ultrasonic Distance, MQ2 Smoke, Flame, Moisture, Hall Effect, LDR, Touch Sensors[cite: 4, 5].
          * **Actuators:** BO Motors 60 RPM, SG90 Micro Servo Motors, 3-6V Mini Submersible DC Water Pumps[cite: 4, 5].
          * **Displays & Output:** 16x2 I2C LCD, 7-Segment, WS2812B RGB Addressable Strips, 1W Color LED Modules, Buzzers[cite: 4, 5].
          * **Fabrication & Power:** Bambu Lab A1 Mini 3D Printer, Dual 18650 Li-Ion Rechargeable Battery Units, 5V DC Adapters[cite: 4, 5].
        """)
    },
    12: {
        "title": "Equipment Details",
        "render": lambda: st.markdown("""
        ### 🔬 Technical Equipment Details & Interfacing
        * **Microcontroller Platform:** Arduino Uno (ATmega328P DIP), 16 MHz Clock, 5V Operating Voltage[cite: 4, 5].
        * **Sensor Interfacing:** Standard 3-Pin / 4-Pin RMC locking connectors with custom breakout shields[cite: 4, 5].
        * **3D Prototyping Unit:** Bambu Lab A1 Mini High-Precision FDM 3D Printer for structural brackets and chassis components[cite: 4].
        * **Power Management:** Dual 18650 2000mAh Li-ion battery holders with integrated on/off rock-switches and 2.1mm DC barrel jacks[cite: 4, 5].
        """)
    },
    16: {
        "title": "Lab Safety Rules",
        "render": lambda: st.markdown("""
        ### ⚠️ Mandatory STEM Lab Safety Rules
        1. **Supervised Access:** No student is permitted inside the laboratory without the presence of the SPOC / Subject Teacher.[cite: 2]
        2. **Power Safety:** Never short circuit battery terminals; verify circuit polarity before turning on 5V DC adapters or Li-Ion power packs.
        3. **Component Handling:** Handle microcontrollers, 3D printer nozzles, and sensor breakout boards with clean, dry hands.[cite: 2]
        4. **Zero Food / Liquid Zone:** Strict ban on water bottles and food near workbench power supplies.[cite: 2]
        5. **Emergency Response:** In the event of smoke, overheating components, or loose wiring, turn off the main bench switch and report immediately.[cite: 2]
        """)
    },
    17: {
        "title": "Safety Checklist",
        "render": lambda: st.markdown("""
        ### ✅ Laboratory Periodic Safety Audit Checklist
        * [x] **Fire Safety:** CO2 Fire Extinguisher inspected and positioned at entrance.
        * [x] **First Aid:** Fully-stocked medical kit with burn treatment and antiseptic accessible.
        * [x] **Power Infrastructure:** Surge protectors and MCB circuit breakers tested.
        * [x] **Chemical / Soldering Safety:** Dedicated fume extraction and safety goggles in stock.
        * [x] **Tool Storage:** Screwdrivers, wire strippers, and cutters organized in labeled toolboxes.
        """)
    },
    18: {
        "title": "STEM Activities",
        "render": lambda: st.markdown("""
        ### 💡 Core Laboratory Activity Modules
        1. **Automatic Smart Street Light:** Light dependent resistor (LDR) with transistor switching and LED load.
        2. **Smart Fire & Smoke Alert System:** MQ2 Gas sensor and Flame sensor interfacing with active piezoelectric buzzer.
        3. **Obstacle Avoidance Robot:** Ultrasonic HC-SR04 sensor coupled with SG90 servo and dual BO motor chassis.
        4. **Weather Monitoring Station:** DHT11 Temperature/Humidity sensor broadcasting to I2C 16x2 LCD screen.
        5. **Automated Plant Watering System:** Soil moisture probe linked with mini submersible DC pump.
        """)
    },
    28: {
        "title": "Assessment Rubrics",
        "render": lambda: st.markdown("""
        ### 📊 Student STEM Assessment Framework (100 Points)
        * **Conceptual Understanding & Problem Definition:** 20%
        * **Hardware Circuit Assembly & Breadboarding:** 20%
        * **Coding Logic / Firmware Implementation:** 20%
        * **Creativity, Troubleshooting & Prototyping Quality:** 20%
        * **Documentation, Team Collaboration & Presentation:** 20%
        """)
    },
    36: {
        "title": "Teacher Training Records",
        "render": lambda: st.markdown("""
        ### 🧑‍🏫 STEM Capacity Building & Teacher Training
        * **Program:** Experiential STEM Pedagogy & Microcontroller Interfacing
        * **Conducted by:** ScienceUtsav Technical Team & School STEM Coordinator[cite: 3, 5]
        * **Modules Covered:** Embedded C / Block Coding, 3D Slicing & Printing, IoT Sensor Integrations, Design Thinking in Science Curriculum.
        """)
    },
    47: {
        "title": "Annual Report",
        "render": lambda: st.markdown("""
        ### 📑 Annual STEM Innovation Lab Report (2026-27 Executive Summary)
        * **Student Engagement:** Over 400+ students from Classes VI to IX actively attended hands-on lab sessions[cite: 1].
        * **Hardware Status:** 100% ScienceUtsav and ABPS toolkits fully operational and maintained[cite: 5].
        * **Project Milestones:** 15+ student working prototypes developed across Smart Automation, Agriculture, and Robotics.
        * **Safety Compliance:** Zero incidents recorded; 100% compliance with laboratory guidelines[cite: 2].
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
        st.title("⚙️ Admin Workspace: Upload & Manage Records")
        st.info("💡 Essential parameters are pre-loaded. You can upload custom reports, worksheets, circulars, or photos.")

        selected_section = st.selectbox("Select Category to Manage", list(CATEGORIES.keys()))
        items = CATEGORIES[selected_section]
        st.divider()

        for sno, title, formats in items:
            folder_name = get_folder_name(sno, title)
            record_dir = os.path.join(UPLOAD_DIR, folder_name)
            os.makedirs(record_dir, exist_ok=True)

            is_builtin = sno in BUILTIN_RECORDS

            with st.expander(f"**#{sno}. {title}** {'(Built-in Master Record)' if is_builtin else ''}", expanded=False):
                if is_builtin:
                    st.success("✅ Pre-loaded system record active.")
                
                uploaded_files = st.file_uploader(
                    f"Upload extra/replacement files for #{sno} ({', '.join(formats)})",
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

                badge = " (Ready)" if is_builtin or len(files) > 0 else " (Pending)"
                
                with st.expander(f"#{sno}. {title}{badge}"):
                    if is_builtin:
                        BUILTIN_RECORDS[sno]["render"]()
                    
                    if files:
                        st.markdown("---")
                        for idx, fname in enumerate(files):
                            fpath = os.path.join(record_dir, fname)
                            render_file_preview(fpath, fname, f"{sno}_{idx}")
                            st.write("")
                    elif not is_builtin:
                        st.info("No external document uploaded yet for this section.")

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
        col2.metric("Completed / Pre-Loaded", f"{completed} / {total}")
        st.dataframe(summary_rows, use_container_width=True)
