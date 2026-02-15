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


# เพิ่มใน CSS section (หลังบรรทัด 100)
st.markdown("""
    <style>
    /* ... CSS เดิม ... */
    
    /* ========================================
       ENTERPRISE DESIGN SYSTEM
       ======================================== */
    
    /* Professional Card Shadows */
    .stMetric {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #E0E0E0;
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        transform: translateY(-4px);
    }
    
    /* Executive Metric Values */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #1565C0 !important;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    
    /* Professional Data Tables */
    .stDataFrame {
        border: 1px solid #E0E0E0 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    .stDataFrame thead tr th {
        background: linear-gradient(135deg, #1565C0, #1976D2) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 1rem 0.8rem !important;
    }
    
    .stDataFrame tbody tr:nth-child(even) {
        background-color: #F5F9FC !important;
    }
    
    .stDataFrame tbody tr:hover {
        background-color: #E3F2FD !important;
        transition: background-color 0.2s;
    }
    
    /* Alert Boxes */
    .alert-success {
        background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
        border-left: 4px solid #FF9800;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-danger {
        background: linear-gradient(135deg, #FFEBEE, #FFCDD2);
        border-left: 4px solid #F44336;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Professional Charts */
    .vega-embed {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    }
    
    /* Tab Navigation */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        padding: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        border-radius: 8px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1565C0, #1976D2);
        color: white !important;
    }
    
    /* Sidebar Enhancement */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D47A1 0%, #1565C0 30%, #1B5E20 100%) !important;
    }
    
    [data-testid="stSidebar"] .stRadio label {
        color: white !important;
        font-weight: 500 !important;
        padding: 0.8rem 1rem !important;
        border-radius: 8px !important;
        transition: all 0.3s !important;
    }
    
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.1) !important;
        transform: translateX(4px) !important;
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-color: #1565C0 transparent transparent transparent !important;
    }
    
    /* Expander Enhancement */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #E3F2FD, #BBDEFB) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 1rem !important;
    }
    
    .streamlit-expanderContent {
        border: 1px solid #BBDEFB !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1.5rem !important;
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
            
            # 200, 201, 206 ถือว่าสำเร็จ
            if response.status_code in [200, 201, 206]:
                return {"data": response.json(), "error": None}
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('message', error_detail)
                    
                    # ถ้าเป็น Foreign Key error ให้อธิบายชัดเจน
                    if 'foreign key' in error_detail.lower() or 'fkey' in error_detail.lower():
                        error_detail = f"⚠️ Foreign Key Error: รหัสโรค (ICD-10) ไม่มีในฐานข้อมูล icd10_master\n{error_detail}"
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
                
                # Supabase ส่ง 206 (Partial Content) เมื่อมี pagination - นี่เป็นเรื่องปกติ
                if response.status_code not in [200, 206]:
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
    
    # ========================================
    # ⚠️ สำคัญ: จัดการ Foreign Key Constraints
    # ========================================
    # ICD-10 codes ต้องมีอยู่ใน icd10_master table
    # ถ้าไม่มี จะเกิด Foreign Key constraint error
    # วิธีแก้: ตั้งเป็น NULL ถ้า code ไม่ถูกต้อง (ไม่ใช่รูปแบบ ICD-10)
    
    icd_columns = ['pdx'] + [f'dx{i}' for i in range(11)]
    op_columns = [f'op{i}' for i in range(12)]
    
    # ทำความสะอาด ICD-10 codes
    invalid_icd_count = 0
    for col in icd_columns:
        if col in df_clean.columns:
            # แปลงเป็น string และ clean
            df_clean[col] = df_clean[col].apply(lambda x: str(x).strip().upper() if pd.notna(x) and str(x).strip() not in ['', 'nan', 'None', 'NaN'] else None)
            
            # นับ code ที่ไม่ valid (เพื่อแจ้งเตือน)
            before_count = df_clean[col].notna().sum()
            
            # ถ้า code มีความยาวผิดปกติมาก (>10 ตัวอักษร) ให้ตั้งเป็น NULL
            # เพราะ schema กำหนดไว้ varchar(10)
            df_clean.loc[df_clean[col].str.len() > 10, col] = None
            
            after_count = df_clean[col].notna().sum()
            if before_count > after_count:
                invalid_icd_count += (before_count - after_count)
    
    if invalid_icd_count > 0:
        warnings.append(f"⚠️ พบรหัส ICD-10 ที่ไม่ถูกต้อง {invalid_icd_count} รายการ (ตั้งเป็น NULL)")
        warnings.append("💡 หมายเหตุ: ถ้ารหัสถูกต้องแต่ยังไม่มีใน icd10_master table ต้องเพิ่มเข้าไปก่อน")
    
    # ทำความสะอาด OP codes
    invalid_op_count = 0
    for col in op_columns:
        if col in df_clean.columns:
            before_count = df_clean[col].notna().sum()
            
            df_clean[col] = df_clean[col].apply(lambda x: str(x).strip() if pd.notna(x) and str(x).strip() not in ['', 'nan', 'None', 'NaN'] else None)
            
            # ตัด length ถ้ายาวเกิน 10
            df_clean.loc[df_clean[col].str.len() > 10, col] = None
            
            after_count = df_clean[col].notna().sum()
            if before_count > after_count:
                invalid_op_count += (before_count - after_count)
    
    if invalid_op_count > 0:
        warnings.append(f"⚠️ พบรหัส OP ที่ไม่ถูกต้อง {invalid_op_count} รายการ (ตั้งเป็น NULL)")
    
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

def show_troubleshooting():
    """หน้าแก้ไขปัญหา"""
    st.markdown("## 🩹 แก้ไขปัญหาที่พบบ่อย")
    
    st.info("""
    หน้านี้รวบรวมวิธีแก้ไขปัญหาที่พบบ่อยในการใช้งานระบบ
    """)
    
    # ปัญหาที่ 1: Foreign Key Constraints
    with st.expander("❌ **ปัญหา: Foreign Key Constraint Error (รหัส ICD-10 ไม่มีในฐานข้อมูล)**", expanded=True):
        st.markdown("""
        ### 🔴 อาการ:
        - นำเข้าข้อมูลแล้วขึ้น error: `foreign key constraint` หรือ `violates foreign key constraint "ipd_monthly_pdx_fkey"`
        - ข้อมูลไม่เข้าฐานข้อมูล
        
        ### 💡 สาเหตุ:
        Table `ipd_monthly` มี Foreign Key Constraints กับ table `icd10_master` สำหรับคอลัมน์:
        - `pdx` (Principal Diagnosis)
        - `dx0` - `dx10` (Secondary Diagnoses)
        
        **หมายความว่า:** รหัส ICD-10 ทุกตัวที่ใส่ลงไปต้อง**มีอยู่แล้ว**ใน table `icd10_master`
        
        ### ✅ วิธีแก้:
        
        **ตัวเลือกที่ 1: ลบ Foreign Key Constraints (แนะนำ)**
        
        รัน SQL นี้ใน Supabase SQL Editor:
        
        ```sql
        -- ลบ Foreign Key Constraints ทั้งหมด
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_pdx_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx0_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx1_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx2_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx3_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx4_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx5_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx6_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx7_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx8_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx9_fkey;
        ALTER TABLE ipd_monthly DROP CONSTRAINT IF EXISTS ipd_monthly_dx10_fkey;
        ```
        
        **ตัวเลือกที่ 2: เพิ่มรหัส ICD-10 เข้า table icd10_master**
        
        ถ้าต้องการเก็บ Foreign Key Constraints ไว้ (เพื่อ data integrity):
        
        1. Export รหัส ICD-10 ที่ใช้จากไฟล์ของคุณ
        2. Import เข้า table `icd10_master` ก่อน
        3. แล้วค่อย import ข้อมูล IPD
        
        **ตัวเลือกที่ 3: ให้ระบบจัดการให้อัตโนมัติ**
        
        ระบบปัจจุบันจะตั้งค่า ICD-10 codes ที่ไม่ถูกต้องเป็น NULL โดยอัตโนมัติ
        แต่ข้อมูลอาจสูญหายบางส่วน
        """)
    
    # ปัญหาที่ 2: วันที่ผิดรูปแบบ
    with st.expander("📅 **ปัญหา: วันที่แสดงผลผิด (ปี พ.ศ. vs ค.ศ.)**"):
        st.markdown("""
        ### 🔴 อาการ:
        - วันที่ admit/discharge แสดงเป็นปี 2568 (พ.ศ.) แทนที่จะเป็น 2025 (ค.ศ.)
        - กราฟแสดงผลผิดพลาด
        
        ### 💡 สาเหตุ:
        - ข้อมูลใน Excel เป็นปี พ.ศ. แต่ระบบคาดหวังปี ค.ศ.
        - ไม่มีการแปลง พ.ศ. → ค.ศ.
        
        ### ✅ วิธีแก้:
        
        **ใน Excel ก่อน import:**
        ```
        = วันที่เดิม - 543 ปี
        เช่น: 01/01/2568 → 01/01/2025
        ```
        
        **หรือแก้โค้ดในส่วน validate_and_prepare_data() เพิ่ม:**
        ```python
        # แปลง พ.ศ. เป็น ค.ศ.
        if col in ['admit_date', 'discharge_date']:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
            # ลบ 543 ปีถ้าปีมากกว่า 2500
            df_clean[col] = df_clean[col].apply(
                lambda x: x.replace(year=x.year-543) if pd.notna(x) and x.year > 2500 else x
            )
        ```
        """)
    
    # ปัญหาที่ 3: อ่านข้อมูลไม่ได้
    with st.expander("📭 **ปัญหา: แสดง 'ไม่พบข้อมูลในระบบ' แต่มีข้อมูลอยู่**"):
        st.markdown("""
        ### 🔴 อาการ:
        - ไปหน้า "รายงาน" แล้วแสดงว่า "ไม่พบข้อมูล"
        - แต่เช็คใน Supabase เห็นข้อมูลอยู่
        
        ### 💡 สาเหตุ:
        - RLS (Row Level Security) ยังเปิดอยู่
        - API Key ไม่มีสิทธิ์อ่านข้อมูล
        
        ### ✅ วิธีแก้:
        
        **1. ปิด RLS ใน Supabase:**
        
        ```sql
        ALTER TABLE ipd_monthly DISABLE ROW LEVEL SECURITY;
        ```
        
        **2. หรือสร้าง Policy ที่อนุญาตให้ anon role อ่านได้:**
        
        ```sql
        CREATE POLICY "Allow public read access"
        ON ipd_monthly
        FOR SELECT
        TO anon
        USING (true);
        ```
        
        **3. ตรวจสอบว่า RLS ปิดแล้ว:**
        
        ไปที่หน้า "🔧 ทดสอบการเชื่อมต่อ" → กด "📥 ดึงข้อมูลตัวอย่าง"
        """)
    
    # ปัญหาที่ 4: ไฟล์ Excel อ่านไม่ได้
    with st.expander("📄 **ปัญหา: อัปโหลดไฟล์ Excel แล้ว error**"):
        st.markdown("""
        ### 🔴 อาการ:
        - อัปโหลด .xlsx/.xls แล้วขึ้น error "ไม่สามารถอ่านไฟล์ได้"
        - error: `Missing optional dependency 'openpyxl'`
        
        ### 💡 สาเหตุ:
        - ไม่มี library สำหรับอ่าน Excel (openpyxl, xlrd)
        - ไฟล์ Excel เสียหาย
        
        ### ✅ วิธีแก้:
        
        **แนะนำ: แปลงเป็น CSV**
        
        1. เปิดไฟล์ใน Excel
        2. File → Save As
        3. เลือก **CSV UTF-8 (Comma delimited) (*.csv)**
        4. Save
        5. อัปโหลดไฟล์ .csv แทน
        
        **หรือติดตั้ง library:**
        ```bash
        pip install openpyxl xlrd
        ```
        """)
    
    st.markdown("---")
    st.info("💡 **หากยังมีปัญหา** ลองไปที่เมนู '🔧 ทดสอบการเชื่อมต่อ' เพื่อตรวจสอบขั้นตอนการทำงาน")



# ========================================
# PROFESSIONAL CHART UTILITIES
# ========================================

def create_professional_chart(data, chart_type, **kwargs):
    """
    สร้าง Chart แบบ Professional สำหรับ Hospital BI
    
    Args:
        data: DataFrame
        chart_type: 'line', 'bar', 'area', 'combo'
        **kwargs: configuration options
    """
    import altair as alt
    
    # Color Scheme สำหรับ Hospital
    HOSPITAL_COLORS = {
        'primary': '#1565C0',
        'secondary': '#2E7D32',
        'accent': '#F57C00',
        'danger': '#D32F2F',
        'warning': '#FFA000',
        'success': '#388E3C',
        'neutral': '#546E7A'
    }
    
    # Base configuration
    base_config = {
        'view': {'strokeWidth': 0},
        'axis': {
            'labelFontSize': 11,
            'titleFontSize': 12,
            'labelFont': '"SF Pro Display", -apple-system, sans-serif',
            'titleFont': '"SF Pro Display", -apple-system, sans-serif',
            'titleFontWeight': 600,
            'titleColor': '#37474F',
            'labelColor': '#546E7A',
            'gridColor': '#ECEFF1',
            'domainColor': '#CFD8DC'
        },
        'legend': {
            'labelFontSize': 11,
            'titleFontSize': 12,
            'labelFont': '"SF Pro Display", sans-serif',
            'titleFont': '"SF Pro Display", sans-serif',
            'titleFontWeight': 600,
            'orient': 'top',
            'padding': 10
        },
        'title': {
            'fontSize': 16,
            'fontWeight': 700,
            'font': '"SF Pro Display", sans-serif',
            'color': '#1565C0',
            'anchor': 'start',
            'offset': 20
        }
    }
    
    if chart_type == 'line':
        chart = alt.Chart(data).mark_line(
            strokeWidth=3,
            point=alt.OverlayMarkDef(
                filled=True,
                size=80,
                color=kwargs.get('color', HOSPITAL_COLORS['primary'])
            )
        ).encode(
            x=alt.X(kwargs['x'], title=kwargs.get('x_title', '')),
            y=alt.Y(kwargs['y'], title=kwargs.get('y_title', ''), 
                   scale=alt.Scale(zero=False)),
            tooltip=kwargs.get('tooltip', []),
            color=alt.value(kwargs.get('color', HOSPITAL_COLORS['primary']))
        ).properties(
            height=kwargs.get('height', 300),
            title=kwargs.get('title', '')
        ).configure(**base_config)
        
    elif chart_type == 'area':
        chart = alt.Chart(data).mark_area(
            line={'color': kwargs.get('color', HOSPITAL_COLORS['primary']), 
                  'strokeWidth': 3},
            color=alt.Gradient(
                gradient='linear',
                stops=[
                    alt.GradientStop(color='white', offset=0),
                    alt.GradientStop(color=kwargs.get('color', HOSPITAL_COLORS['primary']), 
                                   offset=1)
                ],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X(kwargs['x'], title=kwargs.get('x_title', '')),
            y=alt.Y(kwargs['y'], title=kwargs.get('y_title', '')),
            tooltip=kwargs.get('tooltip', [])
        ).properties(
            height=kwargs.get('height', 300),
            title=kwargs.get('title', '')
        ).configure(**base_config)
        
    elif chart_type == 'bar':
        chart = alt.Chart(data).mark_bar(
            cornerRadiusTopLeft=4,
            cornerRadiusTopRight=4
        ).encode(
            x=alt.X(kwargs['x'], title=kwargs.get('x_title', '')),
            y=alt.Y(kwargs['y'], title=kwargs.get('y_title', '')),
            color=alt.value(kwargs.get('color', HOSPITAL_COLORS['primary'])),
            tooltip=kwargs.get('tooltip', [])
        ).properties(
            height=kwargs.get('height', 300),
            title=kwargs.get('title', '')
        ).configure(**base_config)
    
    return chart


def create_kpi_card(title, value, delta=None, icon="📊", color="#1565C0"):
    """
    สร้าง KPI Card แบบ Professional
    """
    delta_html = ""
    if delta is not None:
        delta_color = "#4CAF50" if delta >= 0 else "#F44336"
        delta_icon = "▲" if delta >= 0 else "▼"
        delta_html = f"""
            <div style="color:{delta_color};font-size:0.9rem;font-weight:600;margin-top:0.5rem;">
                {delta_icon} {abs(delta):+.2f}%
            </div>
        """
    
    return f"""
        <div style="background:white;padding:1.5rem;border-radius:12px;
                    box-shadow:0 4px 12px rgba(0,0,0,0.08);
                    border-left:4px solid {color};min-height:140px;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">{icon}</div>
            <div style="color:#546E7A;font-size:0.85rem;font-weight:500;
                        text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.5rem;">
                {title}
            </div>
            <div style="color:{color};font-size:2rem;font-weight:700;">
                {value}
            </div>
            {delta_html}
        </div>
    """
 
# ============================================
# MAIN APP
# ============================================




def main():
    # Header (เดิม)
    st.markdown("""
        <div class="main-header">
            <h1>🏥 ระบบรายงานข้อมูล Sansai-CMI</h1>
            <p>โรงพยาบาลสันทราย | Case Mix Information System</p>
        </div>
    """, unsafe_allow_html=True)
    
    # ========================================
    # ENHANCED SIDEBAR NAVIGATION
    # ========================================
    with st.sidebar:
        # Logo & Title
        st.markdown("""
            <div style="text-align:center;padding:1.5rem 0;border-bottom:2px solid rgba(255,255,255,0.2);">
                <div style="font-size:3rem;margin-bottom:0.5rem;">🏥</div>
                <h2 style="color:white;margin:0;font-size:1.3rem;font-weight:700;">
                    Sansai Hospital
                </h2>
                <p style="color:#B3E5FC;font-size:0.85rem;margin:0.3rem 0 0;">
                    Case Mix Intelligence
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Navigation Menu
        st.markdown("""
            <div style="color:white;font-weight:600;font-size:0.9rem;
                        margin:1rem 0 0.5rem 0.5rem;letter-spacing:0.5px;">
                📋 NAVIGATION
            </div>
        """, unsafe_allow_html=True)
        
        menu_options = {
            "🏠 หน้าแรก": "Executive Dashboard & Real-time KPIs",
            "📊 รายงาน": "Comprehensive Analytics & Reports",
            "📥 นำเข้าข้อมูล": "Data Import & Validation",
            "🔧 ทดสอบการเชื่อมต่อ": "System Health Check",
            "🩹 แก้ไขปัญหา": "Troubleshooting Guide"
        }
        
        # Custom Radio with descriptions
        selected_menu = None
        for menu_key, menu_desc in menu_options.items():
            is_selected = st.session_state.get('selected_menu', '🏠 หน้าแรก') == menu_key
            
            button_style = """
                background: rgba(255,255,255,0.15);
                border-left: 4px solid #4CAF50;
            """ if is_selected else ""
            
            if st.button(
                menu_key,
                key=f"nav_{menu_key}",
                use_container_width=True,
                help=menu_desc
            ):
                st.session_state['selected_menu'] = menu_key
                selected_menu = menu_key
        
        menu = selected_menu or st.session_state.get('selected_menu', '🏠 หน้าแรก')
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # System Info Section
        st.markdown("""
            <div style="border-top:2px solid rgba(255,255,255,0.2);
                        padding-top:1.5rem;margin-top:2rem;">
                <div style="color:#B3E5FC;font-weight:600;font-size:0.9rem;
                            margin-bottom:1rem;letter-spacing:0.5px;">
                    ℹ️ SYSTEM INFO
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Info cards
        current_date = datetime.now()
        st.markdown(f"""
            <div style="background:rgba(255,255,255,0.1);padding:0.8rem;
                        border-radius:8px;margin-bottom:0.5rem;">
                <div style="color:#B3E5FC;font-size:0.75rem;margin-bottom:0.2rem;">
                    📅 CURRENT DATE
                </div>
                <div style="color:white;font-weight:600;font-size:0.9rem;">
                    {current_date.strftime('%d %B %Y')}
                </div>
            </div>
            
            <div style="background:rgba(255,255,255,0.1);padding:0.8rem;
                        border-radius:8px;margin-bottom:0.5rem;">
                <div style="color:#B3E5FC;font-size:0.75rem;margin-bottom:0.2rem;">
                    🔄 VERSION
                </div>
                <div style="color:white;font-weight:600;font-size:0.9rem;">
                    v2.0.0 (Enterprise)
                </div>
            </div>
            
            <div style="background:rgba(76,175,80,0.2);padding:0.8rem;
                        border-radius:8px;border:1px solid rgba(76,175,80,0.4);">
                <div style="color:#C8E6C9;font-size:0.75rem;margin-bottom:0.2rem;">
                    ✅ STATUS
                </div>
                <div style="color:#4CAF50;font-weight:600;font-size:0.9rem;">
                    System Online
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # ========================================
    # ROUTE TO PAGES
    # ========================================
    if menu == "🏠 หน้าแรก":
        show_home()
    elif menu == "📊 รายงาน":
        show_reports()
    elif menu == "📥 นำเข้าข้อมูล":
        show_import()
    elif menu == "🔧 ทดสอบการเชื่อมต่อ":
        show_connection_test()
    elif menu == "🩹 แก้ไขปัญหา":
        show_troubleshooting()
     
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
    """Executive Dashboard Homepage - Hospital Intelligence"""
    
    # ========================================
    # HERO SECTION - Executive Summary
    # ========================================
    st.markdown("""
        <div style="background:linear-gradient(135deg,#1565C0 0%,#0D47A1 50%,#1B5E20 100%);
                    padding:3rem 2rem;border-radius:16px;margin-bottom:2rem;
                    box-shadow:0 8px 32px rgba(0,0,0,0.12);">
            <h1 style="color:white;margin:0;font-size:2.8rem;font-weight:700;
                       text-shadow:2px 2px 4px rgba(0,0,0,0.2);">
                🏥 Sansai Hospital Intelligence Platform
            </h1>
            <p style="color:#E3F2FD;margin:1rem 0 0;font-size:1.2rem;font-weight:300;">
                Case Mix Information System · Real-time Analytics
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # ========================================
    # EXECUTIVE KPI DASHBOARD
    # ========================================
    try:
        client = init_supabase()
        
        # โหลดข้อมูล
        with st.spinner("⚡ Loading real-time data..."):
            result = client.select('ipd_monthly')
        
        if result['error'] or not result['data']:
            st.warning("⚠️ ไม่สามารถโหลดข้อมูลได้ กรุณาตรวจสอบการเชื่อมต่อ")
            return
        
        df_all = pd.DataFrame(result['data'])
        
        # แปลงประเภทข้อมูล
        df_all['month_year'] = pd.to_datetime(df_all['month_year'], errors='coerce')
        df_all['admit_date'] = pd.to_datetime(df_all['admit_date'], errors='coerce')
        df_all['discharge_date'] = pd.to_datetime(df_all['discharge_date'], errors='coerce')
        df_all['age'] = pd.to_numeric(df_all.get('age', pd.Series()), errors='coerce')
        df_all['adjrw'] = pd.to_numeric(df_all.get('adjrw', pd.Series()), errors='coerce')
        df_all['length_of_stay'] = pd.to_numeric(df_all.get('length_of_stay', pd.Series()), errors='coerce')
        
        # คำนวณเดือนปัจจุบันและเดือนก่อนหน้า
        latest_month = df_all['month_year'].max()
        prev_month = latest_month - pd.DateOffset(months=1)
        
        df_current = df_all[df_all['month_year'] == latest_month]
        df_previous = df_all[df_all['month_year'] == prev_month]
        
        # ========================================
        # SECTION 1: PRIMARY KPIs (ระดับ C-Level)
        # ========================================
        st.markdown("""
            <div style="background:white;padding:1.5rem;border-radius:12px;
                        box-shadow:0 4px 16px rgba(0,0,0,0.08);margin-bottom:2rem;">
                <h3 style="color:#1565C0;margin:0 0 1rem 0;font-size:1.4rem;font-weight:600;">
                    📊 Executive KPIs – Latest Month
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        # คำนวณ KPIs
        total_current = len(df_current)
        total_previous = len(df_previous)
        cmi_current = df_current['adjrw'].mean()
        cmi_previous = df_previous['adjrw'].mean()
        total_rw_current = df_current['adjrw'].sum()
        total_rw_previous = df_previous['adjrw'].sum()
        los_current = df_current['length_of_stay'].mean()
        los_previous = df_previous['length_of_stay'].mean()
        death_current = df_current['discharge_status'].str.contains('ตาย', na=False).sum()
        death_previous = df_previous['discharge_status'].str.contains('ตาย', na=False).sum()
        death_rate_current = (death_current / total_current * 100) if total_current else 0
        death_rate_previous = (death_previous / total_previous * 100) if total_previous else 0
        
        # แสดง KPI Cards แบบ Delta
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        
        with k1:
            delta_discharge = total_current - total_previous
            st.metric(
                "👥 Total Discharges",
                f"{total_current:,}",
                f"{delta_discharge:+,} vs prev month",
                delta_color="normal"
            )
        
        with k2:
            delta_cmi = cmi_current - cmi_previous
            st.metric(
                "📈 CMI (Case Mix Index)",
                f"{cmi_current:.3f}",
                f"{delta_cmi:+.3f}",
                delta_color="normal"
            )
        
        with k3:
            delta_rw = total_rw_current - total_rw_previous
            st.metric(
                "💰 Total Adjusted RW",
                f"{total_rw_current:,.1f}",
                f"{delta_rw:+,.1f}",
                delta_color="normal"
            )
        
        with k4:
            delta_los = los_current - los_previous
            st.metric(
                "🛏️ Average LOS",
                f"{los_current:.1f} days",
                f"{delta_los:+.1f}",
                delta_color="inverse"  # LOS ต่ำกว่าดีกว่า
            )
        
        with k5:
            delta_death_rate = death_rate_current - death_rate_previous
            st.metric(
                "💀 Mortality Rate",
                f"{death_rate_current:.2f}%",
                f"{delta_death_rate:+.2f}%",
                delta_color="inverse"
            )
        
        with k6:
            # คำนวณ Bed Turnover Rate (ประมาณการ)
            turnover_current = total_current / 30  # สมมติ 30 เตียง
            st.metric(
                "🔄 Bed Turnover",
                f"{turnover_current:.1f}/day",
                help="Average discharges per day"
            )
        
        st.markdown("---")
        
        # ========================================
        # SECTION 2: TREND ANALYSIS (6 Months)
        # ========================================
        st.markdown("""
            <div style="background:white;padding:1.5rem;border-radius:12px;
                        box-shadow:0 4px 16px rgba(0,0,0,0.08);margin-bottom:1.5rem;">
                <h3 style="color:#1565C0;margin:0 0 1rem 0;font-size:1.4rem;font-weight:600;">
                    📈 6-Month Trend Analysis
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        # เตรียมข้อมูล 6 เดือนล่าสุด
        last_6_months = df_all['month_year'].nlargest(6).unique()
        df_trend = df_all[df_all['month_year'].isin(last_6_months)].copy()
        df_trend['month_label'] = df_trend['month_year'].dt.strftime('%b %Y')
        
        # สร้าง summary รายเดือน
        monthly_summary = df_trend.groupby('month_label').agg({
            'an': 'count',
            'adjrw': ['mean', 'sum'],
            'length_of_stay': 'mean'
        }).reset_index()
        
        monthly_summary.columns = ['Month', 'Discharges', 'CMI', 'Total_RW', 'Avg_LOS']
        monthly_summary = monthly_summary.round(3)
        
        # แสดงกราฟ Trend
        import altair as alt
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            # CMI Trend with Area Chart
            chart_cmi = alt.Chart(monthly_summary).mark_area(
                line={'color': '#1565C0', 'strokeWidth': 3},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='#E3F2FD', offset=0),
                        alt.GradientStop(color='#1565C0', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X('Month:N', title='Month', sort=None),
                y=alt.Y('CMI:Q', title='Case Mix Index', scale=alt.Scale(zero=False)),
                tooltip=[
                    alt.Tooltip('Month:N', title='Month'),
                    alt.Tooltip('CMI:Q', title='CMI', format='.3f'),
                    alt.Tooltip('Discharges:Q', title='Discharges', format=',')
                ]
            ).properties(
                height=280,
                title=alt.TitleParams(
                    text='📊 CMI Trend (6 Months)',
                    fontSize=16,
                    fontWeight='bold',
                    color='#1565C0'
                )
            ).configure_view(
                strokeWidth=0
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            )
            
            st.altair_chart(chart_cmi, use_container_width=True)
        
        with col_t2:
            # Discharge Volume + Average LOS
            base = alt.Chart(monthly_summary).encode(
                x=alt.X('Month:N', title='Month', sort=None)
            )
            
            # Bar chart for discharges
            bar = base.mark_bar(color='#2E7D32', opacity=0.7).encode(
                y=alt.Y('Discharges:Q', title='Discharges'),
                tooltip=[
                    alt.Tooltip('Month:N', title='Month'),
                    alt.Tooltip('Discharges:Q', title='Discharges', format=',')
                ]
            )
            
            # Line chart for LOS
            line = base.mark_line(
                color='#F57C00',
                strokeWidth=3,
                point=alt.OverlayMarkDef(filled=True, size=80, color='#F57C00')
            ).encode(
                y=alt.Y('Avg_LOS:Q', title='Average LOS (days)', scale=alt.Scale(zero=False)),
                tooltip=[
                    alt.Tooltip('Month:N', title='Month'),
                    alt.Tooltip('Avg_LOS:Q', title='Avg LOS', format='.1f')
                ]
            )
            
            chart_combo = alt.layer(bar, line).resolve_scale(
                y='independent'
            ).properties(
                height=280,
                title=alt.TitleParams(
                    text='👥 Volume & LOS Trend',
                    fontSize=16,
                    fontWeight='bold',
                    color='#2E7D32'
                )
            ).configure_view(
                strokeWidth=0
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            )
            
            st.altair_chart(chart_combo, use_container_width=True)
        
        st.markdown("---")
        
        # ========================================
        # SECTION 3: OPERATIONAL INSIGHTS
        # ========================================
        st.markdown("""
            <div style="background:white;padding:1.5rem;border-radius:12px;
                        box-shadow:0 4px 16px rgba(0,0,0,0.08);margin-bottom:1.5rem;">
                <h3 style="color:#1565C0;margin:0 0 1rem 0;font-size:1.4rem;font-weight:600;">
                    🎯 Operational Insights
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        col_i1, col_i2, col_i3 = st.columns(3)
        
        with col_i1:
            # Top 5 High-RW Cases
            st.markdown("#### 🏆 Top 5 High-Value Cases")
            top_rw = df_current.nlargest(5, 'adjrw')[['pdx', 'adjrw', 'ward_name']]
            if not top_rw.empty:
                for idx, row in enumerate(top_rw.itertuples(), 1):
                    st.markdown(f"""
                        <div style="background:#F5F5F5;padding:0.8rem;border-radius:8px;
                                    margin-bottom:0.5rem;border-left:4px solid #1976D2;">
                            <b>#{idx}</b> {row.pdx} <span style="float:right;color:#1976D2;font-weight:600;">RW: {row.adjrw:.2f}</span><br>
                            <small style="color:#666;">{row.ward_name}</small>
                        </div>
                    """, unsafe_allow_html=True)
        
        with col_i2:
            # Alert: Long Stay Cases
            st.markdown("#### ⚠️ Long Stay Alert (>30 days)")
            long_stay = df_current[df_current['length_of_stay'] > 30]
            if len(long_stay) > 0:
                st.error(f"🚨 **{len(long_stay)} cases** require attention")
                for row in long_stay.head(5).itertuples():
                    st.markdown(f"""
                        <div style="background:#FFF3E0;padding:0.6rem;border-radius:6px;
                                    margin-bottom:0.4rem;border-left:3px solid #FF6F00;">
                            <b>AN:</b> {row.an} · <b>LOS:</b> {row.length_of_stay:.0f} days<br>
                            <small>{row.pdx} · {row.ward_name}</small>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No long-stay cases")
        
        with col_i3:
            # Ward Performance
            st.markdown("#### 🏥 Ward CMI Ranking")
            ward_cmi = (df_current.groupby('ward_name')['adjrw']
                        .mean()
                        .sort_values(ascending=False)
                        .head(5))
            
            if not ward_cmi.empty:
                for ward, cmi in ward_cmi.items():
                    bar_width = int((cmi / ward_cmi.max()) * 100)
                    st.markdown(f"""
                        <div style="margin-bottom:0.8rem;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
                                <span style="font-size:0.9rem;font-weight:500;">{ward}</span>
                                <span style="color:#2E7D32;font-weight:600;">{cmi:.3f}</span>
                            </div>
                            <div style="background:#E8F5E9;border-radius:4px;height:8px;">
                                <div style="background:#2E7D32;height:8px;width:{bar_width}%;
                                            border-radius:4px;transition:width 0.3s;"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ========================================
        # SECTION 4: QUICK ACTION CARDS
        # ========================================
        st.markdown("""
            <div style="background:white;padding:1.5rem;border-radius:12px;
                        box-shadow:0 4px 16px rgba(0,0,0,0.08);margin-bottom:1.5rem;">
                <h3 style="color:#1565C0;margin:0 0 1rem 0;font-size:1.4rem;font-weight:600;">
                    🚀 Quick Actions
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        qa1, qa2, qa3, qa4 = st.columns(4)
        
        with qa1:
            st.markdown("""
                <div style="background:linear-gradient(135deg,#1976D2,#1565C0);
                            padding:1.5rem;border-radius:12px;text-align:center;
                            box-shadow:0 4px 12px rgba(25,118,210,0.3);
                            cursor:pointer;transition:transform 0.2s;min-height:140px;">
                    <div style="font-size:2.5rem;margin-bottom:0.5rem;">📊</div>
                    <div style="color:white;font-weight:600;font-size:1.1rem;">View Reports</div>
                    <div style="color:#E3F2FD;font-size:0.85rem;margin-top:0.5rem;">
                        Detailed analytics & dashboards
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with qa2:
            st.markdown("""
                <div style="background:linear-gradient(135deg,#2E7D32,#1B5E20);
                            padding:1.5rem;border-radius:12px;text-align:center;
                            box-shadow:0 4px 12px rgba(46,125,50,0.3);
                            cursor:pointer;transition:transform 0.2s;min-height:140px;">
                    <div style="font-size:2.5rem;margin-bottom:0.5rem;">📥</div>
                    <div style="color:white;font-weight:600;font-size:1.1rem;">Import Data</div>
                    <div style="color:#E8F5E9;font-size:0.85rem;margin-top:0.5rem;">
                        Upload monthly IPD files
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with qa3:
            st.markdown("""
                <div style="background:linear-gradient(135deg,#F57C00,#E65100);
                            padding:1.5rem;border-radius:12px;text-align:center;
                            box-shadow:0 4px 12px rgba(245,124,0,0.3);
                            cursor:pointer;transition:transform 0.2s;min-height:140px;">
                    <div style="font-size:2.5rem;margin-bottom:0.5rem;">🔬</div>
                    <div style="color:white;font-weight:600;font-size:1.1rem;">Deep Analysis</div>
                    <div style="color:#FFF3E0;font-size:0.85rem;margin-top:0.5rem;">
                        Advanced insights & trends
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with qa4:
            st.markdown("""
                <div style="background:linear-gradient(135deg,#7B1FA2,#6A1B9A);
                            padding:1.5rem;border-radius:12px;text-align:center;
                            box-shadow:0 4px 12px rgba(123,31,162,0.3);
                            cursor:pointer;transition:transform 0.2s;min-height:140px;">
                    <div style="font-size:2.5rem;margin-bottom:0.5rem;">⚙️</div>
                    <div style="color:white;font-weight:600;font-size:1.1rem;">Settings</div>
                    <div style="color:#F3E5F5;font-size:0.85rem;margin-top:0.5rem;">
                        Configure system & alerts
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ========================================
        # FOOTER: System Status
        # ========================================
        st.markdown(f"""
            <div style="background:#F5F5F5;padding:1rem;border-radius:8px;
                        text-align:center;color:#666;font-size:0.9rem;">
                <span style="color:#2E7D32;font-weight:600;">✅ System Online</span> · 
                Last updated: {pd.Timestamp.now().strftime('%d %b %Y, %H:%M')} · 
                Data records: {len(df_all):,} · 
                Latest month: {latest_month.strftime('%B %Y')}
            </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการโหลด Dashboard: {str(e)}")
        st.info("💡 ลองไปที่เมนู '🔧 ทดสอบการเชื่อมต่อ' เพื่อตรวจสอบปัญหา")
     
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
