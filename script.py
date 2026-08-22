import streamlit as st
import os
import shutil

st.set_page_config(page_title="STEM Lab Portfolio Portal", page_icon="🔬", layout="wide")

# Base directory for local file storage
UPLOAD_DIR = "stem_lab_records"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 50 STEM Record categories definitions
CATEGORIES = {
    "1. Administration & Planning": [
        (1, "STEM Lab Profile", ["pdf", "docx", "doc"]),
        (2, "Lab Objectives & Guidelines", ["pdf"]),
        (3, "Coordinator / SPOC Details", ["pdf", "docx", "doc"]),
        (4, "Annual STEM Plan", ["xlsx", "xls", "pdf"]),
        (5, "Monthly Activity Plan", ["xlsx", "xls"]),
        (6, "Class-wise Timetable", ["xlsx", "xls", "pdf"]),
        (7, "Session / Lesson Plans", ["pdf", "docx", "doc"]),
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
        (18, "STEM Activities", ["pdf", "docx", "doc"]),
        (19, "Activity Worksheets", ["pdf"]),
        (20, "Activity Photos", ["jpg", "png", "jpeg"]),
        (21, "Activity Videos", ["mp4", "mov", "avi"]),
        (22, "Student Projects", ["pdf", "docx", "doc"]),
        (23, "Prototype Details", ["pdf"]),
        (24, "Problem Statements", ["docx", "doc", "xlsx", "xls"]),
        (25, "Innovation Ideas", ["xlsx", "xls"]),
        (26, "Project Photos", ["jpg", "png", "jpeg"]),
        (27, "Project Videos", ["mp4", "mov", "avi"]),
    ],
    "4. Assessment & Competitions": [
        (28, "Assessment Rubrics", ["xlsx", "xls", "pdf"]),
        (29, "Student Assessment", ["xlsx", "xls"]),
        (30, "Student Performance", ["xlsx", "xls", "csv"]),
        (31, "STEM SPARK Registration", ["pdf", "xlsx", "xls"]),
        (32, "STEM SPARK Team Details", ["xlsx", "xls"]),
        (33, "STEM SPARK Submissions", ["pdf"]),
        (34, "VVM Records", ["pdf", "xlsx", "xls"]),
        (35, "Other Competitions", ["pdf", "xlsx", "xls"]),
    ],
    "5. Training & Communication": [
        (36, "Teacher Training Records", ["xlsx", "xls", "pdf"]),
        (37, "Training Certificates", ["pdf", "jpg", "png", "jpeg"]),
        (38, "Training Attendance", ["xlsx", "xls"]),
        (39, "Workshop Reports", ["docx", "doc", "pdf"]),
        (40, "Workshop Photos", ["jpg", "png", "jpeg"]),
        (41, "Government Circulars", ["pdf"]),
        (42, "School Circulars", ["pdf"]),
        (43, "Official Emails", ["pdf", "jpg", "png"]),
        (44, "Meeting Minutes", ["docx", "doc", "pdf"]),
    ],
    "6. Reports & Achievements": [
        (45, "Monthly Reports", ["pdf"]),
        (46, "Quarterly Reports", ["pdf"]),
        (47, "Annual Report", ["pdf"]),
        (48, "Student Certificates", ["pdf", "jpg", "png", "jpeg"]),
        (49, "Student Achievements", ["xlsx", "xls", "pdf"]),
        (50, "STEM Lab Event Photos", ["jpg", "png", "jpeg"]),
    ]
}

# Helper to format directory names safely
def get_folder_name(sno, title):
    clean_title = title.replace(" ", "_").replace("/", "_")
    return f"{sno:02d}_{clean_title}"

# Sidebar Navigation
st.sidebar.title("🔬 STEM Lab Portal")
access_mode = st.sidebar.radio("Navigation Mode", ["Viewer (Read-Only)", "Admin (Upload & Manage)"])

