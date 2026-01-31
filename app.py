import streamlit as st
import pandas as pd
import sqlite3
import re
import zipfile
import io

# --- Page Config ---
st.set_page_config(page_title="Lister Sorter (via csv file)", layout="wide")

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('ccs_scholars.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS scholars') 
    c.execute('''
        CREATE TABLE scholars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            fullname TEXT,
            course TEXT,
            year_level INTEGER,
            gpa REAL,
            units INTEGER,
            award_type TEXT
        )
    ''')
    conn.commit()
    return conn

def save_to_db(data_list, conn):
    c = conn.cursor()
    c.executemany('''
        INSERT INTO scholars (student_id, fullname, course, year_level, gpa, units, award_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', data_list)
    conn.commit()

# --- CSV Parsing Logic ---
def parse_csv_file(uploaded_file):
    uploaded_file.seek(0)
    df_raw = pd.read_csv(uploaded_file, header=None, keep_default_na=False)
    data = []
    logs = []
    
    current_award = "Rizal" 
    id_pattern = re.compile(r'\d{4}-\d{4}')

    logs.append(f"📂 Loaded CSV with {len(df_raw)} rows.")

    for index, row in df_raw.iterrows():
        row_text = " ".join(row.astype(str)).upper()
        
        # Context Switching
        if "CHANCELLOR" in row_text and "LISTER" in row_text:
            current_award = "Chancellor"
            continue
        elif "DEAN" in row_text and "LISTER" in row_text:
            current_award = "Dean"
            continue
        elif "RIZAL" in row_text and "LISTER" in row_text:
            current_award = "Rizal"
            continue

        # Extract Data
        possible_id = str(row[1]).strip()
        if id_pattern.match(possible_id):
            try:
                student_id = possible_id
                fullname = str(row[2]).strip()
                course = str(row[3]).strip()
                
                year_str = str(row[4]).strip()
                year_level = int(re.sub(r'\D', '', year_str)) if year_str.isdigit() else 0
                
                gpa_str = str(row[5]).strip()
                gpa = float(gpa_str) if gpa_str.replace('.', '', 1).isdigit() else 0.0
                
                units_str = str(row[6]).strip()
                units = int(units_str) if units_str.isdigit() else 0
                
                data.append((student_id, fullname, course, year_level, gpa, units, current_award))
            except Exception as e:
                logs.append(f"⚠️ Error parsing row {index}: {e}")
                continue

    return data, logs

# --- Main Interface ---
st.title("🎓 Lister Sorter (via csv file)")

# Sidebar
st.sidebar.header("1. Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=['csv'])

if 'data_processed' not in st.session_state:
    st.session_state['data_processed'] = False

if uploaded_file:
    if st.sidebar.button("Process CSV Data"):
        conn = init_db()
        try:
            extracted_data, logs = parse_csv_file(uploaded_file)
            if extracted_data:
                save_to_db(extracted_data, conn)
                st.session_state['data_processed'] = True
                st.success(f"✅ Successfully processed {len(extracted_data)} student records!")
                
                df_summary = pd.DataFrame(extracted_data, columns=['ID','Name','Course','Year','GPA','Units','Award'])
                st.info(f"Breakdown: {df_summary['Award'].value_counts().to_dict()}")
            else:
                st.error("❌ No valid student records found.")
                st.write(logs)
            conn.close()
        except Exception as e:
            st.error(f"Critical Error: {e}")

# --- TABS FOR WORKFLOW ---
if st.session_state['data_processed']:
    st.divider()
    
    # Updated Tabs
    tab_single, tab_batch, tab_check = st.tabs(["📋 Single List Generator", "⚡ Batch Auto-Generator", "🔍 Raw Data Inspector"])

    conn = sqlite3.connect('ccs_scholars.db')
    df_master = pd.read_sql("SELECT * FROM scholars", conn)
    
    # === TAB 1: Single List (Manual Filter) ===
    with tab_single:
        st.header("Manual Filter & Export")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            years = sorted(df_master['year_level'].unique())
            sel_year = st.multiselect("Year Level", years, default=years)
        with c2:
            courses = sorted(df_master['course'].unique())
            sel_course = st.multiselect("Course", courses, default=courses)
        with c3:
            awards = sorted(df_master['award_type'].unique())
            sel_award = st.multiselect("Award Type", awards, default=awards)

        if sel_year and sel_course and sel_award:
            fmt = lambda x: "'" + "','".join(map(str, x)) + "'"
            query = f"""
                SELECT student_id, fullname, course, year_level, gpa, award_type
                FROM scholars 
                WHERE year_level IN ({fmt(sel_year)}) 
                AND course IN ({fmt(sel_course)}) 
                AND award_type IN ({fmt(sel_award)})
                ORDER BY award_type, year_level, course, fullname
            """
            df_filtered = pd.read_sql(query, conn)
            st.dataframe(df_filtered, width="stretch", height=600, hide_index=True)
            
            # Dynamic Name
            def get_label(selected, all_options, prefix=""):
                if len(selected) == len(all_options): return "All"
                if len(selected) > 3: return "Mixed"
                return prefix + "-".join(map(str, selected))

            fname = f"{get_label(sel_year, years, 'Y')}_{get_label(sel_course, courses)}_{get_label(sel_award, awards)}.csv"
            
            st.download_button(f"📥 Download ({fname})", df_filtered.to_csv(index=False).encode('utf-8'), fname, "text/csv")

    # === TAB 2: Batch Auto-Generator (The Automation!) ===
    with tab_batch:
        st.header("Batch Process All Lists")
        st.markdown("This will automatically generate and zip **48 separate CSV files** (4 Years × 4 Courses × 3 Awards).")
        
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            if st.button("🚀 Generate All 48 CSVs", type="primary"):
                # 1. Create In-Memory ZIP
                zip_buffer = io.BytesIO()
                file_count = 0
                total_records_exported = 0
                
                all_years = [1, 2, 3, 4]
                all_courses = ["BSIT", "BSCS", "BSIS", "BSCA"]
                all_awards = ["Rizal", "Chancellor", "Dean"]
                
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for y in all_years:
                        for c in all_courses:
                            for a in all_awards:
                                # Filter Data
                                subset = df_master[
                                    (df_master['year_level'] == y) & 
                                    (df_master['course'] == c) & 
                                    (df_master['award_type'] == a)
                                ]
                                
                                # ALWAYS create file, even if empty
                                csv_data = subset.to_csv(index=False)
                                filename = f"Y{y}_{c}_{a}.csv"
                                zf.writestr(filename, csv_data)
                                file_count += 1
                                total_records_exported += len(subset)
                
                # 2. Finalize ZIP
                zip_buffer.seek(0)
                
                # 3. Verification Report
                st.success(f"✅ Batch Complete! Generated {file_count} files.")
                
                # Reconciliation Table
                st.markdown("### 📊 Verification Report")
                metrics_col1, metrics_col2 = st.columns(2)
                metrics_col1.metric("Total Students in Database", len(df_master))
                metrics_col2.metric("Total Students in Batch Export", total_records_exported)
                
                if len(df_master) == total_records_exported:
                    st.balloons()
                    st.info("✨ Perfect Match! All students are accounted for in the generated files.")
                else:
                    st.warning("⚠️ Mismatch detected. Some students might have non-standard Course/Year labels.")

                # 4. Download Button
                st.download_button(
                    label="📦 Download All_Scholars_Lists.zip",
                    data=zip_buffer,
                    file_name="All_Scholars_Lists.zip",
                    mime="application/zip"
                )

    # === TAB 3: Raw Data Inspector ===
    with tab_check:
        st.header("Original Source File Verification")
        if uploaded_file:
            uploaded_file.seek(0)
            df_raw_view = pd.read_csv(uploaded_file, header=None, keep_default_na=False)
            st.dataframe(df_raw_view, width="stretch", height=600)
    
    conn.close()