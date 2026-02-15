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
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3eG5zdXNmeWRyaHRmcWRjc3FuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwOTczNDcsImV4cCI6MjA4NjY3MzM0N30.1KiMRlJJ1jUpS7xfzocahJl3fH78m6CgM3Nm-UhhcRk"


class SupabaseClient:
    """Simple Supabase client using REST API with improved error handling"""
    
    def __init__(self, url, key):
        self.url = url
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    def test_connection(self):
        """ทดสอบการเชื่อมต่อ Supabase"""
        try:
            url = f"{self.url}/rest/v1/"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return {"success": True, "message": "✅ เชื่อมต่อ Supabase สำเร็จ"}
            else:
                return {
                    "success": False, 
                    "message": f"❌ HTTP {response.status_code}",
                    "detail": response.text[:200]
                }
        except requests.exceptions.Timeout:
            return {"success": False, "message": "⏱️ Timeout - เซิร์ฟเวอร์ตอบสนองช้า"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "🔌 ไม่สามารถเชื่อมต่อได้"}
        except Exception as e:
            return {"success": False, "message": f"❌ {str(e)}"}
    
    def insert(self, table, data):
        """Insert data into table"""
        url = f"{self.url}/rest/v1/{table}"
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code in [200, 201]:
                return {"data": response.json(), "error": None}
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_detail)
                except:
                    pass
                return {"data": None, "error": f"HTTP {response.status_code}: {error_detail}"}
        except Exception as e:
            return {"data": None, "error": f"Error: {str(e)}"}
    
    def select(self, table, columns="*", filters=None, limit=None):
        """
        Select data from table with pagination support
        
        Args:
            table: ชื่อตาราง
            columns: คอลัมน์ที่ต้องการ (default: "*")
            filters: เงื่อนไขการกรอง (dict)
            limit: จำกัดจำนวนผลลัพธ์ (None = ดึงทั้งหมด)
        """
        all_data = []
        offset = 0
        page_size = 1000  # Supabase limit per request
        
        while True:
            url = f"{self.url}/rest/v1/{table}?select={columns}"
            url += f"&limit={page_size}&offset={offset}"
            
            if filters:
                for key, value in filters.items():
                    url += f"&{key}=eq.{value}"
            
            # เพิ่ม header สำหรับ pagination
            headers = self.headers.copy()
            headers["Prefer"] = "count=exact"
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get('message', error_detail)
                    except:
                        pass
                    
                    return {
                        "data": None, 
                        "count": 0, 
                        "error": f"HTTP {response.status_code}: {error_detail[:300]}"
                    }
                
                data = response.json()
                
                # ถ้าไม่มีข้อมูลแล้ว หยุด
                if not data:
                    break
                
                all_data.extend(data)
                
                # ถ้าได้ข้อมูลน้อยกว่า page_size แสดงว่าหมดแล้ว
                if len(data) < page_size:
                    break
                
                # ถ้ามี limit และได้ครบแล้ว
                if limit and len(all_data) >= limit:
                    all_data = all_data[:limit]
                    break
                
                offset += page_size
                
            except requests.exceptions.Timeout:
                return {"data": None, "count": 0, "error": "Timeout: เซิร์ฟเวอร์ตอบสนองช้า"}
            except requests.exceptions.ConnectionError:
                return {"data": None, "count": 0, "error": "Connection Error: ไม่สามารถเชื่อมต่อได้"}
            except Exception as e:
                return {"data": None, "count": 0, "error": f"Error: {str(e)}"}
        
        return {"data": all_data, "count": len(all_data), "error": None}
    
    def count(self, table):
        """Count records in table - ปรับปรุงให้ทำงานได้ดีขึ้น"""
        url = f"{self.url}/rest/v1/{table}?select=count"
        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        
        try:
            # ลอง HEAD request ก่อน
            response = requests.head(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content_range = response.headers.get("Content-Range", "")
                if content_range:
                    # Format: "0-999/1234" or "*/1234"
                    parts = content_range.split("/")
                    if len(parts) == 2:
                        try:
                            return int(parts[1])
                        except:
                            pass
            
            # ถ้า HEAD ไม่ได้ ลอง GET
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # ถ้า response เป็น list ให้นับ
                if isinstance(data, list):
                    return len(data)
                # ถ้า response มี count
                if isinstance(data, dict) and 'count' in data:
                    return data['count']
                    
            return 0
            
        except Exception as e:
            st.warning(f"⚠️ ไม่สามารถนับจำนวนได้: {str(e)}")
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
            ["🏠 หน้าแรก", "📊 รายงาน", "📥 นำเข้าข้อมูล", "🔧 ทดสอบการเชื่อมต่อ"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ ข้อมูลระบบ")
        st.info(f"**วันที่:** {datetime.now().strftime('%d/%m/%Y')}\n\n**เวอร์ชัน:** 1.0.1 (Fixed)")
    
    # หน้าแรก
    if menu == "🏠 หน้าแรก":
        show_home()
    
    # รายงาน
    elif menu == "📊 รายงาน":
        show_reports()
    
    # นำเข้าข้อมูล
    elif menu == "📥 นำเข้าข้อมูล":
        show_import()
    
    # ทดสอบการเชื่อมต่อ
    elif menu == "🔧 ทดสอบการเชื่อมต่อ":
        show_connection_test()

def show_connection_test():
    """หน้าทดสอบการเชื่อมต่อ Supabase"""
    st.markdown("## 🔧 ทดสอบการเชื่อมต่อ Supabase")
    
    client = init_supabase()
    
    # ── Test 1: Connection ──
    st.markdown("### 1️⃣ ทดสอบการเชื่อมต่อ")
    if st.button("🔌 ทดสอบเชื่อมต่อ", key="test_conn"):
        with st.spinner("กำลังทดสอบ..."):
            result = client.test_connection()
            
            if result['success']:
                st.success(result['message'])
            else:
                st.error(result['message'])
                if 'detail' in result:
                    with st.expander("📄 รายละเอียดข้อผิดพลาด"):
                        st.code(result['detail'])
    
    st.markdown("---")
    
    # ── Test 2: Count ──
    st.markdown("### 2️⃣ นับจำนวนรายการในตาราง")
    if st.button("🔢 นับจำนวนข้อมูล", key="test_count"):
        with st.spinner("กำลังนับ..."):
            count = client.count('ipd_monthly')
            st.metric("📊 จำนวนรายการทั้งหมด", f"{count:,} ราย")
    
    st.markdown("---")
    
    # ── Test 3: Select ──
    st.markdown("### 3️⃣ ดึงข้อมูลตัวอย่าง (5 รายการแรก)")
    if st.button("📥 ดึงข้อมูลตัวอย่าง", key="test_select"):
        with st.spinner("กำลังดึงข้อมูล..."):
            result = client.select('ipd_monthly', limit=5)
            
            if result['error']:
                st.error(f"❌ เกิดข้อผิดพลาด: {result['error']}")
            elif result['data']:
                st.success(f"✅ ดึงข้อมูลสำเร็จ {len(result['data'])} รายการ")
                df = pd.DataFrame(result['data'])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("📭 ไม่มีข้อมูลในตาราง")
    
    st.markdown("---")
    
    # ── Test 4: API Info ──
    st.markdown("### 4️⃣ ข้อมูล API")
    with st.expander("🔑 ข้อมูล Supabase API", expanded=False):
        st.code(f"""
URL: {SUPABASE_URL}
API Key (ย่อ): {SUPABASE_KEY[:30]}...{SUPABASE_KEY[-15:]}
Table: ipd_monthly
        """)

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
    """หน้ารายงาน — 4 tabs"""

    # ── รหัสโรค ──────────────────────────────────────────
    PNEUMONIA_CODES = [
        'J10', 'J11', 'J12', 'J13', 'J14',
        'J15', 'J16', 'J17', 'J18', 'J85.0', 'J85.1'
    ]
    OP_VENT = ['96.7']  # ventilator op codes

    # ── โหลดข้อมูล ────────────────────────────────────────
    client = init_supabase()
    with st.spinner("กำลังโหลดข้อมูล..."):
        result = client.select('ipd_monthly')

    if result['error']:
        st.error(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {result['error']}")
        st.info("💡 ลองไปที่เมนู '🔧 ทดสอบการเชื่อมต่อ' เพื่อตรวจสอบปัญหา")
        return
    
    if not result['data']:
        st.warning("⚠️ ไม่พบข้อมูลในระบบ กรุณานำเข้าข้อมูลก่อน")
        return

    df_all = pd.DataFrame(result['data'])
    if df_all.empty:
        st.warning("⚠️ ไม่พบข้อมูล")
        return

    # ── แปลงประเภทข้อมูล ─────────────────────────────────
    df_all['month_year']      = pd.to_datetime(df_all['month_year'],      errors='coerce')
    df_all['admit_date']      = pd.to_datetime(df_all['admit_date'],      errors='coerce')
    df_all['discharge_date']  = pd.to_datetime(df_all['discharge_date'],  errors='coerce')
    df_all['age']             = pd.to_numeric(df_all.get('age',            pd.Series()), errors='coerce')
    df_all['adjrw']           = pd.to_numeric(df_all.get('adjrw',          pd.Series()), errors='coerce')
    df_all['length_of_stay']  = pd.to_numeric(df_all.get('length_of_stay', pd.Series()), errors='coerce')
    df_all['month_label']     = df_all['month_year'].dt.strftime('%b %Y')
    df_all['month_sort']      = df_all['month_year'].dt.to_period('M')

    # ── helper ───────────────────────────────────────────
    def is_pneumonia(code):
        if pd.isna(code): return False
        s = str(code).strip()
        return any(s.startswith(c) for c in PNEUMONIA_CODES)

    def has_ventilator(row):
        op_cols = [f'op{i}' for i in range(12)]
        return any(
            str(row[c]).startswith(tuple(OP_VENT))
            for c in op_cols if c in row and pd.notna(row[c])
        )

    def get_vent_codes(row):
        op_cols = [f'op{i}' for i in range(12)]
        return ', '.join(
            f'{c}={row[c]}' for c in op_cols
            if c in row and pd.notna(row[c]) and str(row[c]).startswith(tuple(OP_VENT))
        )

    df_pneumonia = df_all[df_all['pdx'].apply(is_pneumonia)].copy()
    df_pneumonia['on_vent']   = df_pneumonia.apply(has_ventilator, axis=1)
    df_pneumonia['vent_codes'] = df_pneumonia.apply(get_vent_codes, axis=1)

    # ════════════════════════════════════════════════════
    # TABS
    # ════════════════════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏥 Dashboard ภาพรวม",
        "🫁 ปอดบวม (Pneumonia)",
        "💨 VAP Analysis",
        "🔬 เชิงลึก"
    ])

    # ════════════════════════════════════════════════════
    # TAB 1 : DASHBOARD ภาพรวม
    # ════════════════════════════════════════════════════
    with tab1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1565C0,#2E7D32);
                    padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.2rem;">
            <h2 style="color:white;margin:0;font-size:1.5rem;">
                🏥 Dashboard ภาพรวมโรงพยาบาลสันทราย
            </h2>
            <p style="color:#E3F2FD;margin:.3rem 0 0;font-size:.9rem;">
                IPD Monthly — ข้อมูลผู้ป่วยใน
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── KPI cards ──
        total     = len(df_all)
        cmi       = df_all['adjrw'].mean()
        total_rw  = df_all['adjrw'].sum()
        los_mean  = df_all['length_of_stay'].mean()
        death_n   = df_all['discharge_status'].str.contains('ตาย', na=False).sum()
        death_pct = death_n / total * 100 if total else 0
        readmit_n = 0
        readmit_hn = set()
        for _, row in df_all.iterrows():
            if pd.isna(row['discharge_date']) or pd.isna(row['hn']): continue
            same = df_all[
                (df_all['hn'] == row['hn']) &
                (df_all['admit_date'] > row['discharge_date']) &
                (df_all['admit_date'] <= row['discharge_date'] + pd.Timedelta(days=28))
            ]
            if len(same) > 0:
                readmit_hn.add(row['hn'])
        readmit_n   = len(readmit_hn)
        readmit_pct = readmit_n / total * 100 if total else 0

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("👥 จำหน่ายทั้งหมด",   f"{total:,} ราย")
        c2.metric("📊 CMI",               f"{cmi:.3f}")
        c3.metric("💰 Total adjRW",        f"{total_rw:,.1f}")
        c4.metric("🛏 LOS เฉลี่ย",        f"{los_mean:.1f} วัน")
        c5.metric("💀 เสียชีวิต",         f"{death_n} ราย",   f"{death_pct:.1f}%")
        c6.metric("🔄 Readmit ≤28 วัน",   f"{readmit_n} ราย", f"{readmit_pct:.1f}%")

        st.markdown("---")
        import altair as alt

        # ── กราฟ 1: จำหน่ายรายเดือน ──
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 📅 จำนวนจำหน่ายรายเดือน")
            m_count = (df_all.groupby('month_label')
                       .size().reset_index(name='จำนวน'))
            ch = alt.Chart(m_count).mark_bar(color='#1976D2').encode(
                x=alt.X('month_label:N', title='เดือน'),
                y=alt.Y('จำนวน:Q', title='ราย'),
                tooltip=['month_label', 'จำนวน']
            ).properties(height=280)
            st.altair_chart(ch, use_container_width=True)

        with col_b:
            st.markdown("#### 📊 CMI รายเดือน")
            m_cmi = (df_all.groupby('month_label')['adjrw']
                     .mean().reset_index(name='CMI').round(3))
            ch2 = alt.Chart(m_cmi).mark_line(
                point=True, strokeWidth=2, color='#2E7D32'
            ).encode(
                x=alt.X('month_label:N', title='เดือน'),
                y=alt.Y('CMI:Q', title='CMI', scale=alt.Scale(zero=False)),
                tooltip=['month_label', 'CMI']
            ).properties(height=280)
            st.altair_chart(ch2, use_container_width=True)

        # ── กราฟ 2: Top 10 โรค + clinic ──
        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown("#### 🏆 Top 10 โรค (จำนวนราย)")
            top10 = (df_all['pdx'].value_counts().head(10)
                     .reset_index().rename(columns={'pdx':'รหัส','count':'จำนวน'}))
            ch3 = alt.Chart(top10).mark_bar(color='#1565C0').encode(
                x=alt.X('จำนวน:Q', title='จำนวนราย'),
                y=alt.Y('รหัส:N', sort='-x', title='ICD-10'),
                tooltip=['รหัส', 'จำนวน']
            ).properties(height=300)
            st.altair_chart(ch3, use_container_width=True)

        with col_d:
            st.markdown("#### 🏥 สัดส่วน Clinic")
            clinic_df = (df_all['clinic_name'].value_counts().head(8)
                         .reset_index().rename(columns={'clinic_name':'clinic','count':'จำนวน'}))
            ch4 = alt.Chart(clinic_df).mark_arc(innerRadius=50).encode(
                theta=alt.Theta('จำนวน:Q'),
                color=alt.Color('clinic:N', legend=alt.Legend(title='Clinic')),
                tooltip=['clinic', 'จำนวน']
            ).properties(height=300)
            st.altair_chart(ch4, use_container_width=True)

        # ── กราฟ 3: discharge status + กลุ่มอายุ ──
        col_e, col_f = st.columns(2)
        with col_e:
            st.markdown("#### 📋 สถานะการจำหน่าย")
            status_df = (df_all['discharge_status'].value_counts()
                         .reset_index().rename(columns={'discharge_status':'สถานะ','count':'จำนวน'}))
            ch5 = alt.Chart(status_df).mark_bar(color='#43A047').encode(
                x=alt.X('จำนวน:Q'),
                y=alt.Y('สถานะ:N', sort='-x'),
                tooltip=['สถานะ', 'จำนวน']
            ).properties(height=250)
            st.altair_chart(ch5, use_container_width=True)

        with col_f:
            st.markdown("#### 👥 กลุ่มอายุ")
            bins   = [0, 5, 15, 30, 45, 60, 75, 200]
            labels = ['0-5','6-15','16-30','31-45','46-60','61-75','75+']
            df_all['age_grp'] = pd.cut(df_all['age'], bins=bins, labels=labels)
            age_df = (df_all['age_grp'].value_counts().sort_index()
                      .reset_index().rename(columns={'age_grp':'กลุ่มอายุ','count':'จำนวน'}))
            age_df['กลุ่มอายุ'] = age_df['กลุ่มอายุ'].astype(str)
            ch6 = alt.Chart(age_df).mark_bar(color='#F57C00').encode(
                x=alt.X('กลุ่มอายุ:N', sort=labels),
                y=alt.Y('จำนวน:Q'),
                tooltip=['กลุ่มอายุ', 'จำนวน']
            ).properties(height=250)
            st.altair_chart(ch6, use_container_width=True)

        # ── LOS outlier table ──
        st.markdown("---")
        st.markdown("#### ⚠️ ผู้ป่วยนอนนาน (LOS > 30 วัน)")
        long_stay = df_all[df_all['length_of_stay'] > 30].copy()
        if not long_stay.empty:
            cols_show = ['hn','an','age','pdx','ward_name',
                         'length_of_stay','discharge_status']
            avail = [c for c in cols_show if c in long_stay.columns]
            st.dataframe(
                long_stay[avail].sort_values('length_of_stay', ascending=False),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("ไม่พบผู้ป่วย LOS > 30 วัน")

    # ════════════════════════════════════════════════════
    # TAB 2 : ปอดบวม
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1976D2,#2E7D32);
                    padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.2rem;">
            <h2 style="color:white;margin:0;font-size:1.5rem;">
                🫁 ตัวชี้วัดผู้ป่วยปอดบวม (Pneumonia)
            </h2>
            <p style="color:#E3F2FD;margin:.3rem 0 0;font-size:.9rem;">
                ICD-10: J10–J18, J85.0, J85.1 | วิเคราะห์จาก pdx
            </p>
        </div>
        """, unsafe_allow_html=True)

        if df_pneumonia.empty:
            st.warning("⚠️ ไม่พบข้อมูลผู้ป่วยปอดบวม")
        else:
            # filter เดือน
            months_avail  = sorted(df_pneumonia['month_sort'].dropna().unique())
            months_labels = [str(m) for m in months_avail]
            if len(months_labels) > 1:
                cf1, cf2 = st.columns(2)
                with cf1:
                    s_m = st.selectbox("เดือนเริ่มต้น", months_labels, index=0, key='pn_s')
                with cf2:
                    e_m = st.selectbox("เดือนสิ้นสุด",  months_labels, index=len(months_labels)-1, key='pn_e')
                df_pn = df_pneumonia[
                    (df_pneumonia['month_sort'] >= s_m) &
                    (df_pneumonia['month_sort'] <= e_m)
                ].copy()
            else:
                df_pn = df_pneumonia.copy()

            # KPI
            tot_pn    = len(df_pn)
            death_pn  = df_pn['discharge_status'].str.contains('ตาย',na=False).sum()
            improve_pn = df_pn['discharge_status'].str.contains('ดีขึ้น',na=False).sum()
            vent_pn   = df_pn['on_vent'].sum()
            readmit_pn = 0
            for _, row in df_pn.iterrows():
                if pd.isna(row['discharge_date']) or pd.isna(row['hn']): continue
                same = df_all[
                    (df_all['hn'] == row['hn']) &
                    (df_all['admit_date'] > row['discharge_date']) &
                    (df_all['admit_date'] <= row['discharge_date'] + pd.Timedelta(days=28))
                ]
                if len(same) > 0:
                    readmit_pn += 1

            k1,k2,k3,k4,k5 = st.columns(5)
            k1.metric("🏥 จำหน่ายทั้งหมด", f"{tot_pn:,} ราย")
            k2.metric("💀 เสียชีวิต",       f"{death_pn} ราย", f"{death_pn/tot_pn*100:.1f}%")
            k3.metric("✅ Improve",          f"{improve_pn} ราย")
            k4.metric("🔄 Readmit ≤28 วัน", f"{readmit_pn} ราย", f"{readmit_pn/tot_pn*100:.1f}%")
            k5.metric("💨 On Ventilator",   f"{int(vent_pn)} ราย")

            st.markdown("---")

            # ── ตารางรายเดือน ──
            st.markdown("#### 📋 ตารางสรุปรายเดือน")
            rows = []
            for period, grp in df_pn.groupby('month_sort'):
                ml   = grp['month_label'].iloc[0]
                tot  = len(grp)
                dead = grp['discharge_status'].str.contains('ตาย',na=False).sum()
                imp  = grp['discharge_status'].str.contains('ดีขึ้น',na=False).sum()
                vn   = grp['on_vent'].sum()
                ra   = 0
                for _, row in grp.iterrows():
                    if pd.isna(row['discharge_date']) or pd.isna(row['hn']): continue
                    same = df_all[
                        (df_all['hn'] == row['hn']) &
                        (df_all['admit_date'] > row['discharge_date']) &
                        (df_all['admit_date'] <= row['discharge_date'] + pd.Timedelta(days=28))
                    ]
                    if len(same) > 0: ra += 1
                rows.append({
                    'เดือน': ml,
                    'จำหน่ายทั้งหมด': tot,
                    'เสียชีวิต': int(dead),
                    'อัตราเสียชีวิต (%)': round(dead/tot*100, 1) if tot else 0,
                    'Improve': int(imp),
                    'Readmit ≤28 วัน': ra,
                    'อัตรา Readmit (%)': round(ra/tot*100, 1) if tot else 0,
                    'On Ventilator': int(vn),
                })
            df_stat = pd.DataFrame(rows)
            df_stat.index = range(1, len(df_stat)+1)
            st.dataframe(df_stat, use_container_width=True)
            csv = df_stat.to_csv(encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 ดาวน์โหลด CSV", csv,
                               f"pneumonia_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                               "text/csv", key='dl_pn')

            st.markdown("---")
            # ── charts ──
            import altair as alt
            months_order = df_stat['เดือน'].tolist()

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("#### จำนวนจำหน่าย vs เสียชีวิต")
                melt1 = df_stat[['เดือน','จำหน่ายทั้งหมด','เสียชีวิต']].melt(
                    id_vars='เดือน', var_name='ประเภท', value_name='จำนวน')
                ch_p1 = alt.Chart(melt1).mark_bar().encode(
                    x=alt.X('เดือน:N', sort=months_order),
                    y='จำนวน:Q',
                    color=alt.Color('ประเภท:N', scale=alt.Scale(
                        domain=['จำหน่ายทั้งหมด','เสียชีวิต'],
                        range=['#1976D2','#E53935'])),
                    xOffset='ประเภท:N',
                    tooltip=['เดือน','ประเภท','จำนวน']
                ).properties(height=280)
                st.altair_chart(ch_p1, use_container_width=True)

            with col_p2:
                st.markdown("#### อัตราเสียชีวิต & Readmit (%)")
                melt2 = df_stat[['เดือน','อัตราเสียชีวิต (%)','อัตรา Readmit (%)']].melt(
                    id_vars='เดือน', var_name='ตัวชี้วัด', value_name='%')
                ch_p2 = alt.Chart(melt2).mark_line(point=True, strokeWidth=2).encode(
                    x=alt.X('เดือน:N', sort=months_order),
                    y=alt.Y('%:Q', title='%'),
                    color=alt.Color('ตัวชี้วัด:N'),
                    tooltip=['เดือน','ตัวชี้วัด','%']
                ).properties(height=280)
                st.altair_chart(ch_p2, use_container_width=True)

            # ── รายละเอียดผู้ป่วย ──
            st.markdown("---")
            with st.expander("📋 รายการผู้ป่วยปอดบวมทั้งหมด", expanded=False):
                det_cols = ['hn','an','age','sex','pdx','admit_date','discharge_date',
                            'discharge_status','ward_name','length_of_stay','adjrw','month_year']
                av = [c for c in det_cols if c in df_pn.columns]
                st.dataframe(df_pn[av], use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════
    # TAB 3 : VAP
    # ════════════════════════════════════════════════════
    with tab3:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#37474F,#546E7A);
                    padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.2rem;">
            <h2 style="color:white;margin:0;font-size:1.5rem;">
                💨 VAP Analysis
            </h2>
            <p style="color:#CFD8DC;margin:.3rem 0 0;font-size:.9rem;">
                Ventilator-Associated Pneumonia | J95.851 / ปอดบวม + op 96.71/96.72
            </p>
        </div>
        """, unsafe_allow_html=True)

        # หา VAP โดยตรง (J95.851)
        all_dx = ['pdx'] + [f'dx{i}' for i in range(11)]
        vap_code_mask = pd.Series([False]*len(df_all), index=df_all.index)
        for col in all_dx:
            if col in df_all.columns:
                vap_code_mask |= df_all[col].astype(str).str.startswith('J95.85')
        df_vap_coded = df_all[vap_code_mask].copy()

        # ปอดบวม + ventilator
        df_pn_vent = df_pneumonia[df_pneumonia['on_vent']].copy()

        # all ventilator cases
        df_all['on_vent'] = df_all.apply(has_ventilator, axis=1)
        df_vent_all = df_all[df_all['on_vent']].copy()

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("🔴 J95.851 (VAP code)",    f"{len(df_vap_coded)} ราย",
                  "⚠️ ควรตรวจสอบ" if len(df_vap_coded)==0 else "")
        k2.metric("💨 ใช้ Ventilator ทั้งหมด", f"{len(df_vent_all)} ราย")
        k3.metric("🫁 ปอดบวม + Ventilator",    f"{len(df_pn_vent)} ราย")
        k4.metric("💀 เสียชีวิตใน ปอดบวม+Vent",
                  str(df_pn_vent['discharge_status'].str.contains('ตาย',na=False).sum()) + " ราย")

        st.markdown("---")

        # ── VAP coded ──
        st.markdown("#### 🔴 ผู้ป่วยที่ code J95.851 (VAP โดยตรง)")
        if df_vap_coded.empty:
            st.info("""
            ℹ️ **ไม่พบรหัส J95.851** ในข้อมูล

            **ความเป็นไปได้:**
            - ยังไม่มีผู้ป่วย VAP ในช่วงนี้ ✅
            - มีผู้ป่วย VAP แต่ยังไม่ได้ลง code → ควรแจ้ง **ทีม Coder** และ **IC**

            **เกณฑ์การวินิจฉัย VAP:**
            ใส่ท่อช่วยหายใจ > 48 ชั่วโมง แล้วเกิดปอดบวมใหม่
            """)
        else:
            vc = [c for c in ['hn','an','age','pdx','ward_name',
                               'length_of_stay','discharge_status'] if c in df_vap_coded.columns]
            st.dataframe(df_vap_coded[vc], use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── ปอดบวม + ventilator ──
        st.markdown("#### 🫁 ผู้ป่วยปอดบวม + ใช้ Ventilator (Possible VAP)")
        st.caption("⚠️ ไม่ใช่ VAP ทุกราย — ต้องประเมินทางคลินิกเพิ่มเติม (ลำดับเวลา admit vs ventilator)")

        if df_pn_vent.empty:
            st.info("ไม่พบผู้ป่วยในกลุ่มนี้")
        else:
            vc2 = [c for c in ['hn','an','age','sex','pdx','admit_date','discharge_date',
                                'ward_name','length_of_stay','discharge_status','vent_codes']
                   if c in df_pn_vent.columns]
            df_pn_vent_show = df_pn_vent[vc2].copy()
            df_pn_vent_show.index = range(1, len(df_pn_vent_show)+1)
            st.dataframe(df_pn_vent_show, use_container_width=True)

        st.markdown("---")

        # ── Ventilator ทุก ward ──
        st.markdown("#### 💨 การกระจาย Ventilator ตาม Ward")
        if not df_vent_all.empty and 'ward_name' in df_vent_all.columns:
            import altair as alt
            ward_vent = (df_vent_all['ward_name'].value_counts()
                         .reset_index().rename(columns={'ward_name':'Ward','count':'จำนวน'}))
            ch_v = alt.Chart(ward_vent).mark_bar(color='#546E7A').encode(
                x=alt.X('จำนวน:Q'),
                y=alt.Y('Ward:N', sort='-x'),
                tooltip=['Ward','จำนวน']
            ).properties(height=300)
            st.altair_chart(ch_v, use_container_width=True)

        # ── คำแนะนำ ──
        st.markdown("---")
        st.markdown("""
        #### 📌 คำแนะนำ
        | ขั้นตอน | ผู้รับผิดชอบ |
        |---------|------------|
        | ตรวจสอบผู้ป่วย ICU ที่ใส่ ventilator > 48 ชม. | ทีม IC + แพทย์เจ้าของไข้ |
        | Cross-check กับสมุดบันทึก VAP ของ IC | ทีม IC |
        | ลง code J95.851 ถ้าวินิจฉัย VAP | ทีม Coder |
        | ติดตาม VAP rate รายเดือน | งานพัฒนาคุณภาพ |
        """)

    # ════════════════════════════════════════════════════
    # TAB 4 : เชิงลึก
    # ════════════════════════════════════════════════════
    with tab4:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#4A148C,#6A1B9A);
                    padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.2rem;">
            <h2 style="color:white;margin:0;font-size:1.5rem;">
                🔬 วิเคราะห์เชิงลึก
            </h2>
            <p style="color:#E1BEE7;margin:.3rem 0 0;font-size:.9rem;">
                CMI · LOS Outlier · สิทธิ์ · แรงงานต่างด้าว · Top RW
            </p>
        </div>
        """, unsafe_allow_html=True)

        import altair as alt

        sub1, sub2, sub3, sub4 = st.tabs([
            "💰 adjRW / CMI", "🛏 LOS Outlier",
            "🪪 สิทธิ์การรักษา", "🌏 แรงงานต่างด้าว"
        ])

        # ── sub1: adjRW / CMI ──
        with sub1:
            st.markdown("#### 🏆 Top 10 โรค by Total adjRW")
            rw_grp = (df_all.groupby('pdx')['adjrw']
                      .agg(['sum','mean','count']).round(3)
                      .rename(columns={'sum':'Total RW','mean':'Mean RW','count':'จำนวนราย'})
                      .sort_values('Total RW', ascending=False).head(10).reset_index())
            st.dataframe(rw_grp, use_container_width=True, hide_index=True)

            ch_rw = alt.Chart(rw_grp).mark_bar(color='#7B1FA2').encode(
                x=alt.X('Total RW:Q'),
                y=alt.Y('pdx:N', sort='-x', title='ICD-10'),
                tooltip=['pdx','Total RW','Mean RW','จำนวนราย']
            ).properties(height=320)
            st.altair_chart(ch_rw, use_container_width=True)

            st.markdown("---")
            st.markdown("#### 📈 CMI รายเดือน")
            cmi_m = (df_all.groupby('month_label')['adjrw']
                     .mean().reset_index(name='CMI').round(3))
            ch_cmi = alt.Chart(cmi_m).mark_area(
                line={'color':'#7B1FA2'}, color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='#CE93D8', offset=0),
                           alt.GradientStop(color='white', offset=1)],
                    x1=1, x2=1, y1=1, y2=0)
            ).encode(
                x=alt.X('month_label:N', title='เดือน'),
                y=alt.Y('CMI:Q', scale=alt.Scale(zero=False)),
                tooltip=['month_label','CMI']
            ).properties(height=250)
            st.altair_chart(ch_cmi, use_container_width=True)

        # ── sub2: LOS Outlier ──
        with sub2:
            threshold = st.slider("กำหนด LOS threshold (วัน)", 7, 60, 30)
            df_long = df_all[df_all['length_of_stay'] > threshold].copy()
            st.metric(f"ผู้ป่วย LOS > {threshold} วัน",
                      f"{len(df_long)} ราย",
                      f"{len(df_long)/len(df_all)*100:.1f}% ของทั้งหมด")

            if not df_long.empty:
                lc = [c for c in ['hn','an','age','pdx','ward_name',
                                   'length_of_stay','discharge_status','adjrw']
                      if c in df_long.columns]
                st.dataframe(
                    df_long[lc].sort_values('length_of_stay', ascending=False),
                    use_container_width=True, hide_index=True
                )

                # histogram
                hist_df = df_all[['length_of_stay']].dropna()
                ch_h = alt.Chart(hist_df).mark_bar(color='#E65100').encode(
                    x=alt.X('length_of_stay:Q', bin=alt.Bin(maxbins=30), title='LOS (วัน)'),
                    y=alt.Y('count()', title='จำนวนราย'),
                    tooltip=['count()']
                ).properties(height=250, title='Distribution ของ LOS ทั้งหมด')
                st.altair_chart(ch_h, use_container_width=True)

        # ── sub3: สิทธิ์ ──
        with sub3:
            st.markdown("#### 🪪 สิทธิ์การรักษา")
            pt_col = 'pttype_name' if 'pttype_name' in df_all.columns else None
            if pt_col:
                pt_df = (df_all[pt_col].value_counts()
                         .reset_index().rename(columns={pt_col:'สิทธิ์','count':'จำนวน'}))
                st.dataframe(pt_df, use_container_width=True, hide_index=True)

                ch_pt = alt.Chart(pt_df.head(12)).mark_bar(color='#0277BD').encode(
                    x=alt.X('จำนวน:Q'),
                    y=alt.Y('สิทธิ์:N', sort='-x'),
                    tooltip=['สิทธิ์','จำนวน']
                ).properties(height=380)
                st.altair_chart(ch_pt, use_container_width=True)
            else:
                st.info("ไม่พบคอลัมน์ pttype_name ในข้อมูล")

        # ── sub4: แรงงานต่างด้าว ──
        with sub4:
            st.markdown("#### 🌏 แรงงานต่างด้าว")
            pt_col = 'pttype_name' if 'pttype_name' in df_all.columns else None
            if pt_col:
                df_foreign = df_all[df_all[pt_col].str.contains('ต่างด้าว', na=False)].copy()
                f1, f2, f3 = st.columns(3)
                f1.metric("👥 จำนวน",    f"{len(df_foreign):,} ราย")
                f2.metric("💰 adjRW รวม", f"{df_foreign['adjrw'].sum():.1f}")
                f3.metric("🛏 LOS เฉลี่ย", f"{df_foreign['length_of_stay'].mean():.1f} วัน")

                st.markdown("---")
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    st.markdown("**Top 10 โรค**")
                    fdx = (df_foreign['pdx'].value_counts().head(10)
                           .reset_index().rename(columns={'pdx':'รหัส','count':'จำนวน'}))
                    ch_fd = alt.Chart(fdx).mark_bar(color='#00838F').encode(
                        x=alt.X('จำนวน:Q'),
                        y=alt.Y('รหัส:N', sort='-x'),
                        tooltip=['รหัส','จำนวน']
                    ).properties(height=300)
                    st.altair_chart(ch_fd, use_container_width=True)

                with col_f2:
                    st.markdown("**สถานะการจำหน่าย**")
                    fst = (df_foreign['discharge_status'].value_counts()
                           .reset_index().rename(columns={'discharge_status':'สถานะ','count':'จำนวน'}))
                    ch_fs = alt.Chart(fst).mark_arc(innerRadius=45).encode(
                        theta='จำนวน:Q',
                        color=alt.Color('สถานะ:N'),
                        tooltip=['สถานะ','จำนวน']
                    ).properties(height=300)
                    st.altair_chart(ch_fs, use_container_width=True)
            else:
                st.info("ไม่พบคอลัมน์ pttype_name ในข้อมูล")

    st.markdown("---")
    st.caption(f"🕐 อัปเดตล่าสุด: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")


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
    
    # ============================================
    # แสดงข้อมูลที่มีในระบบ
    # ============================================
    st.markdown("### 📊 ข้อมูลที่มีในระบบ")
    
    try:
        client = init_supabase()
        
        # ดึงข้อมูล month_year ที่ไม่ซ้ำพร้อมสถิติ
        with st.spinner("กำลังโหลดข้อมูลในระบบ..."):
            result = client.select('ipd_monthly', columns='month_year,fiscal_year,an,created_at')
        
        if result['error']:
            st.error(f"❌ เกิดข้อผิดพลาด: {result['error']}")
            st.info("💡 ลองไปที่เมนู '🔧 ทดสอบการเชื่อมต่อ' เพื่อตรวจสอบปัญหา")
            st.session_state['existing_months'] = []
        
        elif result['data'] and len(result['data']) > 0:
            df_existing = pd.DataFrame(result['data'])
            df_existing['month_year'] = pd.to_datetime(df_existing['month_year'], errors='coerce')
            df_existing['created_at'] = pd.to_datetime(df_existing['created_at'], errors='coerce')
            
            # สรุปข้อมูลรายเดือน
            summary = df_existing.groupby('month_year').agg({
                'an': 'count',
                'created_at': 'max'
            }).reset_index()
            
            summary.columns = ['เดือน-ปี', 'จำนวนรายการ', 'นำเข้าล่าสุด']
            summary['เดือน-ปี_sort'] = summary['เดือน-ปี']  # เก็บไว้สำหรับ sort
            summary['เดือน-ปี'] = summary['เดือน-ปี'].dt.strftime('%B %Y')
            summary['นำเข้าล่าสุด'] = summary['นำเข้าล่าสุด'].dt.strftime('%d/%m/%Y %H:%M')
            summary = summary.sort_values('เดือน-ปี_sort', ascending=False)
            summary = summary.drop('เดือน-ปี_sort', axis=1)
            summary.index = range(1, len(summary) + 1)
            
            # แสดงข้อมูลสถิติและตาราง
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                st.metric("📅 จำนวนเดือนที่มีข้อมูล", f"{len(summary)} เดือน")
            
            with col_stat2:
                st.metric("📋 รายการทั้งหมด", f"{len(df_existing):,} ราย")
            
            with col_stat3:
                latest_month = df_existing['month_year'].max()
                if pd.notna(latest_month):
                    st.metric("🗓️ เดือนล่าสุด", latest_month.strftime('%B %Y'))
            
            # แสดงตาราง
            with st.expander("📋 รายละเอียดข้อมูลแต่ละเดือน", expanded=True):
                st.dataframe(
                    summary,
                    use_container_width=True,
                    column_config={
                        "เดือน-ปี": st.column_config.TextColumn("เดือน-ปี", width="medium"),
                        "จำนวนรายการ": st.column_config.NumberColumn(
                            "จำนวนรายการ", 
                            format="%d ราย",
                            help="จำนวนรายการทั้งหมดในเดือนนี้"
                        ),
                        "นำเข้าล่าสุด": st.column_config.TextColumn(
                            "นำเข้าล่าสุด", 
                            width="medium",
                            help="วันเวลาที่นำเข้าข้อมูลล่าสุด"
                        ),
                    }
                )
                
                # แสดงรายการเดือนที่มี (สำหรับเช็คซ้ำ)
                existing_months = df_existing['month_year'].dt.strftime('%Y-%m-01').unique().tolist()
                st.info(f"💡 **เดือนที่มีข้อมูลแล้ว:** {len(existing_months)} เดือน")
                
                # เก็บไว้ใน session state เพื่อใช้ตรวจสอบข้อมูลซ้ำ
                st.session_state['existing_months'] = existing_months
        
        else:
            st.info("📭 ยังไม่มีข้อมูลในระบบ - เริ่มนำเข้าข้อมูลได้เลย")
            st.session_state['existing_months'] = []
    
    except Exception as e:
        st.warning(f"⚠️ ไม่สามารถโหลดข้อมูลในระบบได้: {str(e)}")
        st.session_state['existing_months'] = []
    
    st.markdown("---")
    
    # ============================================
    # File Uploader
    # ============================================
    
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
                
                # ============================================
                # เตือนถ้าข้อมูลเดือนนี้มีแล้ว
                # ============================================
                existing_months = st.session_state.get('existing_months', [])
                if month_year in existing_months:
                    st.warning(f"""
                    ⚠️ **พบข้อมูลเดือนนี้ในระบบแล้ว!**
                    
                    เดือน **{month_year_display}** มีข้อมูลในระบบแล้ว  
                    การนำเข้าใหม่อาจทำให้เกิดข้อมูลซ้ำ (ขึ้นอยู่กับ AN)
                    
                    **ตัวเลือก:**
                    - ถ้า AN ซ้ำ → ระบบจะ **ไม่นำเข้า** (ป้องกันโดย unique constraint)
                    - ถ้า AN ใหม่ → ระบบจะ **เพิ่มเข้าไป**
                    """)
                else:
                    st.success(f"✅ เดือนนี้ยังไม่มีข้อมูลในระบบ - พร้อมนำเข้า")
                
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