# ----------------- ADMIN MODE (UPLOAD & MANAGE) -----------------
if access_mode == "Admin (Upload & Manage)":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Admin Authentication")
    password = st.sidebar.text_input("Enter Admin Password", type="password")

    if password == "stem@admin123":
        st.sidebar.success("Authenticated")
        st.title("⚙️ Admin Workspace: Upload & Manage Records")
        st.caption("Upload, replace, and manage STEM records across all categories.")

        selected_section = st.selectbox("Select Record Category", list(CATEGORIES.keys()))
        items = CATEGORIES[selected_section]

        st.divider()

        for sno, title, formats in items:
            folder_name = get_folder_name(sno, title)
            record_dir = os.path.join(UPLOAD_DIR, folder_name)
            os.makedirs(record_dir, exist_ok=True)

            with st.expander(f"**#{sno}. {title}** (Allowed: `.{', .'.join(formats)}`)", expanded=False):
                uploaded_files = st.file_uploader(
                    f"Upload files for: {title}",
                    type=formats,
                    accept_multiple_files=True,
                    key=f"admin_upload_{sno}"
                )

                if uploaded_files:
                    for f in uploaded_files:
                        target_path = os.path.join(record_dir, f.name)
                        with open(target_path, "wb") as buffer:
                            buffer.write(f.getbuffer())
                    st.success(f"Successfully uploaded {len(uploaded_files)} file(s).")
                    st.rerun()

                # Display existing records with deletion controls
                existing_files = os.listdir(record_dir)
                if existing_files:
                    st.markdown("**Existing Files:**")
                    for fname in existing_files:
                        col1, col2 = st.columns([5, 1])
                        col1.text(f"📄 {fname}")
                        if col2.button("Delete", key=f"del_{sno}_{fname}", type="secondary"):
                            os.remove(os.path.join(record_dir, fname))
                            st.rerun()
                else:
                    st.info("No records uploaded yet.")
    else:
        st.title("🔒 Restricted Access")
        if password:
            st.error("Invalid password. Please try again.")
        else:
            st.info("Enter the admin password in the sidebar to access management controls.")

# ----------------- VIEWER MODE (READ / DOWNLOAD ONLY) -----------------
else:
    st.title("📚 STEM Lab Digital Records Repository")
    st.caption("Browse, inspect, and download official STEM documentation.")

    viewer_tab1, viewer_tab2 = st.tabs(["📁 Browse by Category", "📊 Repository Status Summary"])

    with viewer_tab1:
        for section_name, items in CATEGORIES.items():
            st.subheader(f"📑 {section_name}")
            for sno, title, formats in items:
                folder_name = get_folder_name(sno, title)
                record_dir = os.path.join(UPLOAD_DIR, folder_name)
                files = os.listdir(record_dir) if os.path.exists(record_dir) else []

                with st.expander(f"#{sno}. {title} ({len(files)} files available)"):
                    if files:
                        for fname in files:
                            file_path = os.path.join(record_dir, fname)
                            col_a, col_b = st.columns([4, 1])
                            col_a.text(f"📄 {fname}")
                            with open(file_path, "rb") as cur_file:
                                col_b.download_button(
                                    label="Download",
                                    data=cur_file.read(),
                                    file_name=fname,
                                    key=f"dl_view_{sno}_{fname}"
                                )
                    else:
                        st.info("No documents are currently available for this section.")

    with viewer_tab2:
        total_items = 50
        uploaded_items = 0
        summary_data = []

        for section_name, items in CATEGORIES.items():
            for sno, title, formats in items:
                folder_name = get_folder_name(sno, title)
                record_dir = os.path.join(UPLOAD_DIR, folder_name)
                file_count = len(os.listdir(record_dir)) if os.path.exists(record_dir) else 0

                if file_count > 0:
                    uploaded_items += 1
                    status = f"✅ Available ({file_count} files)"
                else:
                    status = "⏳ Pending"

                summary_data.append({
                    "Index": sno,
                    "Parameter / Record": title,
                    "Category": section_name,
                    "Allowed Formats": ", ".join(formats).upper(),
                    "Status": status
                })

        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total Parameters", total_items)
        col_m2.metric("Completed Records", f"{uploaded_items} / {total_items}")

        st.dataframe(summary_data, use_container_width=True)