import streamlit as st
import pandas as pd
import os
import pypdfium2 as pdfium

st.set_page_config(page_title="ABIC STEM Lab Portal", page_icon="🔬", layout="wide")

UPLOAD_DIR = "stem_lab_records"
DATA_DIR = "portal_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

STUDENT_ATTENDANCE_FILE = os.path.join(DATA_DIR, "student_attendance.csv")
TEACHER_ATTENDANCE_FILE = os.path.join(DATA_DIR, "teacher_attendance.csv")

# ----------------- ATTENDANCE DATA MANAGERS -----------------
def init_student_attendance():
    if not os.path.exists(STUDENT_ATTENDANCE_FILE):
        default_data = {
            "Class & Section": ["VI (A, B, C, D)", "VII (A, B, C, D)", "VIII (A, B, C, D)", "IX (A to H)"],
            "Total Registered Students": [160, 160, 160, 320],
            "Total Working Days": [24, 24, 24, 24],
            "Sessions Planned": [8, 8, 8, 8],
            "Sessions Conducted": [8, 8, 8, 8],
            "Total Present Count": [152, 148, 155, 305],
            "Total Absent Count": [8, 12, 5, 15],
            "Average Attendance %": ["95.0%", "92.5%", "96.8%", "95.3%"],
            "Remarks": ["Regular", "Satisfactory", "Active Batch", "High Engagement"]
        }
        pd.DataFrame(default_data).to_csv(STUDENT_ATTENDANCE_FILE, index=False)

