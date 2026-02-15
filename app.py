import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
import json
import re
 

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="ระบบรายงานข้อมูล Sansai-CMI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS สำหรับปรับแต่งสีตามเว็บไซต์โรงพยาบาลสันทราย (โทนสีน้ำเงิน-เขียว)
st.markdown("""
    <style>
    /* สีหลักของระบบ */
    :root {
        --primary-color: #2E7D32;
        --secondary-color: #1976D2;
        --accent-color: #66BB6A;
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1976D2 0%, #2E7D32 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
    }
    
    .main-header p {
        color: #E3F2FD;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1976D2 0%, #2E7D32 100%);
    }
    
    [data-testid="stSidebar"] .sidebar-content {
        color: white;
    }
    
    /* ปุ่ม */
    .stButton>button {
        background: linear-gradient(135deg, #2E7D32 0%, #66BB6A 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #1B5E20 0%, #4CAF50 100%);
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.4);
        transform: translateY(-2px);
    }
    
    /* Cards */
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #2E7D32;
        margin-bottom: 1rem;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
    }
    
    .stError {
        background-color: #FFEBEE;
        border-left: 4px solid #F44336;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background-color: #F5F5F5;
        border: 2px dashed #2E7D32;
        border-radius: 10px;
        padding: 2rem;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #1976D2;
        font-size: 2rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ตั้งค่า Supabase
SUPABASE_URL = "https://qwxnsusfydrhtfqdcsqn.supabase.co"
SUPABASE_KEY = "sb_publishable_Q2bzMBe3jSlQWlGAZhyJig_ILZ8heFz"

class SupabaseClient:
    """Simple Supabase client using REST API"""
    
    def __init__(self, url, key):
        self.url = url
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    def insert(self, table, data):
        """Insert data into table"""
        url = f"{self.url}/rest/v1/{table}"
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code in [200, 201]:
            return {"data": response.json(), "error": None}
        else:
            return {"data": None, "error": response.text}
    
    def select(self, table, columns="*", filters=None):
        """Select data from table"""
        url = f"{self.url}/rest/v1/{table}?select={columns}"
        if filters:
            for key, value in filters.items():
                url += f"&{key}=eq.{value}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return {"data": response.json(), "count": len(response.json()), "error": None}
        else:
            return {"data": None, "count": 0, "error": response.text}
    
    def count(self, table):
        """Count records in table"""
        url = f"{self.url}/rest/v1/{table}?select=count"
        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        response = requests.head(url, headers=headers)
        if response.status_code == 200:
            count = response.headers.get("Content-Range", "0-0/0").split("/")[-1]
            return int(count)
        return 0

@st.cache_resource
def init_supabase():
    """เชื่อมต่อ Supabase"""
    return SupabaseClient(SUPABASE_URL, SUPABASE_KEY)

def parse_month_year_from_filename(filename):
    """
    แปลงชื่อไฟล์เป็น month_year
    ตัวอย่าง: "3_ipd-ธ.ค.68.xlsx" -> "2025-12-01"
    """
    # Dictionary สำหรับแปลงเดือนภาษาไทยเป็นตัวเลข
    thai_months = {
        'ม.ค.': 1, 'มกราคม': 1, 'ม.ค': 1,
        'ก.พ.': 2, 'กุมภาพันธ์': 2, 'ก.พ': 2,
        'มี.ค.': 3, 'มีนาคม': 3, 'มี.ค': 3,
        'เม.ย.': 4, 'เมษายน': 4, 'เม.ย': 4,
        'พ.ค.': 5, 'พฤษภาคม': 5, 'พ.ค': 5,
        'มิ.ย.': 6, 'มิถุนายน': 6, 'มิ.ย': 6,
        'ก.ค.': 7, 'กรกฎาคม': 7, 'ก.ค': 7,
        'ส.ค.': 8, 'สิงหาคม': 8, 'ส.ค': 8,
        'ก.ย.': 9, 'กันยายน': 9, 'ก.ย': 9,
        'ต.ค.': 10, 'ตุลาคม': 10, 'ต.ค': 10,
        'พ.ย.': 11, 'พฤศจิกายน': 11, 'พ.ย': 11,
        'ธ.ค.': 12, 'ธันวาคม': 12, 'ธ.ค': 12,
    }
    
    try:
        # ลบนามสกุลไฟล์
        name = filename.replace('.xlsx', '').replace('.xls', '').replace('.csv', '')
        
        # หาเดือนภาษาไทย
        month_num = None
        for thai_month, num in thai_months.items():
            if thai_month in name:
                month_num = num
                break
        
        if month_num is None:
            return None
        
        # หาปี (หาตัวเลข 2 หลักหลังจากเดือน)
        year_match = re.search(r'(\d{2})(?:\.xlsx|\.xls|\.csv|$)', name)
        if year_match:
            year_buddhist = int(year_match.group(1))
            # แปลงจากปี พ.ศ. 2 หลัก เป็น ค.ศ.
            # 68 = 2568 - 543 = 2025
            if year_buddhist >= 0 and year_buddhist <= 99:
                year_christian = 2500 + year_buddhist - 543
            else:
                return None
            
            # สร้างวันที่ (วันแรกของเดือน)
            month_year = f"{year_christian}-{month_num:02d}-01"
            return month_year
        
        return None
        
    except Exception as e:
        st.error(f"ไม่สามารถแปลงชื่อไฟล์เป็น month_year: {str(e)}")
        return None

def get_fiscal_year(date_value):
    """คำนวณปีงบประมาณ (ตุลาคม-กันยายน)"""
    if pd.isna(date_value):
        return None
    if isinstance(date_value, str):
        date_value = pd.to_datetime(date_value)
    if date_value.month >= 10:
        return date_value.year + 1
    else:
        return date_value.year

def calculate_length_of_stay(admit_date, discharge_date):
    """คำนวณจำนวนวันนอน"""
    if pd.isna(admit_date) or pd.isna(discharge_date):
        return None
    admit = pd.to_datetime(admit_date)
    discharge = pd.to_datetime(discharge_date)
    days = (discharge - admit).days
    return max(days, 0)

def map_columns(df):
    """แปลงชื่อคอลัมน์จากไฟล์ Excel ให้ตรงกับ schema ของ database"""
    
    # Mapping dictionary สำหรับแปลงชื่อคอลัมน์
    column_mapping = {
        'No': None,  # ไม่ใช้
        'an': 'an',
        'hn': 'hn',
        'vn': 'vn',
        'birthday': 'birth_date',
        'Age': 'age',
        'sex': 'sex',
        'AdmitDate': 'admit_date',
        'D/C Date': 'discharge_date',
        'wardname': 'ward_name',
        'pttypename': 'pttype_name',
        'pdx': 'pdx',
        'dx0': 'dx0',
        'dx1': 'dx1',
        'dx2': 'dx2',
        'dx3': 'dx3',
        'dx4': 'dx4',
        'dx5': 'dx5',
        'dx6': 'dx6',
        'dx7': 'dx7',
        'dx8': 'dx8',
        'dx9': 'dx9',
        'dx10': 'dx10',
        'op0': 'op0',
        'op1': 'op1',
        'op2': 'op2',
        'op3': 'op3',
        'op4': 'op4',
        'op5': 'op5',
        'op6': 'op6',
        'op7': 'op7',
        'op8': 'op8',
        'op9': 'op9',
        'op10': 'op10',
        'op11': 'op11',
        'จำนวนวันนอน': 'length_of_stay',
        'adjrw': 'adjrw',
        'discharge_status': 'discharge_status',
        'type_description': 'discharge_type',
        'clinic': 'clinic_name'
    }
    
    # สร้าง DataFrame ใหม่ด้วยชื่อคอลัมน์ที่แปลงแล้ว
    df_mapped = pd.DataFrame()
    
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col is not None:
            df_mapped[new_col] = df[old_col]
    
    return df_mapped

def validate_and_prepare_data(df, filename):
    """ตรวจสอบและเตรียมข้อมูลก่อนนำเข้า"""
    errors = []
    warnings = []
    
    # แปลง month_year จากชื่อไฟล์
    month_year = parse_month_year_from_filename(filename)
    if month_year is None:
        errors.append("ไม่สามารถอ่าน month_year จากชื่อไฟล์ได้ กรุณาตั้งชื่อไฟล์ในรูปแบบ: 'ipd-ธ.ค.68.xlsx'")
        return None, errors, warnings
    
    # แปลงชื่อคอลัมน์ให้ตรงกับ schema
    df_mapped = map_columns(df)
    
    # คอลัมน์ที่จำเป็น
    required_columns = ['an', 'hn']
    missing_cols = [col for col in required_columns if col not in df_mapped.columns]
    
    if missing_cols:
        errors.append(f"ขาดคอลัมน์ที่จำเป็น: {', '.join(missing_cols)}")
        return None, errors, warnings
    
    # ทำสำเนาข้อมูล
    df_clean = df_mapped.copy()
    
    # เพิ่ม month_year ทุกแถว
    df_clean['month_year'] = month_year
    
    # แปลงวันที่
    date_columns = ['birth_date', 'admit_date', 'discharge_date']
    for col in date_columns:
        if col in df_clean.columns:
            try:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                # แปลงเป็น ISO format string
                df_clean[col] = df_clean[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)
            except:
                warnings.append(f"ไม่สามารถแปลงวันที่ในคอลัมน์ {col} บางรายการ")
    
    # แปลง month_year เป็น datetime แล้วแปลงกลับเป็น string
    df_clean['month_year'] = pd.to_datetime(df_clean['month_year']).dt.strftime('%Y-%m-%d')
    
    # คำนวณปีงบประมาณ
    df_clean['fiscal_year'] = pd.to_datetime(df_clean['month_year']).apply(get_fiscal_year)
    
    # ถ้าไม่มี length_of_stay หรือเป็น null ให้คำนวณใหม่
    if 'length_of_stay' not in df_clean.columns or df_clean['length_of_stay'].isna().any():
        if 'admit_date' in df_clean.columns and 'discharge_date' in df_clean.columns:
            # แปลงกลับเป็น datetime เพื่อคำนวณ
            admit_dates = pd.to_datetime(df_clean['admit_date'], errors='coerce')
            discharge_dates = pd.to_datetime(df_clean['discharge_date'], errors='coerce')
            df_clean['length_of_stay'] = (discharge_dates - admit_dates).dt.days
            df_clean['length_of_stay'] = df_clean['length_of_stay'].apply(lambda x: max(x, 0) if pd.notna(x) else None)
    
    # แปลงตัวเลข
    if 'age' in df_clean.columns:
        df_clean['age'] = pd.to_numeric(df_clean['age'], errors='coerce')
    
    if 'adjrw' in df_clean.columns:
        df_clean['adjrw'] = pd.to_numeric(df_clean['adjrw'], errors='coerce')
    
    if 'length_of_stay' in df_clean.columns:
        df_clean['length_of_stay'] = pd.to_numeric(df_clean['length_of_stay'], errors='coerce')
    
    # แปลง AN และ HN เป็น string
    df_clean['an'] = df_clean['an'].astype(str)
    df_clean['hn'] = df_clean['hn'].astype(str)
    if 'vn' in df_clean.columns:
        df_clean['vn'] = df_clean['vn'].astype(str)
    
    # แปลง sex เป็น string (1 ตัวอักษร)
    if 'sex' in df_clean.columns:
        df_clean['sex'] = df_clean['sex'].astype(str).str[:1]
    
    # แปลง op ทั้งหมดเป็น string
    op_columns = [f'op{i}' for i in range(12)]
    for col in op_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(lambda x: str(x) if pd.notna(x) and str(x) != 'nan' else None)
    
    # เพิ่มข้อมูลการนำเข้า
    df_clean['imported_by'] = st.session_state.get('username', 'system')
    df_clean['created_at'] = datetime.now().isoformat()
    df_clean['updated_at'] = datetime.now().isoformat()
    
    # ตรวจสอบข้อมูลซ้ำ (AN + month_year)
    duplicates = df_clean[df_clean.duplicated(subset=['an', 'month_year'], keep=False)]
    if not duplicates.empty:
        warnings.append(f"พบข้อมูลซ้ำในไฟล์ {len(duplicates)} รายการ (AN + month_year ซ้ำ)")
    
    # แทนที่ NaN ด้วย None
    df_clean = df_clean.where(pd.notna(df_clean), None)
    
    return df_clean, errors, warnings

def import_to_supabase(df, batch_size=100):
    """นำเข้าข้อมูลไปยัง Supabase"""
    client = init_supabase()
    total_rows = len(df)
    success_count = 0
    error_count = 0
    error_details = []
    
    # แสดง progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # แบ่งข้อมูลเป็น batch
    for i in range(0, total_rows, batch_size):
        batch = df.iloc[i:i+batch_size]
        batch_data = batch.to_dict('records')
        
        try:
            # ลบคอลัมน์ id ถ้ามี (เพราะเป็น auto-increment)
            for record in batch_data:
                if 'id' in record:
                    del record['id']
            
            # Insert ข้อมูล
            result = client.insert('ipd_monthly', batch_data)
            
            if result['error'] is None:
                success_count += len(batch_data)
            else:
                error_count += len(batch_data)
                error_details.append(f"Batch {i//batch_size + 1}: {result['error']}")
            
        except Exception as e:
            error_count += len(batch_data)
            error_details.append(f"Batch {i//batch_size + 1}: {str(e)}")
        
        # Update progress
        progress = min((i + batch_size) / total_rows, 1.0)
        progress_bar.progress(progress)
        status_text.text(f"กำลังนำเข้าข้อมูล... {min(i + batch_size, total_rows)}/{total_rows} รายการ")
    
    progress_bar.empty()
    status_text.empty()
    
    return success_count, error_count, error_details

# ============================================
# MAIN APP
# ============================================

def main():
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>🏥 ระบบรายงานข้อมูล Sansai-CMI</h1>
            <p>โรงพยาบาลสันทราย | Case Mix Information System</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Menu
    with st.sidebar:
        st.markdown("### 📋 เมนูหลัก")
        menu = st.radio(
            "เลือกเมนู",
            ["🏠 หน้าแรก", "📊 รายงาน", "📥 นำเข้าข้อมูล"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ ข้อมูลระบบ")
        st.info(f"**วันที่:** {datetime.now().strftime('%d/%m/%Y')}\n\n**เวอร์ชัน:** 1.0.0")
    
    # หน้าแรก
    if menu == "🏠 หน้าแรก":
        show_home()
    
    # รายงาน
    elif menu == "📊 รายงาน":
        show_reports()
    
    # นำเข้าข้อมูล
    elif menu == "📥 นำเข้าข้อมูล":
        show_import()

def show_home():
    """หน้าแรก"""
    st.markdown("## ยินดีต้อนรับสู่ระบบรายงานข้อมูล Sansai-CMI")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="info-card">
                <h3>📊 รายงานข้อมูล</h3>
                <p>ดูรายงานและสถิติข้อมูล IPD Monthly</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="info-card">
                <h3>📥 นำเข้าข้อมูล</h3>
                <p>นำเข้าข้อมูลจากไฟล์ Excel/CSV</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="info-card">
                <h3>🔍 วิเคราะห์ข้อมูล</h3>
                <p>วิเคราะห์และประมวลผลข้อมูล</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # แสดงสถิติเบื้องต้น
    try:
        client = init_supabase()
        
        # นับจำนวนรายการทั้งหมด
        total_records = client.count('ipd_monthly')
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 จำนวนรายการทั้งหมด", f"{total_records:,}")
        
        with col2:
            st.metric("📅 ข้อมูลล่าสุด", datetime.now().strftime('%m/%Y'))
        
        with col3:
            st.metric("✅ สถานะระบบ", "ปกติ")
        
        with col4:
            st.metric("🔄 อัพเดตล่าสุด", datetime.now().strftime('%d/%m/%Y'))
        
    except Exception as e:
        st.warning(f"ไม่สามารถโหลดสถิติได้: {str(e)}")
    
    st.markdown("---")
    st.info("💡 **คำแนะนำ:** เลือกเมนูจากแถบด้านซ้ายเพื่อเริ่มใช้งานระบบ")

def show_reports():
    """หน้ารายงาน"""
    st.markdown("## 📊 รายงานข้อมูล")
    st.info("🚧 ส่วนนี้อยู่ระหว่างการพัฒนา")
    
    st.markdown("""
        ### รายงานที่จะพัฒนา:
        - 📈 สถิติผู้ป่วยใน (IPD) รายเดือน
        - 📊 สถิติ Case Mix Index (CMI)
        - 🏥 สถิติแยกตามหอผู้ป่วย
        - 💊 สถิติแยกตามโรค (ICD-10)
        - 📉 แนวโน้มและกราฟ
    """)
def show_import():
    """หน้านำเข้าข้อมูล"""
    st.markdown("## 📥 นำเข้าข้อมูล IPD Monthly")
    
    # ตรวจสอบ libraries ที่มีอยู่
    available_engines = {
        'openpyxl': False,
        'xlrd': False,
        'html': True
    }
    
    try:
        import openpyxl
        available_engines['openpyxl'] = True
    except ImportError:
        pass
    
    try:
        import xlrd
        available_engines['xlrd'] = True
    except ImportError:
        pass
    
    excel_available = available_engines['openpyxl'] or available_engines['xlrd']
    
    # คำแนะนำ
    with st.expander("📖 คำแนะนำการนำเข้าข้อมูล", expanded=True):
        st.markdown(f"""
        ### รูปแบบไฟล์ที่รองรับ:
        - **Excel (.xlsx)** {'✅' if available_engines['openpyxl'] else '⚠️ จำกัด'}
        - **Excel เก่า (.xls)** {'✅' if available_engines['xlrd'] else '⚠️ จำกัด'}
        - **CSV (.csv)** ✅ (แนะนำ)
        - **HTML Table (.html)** ✅
        
        {"⚠️ **หมายเหตุ:** ระบบอาจอ่านไฟล์ Excel ได้ไม่สมบูรณ์ แนะนำให้แปลงเป็น CSV ก่อน" if not excel_available else ""}
        
        ### 🔴 สำคัญ: รูปแบบชื่อไฟล์
        ชื่อไฟล์ต้องมีรูปแบบ: **`ipd-[เดือน].[ปี].[นามสกุล]`**
        
        ตัวอย่าง:
        - `3_ipd-ธ.ค.68.xlsx` → ธันวาคม 2568 (2025-12-01)
        - `ipd-ม.ค.69.csv` → มกราคม 2569 (2026-01-01)
        - `ipd-ก.พ.68.xls` → กุมภาพันธ์ 2568 (2025-02-01)
        
        เดือนที่รองรับ: ม.ค., ก.พ., มี.ค., เม.ย., พ.ค., มิ.ย., ก.ค., ส.ค., ก.ย., ต.ค., พ.ย., ธ.ค.
        
        ### คอลัมน์ที่จำเป็นต้องมีในไฟล์:
        - **an** - รหัสผู้ป่วยใน (Admission Number)
        - **hn** - รหัสผู้ป่วย (Hospital Number)
        
        ### คอลัมน์ที่รองรับ:
        - vn, birthday, Age, sex
        - AdmitDate, D/C Date, จำนวนวันนอน
        - wardname, pttypename, clinic
        - pdx, dx0-dx10 (รหัสโรค ICD-10)
        - op0-op11 (รหัสหัตถการ)
        - adjrw, discharge_status, type_description
        
        ### หมายเหตุ:
        - ระบบจะอ่าน **month_year** จากชื่อไฟล์โดยอัตโนมัติ
        - ระบบจะคำนวณ **fiscal_year** ให้อัตโนมัติ
        - ข้อมูลที่มี AN ซ้ำในเดือนเดียวกันจะไม่สามารถนำเข้าได้
        """)
        
        if not excel_available:
            st.warning("""
            ### ⚠️ ระบบอ่านไฟล์ Excel ได้จำกัด
            
            **วิธีแปลงไฟล์ Excel เป็น CSV (แนะนำ):**
            1. เปิดไฟล์ Excel
            2. คลิก **File** → **Save As**
            3. เลือก **Save as type:** → **CSV UTF-8 (Comma delimited) (*.csv)**
            4. กด **Save**
            5. อัปโหลดไฟล์ CSV ที่นี่
            
            **ทางเลือกอื่น:**
            - ใช้ Google Sheets: File → Download → Comma Separated Values (.csv)
            - ใช้ LibreOffice Calc: File → Save As → Text CSV (.csv)
            """)
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "เลือกไฟล์ข้อมูล",
        type=['xlsx', 'xls', 'csv', 'html'],
        help="อัพโหลดไฟล์ Excel, CSV, หรือ HTML ที่ตั้งชื่อตามรูปแบบ: ipd-ธ.ค.68.xlsx"
    )
    
    if uploaded_file is not None:
        try:
            st.info(f"📁 **ชื่อไฟล์:** {uploaded_file.name}")
            
            month_year = parse_month_year_from_filename(uploaded_file.name)
            if month_year:
                month_year_display = pd.to_datetime(month_year).strftime('%B %Y')
                st.success(f"📅 **เดือน-ปีที่จะนำเข้า:** {month_year_display} ({month_year})")
            else:
                st.error("❌ ไม่สามารถอ่าน month_year จากชื่อไฟล์ได้ กรุณาตั้งชื่อไฟล์ให้ถูกต้อง")
                st.stop()
            
            df = None
            file_ext = uploaded_file.name.split('.')[-1].lower()
            
            with st.spinner(f"กำลังอ่านไฟล์ .{file_ext}..."):
                try:
                    # === CSV File ===
                    if file_ext == 'csv':
                        try:
                            df = pd.read_csv(uploaded_file, encoding='utf-8')
                        except UnicodeDecodeError:
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, encoding='cp874')
                        st.success("✅ อ่านไฟล์ CSV สำเร็จ")
                    
                    # === HTML File ===
                    elif file_ext == 'html':
                        uploaded_file.seek(0)
                        html_content = uploaded_file.read().decode('utf-8', errors='replace')
                        tables = pd.read_html(html_content)
                        
                        if not tables:
                            st.error("❌ ไม่พบตารางในไฟล์ HTML")
                            st.stop()
                        
                        if len(tables) > 1:
                            table_index = st.selectbox(
                                f"พบ {len(tables)} ตาราง กรุณาเลือกตารางที่ต้องการ:",
                                range(len(tables)),
                                format_func=lambda x: f"ตารางที่ {x+1} ({len(tables[x])} แถว, {len(tables[x].columns)} คอลัมน์)"
                            )
                            df = tables[table_index]
                        else:
                            df = tables[0]
                        
                        st.success(f"✅ อ่านไฟล์ HTML สำเร็จ (ตารางที่ 1/{len(tables)})")
                    
                    # === Excel Files (.xlsx, .xls) ===
                    elif file_ext in ['xlsx', 'xls']:
                        if file_ext == 'xlsx':
                            engines_to_try = ['openpyxl', 'xlrd']
                        else:
                            engines_to_try = ['xlrd', 'openpyxl']
                        
                        success = False
                        errors = []
                        
                        for engine in engines_to_try:
                            try:
                                uploaded_file.seek(0)
                                df = pd.read_excel(uploaded_file, engine=engine)
                                st.success(f"✅ อ่านไฟล์ Excel สำเร็จด้วย engine: {engine}")
                                success = True
                                break
                            except ImportError as e:
                                errors.append(f"- {engine} (ไม่ได้ติดตั้ง): {str(e)[:80]}")
                                continue
                            except Exception as e:
                                errors.append(f"- {engine}: {str(e)[:80]}")
                                continue
                        
                        # Fallback: ลองอ่านเป็น HTML (บาง .xls เป็น HTML จริงๆ)
                        if not success:
                            try:
                                uploaded_file.seek(0)
                                raw_content = uploaded_file.read(4096)
                                uploaded_file.seek(0)
                                
                                if b"<table" in raw_content.lower() or b"<html" in raw_content.lower():
                                    html_text = uploaded_file.read().decode('utf-8', errors='replace')
                                    tables = pd.read_html(html_text)
                                    if tables:
                                        df = tables[0]
                                        st.info("✅ อ่านไฟล์สำเร็จในรูปแบบ HTML Table")
                                        success = True
                            except Exception as e:
                                errors.append(f"- HTML fallback: {str(e)[:80]}")
                        
                        # ถ้ายังไม่สำเร็จ — หยุดและแนะนำ
                        if not success:
                            st.error(f"""
❌ **ไม่สามารถอ่านไฟล์ Excel ได้**

**ข้อผิดพลาดที่พบ:**
{chr(10).join(errors)}

**วิธีแก้ — แปลงไฟล์เป็น CSV:**
1. เปิดไฟล์ด้วย Excel
2. กด File → Save As
3. เลือก CSV UTF-8 (Comma delimited) (*.csv)
4. อัปโหลดไฟล์ .csv แทน
                            """)
                            st.stop()
                    
                    else:
                        st.error(f"❌ ไฟล์นามสกุล .{file_ext} ไม่รองรับ")
                        st.stop()
                
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}")
                    st.info("""
                    💡 **แนะนำวิธีแก้:**
                    1. แปลงไฟล์เป็น **CSV** (แนะนำที่สุด)
                       - Excel: File → Save As → CSV UTF-8
                       - Google Sheets: File → Download → CSV
                    2. ตรวจสอบว่าไฟล์ไม่เสียหาย
                    3. ลองเปิดไฟล์ด้วย Excel/LibreOffice แล้วบันทึกใหม่
                    """)
                    st.exception(e)
                    st.stop()
            
            if df is None or df.empty:
                st.error("❌ ไม่สามารถอ่านข้อมูลจากไฟล์ได้ หรือไฟล์ว่างเปล่า")
                st.stop()
            
            # แสดงข้อมูลตัวอย่าง
            st.markdown("### 👀 ตัวอย่างข้อมูลจากไฟล์")
            st.dataframe(df.head(10), use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 จำนวนแถว", f"{len(df):,}")
            with col2:
                st.metric("📋 จำนวนคอลัมน์", f"{len(df.columns):,}")
            with col3:
                st.metric("🔍 ขนาดไฟล์", f"{uploaded_file.size/1024:.2f} KB")
            
            st.markdown("---")
            
            # ตรวจสอบและเตรียมข้อมูล
            st.markdown("### 🔍 ตรวจสอบและแปลงข้อมูล")
            
            with st.spinner("กำลังตรวจสอบและแปลงข้อมูล..."):
                df_clean, errors, warnings = validate_and_prepare_data(df, uploaded_file.name)
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
                st.stop()
            
            if warnings:
                for warning in warnings:
                    st.warning(f"⚠️ {warning}")
            
            if df_clean is not None:
                st.success("✅ ข้อมูลผ่านการตรวจสอบเรียบร้อย")
                
                with st.expander("📋 ดูข้อมูลที่เตรียมนำเข้า (แปลงเป็น schema database แล้ว)"):
                    st.dataframe(df_clean.head(20), use_container_width=True)
                    st.info(f"💡 ข้อมูลมีคอลัมน์: {', '.join(df_clean.columns.tolist())}")
                
                st.markdown("---")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🚀 เริ่มนำเข้าข้อมูล", type="primary", use_container_width=True):
                        st.session_state.confirm_import = True
                
                if st.session_state.get('confirm_import', False):
                    st.markdown("### 📤 กำลังนำเข้าข้อมูล")
                    
                    with st.spinner("กรุณารอสักครู่..."):
                        success_count, error_count, error_details = import_to_supabase(df_clean)
                    
                    if error_count == 0:
                        st.balloons()
                        st.success(f"🎉 นำเข้าข้อมูลสำเร็จ **{success_count:,}** รายการ!")
                    else:
                        st.warning(f"⚠️ นำเข้าสำเร็จ **{success_count:,}** รายการ, ล้มเหลว **{error_count:,}** รายการ")
                        
                        if error_details:
                            with st.expander("🔍 รายละเอียดข้อผิดพลาด"):
                                for detail in error_details:
                                    st.error(detail)
                    
                    st.session_state.confirm_import = False
                    
                    if st.button("📥 นำเข้าข้อมูลชุดใหม่"):
                        st.rerun()
        
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {str(e)}")
            st.exception(e)

# เรียกใช้งาน
if __name__ == "__main__":
    main()