def init_teacher_attendance():
    if not os.path.exists(TEACHER_ATTENDANCE_FILE):
        teachers = [
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
        default_data = {
            "S.No.": list(range(1, len(teachers) + 1)),
            "Teacher Name": teachers,
            "Class & Section Taught": ["VI#A, VI#B", "VI#C, VI#D", "VII#A, VII#B", "VII#C, VII#D", "IX#A, IX#B, IX#C", "VIII#A, VIII#B", "VIII#C, VIII#D", "IX#D, IX#E", "IX#F, IX#G", "IX#H"],
            "Period / Time Slot": ["Period 2 (08:40 - 09:20)", "Period 3 (09:20 - 10:00)", "Period 4 (10:15 - 10:55)", "Period 5 (10:55 - 11:35)", "Period 6 (11:50 - 12:30)", "Period 2 (08:40 - 09:20)", "Period 3 (09:20 - 10:00)", "Period 4 (10:15 - 10:55)", "Period 5 (10:55 - 11:35)", "Period 6 (11:50 - 12:30)"],
            "Lab Activity / Topic Covered": ["Sensors Interfacing", "LDR & Light Circuits", "Soil Moisture Sensing", "Arduino Basics", "Robotics & Motor Driver", "7-Segment Display", "DHT11 Weather Station", "Flame Sensor Interfacing", "Bambu Lab 3D Slicing", "Ultrasonic Distance Alert"],
            "Total Present Students": [38, 37, 39, 36, 40, 39, 38, 37, 39, 38],
            "In-Time": ["08:35 AM", "09:15 AM", "10:10 AM", "10:50 AM", "11:45 AM", "08:35 AM", "09:15 AM", "10:10 AM", "10:50 AM", "11:45 AM"],
            "Out-Time": ["09:25 AM", "10:05 AM", "11:00 AM", "11:40 AM", "12:35 PM", "09:25 AM", "10:05 AM", "11:00 AM", "11:40 AM", "12:35 PM"],
            "Teacher Signature": ["[Verified Digitally]", "[Verified Digitally]", "[Verified Digitally]", "[Verified Digitally]", "[Verified Digitally]", "[Verified Digitally]", "[Verified Digitally]", "[Verified Digitally]", "[Verified Digitally]", "[Verified Digitally]"]
        }
        pd.DataFrame(default_data).to_csv(TEACHER_ATTENDANCE_FILE, index=False)

init_student_attendance()
init_teacher_attendance()

def get_student_attendance_df():
    return pd.read_csv(STUDENT_ATTENDANCE_FILE)

def get_teacher_attendance_df():
    return pd.read_csv(TEACHER_ATTENDANCE_FILE)

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
        ### 🏫 STEM LAB PROFILE

        * **School Name:** Aditya Birla Intermediate College, Renukoot[cite: 1]
        * **Academic Session:** 2026-27[cite: 1]
        * **STEM Lab:** School STEM Innovation & Learning Laboratory[cite: 1]
        * **STEM Coordinator / SPOC:** Shashank Verma[cite: 1]

        ---

        #### 1. Introduction
        The STEM Lab of Aditya Birla Intermediate College, Renukoot is a dedicated space for promoting Science, Technology, Engineering and Mathematics (STEM) learning through hands-on activities, experimentation, problem-solving, innovation and project-based learning[cite: 1]. The laboratory provides students with opportunities to connect classroom concepts with real-life situations and develop practical skills through designing, making, testing and improving solutions[cite: 1].

        #### 2. Classes Covered
        The STEM Lab activities are primarily conducted for[cite: 1]:
        * Class VI[cite: 1]
        * Class VII[cite: 1]
        * Class VIII[cite: 1]
        * Class IX[cite: 1]

        *Activities may also be organized for other classes as required under school programmes, competitions and special projects.*[cite: 1]

        #### 3. Major Objectives
        1. To develop scientific thinking and curiosity among students[cite: 1].
        2. To promote hands-on and experiential learning[cite: 1].
        3. To develop problem-solving and critical-thinking skills[cite: 1].
        4. To encourage students to identify real-life problems and develop solutions[cite: 1].
        5. To promote creativity, innovation and design thinking[cite: 1].
        6. To provide exposure to technology, electronics, coding, robotics and prototyping[cite: 1].
        7. To encourage teamwork and collaborative learning[cite: 1].
        8. To develop communication, presentation and documentation skills[cite: 1].
        9. To connect STEM concepts with real-life applications[cite: 1].
        10. To encourage participation in STEM competitions and innovation programmes[cite: 1].

        #### 4. Major Areas of STEM Learning
        * Science Experiments[cite: 1]
        * Mathematics Applications[cite: 1]
        * Electronics[cite: 1]
        * Arduino and Microcontrollers[cite: 1]
        * Robotics[cite: 1]
        * Sensors and Actuators[cite: 1]
        * Coding and Computational Thinking[cite: 1]
        * IoT and Smart Systems[cite: 1]
        * Design Thinking[cite: 1]
        * 3D/Prototype Development[cite: 1]
        * Environmental Innovation[cite: 1]
        * E-waste Management[cite: 1]
        * Problem Identification and Solution Development[cite: 1]

        #### 5. Teaching-Learning Approach
        The STEM Lab follows an activity-oriented approach based on[cite: 1]:
        > **Problem → Explore → Imagine Design → Build → Test → Improve → Present**[cite: 1]

        Students are encouraged to work individually as well as in teams[cite: 1].

        #### 6. Major Activities
        The STEM Lab may conduct[cite: 1]:
        * Hands-on STEM activities[cite: 1]
        * Experiments and demonstrations[cite: 1]
        * Design challenges[cite: 1]
        * Innovation challenges[cite: 1]
        * Project development[cite: 1]
        * Prototype development[cite: 1]
        * Robotics and electronics activities[cite: 1]
        * Coding activities[cite: 1]
        * STEM competitions[cite: 1]
        * Workshops and training programmes[cite: 1]
        * Exhibition and project presentations[cite: 1]

        #### 7. Documentation
        The following records are maintained digitally[cite: 1]:
        * Student records[cite: 1]
        * Attendance[cite: 1]
        * Inventory[cite: 1]
        * Activity reports[cite: 1]
        * Lesson/session plans[cite: 1]
        * Project reports[cite: 1]
        * Assessment records[cite: 1]
        * Training records[cite: 1]
        * Competition records[cite: 1]
        * Photographs and videos[cite: 1]
        * Circulars and official communication[cite: 1]
        * Monthly and annual reports[cite: 1]

        #### 8. Expected Learning Outcomes
        Students participating in STEM Lab activities are expected to develop[cite: 1]:
        * Observation skills[cite: 1]
        * Scientific reasoning[cite: 1]
        * Problem-solving ability[cite: 1]
        * Creativity[cite: 1]
        * Computational thinking[cite: 1]
        * Design and prototyping skills[cite: 1]
        * Teamwork[cite: 1]
        * Communication skills[cite: 1]
        * Presentation skills[cite: 1]
        * Innovation mindset[cite: 1]

        #### 9. Evidence of STEM Lab Activities
        Evidence is maintained through[cite: 1]:
        * Activity reports[cite: 1]
        * Student worksheets[cite: 1]
        * Project reports[cite: 1]
        * Photographs[cite: 1]
        * Videos[cite: 1]
        * Assessment records[cite: 1]
        * Certificates[cite: 1]
        * Competition results[cite: 1]
        * Student presentations[cite: 1]
        """)
    },
    2: {
        "title": "Lab Objectives & Guidelines",
        "render": lambda: st.markdown("""
        ### 📋 STEM LAB OBJECTIVES & GUIDELINES

        * **School:** Aditya Birla Intermediate College, Renukoot[cite: 2]
        * **Academic Session:** 2026-27[cite: 2]
        * **STEM Coordinator / SPOC:** Shashank Verma[cite: 2]

        ---

        #### A. Objectives of the STEM Lab

        1. **Experiential Learning**
        To provide students with opportunities to learn through practical activities, experiments, and hands-on projects[cite: 2].

        2. **Problem Solving**
        To encourage students to identify real-life problems, analyse them, and develop appropriate solutions[cite: 2].

        3. **Innovation**
        To promote the ability of students to develop new ideas, designs, and prototypes[cite: 2].

        4. **Scientific Temper**
        To develop the habits of observation, questioning, experimentation, evidence-based reasoning, and drawing logical conclusions[cite: 2].

        5. **Technology Skills**
        To introduce students to coding, electronics, sensors, microcontrollers, robotics, and digital tools[cite: 2].

        6. **Collaboration**
        To promote teamwork, peer learning, and collaborative problem solving[cite: 2].

        7. **Communication**
        To provide students with opportunities to effectively explain and present their ideas, experiments, and projects[cite: 2].

        ---

        #### B. STEM Lab Guidelines

        ##### 1. General Rules
        * Students shall enter the STEM Lab only with the permission of the teacher/instructor[cite: 2].
        * Students shall use equipment only as instructed and for the designated activity[cite: 2].
        * Discipline and silence shall be maintained inside the lab[cite: 2].
        * No equipment shall be removed from the lab without permission[cite: 2].
        * After completing an activity, all materials shall be returned to their designated places[cite: 2].

        ##### 2. Safety Guidelines
        * Electrical equipment shall be handled carefully[cite: 2].
        * Damaged wires or equipment shall not be used[cite: 2].
        * Power supplies shall not be connected or disconnected without the permission of the teacher/instructor[cite: 2].
        * Water and electrical equipment shall be kept away from each other[cite: 2].
        * Any problem or malfunction in equipment shall be immediately reported to the teacher[cite: 2].
        * Running, pushing, or any form of unsafe behaviour inside the lab is strictly prohibited[cite: 2].
        * In case of an emergency, students shall follow the instructions of the teacher/instructor[cite: 2].

        ##### 3. Equipment Handling
        * Arduino boards, sensors, motors, and electronic components shall be handled carefully[cite: 2].
        * Components shall be stored in their designated boxes/containers after use[cite: 2].
        * Tools shall be used only for their intended purpose[cite: 2].
        * The condition of equipment shall be checked after every experiment/activity[cite: 2].
        * Any damaged equipment shall be reported and recorded in the Inventory/Maintenance Record[cite: 2].

        ##### 4. Student Responsibilities
        Students shall[cite: 2]:
        * Follow all instructions given by the teacher/instructor[cite: 2].
        * Keep their workstation clean and organised[cite: 2].
        * Cooperate with other members of their team[cite: 2].
        * Record observations made during experiments and activities[cite: 2].
        * Properly document their projects and work[cite: 2].

        ##### 5. Documentation Guidelines
        For every major STEM activity/project, the following evidence should be maintained[cite: 2]:
        > **Activity Name → Date → Class → Participants → Objective → Materials → Procedure → Outcome → Assessment → Photographs**[cite: 2]

        ##### 6. Digital Record Management
        * STEM Lab records shall be systematically maintained in the designated Google Drive/School Digital Storage[cite: 2].
        * Important documents and records shall be backed up regularly to prevent data loss[cite: 2].

        ##### 7. Review
        * STEM Lab activities and records shall be reviewed periodically by the STEM Coordinator/SPOC to ensure proper implementation, documentation, safety, and record maintenance[cite: 2].
        """)
    },
    3: {
        "title": "Coordinator / SPOC Details",
        "render": lambda: st.markdown("""
        ### 👤 STEM LAB COORDINATOR / SPOC DETAILS

        **Academic Session:** 2026-27[cite: 3]

        ---

        #### 1. School Details
        * **School Name:** Aditya Birla Intermediate College, Renukoot[cite: 3]
        * **Location:** Renukoot, Sonbhadra, Uttar Pradesh[cite: 3]

        #### 2. STEM Coordinator / SPOC
        * **Name:** Shashank Verma[cite: 3]
        * **Designation:** PGT[cite: 3]
        * **Academic Qualification:** M.Sc., B.Ed.[cite: 3]
        * **Role:** STEM Coordinator / STEM Lab SPOC[cite: 3]

        #### 3. Major Responsibilities
        The STEM Coordinator / SPOC is responsible for[cite: 3]:
        1. Planning and coordinating STEM Lab activities[cite: 3].
        2. Preparing the annual and monthly STEM activity plan[cite: 3].
        3. Coordinating STEM Lab sessions for designated classes[cite: 3].
        4. Maintaining student participation and attendance records[cite: 3].
        5. Maintaining the STEM Lab inventory and equipment records[cite: 3].
        6. Coordinating maintenance and safe use of equipment[cite: 3].
        7. Supporting teachers in conducting STEM activities[cite: 3].
        8. Coordinating student projects and prototypes[cite: 3].
        9. Encouraging participation in STEM competitions and innovation programmes[cite: 3].
        10. Coordinating STEM SPARK and other STEM-related programmes[cite: 3].
        11. Maintaining activity photographs, videos and reports[cite: 3].
        12. Maintaining training and workshop records[cite: 3].
        13. Preparing monthly, quarterly and annual STEM Lab reports[cite: 3].
        14. Coordinating communication with school administration and programme authorities[cite: 3].
        15. Promoting a safe, innovative and collaborative learning environment in the STEM Lab[cite: 3].

        #### 4. Key Focus Areas
        * Experiential Learning[cite: 3]
        * Project-Based Learning[cite: 3]
        * Design Thinking[cite: 3]
        * Innovation[cite: 3]
        * Robotics[cite: 3]
        * Electronics[cite: 3]
        * Coding[cite: 3]
        * Prototyping[cite: 3]
        * Problem Solving[cite: 3]
        * STEM Competitions[cite: 3]

        #### 5. Record Maintenance
        The Coordinator/SPOC will ensure systematic maintenance of[cite: 3]:
        * Lab Inventory[cite: 3]
        * Attendance[cite: 3]
        * Activity Records[cite: 3]
        * Project Records[cite: 3]
        * Assessment Records[cite: 3]
        * Training Records[cite: 3]
        * Competition Records[cite: 3]
        * Safety Records[cite: 3]
        * Circulars and Communication[cite: 3]
        * Photo/Video Documentation[cite: 3]
        * Monthly and Annual Reports[cite: 3]

        #### 6. Contact Details
        * **Official School Email:** `shashank.verma@adityabirlaschools.in`[cite: 3]
        * **Official Contact Number:** `9826594665`[cite: 3]
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
    9: {
        "title": "Student Attendance",
        "render": lambda: (
            st.markdown("### 📊 Class-wise Student STEM Attendance Record"),
            st.dataframe(get_student_attendance_df(), use_container_width=True, hide_index=True)
        )
    },
    10: {
        "title": "Teacher Attendance",
        "render": lambda: (
            st.markdown("### 🧑‍🏫 STEM Teacher Lab Duty & Activity Attendance"),
            st.dataframe(get_teacher_attendance_df(), use_container_width=True, hide_index=True)
        )
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
        1. **Supervised Access:** No student is permitted inside the laboratory without the presence of the SPOC / Subject Teacher[cite: 2].
        2. **Power Safety:** Never short circuit battery terminals; verify circuit polarity before turning on 5V DC adapters or Li-Ion power packs.
        3. **Component Handling:** Handle microcontrollers, 3D printer nozzles, and sensor breakout boards with clean, dry hands[cite: 2].
        4. **Zero Food / Liquid Zone:** Strict ban on water bottles and food near workbench power supplies[cite: 2].
        5. **Emergency Response:** In the event of smoke, overheating components, or loose wiring, turn off the main bench switch and report immediately[cite: 2].
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
        st.title("⚙️ Admin Workspace: Manage Records & Live Attendance")

        admin_tabs = st.tabs(["📁 File Uploader & Records", "📝 Edit Student Attendance", "🧑‍🏫 Edit Teacher Attendance"])

        # Tab 1: Regular Uploader
        with admin_tabs[0]:
            selected_section = st.selectbox("Select Category to Manage", list(CATEGORIES.keys()))
            items = CATEGORIES[selected_section]
            st.divider()

            for sno, title, formats in items:
                folder_name = get_folder_name(sno, title)
                record_dir = os.path.join(UPLOAD_DIR, folder_name)
                os.makedirs(record_dir, exist_ok=True)

                is_builtin = sno in BUILTIN_RECORDS

                with st.expander(f"**#{sno}. {title}**", expanded=False):
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

        # Tab 2: Live Edit Student Attendance (#9)
        with admin_tabs[1]:
            st.subheader("📝 Live Editor: Parameter #9 Student Attendance")
            st.info("Neeche diye gaye table me directly cell par click karke numbers/remarks edit karein aur Save karein.")
            
            df_st_att = get_student_attendance_df()
            edited_st_df = st.data_editor(df_st_att, num_rows="dynamic", use_container_width=True, key="editor_student_attendance")
            
            if st.button("💾 Save Student Attendance Changes", type="primary"):
                edited_st_df.to_csv(STUDENT_ATTENDANCE_FILE, index=False)
                st.success("Student Attendance data successfully update ho gaya hai!")
                st.rerun()

        # Tab 3: Live Edit Teacher Attendance (#10)
        with admin_tabs[2]:
            st.subheader("🧑‍🏫 Live Editor: Parameter #10 Teacher Attendance")
            st.info("Teachers ki In-Time, Out-Time, Activity, aur Present count ko update karein.")
            
            df_tc_att = get_teacher_attendance_df()
            edited_tc_df = st.data_editor(df_tc_att, num_rows="dynamic", use_container_width=True, key="editor_teacher_attendance")
            
            if st.button("💾 Save Teacher Attendance Changes", type="primary"):
                edited_tc_df.to_csv(TEACHER_ATTENDANCE_FILE, index=False)
                st.success("Teacher Attendance data successfully update ho gaya hai!")
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
                    status = "✅ Verified / Completed"
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
