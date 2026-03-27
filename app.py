import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
import json
import re
import altair as alt  # ⚠️ ต้องมีบรรทัดนี้
import streamlit.components.v1 as components

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



def show_reports():
    """หน้ารายงาน — 4 tabs"""

    # ── รหัสโรค ──────────────────────────────────────────
     
    PNEUMONIA_CODES = [
        'J10', 'J11', 'J12', 'J13', 'J14',
        'J15', 'J16', 'J17', 'J18', 'J85.0', 'J85.1',
        'J95.0', 'J95.85', 'J95.851',  # ← เพิ่ม HAP และ VAP
        'J22'                            # ← เพิ่ม HAP
    ]
    OP_VENT = ['96.7']  # ventilator op codes

    # ── โหลดข้อมูล ────────────────────────────────────────
    client = init_supabase()
    
    with st.spinner("กำลังโหลดข้อมูล..."):
        try:
            result = client.select('ipd_monthly')
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล: {str(e)}")
            st.info("💡 ลองไปที่เมนู '🔧 ทดสอบการเชื่อมต่อ' เพื่อตรวจสอบปัญหา")
            return

    if result.get('error'):
        st.error(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {result['error']}")
        st.info("💡 ลองไปที่เมนู '🔧 ทดสอบการเชื่อมต่อ' เพื่อตรวจสอบปัญหา")
        return
    
    if not result.get('data'):
        st.warning("⚠️ ไม่พบข้อมูลในระบบ กรุณานำเข้าข้อมูลก่อน")
        return

    try:
        df_all = pd.DataFrame(result['data'])
    except Exception as e:
        st.error(f"❌ ไม่สามารถแปลงข้อมูลเป็น DataFrame: {str(e)}")
        return
        
    if df_all.empty:
        st.warning("⚠️ ไม่พบข้อมูล")
        return

    # ── แปลงประเภทข้อมูล ─────────────────────────────────
    try:
        df_all['month_year'] = pd.to_datetime(df_all['month_year'], errors='coerce')
        df_all['admit_date'] = pd.to_datetime(df_all['admit_date'], errors='coerce')
        df_all['discharge_date'] = pd.to_datetime(df_all['discharge_date'], errors='coerce')
        df_all['age'] = pd.to_numeric(df_all.get('age', pd.Series()), errors='coerce')
        df_all['adjrw'] = pd.to_numeric(df_all.get('adjrw', pd.Series()), errors='coerce')
        df_all['length_of_stay'] = pd.to_numeric(df_all.get('length_of_stay', pd.Series()), errors='coerce')
        df_all['month_label'] = df_all['month_year'].dt.strftime('%b %Y')
        df_all['month_sort'] = df_all['month_year'].dt.to_period('M')
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการแปลงประเภทข้อมูล: {str(e)}")
        st.info("💡 ตรวจสอบว่าข้อมูลในฐานข้อมูลมีรูปแบบที่ถูกต้อง")
        return

    # ── helper ───────────────────────────────────────────
    def is_pneumonia(code):
        if pd.isna(code): 
            return False
        s = str(code).strip()
        return any(s.startswith(c) for c in PNEUMONIA_CODES)

    def has_ventilator(row):
        op_cols = [f'op{i}' for i in range(12)]
        try:
            return any(
                str(row.get(c, '')).startswith(tuple(OP_VENT))
                for c in op_cols if c in row and pd.notna(row.get(c))
            )
        except Exception:
            return False

    def get_vent_codes(row):
        op_cols = [f'op{i}' for i in range(12)]
        try:
            return ', '.join(
                f'{c}={row[c]}' for c in op_cols
                if c in row and pd.notna(row.get(c)) and str(row.get(c, '')).startswith(tuple(OP_VENT))
            )
        except Exception:
            return ""

    # ✅ ตรวจสอบว่ามีคอลัมน์ pdx ก่อนใช้งาน
    if 'pdx' not in df_all.columns:
        st.error("❌ ไม่พบคอลัมน์ 'pdx' ในข้อมูล ไม่สามารถวิเคราะห์โรคปอดบวมได้")
        df_pneumonia = pd.DataFrame()
    else:
        df_pneumonia = df_all[df_all['pdx'].apply(is_pneumonia)].copy()
        df_pneumonia['on_vent'] = df_pneumonia.apply(has_ventilator, axis=1)
        df_pneumonia['vent_codes'] = df_pneumonia.apply(get_vent_codes, axis=1)

    # ════════════════════════════════════════════════════
    # TABS
    # ════════════════════════════════════════════════════
    try:
        import altair as alt
    except ImportError:
        st.error("❌ ไม่สามารถโหลด Altair library กรุณาติดตั้ง: pip install altair")
        return
        
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏥 Dashboard ภาพรวม",
        "🫁 ปอดบวม (Pneumonia)",
        "💨 VAP Analysis",
        "🧠 Stroke & ACS",
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

        try:
            # ── KPI cards ──
            total = len(df_all)
            cmi = df_all['adjrw'].mean() if 'adjrw' in df_all.columns else 0
            total_rw = df_all['adjrw'].sum() if 'adjrw' in df_all.columns else 0
            los_mean = df_all['length_of_stay'].mean() if 'length_of_stay' in df_all.columns else 0
            
            if 'discharge_status' in df_all.columns:
                death_n = df_all['discharge_status'].str.contains('ตาย', na=False).sum()
            else:
                death_n = 0
                
            death_pct = (death_n / total * 100) if total > 0 else 0
            
            readmit_n = 0
            readmit_hn = set()
            if 'discharge_date' in df_all.columns and 'hn' in df_all.columns and 'admit_date' in df_all.columns:
                try:
                    for _, row in df_all.iterrows():
                        if pd.isna(row.get('discharge_date')) or pd.isna(row.get('hn')): 
                            continue
                        same = df_all[
                            (df_all['hn'] == row['hn']) &
                            (df_all['admit_date'] > row['discharge_date']) &
                            (df_all['admit_date'] <= row['discharge_date'] + pd.Timedelta(days=28))
                        ]
                        if len(same) > 0:
                            readmit_hn.add(row['hn'])
                    readmit_n = len(readmit_hn)
                except Exception:
                    pass
                    
            readmit_pct = (readmit_n / total * 100) if total > 0 else 0

            c1, c2, c3, c4, c5, c6 = st.columns(6)
        
            c1.metric(
                "👥 จำหน่ายทั้งหมด", 
                f"{total:,} ราย",
                help="📊 **จำนวนผู้ป่วยจำหน่ายทั้งหมด**\n\nรวมผู้ป่วยทุกรายที่ออกจาก รพ. ในช่วงเวลาที่เลือก (ข้อมูลทั้งหมดในระบบ)\n\n🔹 **นับจาก:** Admit Date ถึง Discharge Date\n🔹 **รวมทุกสถานะ:** กลับบ้าน, ส่งต่อ, เสียชีวิต, AMA"
            )
            
            c2.metric(
                "📊 CMI", 
                f"{cmi:.3f}",
                help="📈 **ดัชนีความหนักของโรค (Case Mix Index)**\n\nค่าเฉลี่ยของ Adjusted RW ทั้งหมด บ่งบอกความซับซ้อนของผู้ป่วย\n\n🔹 **CMI = 1.0** = ความหนักมาตรฐาน\n🔹 **CMI > 1.5** = รพ.รักษาผู้ป่วยหนักสูง\n🔹 **CMI < 0.8** = รักษาผู้ป่วยเบา\n\n💡 **สูตร:** ΣadjRW ÷ จำนวนผู้ป่วย"
            )
            
            c3.metric(
                "💰 Total adjRW", 
                f"{total_rw:,.1f}",
                help="💰 **น้ำหนักสัมพัทธ์รวม (Total Adjusted RW)**\n\nผลรวม Adjusted RW ทั้งหมด ใช้คำนวณรายได้จาก สปสช.\n\n🔹 **ใช้สำหรับ:** คำนวณค่า DRG Payment\n🔹 **1 RW** ≈ ค่าตอบแทนฐาน × RW Rate\n🔹 **ยิ่งสูง** = รายได้มากขึ้น (ถ้า CMI เหมาะสม)\n\n💡 **RW รวมสูง + CMI ต่ำ** = ปริมาณงานมาก"
            )
            
            c4.metric(
                "🛏 LOS เฉลี่ย", 
                f"{los_mean:.1f} วัน",
                help="🛏️ **ระยะเวลานอน รพ. เฉลี่ย (Average Length of Stay)**\n\nจำนวนวันเฉลี่ยที่ผู้ป่วยนอนใน รพ.\n\n🔹 **LOS ต่ำ** = ประสิทธิภาพสูง, หมุนเวียนเตียงดี\n🔹 **LOS สูง** = อาจมีผู้ป่วยซับซ้อน หรือ Delay Discharge\n🔹 **เกณฑ์:** 3-5 วัน (ขึ้นกับประเภท รพ.)\n\n⚠️ **LOS > 30 วัน** = ควรตรวจสอบ"
            )
            
            c5.metric(
                "💀 เสียชีวิต", 
                f"{death_n} ราย", 
                f"{death_pct:.1f}%",
                help="💀 **จำนวนและอัตราการเสียชีวิต**\n\nผู้ป่วยที่เสียชีวิตระหว่างนอน รพ.\n\n🔹 **ไม่รวม:** DOA (Dead on Arrival)\n🔹 **เกณฑ์:** < 2% (รพ.ทั่วไป)\n🔹 **Adjusted Mortality Rate** ควรคำนวณตาม CMI\n\n💡 **Mortality สูง + CMI ต่ำ** = ควรตรวจสอบคุณภาพ"
            )
            
            c6.metric(
                "🔄 Readmit ≤28 วัน", 
                f"{readmit_n} ราย", 
                f"{readmit_pct:.1f}%",
                help="🔄 **อัตราผู้ป่วยกลับเข้ารักษาซ้ำภายใน 28 วัน**\n\nผู้ป่วยที่กลับมารักษาซ้ำหลังจำหน่ายไม่เกิน 28 วัน (Same HN)\n\n🔹 **เกณฑ์:** < 10%\n🔹 **Readmit สูง** = อาจเกิดจาก:\n   • จำหน่ายเร็วเกินไป\n   • Follow-up ไม่ดี\n   • โรคซับซ้อน\n\n💡 **ไม่รวม:** Planned Readmission (เช่น Chemo)"
            )
            st.markdown("---")

            # ── กราฟ 1: จำหน่ายรายเดือน ──
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### 📅 จำนวนจำหน่ายรายเดือน")
                if 'month_label' in df_all.columns:
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
                if 'month_label' in df_all.columns and 'adjrw' in df_all.columns:
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
                if 'pdx' in df_all.columns:
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
                if 'clinic_name' in df_all.columns:
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
                if 'discharge_status' in df_all.columns:
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
                if 'age' in df_all.columns:
                    bins = [0, 5, 15, 30, 45, 60, 75, 200]
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
            if 'length_of_stay' in df_all.columns:
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
                
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดใน Tab Dashboard: {str(e)}")

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
            months_avail = sorted(df_pneumonia['month_sort'].dropna().unique())
            months_labels = [str(m) for m in months_avail]
            if len(months_labels) > 1:
                cf1, cf2 = st.columns(2)
                with cf1:
                    s_m = st.selectbox("เดือนเริ่มต้น", months_labels, index=0, key='pn_s')
                with cf2:
                    e_m = st.selectbox("เดือนสิ้นสุด", months_labels, index=len(months_labels)-1, key='pn_e')
                df_pn = df_pneumonia[
                    (df_pneumonia['month_sort'] >= s_m) &
                    (df_pneumonia['month_sort'] <= e_m)
                ].copy()
            else:
                df_pn = df_pneumonia.copy()

            # KPI
            tot_pn = len(df_pn)
            death_pn = df_pn['discharge_status'].str.contains('ตาย',na=False).sum() if 'discharge_status' in df_pn.columns else 0
            improve_pn = df_pn['discharge_status'].str.contains('ดีขึ้น',na=False).sum() if 'discharge_status' in df_pn.columns else 0
            vent_pn = df_pn['on_vent'].sum() if 'on_vent' in df_pn.columns else 0
            
            readmit_pn = 0
            if 'discharge_date' in df_pn.columns and 'hn' in df_pn.columns:
                for _, row in df_pn.iterrows():
                    if pd.isna(row.get('discharge_date')) or pd.isna(row.get('hn')): 
                        continue
                    same = df_all[
                        (df_all['hn'] == row['hn']) &
                        (df_all['admit_date'] > row['discharge_date']) &
                        (df_all['admit_date'] <= row['discharge_date'] + pd.Timedelta(days=28))
                    ]
                    if len(same) > 0:
                        readmit_pn += 1

  

            k1,k2,k3,k4,k5 = st.columns(5)
            
            k1.metric(
                "🏥 จำหน่ายทั้งหมด", 
                f"{tot_pn:,} ราย",
                help="🫁 **ผู้ป่วยปอดบวมทั้งหมด**\n\nผู้ป่วยที่มี PDX เป็นรหัสโรคปอดบวม (J10-J18, J85.0, J85.1)\n\n🔹 **J10-J11:** Influenza pneumonia\n🔹 **J12-J18:** Pneumonia (bacterial, viral, etc.)\n🔹 **J85:** Lung abscess\n\n💡 **ไม่รวม:** Aspiration pneumonia, VAP (ดูใน Tab VAP)"
            )
            
            k2.metric(
                "💀 เสียชีวิต", 
                f"{death_pn} ราย", 
                f"{death_pn/tot_pn*100:.1f}%" if tot_pn else "0%",
                help="💀 **อัตราเสียชีวิตในผู้ป่วยปอดบวม**\n\nเปอร์เซ็นต์ของผู้ป่วยปอดบวมที่เสียชีวิตใน รพ.\n\n🔹 **เกณฑ์ทั่วไป:** 5-10% (ขึ้นกับ severity)\n🔹 **Pneumonia with sepsis:** 20-30%\n🔹 **Ventilator pneumonia:** 30-50%\n\n⚠️ **Mortality สูง** → ตรวจสอบ:\n   • ระยะเวลารอรักษา\n   • Antibiotic appropriateness\n   • Comorbidity"
            )
            
            k3.metric(
                "✅ Improve", 
                f"{improve_pn} ราย",
                help="✅ **จำหน่ายโดยอาการดีขึ้น**\n\nผู้ป่วยปอดบวมที่รักษาหายและจำหน่ายกลับบ้าน\n\n🔹 **Discharge Status:** 'ดีขึ้น', 'หาย'\n🔹 **เป้าหมาย:** > 85%\n\n💡 **ปัจจัยสำเร็จ:**\n   • Early antibiotic\n   • Appropriate treatment\n   • Good respiratory care"
            )
            
            k4.metric(
                "🔄 Readmit ≤28 วัน", 
                f"{readmit_pn} ราย", 
                f"{readmit_pn/tot_pn*100:.1f}%" if tot_pn else "0%",
                help="🔄 **ผู้ป่วยปอดบวมกลับเข้ารักษาซ้ำภายใน 28 วัน**\n\nผู้ป่วยปอดบวมที่จำหน่ายแล้วกลับมารักษาซ้ำ\n\n🔹 **เกณฑ์:** < 15% (สำหรับ pneumonia)\n🔹 **Readmit สูง** อาจเกิดจาก:\n   • Treatment failure\n   • Recurrent infection\n   • Underlying chronic disease\n   • Poor compliance\n\n💡 **ป้องกัน:** Patient education + Follow-up plan"
            )
            
            k5.metric(
                "💨 On Ventilator", 
                f"{int(vent_pn)} ราย",
                help="💨 **ผู้ป่วยปอดบวมที่ใช้เครื่องช่วยหายใจ**\n\nผู้ป่วยปอดบวมที่มี OP Code 96.7x (Mechanical Ventilation)\n\n🔹 **OP 96.71:** < 96 hours\n🔹 **OP 96.72:** >= 96 hours\n\n⚠️ **Risk:**\n   • VAP (Ventilator-Associated Pneumonia)\n   • Prolonged LOS\n   • Higher mortality\n\n💡 **ควรตรวจสอบ:** VAP bundle compliance"
            )

            # ── คำนิยาม ICD-10 ──────────────────────────────────────────────
            # CAP: Community-Acquired Pneumonia
            CAP_CODES = ['J13', 'J14', 'J15', 'J16', 'J17', 'J18',
                         'J10', 'J11', 'J12']
            # HAP: Hospital-Acquired Pneumonia (รวม J95.0 = Tracheostomy complications with infection)
            HAP_CODES = ['J95.0', 'J22']
            # VAP: Ventilator-Associated Pneumonia
            VAP_CODES = ['J95.851', 'J95.85']
             

            TARGET_WARDS_KEYWORDS = {
                'MB2':  ['MB2_หอผู้ป่วยในชายตึกแสงเดือน'],
                'MB4':  ['MB4_หอผู้ป่วย SP'],
                'MB5':  ['MB5_หอผู้ป่วยในหญิงตึกแสงเดือน'],
                'VIP':  ['MB6_ห้องพิเศษตึกแสงเดือน', 'MB7_ห้องพิเศษตึกแสงเดือน',
                         'F6_ห้องพิเศษตึก 7 ชั้น', 'F7_ห้องพิเศษตึก 7 ชั้น'],
                'ICU':  ['หอผู้ป่วยหนัก ICU'],
                'PICU': ['PICU'],
                'NICU': ['หอผู้ป่วยใน NICU'],
                'LR':   ['LR_ห้องคลอด'],
                'F1':   ['F1_หอผู้ป่วยในชายตึกสายลม'],
                'F2':   ['F2_หอผู้ป่วยในหญิงตึกสายลม'],
                'Peds': ['หอผู้ป่วยกุมารเวชกรรม'],
                'LW':   ['หอผู้ป่วยหลังคลอดและนรีเวชกรรม'],
            }
             
            st.markdown("""
            <table style="width:100%;border-collapse:separate;border-spacing:12px;">
            <tr>
              <td style="background:white;padding:1rem;border-radius:8px;
                         border-left:4px solid #1976D2;vertical-align:top;width:33%;">
                <b style="color:#1976D2;">🏘️ CAP</b><br>
                <span style="color:#37474F;font-size:0.85rem;">
                  <b>Community-Acquired Pneumonia</b><br>
                  ปอดบวมที่ติดเชื้อจากชุมชน (ก่อน admit หรือ ≤48 ชม.หลัง admit)<br><br>
                  <b>รหัส ICD-10:</b><br>
                  J10 – Flu w/ pneumonia (identified)<br>
                  J11 – Flu w/ pneumonia (unidentified)<br>
                  J12 – Viral pneumonia NEC<br>
                  J13 – Pneumococcal pneumonia<br>
                  J14 – H. influenzae pneumonia<br>
                  J15 – Bacterial pneumonia NEC<br>
                  J16 – Pneumonia (other organisms)<br>
                  J17 – Pneumonia in diseases<br>
                  J18 – Pneumonia, unspecified<br><br>
                  <b>Logic การจำแนก:</b><br>
                  ✅ มีรหัส J10-J18 ใน pdx<br>
                  ✅ ไม่มีเงื่อนไข HAP/VAP
                </span>
              </td>
            
              <td style="background:white;padding:1rem;border-radius:8px;
                         border-left:4px solid #F57C00;vertical-align:top;width:33%;">
                <b style="color:#F57C00;">🏥 HAP</b><br>
                <span style="color:#37474F;font-size:0.85rem;">
                  <b>Hospital-Acquired Pneumonia</b><br>
                  ปอดบวมที่เกิดขณะนอน รพ. >48 ชม. แต่ยังไม่ได้ใช้เครื่องช่วยหายใจ<br><br>
                  <b>รหัส ICD-10:</b><br>
                  J95.0 – Tracheostomy complication w/ infection<br>
                  J22 – Unspecified acute lower respiratory infection<br><br>
                  <b>Logic การจำแนก (ถ้าไม่มี J95.0/J22):</b><br>
                  ✅ มีรหัส J10-J18 ใน pdx<br>
                  ✅ LOS > 2 วัน<br>
                  ✅ ไม่ใช่ไข้หวัดใหญ่ (ไม่ใช่ J10/J11)<br>
                  ✅ ไม่มี Ventilator (OP 96.7x)<br><br>
                  <b>หมายเหตุ:</b><br>
                  โรงพยาบาลบางแห่งยังใช้ J18.x<br>
                  ควร cross-check กับ IC team
                </span>
              </td>
            
              <td style="background:white;padding:1rem;border-radius:8px;
                         border-left:4px solid #D32F2F;vertical-align:top;width:33%;">
                <b style="color:#D32F2F;">💨 VAP</b><br>
                <span style="color:#37474F;font-size:0.85rem;">
                  <b>Ventilator-Associated Pneumonia</b><br>
                  ปอดบวมที่เกิดขณะใส่ท่อช่วยหายใจ >48 ชม.<br><br>
                  <b>รหัส ICD-10:</b><br>
                  J95.851 – VAP (specific code)<br>
                  J95.85 – VAP (broader)<br><br>
                  <b>Logic การจำแนก (ถ้าไม่มี J95.85):</b><br>
                  ✅ มีรหัส J10-J18 ใน pdx<br>
                  ✅ อยู่ใน ICU<br>
                  ✅ มี Ventilator (OP 96.7x)<br>
                  ✅ LOS > 2 วัน<br><br>
                  <b>เงื่อนไขเพิ่มเติม:</b><br>
                  ควร cross-check: IC records + สมุด VAP
                </span>
              </td>
            </tr>
            </table>
            
            <div style="margin-top:0.8rem;padding:0.8rem 1rem;background:rgba(255,152,0,0.1);
                        border-radius:6px;border-left:3px solid #FF9800;">
              <span style="color:#E65100;font-size:0.85rem;">
                ⚠️ <b>ข้อจำกัด:</b> การจำแนก CAP/HAP/VAP ในรายงานนี้ใช้ <b>รหัส pdx เป็นหลัก</b>
                และใช้ <b>Logic เสริม</b> (LOS + Ward + Ventilator)
                กรณีที่ไม่มีรหัส J95.0/J95.85<br>
                ควรใช้ <b>ร่วมกับการ review clinical records</b> โดยทีม IC<br><br>
                🔵 <b>CAP</b> = J10-J18 (ไม่มีเงื่อนไข HAP/VAP)<br>
                🟠 <b>HAP (ประมาณ)</b> = J10-J18 + LOS > 2 วัน + ไม่มี Ventilator + ไม่ใช่ Flu<br>
                🔴 <b>VAP (ประมาณ)</b> = J10-J18 + ICU + Ventilator + LOS > 2 วัน
              </span>
            </div>
            """, unsafe_allow_html=True)

             


            def classify_pneumonia_type(row):
                pdx_val = str(row.get('pdx', '') or '').strip().upper()
                los     = row.get('length_of_stay', 0) or 0
                on_vent = row.get('on_vent', False)
                ward    = str(row.get('ward_name', '') or '').upper()
            
                # VAP ก่อน (highest priority)
                # — ลง code J95.85 โดยตรง
                if any(pdx_val.startswith(c.upper()) for c in VAP_CODES):
                    return 'vap'
            
                # — ประมาณ VAP: ปอดบวม + ICU + ventilator + LOS > 2 วัน
                is_pneumonia_code = any(
                    pdx_val.startswith(c.upper()) for c in CAP_CODES
                )
                is_icu = ward == 'หอผู้ป่วยหนัก ICU'.upper()
                if is_pneumonia_code and is_icu and on_vent and los > 2:
                    return 'vap'
            
                # HAP
                # — ลง code J95.0, J22 โดยตรง
                if any(pdx_val.startswith(c.upper()) for c in HAP_CODES):
                    return 'hap'
            
                # — ประมาณ HAP: ปอดบวม + LOS > 2 วัน + ไม่ใช่ Flu + ไม่มี ventilator
                FLU_CODES = ['J10', 'J11']
                is_flu = any(pdx_val.startswith(c.upper()) for c in FLU_CODES)
                if is_pneumonia_code and not is_flu and not on_vent and los > 2:
                    return 'hap'
            
                # CAP
                if is_pneumonia_code:
                    return 'cap'
            
                return 'other'
           
            def get_ward_group(ward_name):
                if pd.isna(ward_name):
                    return None
                s = str(ward_name).strip()
                for key, keywords in TARGET_WARDS_KEYWORDS.items():
                    if s in keywords:
                        return key
                return None
            
            # ── เตรียมข้อมูล ──────────────────────────────────────────────
            df_pn2 = df_pn.copy()  # ใช้ df_pn ที่ filter เดือนมาแล้ว
            
            df_pn2['pneu_type']  = df_pn2.apply(classify_pneumonia_type, axis=1)
            df_pn2['ward_group'] = df_pn2['ward_name'].apply(get_ward_group) \
                                   if 'ward_name' in df_pn2.columns else None
            df_pn2['is_death']   = df_pn2['discharge_status'].str.contains('ตาย', na=False) \
                                   if 'discharge_status' in df_pn2.columns \
                                   else pd.Series([False] * len(df_pn2))
            
            # ── สร้างตาราง Summary Matrix ──────────────────────────────────
            
            WARD_ORDER = ['F1', 'F2', 'MB2', 'MB4', 'MB5', 'VIP', 'LR', 'LW', 'Peds', 'PICU', 'NICU', 'ICU']
            TYPES      = ['cap', 'hap', 'vap']
            TYPE_LABEL = {'cap': 'CAP', 'hap': 'HAP', 'vap': 'VAP'}
            TYPE_COLOR = {'cap': '#1976D2', 'hap': '#F57C00', 'vap': '#D32F2F'}
             

            def build_summary_row(subset):
                row = {}
                for t in TYPES:
                    grp = subset[subset['pneu_type'] == t]
                    row[f'{TYPE_LABEL[t]}_n']     = len(grp)
                    row[f'{TYPE_LABEL[t]}_death'] = int(grp['is_death'].sum())
                row['Total_n']     = len(subset)
                row['Total_death'] = int(subset['is_death'].sum())
                return row
            
            all_table_rows = []
       

            for period, df_period in df_pn2.groupby('month_sort'):
                month_label_str = df_period['month_label'].iloc[0] if 'month_label' in df_period.columns else str(period)
                period_key_str  = str(period)   # ← เพิ่มบรรทัดนี้
                first_row = True
            
                for ward in WARD_ORDER:
                    ward_df = df_period[df_period['ward_group'] == ward]
                    r = build_summary_row(ward_df)
                    r['Ward']          = ward
                    r['_month_label']  = month_label_str if first_row else ""
                    r['_period_key']   = period_key_str   # ← เพิ่มบรรทัดนี้
                    r['_is_total']     = False
                    all_table_rows.append(r)
                    first_row = False
            
                total_r = build_summary_row(df_period)
                total_r['Ward']         = '🔷 Total'
                total_r['_month_label'] = ""
                total_r['_period_key']  = period_key_str  # ← เพิ่มบรรทัดนี้
                total_r['_is_total']    = True
                all_table_rows.append(total_r)
            
            
            df_summary_matrix = pd.DataFrame(all_table_rows)
            
            # ── แสดงตาราง ──────────────────────────────────────────────────────────────
            st.markdown("#### 📊 ตารางสรุป CAP / HAP / VAP แยกตาม Ward")

            def render_matrix_table_v2(df_m, hn_data=None):
                import json
            
                if hn_data is None:
                    hn_data = {}
            
                hn_json = json.dumps(hn_data, ensure_ascii=False)
            
                def num_td(val, color, period_key, wk, tlabel, flag="all"):
                    key = f"{period_key}||{wk}||{tlabel}||{flag}"
                    if val == 0:
                        inner = '<span style="color:#BDBDBD;">0</span>'
                    else:
                        inner = (
                            f'<span class="clickable" data-key="{key}" '
                            f'style="color:{color};font-weight:700;cursor:pointer;'
                            f'border-bottom:2px dotted {color};">{val}</span>'
                        )
                    return f'<td style="text-align:center;padding:0.6rem 0.8rem;">{inner}</td>'
            
                def death_td(val, period_key, wk, tlabel):
                    key = f"{period_key}||{wk}||{tlabel}||dead"
                    if val == 0:
                        badge = '<span style="color:#9E9E9E;">—</span>'
                    else:
                        badge = (
                            f'<span class="clickable" data-key="{key}" '
                            f'style="background:#FFCDD2;color:#C62828;padding:2px 8px;'
                            f'border-radius:10px;font-size:0.85rem;font-weight:700;cursor:pointer;">{val}</span>'
                        )
                    return f'<td style="text-align:center;padding:0.6rem 0.8rem;">{badge}</td>'
            
                rows_html = ""
                for i, row in df_m.iterrows():
                    is_total   = row.get("_is_total", False)
                    ml_display = row.get("_month_label", "")
                    period_key = str(row.get("_period_key", ""))
                    bg = "#EDE7F6" if is_total else ("white" if i % 2 == 0 else "#F5F5F5")
                    fw = "700" if is_total else "400"
                    ward = str(row["Ward"])
                    wk   = ward.replace("🔷 ", "")
            
                    rows_html += f"""
                    <tr style="background:{bg};font-weight:{fw};">
                      <td style="padding:0.6rem 1rem;color:#E65100;font-weight:600;white-space:nowrap;">{ml_display}</td>
                      <td style="padding:0.6rem 1rem;font-weight:{fw};color:#1565C0;white-space:nowrap;">{ward}</td>
                      {num_td(row['CAP_n'],   '#1976D2', period_key, wk, 'CAP')}
                      {death_td(row['CAP_death'],         period_key, wk, 'CAP')}
                      {num_td(row['HAP_n'],   '#F57C00', period_key, wk, 'HAP')}
                      {death_td(row['HAP_death'],         period_key, wk, 'HAP')}
                      {num_td(row['VAP_n'],   '#D32F2F', period_key, wk, 'VAP')}
                      {death_td(row['VAP_death'],         period_key, wk, 'VAP')}
                      {num_td(row['Total_n'], '#4CAF50', period_key, wk, 'Total')}
                      {death_td(row['Total_death'],       period_key, wk, 'Total')}
                    </tr>"""
            
                return f"""<!DOCTYPE html>
            <html><head><meta charset="utf-8">
            <style>
              body {{ margin:0; font-family:sans-serif; font-size:14px; }}
              #overlay {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:9999; align-items:center; justify-content:center; }}
              #overlay.show {{ display:flex; }}
              #modal {{ background:#fff; border-radius:14px; padding:1.5rem 2rem; width:90%; max-width:560px; max-height:75vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,0.3); position:relative; }}
              #modal-title {{ color:#1565C0; font-size:1rem; font-weight:700; margin:0 2rem 1rem 0; line-height:1.4; }}
              #modal-list {{ list-style:none; padding:0; margin:0; }}
              #modal-list li {{ padding:0.5rem 0.8rem; margin-bottom:0.35rem; border-radius:6px; background:#F5F9FC; border-left:3px solid #1976D2; font-family:monospace; font-size:0.85rem; color:#37474F; }}
              .empty-msg {{ color:#9E9E9E; font-style:italic; }}
              #btn-close {{ position:absolute; top:0.8rem; right:1rem; background:none; border:none; font-size:1.5rem; cursor:pointer; color:#9E9E9E; }}
              #btn-close:hover {{ color:#1565C0; }}
              #btn-copy {{ margin-top:1rem; padding:0.45rem 1.2rem; background:#1565C0; color:#fff; border:none; border-radius:8px; cursor:pointer; font-size:0.88rem; font-weight:600; }}
              .wrap {{ overflow-x:auto; overflow-y:auto; max-height:460px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.08); }}
              table {{ width:100%; border-collapse:collapse; min-width:900px; }}
              thead {{ position:sticky; top:0; z-index:10; }}
              .clickable:hover {{ opacity:0.75; }}
            </style>
            </head><body>
            <div id="overlay">
              <div id="modal">
                <button id="btn-close">✕</button>
                <div id="modal-title"></div>
                <ul id="modal-list"></ul>
                <button id="btn-copy">📋 คัดลอก HN ทั้งหมด</button>
              </div>
            </div>
            <div class="wrap">
            <table>
              <thead>
                <tr style="background:linear-gradient(135deg,#1565C0,#283593);color:white;">
                  <th rowspan="2" style="padding:0.8rem 1rem;text-align:left;min-width:100px;">📅 เดือน</th>
                  <th rowspan="2" style="padding:0.8rem 1rem;text-align:left;min-width:160px;">🏥 Ward</th>
                  <th colspan="2" style="padding:0.8rem;text-align:center;border-right:2px solid rgba(255,255,255,0.3);">🏘️ CAP</th>
                  <th colspan="2" style="padding:0.8rem;text-align:center;border-right:2px solid rgba(255,255,255,0.3);">🏥 HAP</th>
                  <th colspan="2" style="padding:0.8rem;text-align:center;border-right:2px solid rgba(255,255,255,0.3);">💨 VAP</th>
                  <th colspan="2" style="padding:0.8rem;text-align:center;">📊 Total</th>
                </tr>
                <tr style="background:#1976D2;color:white;font-size:0.85rem;">
                  <th style="padding:0.5rem 0.8rem;text-align:center;">จำนวน</th>
                  <th style="padding:0.5rem 0.8rem;text-align:center;border-right:2px solid rgba(255,255,255,0.3);">💀 ตาย</th>
                  <th style="padding:0.5rem 0.8rem;text-align:center;">จำนวน</th>
                  <th style="padding:0.5rem 0.8rem;text-align:center;border-right:2px solid rgba(255,255,255,0.3);">💀 ตาย</th>
                  <th style="padding:0.5rem 0.8rem;text-align:center;">จำนวน</th>
                  <th style="padding:0.5rem 0.8rem;text-align:center;border-right:2px solid rgba(255,255,255,0.3);">💀 ตาย</th>
                  <th style="padding:0.5rem 0.8rem;text-align:center;">จำนวน</th>
                  <th style="padding:0.5rem 0.8rem;text-align:center;">💀 ตาย</th>
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
            </div>
            <script>
              const HN = {hn_json};
              document.body.addEventListener('click', function(e) {{
                const el = e.target.closest('.clickable');
                if (el) openModal(el.dataset.key);
              }});
              function openModal(key) {{
                const list  = HN[key] || [];
                const parts = key.split('||');
                const flag  = parts[3] || 'all';
                document.getElementById('modal-title').textContent =
                  parts[1] + '  ·  ' + parts[2] + (flag==='dead' ? ' (เสียชีวิต)' : '') + '  —  ' + list.length + ' ราย';
                const ul = document.getElementById('modal-list');
                ul.innerHTML = list.length === 0
                  ? '<li class="empty-msg">ไม่มีข้อมูล</li>'
                  : list.map(h => '<li>' + h + '</li>').join('');
                document.getElementById('overlay').classList.add('show');
              }}
              document.getElementById('btn-close').onclick = function() {{
                document.getElementById('overlay').classList.remove('show');
              }};
              document.getElementById('overlay').onclick = function(e) {{
                if (e.target === this) document.getElementById('overlay').classList.remove('show');
              }};
              document.getElementById('btn-copy').onclick = function() {{
                const text = [...document.querySelectorAll('#modal-list li')].map(li => li.textContent).join('\\n');
                navigator.clipboard.writeText(text).then(() => {{
                  this.textContent = '✅ คัดลอกแล้ว!';
                  setTimeout(() => this.textContent = '📋 คัดลอก HN ทั้งหมด', 2000);
                }});
              }};
            </script>
            </body></html>"""

             # ── สร้าง hn_data ก่อนส่งเข้าฟังก์ชัน ────────────────────────────
            TYPE_MAP = {"cap": "CAP", "hap": "HAP", "vap": "VAP"}
            hn_data  = {}

            for period, grp in df_pn2.groupby("month_sort"):
                period_key = str(period)
                for ward_key in grp["ward_group"].dropna().unique():
                    ward_key = str(ward_key)
                    ward_df  = grp[grp["ward_group"] == ward_key]
                    for t_code, t_label in TYPE_MAP.items():
                        sub = ward_df[ward_df["pneu_type"] == t_code]
                        hn_data[f"{period_key}||{ward_key}||{t_label}||all"] = [
                            str(r.get('hn','?'))
                            for _, r in sub.iterrows()
                        ]
                        hn_data[f"{period_key}||{ward_key}||{t_label}||dead"] = [
                            str(r.get('hn','?'))
                            for _, r in sub[sub["is_death"]].iterrows()
                        ]
                    hn_data[f"{period_key}||{ward_key}||Total||all"] = [
                        str(r.get('hn','?'))
                        for _, r in ward_df.iterrows()
                    ]
                    hn_data[f"{period_key}||{ward_key}||Total||dead"] = [
                        str(r.get('hn','?'))
                        for _, r in ward_df[ward_df["is_death"]].iterrows()
                    ]
             
            
            # ── call site ──────────────────────────────────────────────────────
            html_content = render_matrix_table_v2(df_summary_matrix, hn_data)
            components.html(html_content, height=560, scrolling=False)
            
 
   
  
             
            # ── Download ────────────────────────────────────────────────────
            csv_matrix = df_summary_matrix.drop(
                columns=['_month_label', '_is_total','_period_key'], errors='ignore'
            ).to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                "📥 ดาวน์โหลดตาราง CSV",
                csv_matrix,
                f"cap_hap_vap_summary_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                key='dl_cap_hap_vap'
            )
 
            # ── กราฟ Stacked Bar ───────────────────────────────────────────
            st.markdown("#### 📊 จำนวนผู้ป่วยแยกประเภทตาม Ward")
            
            chart_rows = []
            for _, row in df_summary_matrix.iterrows():
                if 'Total' not in str(row['Ward']):
                    for t in TYPES:
                        chart_rows.append({
                            'Ward': row['Ward'],
                            'ประเภท': TYPE_LABEL[t],
                            'จำนวน': row[f'{TYPE_LABEL[t]}_n']
                        })
            
            df_chart = pd.DataFrame(chart_rows)
            
            if not df_chart.empty and df_chart['จำนวน'].sum() > 0:
                color_scale = alt.Scale(
                    domain=['CAP', 'HAP', 'VAP'],
                    range=['#1976D2', '#F57C00', '#D32F2F']
                )
                ch_stack = alt.Chart(df_chart).mark_bar(cornerRadiusTopLeft=4,
                                                         cornerRadiusTopRight=4).encode(
                    x=alt.X('Ward:N', title='หอผู้ป่วย', sort=WARD_ORDER),
                    y=alt.Y('จำนวน:Q', title='จำนวนราย', stack=True),
                    color=alt.Color('ประเภท:N', scale=color_scale,
                                    legend=alt.Legend(title='ประเภทปอดบวม')),
                    tooltip=['Ward', 'ประเภท', 'จำนวน']
                ).properties(height=300)
                st.altair_chart(ch_stack, use_container_width=True)
            else:
                st.info("ℹ️ ไม่มีข้อมูลเพียงพอสำหรับแสดงกราฟ")
             
            st.markdown("---")

            # ── ตารางรายเดือน ──
            st.markdown("#### 📋 ตารางสรุปรายเดือน")
            rows = []
            for period, grp in df_pn.groupby('month_sort'):
                ml = grp['month_label'].iloc[0]
                tot = len(grp)
                dead = grp['discharge_status'].str.contains('ตาย',na=False).sum() if 'discharge_status' in grp.columns else 0
                imp = grp['discharge_status'].str.contains('ดีขึ้น',na=False).sum() if 'discharge_status' in grp.columns else 0
                vn = grp['on_vent'].sum() if 'on_vent' in grp.columns else 0
                ra = 0
                for _, row in grp.iterrows():
                    if pd.isna(row.get('discharge_date')) or pd.isna(row.get('hn')): 
                        continue
                    same = df_all[
                        (df_all['hn'] == row['hn']) &
                        (df_all['admit_date'] > row['discharge_date']) &
                        (df_all['admit_date'] <= row['discharge_date'] + pd.Timedelta(days=28))
                    ]
                    if len(same) > 0: 
                        ra += 1
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



            # ── ข้อมูลดิบ Pneumonia แยก Ward ──────────────────────────
            st.markdown("---")
            st.markdown("#### 📋 ข้อมูลดิบ Pneumonia แยกตาม Ward") 
            if 'pdx' in df_pn2.columns:
                df_pneu_raw = df_pn2.copy()
                df_pneu_raw['Pneumonia_Type'] = df_pneu_raw['pneu_type'].map({
                    'cap': '🏘️ CAP',
                    'hap': '🏥 HAP', 
                    'vap': '💨 VAP'
                })
                df_pneu_raw['เสียชีวิต'] = df_pneu_raw['discharge_status'].str.contains(
                    'ตาย', na=False).map({True: '💀 ใช่', False: '—'})
                df_pneu_raw['On Vent'] = df_pneu_raw['on_vent'].map(
                    {True: '✅ ใช่', False: '—'})
                
                # แปลง month_year
                if 'month_year' in df_pneu_raw.columns:
                    df_pneu_raw['month_year'] = pd.to_datetime(
                        df_pneu_raw['month_year'], errors='coerce'
                    ).dt.strftime('%b %Y')
            
                # แปลงวันที่
                for date_col in ['admit_date', 'discharge_date']:
                    if date_col in df_pneu_raw.columns:
                        df_pneu_raw[date_col] = pd.to_datetime(
                            df_pneu_raw[date_col], errors='coerce'
                        ).dt.strftime('%d/%m/%Y')
            
                # คอลัมน์ที่แสดง
                show_cols_pn = ['month_year', 'hn', 'an', 'age', 'sex',
                                'Pneumonia_Type', 'pdx',
                                'admit_date', 'discharge_date', 'length_of_stay',
                                'discharge_status', 'เสียชีวิต', 'On Vent',
                                'ward_name', 'adjrw']
                show_cols_pn = [c for c in show_cols_pn if c in df_pneu_raw.columns]
            
                # column_config
                pn_col_config = {
                    "month_year":      st.column_config.TextColumn("เดือน"),
                    "hn":              st.column_config.TextColumn("HN"),
                    "an":              st.column_config.TextColumn("AN"),
                    "age":             st.column_config.NumberColumn("อายุ", format="%d ปี"),
                    "Pneumonia_Type":  st.column_config.TextColumn("ประเภท"),
                    "pdx":             st.column_config.TextColumn("ICD-10"),
                    "admit_date":      st.column_config.TextColumn("วันที่ admit"),
                    "discharge_date":  st.column_config.TextColumn("วันที่จำหน่าย"),
                    "length_of_stay":  st.column_config.NumberColumn("LOS", format="%d วัน"),
                    "adjrw":           st.column_config.NumberColumn("adjRW", format="%.2f"),
                    "เสียชีวิต":       st.column_config.TextColumn("เสียชีวิต"),
                    "On Vent":         st.column_config.TextColumn("On Ventilator"),
                }
            
                # แสดงแยก Ward
                ward_list_pn = ['MB2', 'MB4', 'MB5', 'VIP', 'ICU']
                for ward in ward_list_pn:
                    ward_df_pn = df_pneu_raw[df_pneu_raw['ward_group'] == ward]
                    if ward_df_pn.empty:
                        continue
            
                    n_total_pn = len(ward_df_pn)
                    n_cap      = (ward_df_pn['Pneumonia_Type'] == '🏘️ CAP').sum()
                    n_hap      = (ward_df_pn['Pneumonia_Type'] == '🏥 HAP').sum()
                    n_vap      = (ward_df_pn['Pneumonia_Type'] == '💨 VAP').sum()
                    n_vent_pn  = (ward_df_pn['On Vent'] == '✅ ใช่').sum() \
                                 if 'On Vent' in ward_df_pn.columns else 0
                    n_death_pn = ward_df_pn['discharge_status'].str.contains(
                        'ตาย', na=False).sum()
            
                    with st.expander(
                        f"🏥 {ward} — รวม {n_total_pn} ราย | "
                        f"CAP {n_cap} · HAP {n_hap} · VAP {n_vap} | "
                        f"💨 On Vent {n_vent_pn} | "
                        f"💀 เสียชีวิต {n_death_pn} ราย",
                        expanded=False
                    ):
                        # KPI
                        kp1, kp2, kp3, kp4, kp5, kp6 = st.columns(6)
                        kp1.metric("👥 ทั้งหมด",    f"{n_total_pn} ราย")
                        kp2.metric("🏘️ CAP",        f"{n_cap} ราย",
                                   f"{n_cap/n_total_pn*100:.1f}%" if n_total_pn else "0%")
                        kp3.metric("🏥 HAP",        f"{n_hap} ราย",
                                   f"{n_hap/n_total_pn*100:.1f}%" if n_total_pn else "0%")
                        kp4.metric("💨 VAP",        f"{n_vap} ราย",
                                   f"{n_vap/n_total_pn*100:.1f}%" if n_total_pn else "0%")
                        kp5.metric("🫁 On Vent",    f"{n_vent_pn} ราย",
                                   f"{n_vent_pn/n_total_pn*100:.1f}%" if n_total_pn else "0%")
                        kp6.metric("💀 เสียชีวิต", f"{n_death_pn} ราย",
                                   f"{n_death_pn/n_total_pn*100:.1f}%" if n_total_pn else "0%",
                                   delta_color="inverse")
            
                        st.markdown("**รายชื่อผู้ป่วย:**")
                        st.dataframe(
                            ward_df_pn[show_cols_pn].sort_values(
                                'Pneumonia_Type'
                            ).reset_index(drop=True),
                            use_container_width=True,
                            hide_index=True,
                            column_config=pn_col_config
                        )
            
                        csv_pn_ward = ward_df_pn[show_cols_pn].to_csv(
                            index=False, encoding='utf-8-sig'
                        ).encode('utf-8-sig')
                        st.download_button(
                            f"📥 ดาวน์โหลด {ward} CSV",
                            csv_pn_ward,
                            f"pneumonia_{ward}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                            "text/csv",
                            key=f'dl_pn_ward_{ward}'
                        )
            
                # ── expander รวมทุก Ward ──
                with st.expander(
                    f"🔷 ทุก Ward รวม — {len(df_pneu_raw)} ราย | "
                    f"💀 เสียชีวิต "
                    f"{df_pneu_raw['discharge_status'].str.contains('ตาย', na=False).sum()} ราย",
                    expanded=False
                ):
                    df_pn_display = df_pneu_raw.sort_values(
                        ['ward_group', 'Pneumonia_Type']
                    )[show_cols_pn].reset_index(drop=True)
            
                    st.dataframe(
                        df_pn_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config=pn_col_config
                    )
            
                    csv_pn_all = df_pn_display.to_csv(
                        index=False, encoding='utf-8-sig'
                    ).encode('utf-8-sig')
                    st.download_button(
                        "📥 ดาวน์โหลดทั้งหมด CSV",
                        csv_pn_all,
                        f"pneumonia_all_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        key='dl_pn_all'
                    )
            
            else:
                st.info("ไม่พบคอลัมน์ pdx")

            
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

        
        with tab3:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#37474F,#546E7A);
                        padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.2rem;">
                <h2 style="color:white;margin:0;font-size:1.5rem;">
                    💨 VAP Analysis
                </h2>
            </div>
            """, unsafe_allow_html=True)
        
            # ✅ debug วางตรงนี้
            all_dx_cols_debug = ['pdx'] + [f'dx{i}' for i in range(11)]
            all_dx_cols_debug = [c for c in all_dx_cols_debug if c in df_all.columns]
        
            j95_found = []
            for col in all_dx_cols_debug:
                mask = df_all[col].astype(str).str.startswith('J95')
                found = df_all[mask][['hn', 'an', 'ward_name', col]].copy()
                found['found_in_col'] = col
                found = found.rename(columns={col: 'code'})
                j95_found.append(found)
        
            if j95_found:
                df_j95 = pd.concat(j95_found, ignore_index=True)
                df_j95 = df_j95[df_j95['code'] != 'nan']
                st.write(f"พบ J95.x ทั้งหมด {len(df_j95)} รายการ")
                st.write(df_j95['code'].value_counts())
                st.dataframe(df_j95, use_container_width=True)
            else:
                st.warning("ไม่พบ J95.x เลยในทุก column")

        
        # หา VAP โดยตรง (J95.851)
        all_dx = ['pdx'] + [f'dx{i}' for i in range(11)]
        vap_code_mask = pd.Series([False]*len(df_all), index=df_all.index)
        for col in all_dx:
            if col in df_all.columns:
                vap_code_mask |= df_all[col].astype(str).str.startswith('J95.85')
        df_vap_coded = df_all[vap_code_mask].copy()

        # ปอดบวม + ventilator
        df_pn_vent = df_pneumonia[df_pneumonia['on_vent']].copy() if 'on_vent' in df_pneumonia.columns else pd.DataFrame()

        # all ventilator cases
        df_all['on_vent'] = df_all.apply(has_ventilator, axis=1)
        df_vent_all = df_all[df_all['on_vent']].copy()

         # ✅ แก้ Bug: คำนวณ death_pn_vent ก่อนใช้งาน
        if not df_pn_vent.empty and 'discharge_status' in df_pn_vent.columns:
            death_pn_vent = int(
                df_pn_vent['discharge_status'].str.contains('ตาย', na=False).sum()
            )
        else:
            death_pn_vent = 0
            
        k1, k2, k3, k4 = st.columns(4)
        
        k1.metric(
            "🔴 J95.851 (VAP code)", 
            f"{len(df_vap_coded)} ราย",
            "⚠️ ควรตรวจสอบ" if len(df_vap_coded)==0 else "",
            help="🔴 **VAP ที่ลง Code โดยตรง (J95.851)**\n\nVentilator-Associated Pneumonia ที่ Coder ลงรหัสไว้แล้ว\n\n🔹 **เกณฑ์วินิจฉัย VAP:**\n   • ใส่ท่อช่วยหายใจ > 48 ชม.\n   • เกิดปอดบวมใหม่หลังใส่ท่อ\n   • มี Clinical + Radiologic evidence\n\n⚠️ **ถ้าเป็น 0:**\n   • ยังไม่มี VAP ✅\n   • หรือมีแต่ยังไม่ได้ลง Code ❌\n\n💡 **ต้อง cross-check กับ IC records**"
        )
        
        k2.metric(
            "💨 ใช้ Ventilator ทั้งหมด", 
            f"{len(df_vent_all)} ราย",
            help="💨 **ผู้ป่วยทั้งหมดที่ใช้เครื่องช่วยหายใจ**\n\nผู้ป่วยทุกรายที่มี OP 96.7x (Mechanical Ventilation)\n\n🔹 **รวมทุก diagnosis:** ไม่เฉพาะปอดบวม\n🔹 **At risk for VAP:** ทุกรายที่ใส่ท่อ > 48 ชม.\n\n💡 **VAP rate = (จำนวน VAP / Ventilator days) × 1000**\n\n⚠️ **Target:** < 2-3 per 1000 ventilator days"
        )
        
        k3.metric(
            "🫁 ปอดบวม + Ventilator", 
            f"{len(df_pn_vent)} ราย",
            help="🫁 **ผู้ป่วยปอดบวมที่ใช้ Ventilator (Possible VAP)**\n\nผู้ป่วยที่มีทั้ง:\n• PDX = Pneumonia (J10-J18)\n• OP = Ventilator (96.7x)\n\n⚠️ **ไม่ใช่ VAP ทุกราย!**\n\nต้องตรวจสอบ:\n🔹 **Timeline:** ใส่ท่อก่อนหรือหลังเกิดปอดบวม?\n🔹 **Community-acquired** vs **Hospital-acquired**\n🔹 **Aspiration pneumonia** vs **VAP**\n\n💡 **การยืนยัน:** ดูจาก medical records + IC team"
        )
        
        k4.metric(
            "💀 เสียชีวิตใน ปอดบวม+Vent", 
            f"{death_pn_vent} ราย",
            help="💀 **Mortality ในผู้ป่วยปอดบวมที่ใช้ Ventilator**\n\nอัตราเสียชีวิตในกลุ่ม high-risk นี้\n\n🔹 **Expected mortality:** 30-50%\n🔹 **ปัจจัยเสี่ยง:**\n   • VAP\n   • Sepsis\n   • Multi-organ failure\n   • Prolonged ventilation\n\n💡 **Quality indicators:**\n   • VAP bundle compliance\n   • Time to appropriate antibiotic\n   • Weaning protocol"
        )
        
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
    # TAB 4 : Stroke & ACS 
    # ════════════════════════════════════════════════════
    with tab4:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#B71C1C,#880E4F);
                    padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.2rem;">
            <h2 style="color:white;margin:0;font-size:1.5rem;">
                🧠 Stroke & ACS Summary Report
            </h2>
            <p style="color:#FFCDD2;margin:.3rem 0 0;font-size:.9rem;">
                Stroke (Ischemic / Hemorrhagic) · ACS (STEMI / NSTEMI) | วิเคราะห์จาก pdx
            </p>
        </div>
        """, unsafe_allow_html=True)
    
        # ── ICD-10 Definitions ──────────────────────────────────────
        ISCHEMIC_CODES = [
            'I63',           # Cerebral infarction (ทุก subtype)
            'I64',           # Stroke NOS (not specified as haemorrhage/infarction)
            'I65',           # Occlusion/stenosis precerebral → ischemic territory
            'I66',           # Occlusion/stenosis cerebral arteries
        ]
    
        HEMORRHAGIC_CODES = [
            'I60',           # Subarachnoid haemorrhage
            'I61',           # Intracerebral haemorrhage
            'I62',           # Other nontraumatic intracranial haemorrhage
        ]
    
        STEMI_CODES = [
            'I21.0',         # Anterior STEMI
            'I21.1',         # Inferior STEMI
            'I21.2',         # Other STEMI
            'I21.3',         # STEMI, unspecified site
            'I22.0',         # Subsequent anterior STEMI
            'I22.1',         # Subsequent inferior STEMI
            'I22.8',         # Subsequent STEMI, other site
            'I22.9',         # Subsequent STEMI, unspecified
        ]
     
        NSTEMI_CODES = [
            'I21.4',         # NSTEMI
            'I21.9',         # Acute MI, unspecified
            'I22.2',         # Subsequent NSTEMI
        ]
        
        UA_CODES = [
            'I20.0',         # Unstable angina
            'I24.0',         # Coronary thrombosis not resulting in MI
            'I24.8',         # Other forms of acute ischaemic heart disease
            'I24.9',         # Acute ischaemic heart disease, unspecified
        ]
        
        TARGET_WARDS_STROKE_ACS = {
            'MB2':  ['MB2_หอผู้ป่วยในชายตึกแสงเดือน'],
            'MB4':  ['MB4_หอผู้ป่วย SP'],
            'MB5':  ['MB5_หอผู้ป่วยในหญิงตึกแสงเดือน'],
            'VIP':  ['MB6_ห้องพิเศษตึกแสงเดือน', 'MB7_ห้องพิเศษตึกแสงเดือน',
                     'F6_ห้องพิเศษตึก 7 ชั้น', 'F7_ห้องพิเศษตึก 7 ชั้น'],
            'ICU':  ['หอผู้ป่วยหนัก ICU'],
            'PICU': ['PICU'],
            'NICU': ['หอผู้ป่วยใน NICU'],
            'LR':   ['LR_ห้องคลอด'],
            'F1':   ['F1_หอผู้ป่วยในชายตึกสายลม'],
            'F2':   ['F2_หอผู้ป่วยในหญิงตึกสายลม'],
            'Peds': ['หอผู้ป่วยกุมารเวชกรรม'],
            'LW':   ['หอผู้ป่วยหลังคลอดและนรีเวชกรรม'],
        }
        
        WARD_ORDER_5 = ['F1', 'F2', 'MB2', 'MB4', 'MB5', 'VIP', 'LR', 'LW', 'Peds', 'PICU', 'NICU', 'ICU']
        
    
        # ── Filter เดือน (ใช้ df_all ทั้งหมด ไม่ผ่าน df_pneumonia) ──
        months_avail5 = sorted(
            df_all['month_sort'].dropna().unique()
        )
        months_labels5 = [str(m) for m in months_avail5]
    
        if len(months_labels5) > 1:
            cf5a, cf5b = st.columns(2)
            with cf5a:
                s_m5 = st.selectbox(
                    "เดือนเริ่มต้น", months_labels5,
                    index=0, key='stroke_s'
                )
            with cf5b:
                e_m5 = st.selectbox(
                    "เดือนสิ้นสุด", months_labels5,
                    index=len(months_labels5)-1, key='stroke_e'
                )
            df_sa = df_all[
                (df_all['month_sort'] >= s_m5) &
                (df_all['month_sort'] <= e_m5)
            ].copy()
        else:
            df_sa = df_all.copy()
    
        if 'discharge_status' not in df_sa.columns:
            df_sa['discharge_status'] = ''
        df_sa['is_death'] = df_sa['discharge_status'].str.contains('ตาย', na=False)
    
        # ── Helper ─────────────────────────────────────────────────
        def starts_with_any(code_str, code_list):
            """ตรวจสอบว่า code ขึ้นต้นด้วย code ใดใน list"""
            if pd.isna(code_str):
                return False
            s = str(code_str).strip().upper()
            return any(s.startswith(c.upper()) for c in code_list)
      
        def get_ward_group5(ward_name):
            if pd.isna(ward_name):
                return None
            s = str(ward_name).strip()
            for key, keywords in TARGET_WARDS_STROKE_ACS.items():
                if s in keywords:
                    return key
            return None

        
        def build_matrix(df_src, type_a_codes, type_b_codes,
                         label_a, label_b):
            """
            สร้าง summary matrix 2 ประเภท × N ward
            Returns: DataFrame พร้อมแสดงผล
            """
            if 'pdx' not in df_src.columns:
                return pd.DataFrame()
    
            df_src = df_src.copy()
            df_src['ward_group'] = df_src['ward_name'].apply(get_ward_group5) \
                                   if 'ward_name' in df_src.columns else None
    
            df_src['is_type_a'] = df_src['pdx'].apply(
                lambda x: starts_with_any(x, type_a_codes)
            )
            df_src['is_type_b'] = df_src['pdx'].apply(
                lambda x: starts_with_any(x, type_b_codes)
            )
            df_src['is_either'] = df_src['is_type_a'] | df_src['is_type_b']
    
            rows = []
            for ward in WARD_ORDER_5:
                sub = df_src[
                    (df_src['ward_group'] == ward) & df_src['is_either']
                ]
                sub_a = sub[sub['is_type_a']]
                sub_b = sub[sub['is_type_b']]
                rows.append({
                    'Ward': ward,
                    f'{label_a}_n':     len(sub_a),
                    f'{label_a}_death': int(sub_a['is_death'].sum()),
                    f'{label_b}_n':     len(sub_b),
                    f'{label_b}_death': int(sub_b['is_death'].sum()),
                    'Total_n':          len(sub),
                    'Total_death':      int(sub['is_death'].sum()),
                })
    
            # Total row (ทุก ward รวมกัน)
            df_all_either = df_src[df_src['is_either']]
            df_all_a = df_src[df_src['is_type_a']]
            df_all_b = df_src[df_src['is_type_b']]
            rows.append({
                'Ward': '🔷 Total',
                f'{label_a}_n':     len(df_all_a),
                f'{label_a}_death': int(df_all_a['is_death'].sum()),
                f'{label_b}_n':     len(df_all_b),
                f'{label_b}_death': int(df_all_b['is_death'].sum()),
                'Total_n':          len(df_all_either),
                'Total_death':      int(df_all_either['is_death'].sum()),
            })
    
            return pd.DataFrame(rows)



        def build_matrix_3(df_src, codes_a, codes_b, codes_c, label_a, label_b, label_c):
            """สร้าง summary matrix 3 ประเภท × N ward"""
            if 'pdx' not in df_src.columns:
                return pd.DataFrame()
        
            df_src = df_src.copy()
            df_src['ward_group'] = df_src['ward_name'].apply(get_ward_group5) \
                                   if 'ward_name' in df_src.columns else None
            df_src['is_a'] = df_src['pdx'].apply(lambda x: starts_with_any(x, codes_a))
            df_src['is_b'] = df_src['pdx'].apply(lambda x: starts_with_any(x, codes_b))
            df_src['is_c'] = df_src['pdx'].apply(lambda x: starts_with_any(x, codes_c))
            df_src['is_any'] = df_src['is_a'] | df_src['is_b'] | df_src['is_c']
        
            rows = []
            for ward in WARD_ORDER_5:
                sub   = df_src[(df_src['ward_group'] == ward) & df_src['is_any']]
                sub_a = sub[sub['is_a']]
                sub_b = sub[sub['is_b']]
                sub_c = sub[sub['is_c']]
                rows.append({
                    'Ward': ward,
                    f'{label_a}_n':     len(sub_a),
                    f'{label_a}_death': int(sub_a['is_death'].sum()),
                    f'{label_b}_n':     len(sub_b),
                    f'{label_b}_death': int(sub_b['is_death'].sum()),
                    f'{label_c}_n':     len(sub_c),
                    f'{label_c}_death': int(sub_c['is_death'].sum()),
                    'Total_n':          len(sub),
                    'Total_death':      int(sub['is_death'].sum()),
                })
        
            # Total row
            df_any = df_src[df_src['is_any']]
            rows.append({
                'Ward': '🔷 Total',
                f'{label_a}_n':     int(df_src['is_a'].sum()),
                f'{label_a}_death': int(df_src.loc[df_src['is_a'], 'is_death'].sum()),
                f'{label_b}_n':     int(df_src['is_b'].sum()),
                f'{label_b}_death': int(df_src.loc[df_src['is_b'], 'is_death'].sum()),
                f'{label_c}_n':     int(df_src['is_c'].sum()),
                f'{label_c}_death': int(df_src.loc[df_src['is_c'], 'is_death'].sum()),
                'Total_n':          len(df_any),
                'Total_death':      int(df_any['is_death'].sum()),
            })
            return pd.DataFrame(rows)
        
        # ── Render HTML Table (reusable) ───────────────────────────
        def render_two_type_table(df_m, label_a, label_b,
                                   color_a, color_b, icon_a, icon_b):
            """สร้าง HTML table แบบ 2-type matrix"""
            if df_m.empty:
                return "<p style='color:#757575;'>ไม่พบข้อมูล</p>"

        def render_three_type_table(df_m, label_a, label_b, label_c,
                                     color_a, color_b, color_c,
                                     icon_a, icon_b, icon_c):
            """สร้าง HTML table แบบ 3-type matrix"""
            if df_m.empty:
                return "<p style='color:#757575;'>ไม่พบข้อมูล</p>"                                       
    
            def death_badge(n):
                if n == 0:
                    return '<span style="color:#BDBDBD;">—</span>'
                return (f'<span style="background:#FFCDD2;color:#C62828;'
                        f'padding:2px 8px;border-radius:10px;'
                        f'font-size:0.85rem;font-weight:700;">{n}</span>')
    
            def num_cell(val, color, bold=True):
                fw = "font-weight:700;" if bold else ""
                return (f'<td style="text-align:center;padding:0.55rem 0.7rem;'
                        f'{fw}color:{color};font-size:1rem;">{val}</td>')
    
            def dc_cell(val):
                return (f'<td style="text-align:center;padding:0.55rem 0.7rem;">'
                        f'{death_badge(val)}</td>')
    
            rows_html = ""
            for i, row in df_m.iterrows():
                is_total = 'Total' in str(row['Ward'])
                bg = "#F3E5F5" if is_total else ("white" if i % 2 == 0 else "#FAFAFA")
                fw = "700" if is_total else "400"
                ward_color = "#6A1B9A" if is_total else "#1565C0"
    
                rows_html += f"""
                <tr style="background:{bg};font-weight:{fw};">
                  <td style="padding:0.55rem 1rem;font-weight:{fw};
                             color:{ward_color};white-space:nowrap;">
                      {row['Ward']}
                  </td>
                  {num_cell(row[f'{label_a}_n'],     color_a)}
                  {dc_cell( row[f'{label_a}_death'])}
                  {num_cell(row[f'{label_b}_n'],     color_b)}
                  {dc_cell( row[f'{label_b}_death'])}
                  {num_cell(row['Total_n'],           '#2E7D32')}
                  {dc_cell( row['Total_death'])}
                </tr>
                """
    
            return f"""
            <div style="overflow-x:auto;margin-bottom:1rem;">
            <table style="width:100%;border-collapse:collapse;border-radius:12px;
                          overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
              <thead>
                <tr style="background:linear-gradient(135deg,#37474F,#546E7A);color:white;">
                  <th rowspan="2"
                      style="padding:0.8rem 1rem;text-align:left;min-width:140px;">
                      🏥 Ward
                  </th>
                  <th colspan="2"
                      style="padding:0.7rem;text-align:center;
                             border-right:2px solid rgba(255,255,255,0.25);">
                      {icon_a} {label_a}
                  </th>
                  <th colspan="2"
                      style="padding:0.7rem;text-align:center;
                             border-right:2px solid rgba(255,255,255,0.25);">
                      {icon_b} {label_b}
                  </th>
                  <th colspan="2"
                      style="padding:0.7rem;text-align:center;">
                      📊 Total
                  </th>
                </tr>
                <tr style="background:#455A64;color:white;font-size:0.85rem;">
                  <th style="padding:0.45rem 0.7rem;text-align:center;">จำนวน</th>
                  <th style="padding:0.45rem 0.7rem;text-align:center;
                             border-right:2px solid rgba(255,255,255,0.25);">
                      💀 ตาย
                  </th>
                  <th style="padding:0.45rem 0.7rem;text-align:center;">จำนวน</th>
                  <th style="padding:0.45rem 0.7rem;text-align:center;
                             border-right:2px solid rgba(255,255,255,0.25);">
                      💀 ตาย
                  </th>
                  <th style="padding:0.45rem 0.7rem;text-align:center;">จำนวน</th>
                  <th style="padding:0.45rem 0.7rem;text-align:center;">💀 ตาย</th>
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
            </div>
            """
    
        # ════════════════════════════════════════════════════════════
        # SECTION A : STROKE
        # ════════════════════════════════════════════════════════════
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1A237E,#283593);
                    padding:1rem 1.5rem;border-radius:10px;margin:1.2rem 0 1rem 0;">
            <h3 style="color:white;margin:0;font-size:1.2rem;">
                🧠 STROKE — Ischemic vs Hemorrhagic
            </h3>
        </div>
        """, unsafe_allow_html=True)
    
        # คำอธิบาย ICD-10 Stroke
       
        with st.expander("📖 นิยามและรหัส ICD-10 — Stroke", expanded=False):
            st.markdown("""
            <table style="width:100%;border-collapse:separate;border-spacing:8px;
                          padding:0.5rem 0;">
            <tr>

              <td style="background:#E8EAF6;padding:1rem;border-radius:8px;
                         border-left:4px solid #3949AB;vertical-align:top;width:50%;">
                <b style="color:#283593;font-size:1rem;">🔵 Ischemic Stroke</b><br><br>
                <span style="color:#37474F;font-size:0.85rem;line-height:1.8;">
                  <b>นิยาม:</b> Stroke จากการอุดตันของหลอดเลือดสมอง
                  ทำให้เนื้อสมองขาดเลือด (Infarction)<br><br>
                  <b>รหัส ICD-10:</b><br>
                  I63.x – Cerebral infarction (ทุก subtype)<br>
                  I64 – Stroke, not specified as haemorrhage or infarction (NOS)<br>
                  I65.x – Occlusion/stenosis precerebral arteries<br>
                  I66.x – Occlusion/stenosis cerebral arteries<br><br>
                  <b>สัดส่วน:</b> ~80-85% ของ stroke ทั้งหมด<br>
                  <b>การรักษา:</b> tPA, Thrombectomy
                </span>
              </td>

              <td style="background:#FCE4EC;padding:1rem;border-radius:8px;
                         border-left:4px solid #C62828;vertical-align:top;width:50%;">
                <b style="color:#B71C1C;font-size:1rem;">🔴 Hemorrhagic Stroke</b><br><br>
                <span style="color:#37474F;font-size:0.85rem;line-height:1.8;">
                  <b>นิยาม:</b> Stroke จากการแตกของหลอดเลือดในสมองหรือรอบสมอง (Bleeding)<br><br>
                  <b>รหัส ICD-10:</b><br>
                  I60.x – Subarachnoid haemorrhage (SAH)<br>
                  I61.x – Intracerebral haemorrhage (ICH)<br>
                  I62.x – Other nontraumatic intracranial haemorrhage (SDH, EDH)<br><br>
                  <b>สัดส่วน:</b> ~15-20% ของ stroke ทั้งหมด<br>
                  <b>การรักษา:</b> BP control, Surgery (กรณีจำเป็น)
                </span>
              </td>

            </tr>
            </table>
            <div style="margin-top:0.8rem;padding:0.6rem 1rem;
                        background:rgba(33,33,33,0.05);border-radius:6px;
                        border-left:3px solid #78909C;">
              <span style="color:#455A64;font-size:0.85rem;">
                ⚠️ <b>ข้อจำกัด:</b> รายงานนี้จำแนกโดยใช้ <b>รหัส pdx เท่านั้น</b>
                ไม่ได้ยืนยันจาก CT/MRI —
                ควร review กับทีมแพทย์
              </span>
            </div>
            """, unsafe_allow_html=True)
            
        # สร้างและแสดง Stroke Matrix
        df_stroke = build_matrix(
            df_sa,
            ISCHEMIC_CODES,   HEMORRHAGIC_CODES,
            'Ischemic',        'Hemorrhagic'
        )
    
        # KPI Stroke
        if not df_stroke.empty:
            total_row_s = df_stroke[df_stroke['Ward'] == '🔷 Total'].iloc[0] \
                          if len(df_stroke[df_stroke['Ward'] == '🔷 Total']) > 0 \
                          else None
            if total_row_s is not None:
                ks1, ks2, ks3, ks4, ks5 = st.columns(5)
                tot_s   = int(total_row_s['Total_n'])
                isc_n   = int(total_row_s['Ischemic_n'])
                hem_n   = int(total_row_s['Hemorrhagic_n'])
                isc_d   = int(total_row_s['Ischemic_death'])
                hem_d   = int(total_row_s['Hemorrhagic_death'])
                tot_d   = int(total_row_s['Total_death'])
    
                ks1.metric(
                    "🧠 Stroke ทั้งหมด",
                    f"{tot_s} ราย",
                    help="จำนวนผู้ป่วย Stroke ทุกประเภทในช่วงที่เลือก"
                )
                ks2.metric(
                    "🔵 Ischemic",
                    f"{isc_n} ราย",
                    f"{isc_n/tot_s*100:.1f}%" if tot_s else "0%",
                    help="Ischemic Stroke (I63, I64, I65, I66)"
                )
                ks3.metric(
                    "🔴 Hemorrhagic",
                    f"{hem_n} ราย",
                    f"{hem_n/tot_s*100:.1f}%" if tot_s else "0%",
                    help="Hemorrhagic Stroke (I60, I61, I62)"
                )
                ks4.metric(
                    "💀 เสียชีวิต Ischemic",
                    f"{isc_d} ราย",
                    f"{isc_d/isc_n*100:.1f}%" if isc_n else "0%",
                    delta_color="inverse",
                    help="อัตราเสียชีวิตใน Ischemic Stroke"
                )
                ks5.metric(
                    "💀 เสียชีวิต Hemorrhagic",
                    f"{hem_d} ราย",
                    f"{hem_d/hem_n*100:.1f}%" if hem_n else "0%",
                    delta_color="inverse",
                    help="อัตราเสียชีวิตใน Hemorrhagic Stroke (มักสูงกว่า)"
                )
 

        html_stroke = render_two_type_table(
            df_stroke, 'Ischemic', 'Hemorrhagic',
            '#3949AB', '#C62828', '🔵', '🔴'
        )
        components.html(
            f"<div style='font-family:sans-serif;font-size:14px;'>{html_stroke}</div>",
            height=300,
            scrolling=False
        )
        # Download Stroke
        if not df_stroke.empty:
            csv_s = df_stroke.to_csv(
                index=False, encoding='utf-8-sig'
            ).encode('utf-8-sig')
            st.download_button(
                "📥 ดาวน์โหลด Stroke CSV",
                csv_s,
                f"stroke_summary_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                "text/csv", key='dl_stroke'
            )
    
        # ── Stroke Stacked Bar ─────────────────────────────────────
        stroke_chart_rows = []
        if not df_stroke.empty:
            for _, row in df_stroke.iterrows():
                if 'Total' not in str(row['Ward']):
                    stroke_chart_rows.append({
                        'Ward': row['Ward'],
                        'ประเภท': 'Ischemic',
                        'จำนวน': row['Ischemic_n']
                    })
                    stroke_chart_rows.append({
                        'Ward': row['Ward'],
                        'ประเภท': 'Hemorrhagic',
                        'จำนวน': row['Hemorrhagic_n']
                    })
    
        df_stroke_chart = pd.DataFrame(stroke_chart_rows)
        if not df_stroke_chart.empty and df_stroke_chart['จำนวน'].sum() > 0:
            ch_stroke = alt.Chart(df_stroke_chart).mark_bar(
                cornerRadiusTopLeft=4, cornerRadiusTopRight=4
            ).encode(
                x=alt.X('Ward:N', title='หอผู้ป่วย', sort=WARD_ORDER_5),
                y=alt.Y('จำนวน:Q', title='จำนวนราย', stack=True),
                color=alt.Color(
                    'ประเภท:N',
                    scale=alt.Scale(
                        domain=['Ischemic', 'Hemorrhagic'],
                        range=['#3949AB', '#C62828']
                    ),
                    legend=alt.Legend(title='ประเภท Stroke')
                ),
                tooltip=['Ward', 'ประเภท', 'จำนวน']
            ).properties(height=260)
            st.altair_chart(ch_stroke, use_container_width=True)
        else:
            st.info("ℹ️ ไม่มีข้อมูล Stroke ในช่วงเวลาที่เลือก")
    
        st.markdown("---") 


 
        st.markdown("""
        <div style="background:linear-gradient(135deg,#BF360C,#E64A19);
                    padding:1rem 1.5rem;border-radius:10px;margin:1rem 0;">
            <h3 style="color:white;margin:0;font-size:1.2rem;">
                ❤️ ACS — STEMI / NSTEMI / Unstable Angina
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📖 นิยามและรหัส ICD-10 — ACS", expanded=False):
            st.markdown("""
            <table style="width:100%;border-collapse:separate;border-spacing:8px;padding:0.5rem 0;">
            <tr>
              <td style="background:#FBE9E7;padding:1rem;border-radius:8px;
                         border-left:4px solid #BF360C;vertical-align:top;width:33%;">
                <b style="color:#BF360C;font-size:1rem;">🔴 STEMI</b><br><br>
                <span style="color:#37474F;font-size:0.85rem;line-height:1.8;">
                  <b>นิยาม:</b> ST-Elevation Myocardial Infarction<br>
                  หลอดเลือดหัวใจอุดตันสมบูรณ์ — <b>ฉุกเฉินสูงสุด</b><br><br>
                  <b>รหัส ICD-10:</b><br>
                  I21.0 – Anterior wall STEMI<br>
                  I21.1 – Inferior wall STEMI<br>
                  I21.2 – Other specified STEMI<br>
                  I21.3 – STEMI, unspecified site<br>
                  I22.0 – Subsequent anterior STEMI<br>
                  I22.1 – Subsequent inferior STEMI<br>
                  I22.8 – Subsequent STEMI, other<br>
                  I22.9 – Subsequent STEMI, unspecified<br><br>
                  <b>Door-to-balloon:</b> &lt; 90 นาที<br>
                  <b>Mortality:</b> ~5-10%
                </span>
              </td>
              <td style="background:#FFF8E1;padding:1rem;border-radius:8px;
                         border-left:4px solid #F9A825;vertical-align:top;width:33%;">
                <b style="color:#F57F17;font-size:1rem;">🟡 NSTEMI</b><br><br>
                <span style="color:#37474F;font-size:0.85rem;line-height:1.8;">
                  <b>นิยาม:</b> Non-ST-Elevation Myocardial Infarction<br>
                  มีการตายของกล้ามเนื้อหัวใจ แต่ไม่มี ST elevation<br><br>
                  <b>รหัส ICD-10:</b><br>
                  I21.4 – NSTEMI (specific)<br>
                  I21.9 – Acute MI, unspecified<br>
                  I22.2 – Subsequent NSTEMI<br><br>
                  <b>เป้าหมาย:</b> Early invasive &lt; 24-72 ชม.<br>
                  <b>Mortality:</b> ~3-5%<br><br>
                  <b>หมายเหตุ:</b> I21.9 ใช้เมื่อยังไม่ระบุประเภท
                </span>
              </td>
              <td style="background:#E8F5E9;padding:1rem;border-radius:8px;
                         border-left:4px solid #388E3C;vertical-align:top;width:33%;">
                <b style="color:#2E7D32;font-size:1rem;">🟢 Unstable Angina (UA)</b><br><br>
                <span style="color:#37474F;font-size:0.85rem;line-height:1.8;">
                  <b>นิยาม:</b> เจ็บหน้าอกไม่คงที่ ยังไม่มีการตายของกล้ามเนื้อหัวใจ<br>
                  (Troponin ไม่สูง)<br><br>
                  <b>รหัส ICD-10:</b><br>
                  I20.0 – Unstable angina<br>
                  I24.0 – Coronary thrombosis (no MI)<br>
                  I24.8 – Other acute ischaemic HD<br>
                  I24.9 – Acute ischaemic HD, unspecified<br><br>
                  <b>เป้าหมาย:</b> Risk stratify + Medical therapy<br>
                  <b>Mortality:</b> ~1-3%
                </span>
              </td>
            </tr>
            </table>
            <div style="margin-top:0.8rem;padding:0.6rem 1rem;
                        background:rgba(33,33,33,0.05);border-radius:6px;
                        border-left:3px solid #FF8F00;">
              <span style="color:#E65100;font-size:0.85rem;">
                ⚠️ <b>ความแตกต่างสำคัญ NSTEMI vs UA:</b>
                NSTEMI มี Troponin สูง (มีการตายของกล้ามเนื้อ) —
                UA Troponin ปกติ — การแยกต้องใช้ Lab ร่วมด้วย
              </span>
            </div>
            """, unsafe_allow_html=True)
        
        # สร้าง ACS Matrix 3 ประเภท
        df_acs = build_matrix_3(
            df_sa,
            STEMI_CODES, NSTEMI_CODES, UA_CODES,
            'STEMI', 'NSTEMI', 'UA'
        )
        
        # KPI ACS — 6 metrics
        if not df_acs.empty:
            total_row_a = df_acs[df_acs['Ward'] == '🔷 Total'].iloc[0] \
                          if len(df_acs[df_acs['Ward'] == '🔷 Total']) > 0 else None
            if total_row_a is not None:
                tot_a    = int(total_row_a['Total_n'])
                stemi_n  = int(total_row_a['STEMI_n'])
                nstemi_n = int(total_row_a['NSTEMI_n'])
                ua_n     = int(total_row_a['UA_n'])
                stemi_d  = int(total_row_a['STEMI_death'])
                nstemi_d = int(total_row_a['NSTEMI_death'])
                ua_d     = int(total_row_a['UA_death'])
        
                ka1, ka2, ka3, ka4, ka5, ka6, ka7 = st.columns(7)
                ka1.metric("❤️ ACS ทั้งหมด", f"{tot_a} ราย",
                           help="STEMI + NSTEMI + UA")
                ka2.metric("🔴 STEMI", f"{stemi_n} ราย",
                           f"{stemi_n/tot_a*100:.1f}%" if tot_a else "0%",
                           help="I21.0-I21.3, I22.0-I22.9")
                ka3.metric("🟡 NSTEMI", f"{nstemi_n} ราย",
                           f"{nstemi_n/tot_a*100:.1f}%" if tot_a else "0%",
                           help="I21.4, I21.9, I22.2")
                ka4.metric("🟢 UA", f"{ua_n} ราย",
                           f"{ua_n/tot_a*100:.1f}%" if tot_a else "0%",
                           help="I20.0, I24.0, I24.8, I24.9")
                ka5.metric("💀 ตาย STEMI", f"{stemi_d} ราย",
                           f"{stemi_d/stemi_n*100:.1f}%" if stemi_n else "0%",
                           delta_color="inverse")
                ka6.metric("💀 ตาย NSTEMI", f"{nstemi_d} ราย",
                           f"{nstemi_d/nstemi_n*100:.1f}%" if nstemi_n else "0%",
                           delta_color="inverse")
                ka7.metric("💀 ตาย UA", f"{ua_d} ราย",
                           f"{ua_d/ua_n*100:.1f}%" if ua_n else "0%",
                           delta_color="inverse")
        
        # แสดงตาราง
        html_acs = render_three_type_table(
            df_acs, 'STEMI', 'NSTEMI', 'UA',
            '#BF360C', '#F9A825', '#388E3C',
            '🔴', '🟡', '🟢'
        )
        components.html(
            f"<div style='font-family:sans-serif;font-size:14px;'>{html_acs}</div>",
            height=320,
            scrolling=False
        )
        
        # Download
        if not df_acs.empty:
            csv_a = df_acs.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                "📥 ดาวน์โหลด ACS CSV", csv_a,
                f"acs_summary_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                "text/csv", key='dl_acs'
            )
        
        # Stacked Bar — 3 ประเภท
        acs_chart_rows = []
        if not df_acs.empty:
            for _, row in df_acs.iterrows():
                if 'Total' not in str(row['Ward']):
                    for lbl in ['STEMI', 'NSTEMI', 'UA']:
                        acs_chart_rows.append({
                            'Ward': row['Ward'], 'ประเภท': lbl, 'จำนวน': row[f'{lbl}_n']
                        })
        
        df_acs_chart = pd.DataFrame(acs_chart_rows)
        if not df_acs_chart.empty and df_acs_chart['จำนวน'].sum() > 0:
            ch_acs = alt.Chart(df_acs_chart).mark_bar(
                cornerRadiusTopLeft=4, cornerRadiusTopRight=4
            ).encode(
                x=alt.X('Ward:N', title='หอผู้ป่วย', sort=WARD_ORDER_5),
                y=alt.Y('จำนวน:Q', title='จำนวนราย', stack=True),
                color=alt.Color('ประเภท:N',
                    scale=alt.Scale(
                        domain=['STEMI', 'NSTEMI', 'UA'],
                        range=['#BF360C', '#F9A825', '#388E3C']
                    ),
                    legend=alt.Legend(title='ประเภท ACS')
                ),
                tooltip=['Ward', 'ประเภท', 'จำนวน']
            ).properties(height=260)
            st.altair_chart(ch_acs, use_container_width=True)
        else:
            st.info("ℹ️ ไม่มีข้อมูล ACS ในช่วงเวลาที่เลือก")

        # ── ข้อมูลดิบ Stroke แยก Ward ──────────────────────────────
        st.markdown("---")
        st.markdown("#### 📋 ข้อมูลดิบ Stroke แยกตาม Ward")
        
        if 'pdx' in df_sa.columns:
            # สร้าง flag ประเภท Stroke
            df_stroke_raw = df_sa.copy()
            df_stroke_raw['Stroke_Type'] = None
            df_stroke_raw.loc[df_stroke_raw['pdx'].apply(
                lambda x: starts_with_any(x, ISCHEMIC_CODES)), 'Stroke_Type'] = '🔵 Ischemic'
            df_stroke_raw.loc[df_stroke_raw['pdx'].apply(
                lambda x: starts_with_any(x, HEMORRHAGIC_CODES)), 'Stroke_Type'] = '🔴 Hemorrhagic'
        
            # กรองเฉพาะ Stroke
            df_stroke_raw = df_stroke_raw[df_stroke_raw['Stroke_Type'].notna()].copy()
            df_stroke_raw['ward_group'] = df_stroke_raw['ward_name'].apply(get_ward_group5) \
                                          if 'ward_name' in df_stroke_raw.columns else None
            df_stroke_raw['เสียชีวิต'] = df_stroke_raw['discharge_status'].str.contains(
                'ตาย', na=False).map({True: '💀 ใช่', False: '—'})
        
            # แปลง month_year
            if 'month_year' in df_stroke_raw.columns:
                df_stroke_raw['month_year'] = pd.to_datetime(
                    df_stroke_raw['month_year'], errors='coerce'
                ).dt.strftime('%b %Y')
        
            # แปลงวันที่
            for date_col in ['admit_date', 'discharge_date']:
                if date_col in df_stroke_raw.columns:
                    df_stroke_raw[date_col] = pd.to_datetime(
                        df_stroke_raw[date_col], errors='coerce'
                    ).dt.strftime('%d/%m/%Y')
        
            # คอลัมน์ที่แสดง
            show_cols_stroke = ['month_year', 'hn', 'an', 'age', 'sex',
                                'Stroke_Type', 'pdx',
                                'admit_date', 'discharge_date', 'length_of_stay',
                                'discharge_status', 'เสียชีวิต', 'ward_name', 'adjrw']
            show_cols_stroke = [c for c in show_cols_stroke if c in df_stroke_raw.columns]
        
            # column_config
            stroke_col_config = {
                "month_year":       st.column_config.TextColumn("เดือน"),
                "hn":               st.column_config.TextColumn("HN"),
                "an":               st.column_config.TextColumn("AN"),
                "age":              st.column_config.NumberColumn("อายุ", format="%d ปี"),
                "Stroke_Type":      st.column_config.TextColumn("ประเภท Stroke"),
                "pdx":              st.column_config.TextColumn("ICD-10"),
                "admit_date":       st.column_config.TextColumn("วันที่ admit"),
                "discharge_date":   st.column_config.TextColumn("วันที่จำหน่าย"),
                "length_of_stay":   st.column_config.NumberColumn("LOS", format="%d วัน"),
                "adjrw":            st.column_config.NumberColumn("adjRW", format="%.2f"),
                "เสียชีวิต":        st.column_config.TextColumn("เสียชีวิต"),
            }
        
            # แสดงแยก Ward
            ward_list_stroke = ['ER', 'MB2', 'MB4', 'MB5', 'VIP', 'ICU']
            for ward in ward_list_stroke:
                ward_df_s = df_stroke_raw[df_stroke_raw['ward_group'] == ward]
                if ward_df_s.empty:
                    continue
        
                n_total_s = len(ward_df_s)
                n_isc     = (ward_df_s['Stroke_Type'] == '🔵 Ischemic').sum()
                n_hem     = (ward_df_s['Stroke_Type'] == '🔴 Hemorrhagic').sum()
                n_death_s = ward_df_s['discharge_status'].str.contains('ตาย', na=False).sum()
        
                with st.expander(
                    f"🏥 {ward} — รวม {n_total_s} ราย | "
                    f"Ischemic {n_isc} · Hemorrhagic {n_hem} | "
                    f"💀 เสียชีวิต {n_death_s} ราย",
                    expanded=False
                ):
                    # KPI
                    ks1, ks2, ks3, ks4 = st.columns(4)
                    ks1.metric("👥 ทั้งหมด",       f"{n_total_s} ราย")
                    ks2.metric("🔵 Ischemic",      f"{n_isc} ราย",
                               f"{n_isc/n_total_s*100:.1f}%" if n_total_s else "0%")
                    ks3.metric("🔴 Hemorrhagic",   f"{n_hem} ราย",
                               f"{n_hem/n_total_s*100:.1f}%" if n_total_s else "0%")
                    ks4.metric("💀 เสียชีวิต",     f"{n_death_s} ราย",
                               f"{n_death_s/n_total_s*100:.1f}%" if n_total_s else "0%",
                               delta_color="inverse")
        
                    st.markdown("**รายชื่อผู้ป่วย:**")
                    st.dataframe(
                        ward_df_s[show_cols_stroke].sort_values(
                            'Stroke_Type'
                        ).reset_index(drop=True),
                        use_container_width=True,
                        hide_index=True,
                        column_config=stroke_col_config
                    )
        
                    csv_stroke_ward = ward_df_s[show_cols_stroke].to_csv(
                        index=False, encoding='utf-8-sig'
                    ).encode('utf-8-sig')
                    st.download_button(
                        f"📥 ดาวน์โหลด {ward} CSV",
                        csv_stroke_ward,
                        f"stroke_{ward}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        key=f'dl_stroke_ward_{ward}'
                    )
        
            # ── expander รวมทุก Ward ──
            with st.expander(
                f"🔷 ทุก Ward รวม — {len(df_stroke_raw)} ราย | "
                f"💀 เสียชีวิต "
                f"{df_stroke_raw['discharge_status'].str.contains('ตาย', na=False).sum()} ราย",
                expanded=False
            ):
                df_stroke_display = df_stroke_raw.sort_values(
                    ['ward_group', 'Stroke_Type']
                )[show_cols_stroke].reset_index(drop=True)
        
                st.dataframe(
                    df_stroke_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config=stroke_col_config
                )
        
                csv_stroke_all = df_stroke_display.to_csv(
                    index=False, encoding='utf-8-sig'
                ).encode('utf-8-sig')
                st.download_button(
                    "📥 ดาวน์โหลดทั้งหมด CSV",
                    csv_stroke_all,
                    f"stroke_all_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    key='dl_stroke_all'
                )
        
        else:
            st.info("ไม่พบคอลัมน์ pdx")


        # ── ข้อมูลดิบแยก Ward ──────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📋 ข้อมูลดิบ ACS แยกตาม Ward")
        
        if 'pdx' in df_sa.columns:
            # สร้าง flag ประเภท ACS
            df_acs_raw = df_sa.copy()
            df_acs_raw['ACS_Type'] = None
            df_acs_raw.loc[df_acs_raw['pdx'].apply(
                lambda x: starts_with_any(x, STEMI_CODES)), 'ACS_Type'] = '🔴 STEMI'
            df_acs_raw.loc[df_acs_raw['pdx'].apply(
                lambda x: starts_with_any(x, NSTEMI_CODES)), 'ACS_Type'] = '🟡 NSTEMI'
            df_acs_raw.loc[df_acs_raw['pdx'].apply(
                lambda x: starts_with_any(x, UA_CODES)), 'ACS_Type'] = '🟢 UA'
        
            # กรองเฉพาะ ACS
            df_acs_raw = df_acs_raw[df_acs_raw['ACS_Type'].notna()].copy()
            df_acs_raw['ward_group'] = df_acs_raw['ward_name'].apply(get_ward_group5) \
                                       if 'ward_name' in df_acs_raw.columns else None
            df_acs_raw['เสียชีวิต'] = df_acs_raw['discharge_status'].str.contains(
                'ตาย', na=False).map({True: '💀 ใช่', False: '—'})

                # ✅ วางตรงนี้ — ต่อจากบรรทัด เสียชีวิต
            if 'month_year' in df_acs_raw.columns:
                df_acs_raw['month_year'] = pd.to_datetime(
                    df_acs_raw['month_year'], errors='coerce'
                ).dt.strftime('%b %Y')
                
            # คอลัมน์ที่แสดง
           
            show_cols = ['month_year', 'hn', 'an', 'age', 'sex', 'ACS_Type', 'pdx',
                         'admit_date', 'discharge_date', 'length_of_stay',
                         'discharge_status', 'เสียชีวิต', 'ward_name', 'adjrw']
            
            show_cols = [c for c in show_cols if c in df_acs_raw.columns]
        
            # แสดงแยก ward
            ward_list = ['ER', 'MB2', 'MB4', 'MB5', 'VIP', 'ICU']
 

            for ward in ward_list:
                    ward_df = df_acs_raw[df_acs_raw['ward_group'] == ward]
                    if ward_df.empty:
                        continue
            
                    n_total  = len(ward_df)
                    n_stemi  = (ward_df['ACS_Type'] == '🔴 STEMI').sum()
                    n_nstemi = (ward_df['ACS_Type'] == '🟡 NSTEMI').sum()
                    n_ua     = (ward_df['ACS_Type'] == '🟢 UA').sum()
                    n_death  = ward_df['discharge_status'].str.contains('ตาย', na=False).sum()
            
                    with st.expander(
                        f"🏥 {ward} — รวม {n_total} ราย | "
                        f"STEMI {n_stemi} · NSTEMI {n_nstemi} · UA {n_ua} | "
                        f"💀 เสียชีวิต {n_death} ราย",
                        expanded=False
                    ):
                        # ✅ วางตรงนี้ — แปลงวันที่ก่อนแสดงผล
                        ward_df = ward_df.copy()
                        for date_col in ['admit_date', 'discharge_date']:
                            if date_col in ward_df.columns:
                                ward_df[date_col] = pd.to_datetime(
                                    ward_df[date_col], errors='coerce'
                                ).dt.strftime('%d/%m/%Y')
            
                        col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
                        col_s1.metric("👥 ทั้งหมด",  f"{n_total} ราย")
                        col_s2.metric("🔴 STEMI",    f"{n_stemi} ราย")
                        col_s3.metric("🟡 NSTEMI",   f"{n_nstemi} ราย")
                        col_s4.metric("🟢 UA",       f"{n_ua} ราย")
                        col_s5.metric("💀 เสียชีวิต",
                                      f"{n_death} ราย",
                                      f"{n_death/n_total*100:.1f}%" if n_total else "0%",
                                      delta_color="inverse")
            
                        st.markdown("**รายชื่อผู้ป่วย:**")
                        st.dataframe(
                            ward_df[show_cols].sort_values('ACS_Type').reset_index(drop=True),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "month_year":     st.column_config.TextColumn("เดือน"),
                                "hn":             st.column_config.TextColumn("HN"),
                                "an":             st.column_config.TextColumn("AN"),
                                "age":            st.column_config.NumberColumn("อายุ", format="%d ปี"),
                                "ACS_Type":       st.column_config.TextColumn("ประเภท ACS"),
                                "pdx":            st.column_config.TextColumn("ICD-10"),
                                "admit_date":     st.column_config.TextColumn("วันที่ admit"),
                                "discharge_date": st.column_config.TextColumn("วันที่จำหน่าย"),
                                "length_of_stay": st.column_config.NumberColumn("LOS", format="%d วัน"),
                                "adjrw":          st.column_config.NumberColumn("adjRW", format="%.2f"),
                                "เสียชีวิต":      st.column_config.TextColumn("เสียชีวิต"),
                            }
                        )
            
                        csv_ward = ward_df[show_cols].to_csv(
                            index=False, encoding='utf-8-sig'
                        ).encode('utf-8-sig')
                        st.download_button(
                            f"📥 ดาวน์โหลด {ward} CSV",
                            csv_ward,
                            f"acs_{ward}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                            "text/csv",
                            key=f'dl_acs_ward_{ward}'
                        )
            
                # ── expander รวมทุก Ward ──────────────────────────────
            with st.expander(
                f"🔷 ทุก Ward รวม — {len(df_acs_raw)} ราย | "
                f"💀 เสียชีวิต "
                f"{df_acs_raw['discharge_status'].str.contains('ตาย', na=False).sum()} ราย",
                expanded=False
            ):
                    # ✅ วางตรงนี้ด้วย — แปลงวันที่ก่อนแสดงผล
                    df_acs_display = df_acs_raw.copy()
                    for date_col in ['admit_date', 'discharge_date']:
                        if date_col in df_acs_display.columns:
                            df_acs_display[date_col] = pd.to_datetime(
                                df_acs_display[date_col], errors='coerce'
                            ).dt.strftime('%d/%m/%Y')
            
                    df_display = df_acs_display.sort_values('ACS_Type')
                    df_display = df_display[show_cols].reset_index(drop=True)
            
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "hn":             st.column_config.TextColumn("HN"),
                            "an":             st.column_config.TextColumn("AN"),
                            "age":            st.column_config.NumberColumn("อายุ", format="%d ปี"),
                            "ACS_Type":       st.column_config.TextColumn("ประเภท ACS"),
                            "pdx":            st.column_config.TextColumn("ICD-10"),
                            "admit_date":     st.column_config.TextColumn("วันที่ admit"),
                            "discharge_date": st.column_config.TextColumn("วันที่จำหน่าย"),
                            "length_of_stay": st.column_config.NumberColumn("LOS", format="%d วัน"),
                            "adjrw":          st.column_config.NumberColumn("adjRW", format="%.2f"),
                            "เสียชีวิต":      st.column_config.TextColumn("เสียชีวิต"),
                        }
                    )
            
                    csv_all = df_acs_display[show_cols].to_csv(
                        index=False, encoding='utf-8-sig'
                    ).encode('utf-8-sig')
                    st.download_button(
                        "📥 ดาวน์โหลดทั้งหมด CSV",
                        csv_all,
                        f"acs_all_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        key='dl_acs_all'
                    )

        
        else:
            st.info("ไม่พบคอลัมน์ pdx")
 
        # ── ค้นหา Bruise/Hematoma จาก dx columns โดยตรง ──

        st.markdown("---")
        st.markdown("#### 🩸 ประมาณการ Bruise/Hematoma จาก Enoxaparin (ICU)")

        with st.expander("📖 วิธีคำนวณและข้อจำกัด", expanded=False):
            st.markdown("""
            <div style="font-family:sans-serif;">
        
            <div style="background:linear-gradient(135deg,#E3F2FD,#BBDEFB);
                        padding:1rem 1.5rem;border-radius:10px;margin-bottom:1rem;">
                <h4 style="color:#1565C0;margin:0 0 0.5rem 0;">📐 สูตรคำนวณ</h4>
                <div style="background:white;padding:1rem;border-radius:8px;
                            text-align:center;font-size:1.1rem;">
                    <b style="color:#1565C0;">อัตรา Bruise/Hematoma (%)</b>
                    <br><br>
                    <span style="font-size:1.3rem;">
                        = 
                        <span style="border-bottom:2px solid #1565C0;padding:0 0.5rem;">
                            ผู้ป่วย ICU ที่มี Enoxaparin Indication <b>และ</b> พบ Bruise/Hematoma
                        </span>
                        <br>
                        &nbsp;&nbsp;&nbsp;ผู้ป่วย ICU ที่มี Enoxaparin Indication ทั้งหมด
                    </span>
                    <br><br>
                    <span style="color:#546E7A;font-size:0.95rem;">× 100</span>
                </div>
            </div>
        
            <table style="width:100%;border-collapse:separate;border-spacing:8px;">
            <tr>
              <td style="background:#E8F5E9;padding:1rem;border-radius:8px;
                         border-left:4px solid #2E7D32;vertical-align:top;width:50%;">
                <b style="color:#2E7D32;">✅ ตัวเศษ (Numerator)</b><br><br>
                <span style="color:#37474F;font-size:0.88rem;line-height:1.8;">
                  ผู้ป่วย ICU ที่มี <b>ครบทั้ง 2 เงื่อนไข</b><br><br>
                  <b>เงื่อนไขที่ 1</b> — มี ICD-10 บ่งชี้ว่าได้ Enoxaparin<br>
                  &nbsp;&nbsp;• I21, I22 — กล้ามเนื้อหัวใจตาย (MI)<br>
                  &nbsp;&nbsp;• I20.0 — Unstable angina<br>
                  &nbsp;&nbsp;• I24 — Acute ischaemic HD<br>
                  &nbsp;&nbsp;• I26 — Pulmonary embolism<br>
                  &nbsp;&nbsp;• I80, I82 — DVT<br>
                  &nbsp;&nbsp;• I48 — Atrial fibrillation<br><br>
                  <b>เงื่อนไขที่ 2</b> — มี ICD-10 บ่งชี้ Bruise/Bleeding<br>
                  &nbsp;&nbsp;• T45.5 — Adverse effect of anticoagulants<br>
                  &nbsp;&nbsp;• L76 — Bruising<br>
                  &nbsp;&nbsp;• R58 — Hemorrhage NEC<br>
                  &nbsp;&nbsp;• D68 — Coagulation defect<br>
                  &nbsp;&nbsp;• S00-S09 — Superficial injury
                </span>
              </td>
        
              <td style="background:#FFF3E0;padding:1rem;border-radius:8px;
                         border-left:4px solid #F57C00;vertical-align:top;width:50%;">
                <b style="color:#E65100;">📊 ตัวส่วน (Denominator)</b><br><br>
                <span style="color:#37474F;font-size:0.88rem;line-height:1.8;">
                  ผู้ป่วย ICU ทั้งหมดที่มี <b>Enoxaparin Indication</b><br>
                  (มี ICD-10 ข้อใดข้อหนึ่งจากรายการเงื่อนไขที่ 1)<br><br>
                  <b>ตัวอย่าง:</b><br>
                  ผู้ป่วย ICU ทั้งหมด = 50 ราย<br>
                  มี Enoxaparin Indication = 30 ราย<br>
                  พบ Bruise + Indication = 3 ราย<br><br>
                  <b style="color:#E65100;font-size:1.1rem;">
                    อัตรา = 3/30 × 100 = 10%
                  </b>
                </span>
              </td>
            </tr>
            </table>
        
            <div style="background:#FFEBEE;padding:1rem;border-radius:8px;
                        border-left:4px solid #C62828;margin-top:1rem;">
                <b style="color:#C62828;">⚠️ ข้อจำกัดสำคัญ — ต้องแจ้งเมื่อรายงาน</b>
                <br><br>
                <table style="width:100%;font-size:0.88rem;border-collapse:collapse;">
                <tr style="background:#FFCDD2;">
                    <th style="padding:0.5rem;text-align:left;">ข้อจำกัด</th>
                    <th style="padding:0.5rem;text-align:left;">ผลกระทบ</th>
                    <th style="padding:0.5rem;text-align:left;">ทิศทาง</th>
                </tr>
                <tr style="background:white;">
                    <td style="padding:0.5rem;">ผู้ป่วยได้ Enoxaparin จริงแต่ไม่มี ICD-10 indication</td>
                    <td style="padding:0.5rem;">ตัวส่วนน้อยกว่าจริง</td>
                    <td style="padding:0.5rem;color:#C62828;">อัตราสูงเกินจริง ↑</td>
                </tr>
                <tr style="background:#FFEBEE;">
                    <td style="padding:0.5rem;">Bruise เล็กน้อยไม่ได้ลง ICD-10</td>
                    <td style="padding:0.5rem;">ตัวเศษน้อยกว่าจริง</td>
                    <td style="padding:0.5rem;color:#1976D2;">อัตราต่ำกว่าจริง ↓</td>
                </tr>
                <tr style="background:white;">
                    <td style="padding:0.5rem;">Coder ลง T45.5 ไม่ครบ</td>
                    <td style="padding:0.5rem;">ตัวเศษน้อยกว่าจริง</td>
                    <td style="padding:0.5rem;color:#1976D2;">อัตราต่ำกว่าจริง ↓</td>
                </tr>
                </table>
            </div>
        
            <div style="background:#E8F5E9;padding:0.8rem 1rem;border-radius:8px;
                        border-left:4px solid #4CAF50;margin-top:1rem;">
                <b style="color:#2E7D32;">💡 วิธีรายงานที่แนะนำ</b><br>
                <span style="color:#37474F;font-size:0.88rem;">
                "อัตรา Bruise/Hematoma จาก Enoxaparin = <b>X%</b>
                <br>
                (ประมาณการจาก ICD-10 เท่านั้น — ไม่ใช่ข้อมูล ADR จริง
                อาจต่ำกว่าความเป็นจริง เนื่องจากไม่มีการบันทึก ADR อย่างเป็นระบบ
                ในช่วงเวลาดังกล่าว)"
                </span>
            </div>
        
            </div>
            """, unsafe_allow_html=True)

        
        # ── กลุ่ม 1: ผู้ป่วยที่น่าจะได้ Enoxaparin ──
        ENOX_INDICATION_CODES = [
            # ACS
            'I21', 'I22',           # MI
            'I20.0',                # Unstable angina
            'I24',                  # Acute ischaemic HD
            # VTE
            'I26',                  # Pulmonary embolism
            'I80', 'I82',           # DVT
            # AF
            'I48',
        ]
        
        # ── กลุ่ม 2: รหัส Bruise/Hematoma/Bleeding ──
        BRUISE_CODES = [
            'T45.5',                # Adverse effect of anticoagulants
            'T45.51',
            'T45.515',
            'L76',                  # Bruising
            'S00', 'S09',           # Superficial injury
            'M79.3',                # Panniculitis (injection site)
            'D68',                  # Coagulation defect
            'R58',                  # Hemorrhage NEC
            'T14.0',                # Superficial injury unspecified
        ]
        
        if 'pdx' in df_sa.columns:
            # ── Filter เฉพาะ ICU ──
            df_icu = df_sa[
                df_sa['ward_name'].str.strip() == 'หอผู้ป่วยหนัก ICU'
            ].copy()
        
            all_dx_cols = ['pdx'] + [f'dx{i}' for i in range(11)]
            all_dx_cols = [c for c in all_dx_cols if c in df_icu.columns]
        
            # หาผู้ป่วยที่มี indication สำหรับ enoxaparin
            def has_enox_indication(row):
                for col in all_dx_cols:
                    val = str(row.get(col, '') or '')
                    if any(val.startswith(c) for c in ENOX_INDICATION_CODES):
                        return True
                return False
        
            # หาผู้ป่วยที่มี bruise/hematoma/bleeding
            def has_bruise(row):
                for col in all_dx_cols:
                    val = str(row.get(col, '') or '')
                    if any(val.startswith(c) for c in BRUISE_CODES):
                        return True
                return False
        
            df_icu['enox_indication'] = df_icu.apply(has_enox_indication, axis=1)
            df_icu['has_bruise']      = df_icu.apply(has_bruise, axis=1)
            df_icu['both']            = df_icu['enox_indication'] & df_icu['has_bruise']
        
            n_icu_total  = len(df_icu)
            n_enox       = df_icu['enox_indication'].sum()
            n_bruise     = df_icu['has_bruise'].sum()
            n_both       = df_icu['both'].sum()
            rate         = (n_both / n_enox * 100) if n_enox else 0
        
            # ── KPI ──
            kb1, kb2, kb3, kb4 = st.columns(4)
            kb1.metric("🏥 ผู้ป่วย ICU ทั้งหมด", f"{n_icu_total} ราย")
            kb2.metric("💉 มี Indication Enoxaparin", f"{n_enox} ราย",
                       f"{n_enox/n_icu_total*100:.1f}%" if n_icu_total else "0%")
            kb3.metric("🩸 พบ Bruise/Hematoma/Bleeding", f"{n_bruise} ราย")
            kb4.metric("⚠️ Enoxaparin + Bruise (ประมาณการ)", f"{n_both} ราย",
                       f"อัตรา {rate:.1f}%",
                       delta_color="inverse")
        
            # ── คำเตือน ──
            st.markdown(f"""
            <div style="background:#FFF3E0;padding:1rem;border-radius:8px;
                        border-left:4px solid #FF9800;margin:1rem 0;">
                <b style="color:#E65100;">⚠️ ข้อจำกัดของการประมาณการนี้</b><br>
                <span style="color:#37474F;font-size:0.9rem;">
                • ใช้ <b>ICD-10 secondary diagnosis</b> เป็นตัวแทน
                  ไม่ใช่ข้อมูล ADR จริง<br>
                • ผู้ป่วยที่ได้ Enoxaparin จริงอาจมากกว่า/น้อยกว่าที่ประมาณ<br>
                • Bruise ที่ไม่ได้ลง code จะไม่ถูกนับ<br>
                • <b>ควรใช้เป็นข้อมูลเบื้องต้นเท่านั้น</b>
                  และเริ่มเก็บข้อมูลจริงตั้งแต่เดือนนี้
                </span>
            </div>
            """, unsafe_allow_html=True)
        
            st.markdown("---")
        
            # ── ตารางรายเดือน ──
            st.markdown("#### 📅 แนวโน้มรายเดือน")
        
            if 'month_sort' in df_icu.columns:
                monthly_rows = []
                for period, grp in df_icu.groupby('month_sort'):
                    ml   = grp['month_label'].iloc[0] if 'month_label' in grp.columns else str(period)
                    n_e  = grp['enox_indication'].sum()
                    n_b  = grp['both'].sum()
                    r    = (n_b / n_e * 100) if n_e else 0
                    monthly_rows.append({
                        'เดือน':                    ml,
                        'ผู้ป่วย ICU':              len(grp),
                        'Enoxaparin Indication':    int(n_e),
                        'Bruise/Hematoma (ประมาณ)': int(n_b),
                        'อัตรา (%)':               round(r, 1),
                    })
        
                df_monthly_bruise = pd.DataFrame(monthly_rows)
                st.dataframe(df_monthly_bruise, use_container_width=True, hide_index=True)
        
                # กราฟ
                if not df_monthly_bruise.empty:
                    ch_bruise = alt.Chart(df_monthly_bruise).mark_line(
                        point=True, strokeWidth=2, color='#E53935'
                    ).encode(
                        x=alt.X('เดือน:N', title='เดือน'),
                        y=alt.Y('อัตรา (%):Q', title='อัตรา (%)',
                                scale=alt.Scale(zero=True)),
                        tooltip=['เดือน', 'Enoxaparin Indication',
                                 'Bruise/Hematoma (ประมาณ)', 'อัตรา (%)']
                    ).properties(height=250,
                                 title='อัตรา Bruise/Hematoma (ประมาณการ) รายเดือน')
                    st.altair_chart(ch_bruise, use_container_width=True)
        
            # ── รายชื่อผู้ป่วย ──
            st.markdown("---")
            with st.expander("📋 รายชื่อผู้ป่วย ICU ที่มี Enoxaparin Indication + Bruise/Hematoma",
                             expanded=False):
                if df_icu['both'].any():
                    show_b = ['hn', 'an', 'age', 'sex', 'pdx'] + \
                             [f'dx{i}' for i in range(5)] + \
                             ['admit_date', 'discharge_date',
                              'length_of_stay', 'discharge_status', 'adjrw']
                    show_b = [c for c in show_b if c in df_icu.columns]
        
                    st.dataframe(
                        df_icu[df_icu['both']][show_b].reset_index(drop=True),
                        use_container_width=True,
                        hide_index=True
                    )
        
                    csv_b = df_icu[df_icu['both']][show_b].to_csv(
                        index=False, encoding='utf-8-sig'
                    ).encode('utf-8-sig')
                    st.download_button(
                        "📥 ดาวน์โหลด CSV",
                        csv_b,
                        f"enox_bruise_icu_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        key='dl_enox_bruise'
                    )
                else:
                    st.info("ℹ️ ไม่พบผู้ป่วยที่มีทั้ง Enoxaparin Indication และ Bruise/Hematoma")
        
        else:
            st.info("ไม่พบคอลัมน์ pdx")





        
        # ── คำแนะนำ Quality Indicators ────────────────────────────
        st.markdown("---")
        st.markdown("""
        #### 📌 Quality Indicators ที่ควรติดตาม
        | ตัวชี้วัด | Stroke | ACS |
        |-----------|--------|-----|
        | **Time to Treatment** | Door-to-needle (tPA) < 60 นาที | Door-to-balloon < 90 นาที |
        | **Mortality Rate** | Ischemic < 10% · Hemorrhagic < 30% | STEMI < 10% · NSTEMI < 5% |
        | **Readmission 28 วัน** | < 15% | < 10% |
        | **LOS** | 5-7 วัน | 3-5 วัน |
        | **Coding ถูกต้อง** | I63 vs I64 ระบุให้ชัด | I21.x ระบุ site ให้ครบ |
        """)
    # ════════════════════════════════════════════════════
    # [จบ TAB 4]
    # ════════════════════════════════════════════════════


    
    # ════════════════════════════════════════════════════
    # TAB 5 : เชิงลึก
    # ════════════════════════════════════════════════════
    with tab5:
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

        sub1, sub2, sub3, sub4 = st.tabs([
            "💰 adjRW / CMI", "🛏 LOS Outlier",
            "🪪 สิทธิ์การรักษา", "🌏 แรงงานต่างด้าว"
        ])

        # ── sub1: adjRW / CMI ──
        with sub1:
            st.markdown("#### 🏆 Top 10 โรค by Total adjRW")
            if 'pdx' in df_all.columns and 'adjrw' in df_all.columns:
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
            if 'month_label' in df_all.columns and 'adjrw' in df_all.columns:
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
            
            threshold = st.slider(
                "กำหนด LOS threshold (วัน)", 
                7, 60, 30,
                help="🛏️ **กำหนดจำนวนวันขั้นต่ำที่ถือว่า 'นอนนาน'**\n\n🔹 **7-14 วัน:** Long stay\n🔹 **15-29 วัน:** Very long stay\n🔹 **30+ วัน:** Outlier (ควรตรวจสอบ)\n\n💡 **LOS นานมาก** อาจเกิดจาก:\n   • Chronic care\n   • Complication\n   • Social admission\n   • Waiting for transfer"
            )

  
            if threshold <= 10:
                level, color, msg = "🟡 Low", "#F9A825", "เห็นผู้ป่วยจำนวนมาก — เหมาะสำหรับ IC Surveillance"
            elif threshold <= 20:
                level, color, msg = "🟠 Medium", "#F57C00", "เหมาะสำหรับ Sub-acute / Chronic care review"
            elif threshold <= 35:
                level, color, msg = "🔵 Standard", "#1976D2", "เกณฑ์มาตรฐานทั่วไป — เหมาะสำหรับรายงานผู้บริหาร"
            else:
                level, color, msg = "🔴 Strict", "#C62828", "เฉพาะรายที่นอนนานมากผิดปกติ"
            
            st.markdown(f"""
            <div style="background:#F5F5F5;padding:0.6rem 1rem;border-radius:8px;
                        border-left:4px solid {color};margin-bottom:1rem;">
                <span style="color:{color};font-weight:700;">{level}</span>
                <span style="color:#546E7A;font-size:0.9rem;margin-left:0.5rem;">{msg}</span>
            </div>
            """, unsafe_allow_html=True)           
            if 'length_of_stay' in df_all.columns:
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
                f1.metric("👥 จำนวน", f"{len(df_foreign):,} ราย")
                f2.metric("💰 adjRW รวม", f"{df_foreign['adjrw'].sum():.1f}" if 'adjrw' in df_foreign.columns else "N/A")
                f3.metric("🛏 LOS เฉลี่ย", f"{df_foreign['length_of_stay'].mean():.1f} วัน" if 'length_of_stay' in df_foreign.columns else "N/A")

                st.markdown("---")
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    st.markdown("**Top 10 โรค**")
                    if 'pdx' in df_foreign.columns:
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
                    if 'discharge_status' in df_foreign.columns:
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
            "📥 นำเข้าข้อมูล": "Data Import & Validation"
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



        # ========================================
        # SECTION 1: PRIMARY KPIs (ระดับ C-Level)
        # ========================================
  
        
        # ✅ เพิ่มส่วนนี้ (Info Banner สั้น ๆ)
        st.markdown("""
            <div style="background:linear-gradient(135deg, #E3F2FD 0%, #F3E5F5 100%);
                        padding:0.8rem 1.2rem;border-radius:8px;margin-bottom:1.5rem;
                        border-left:4px solid #1565C0;">
                <div style="display:flex;align-items:center;gap:0.8rem;">
                    <div style="font-size:1.5rem;">💡</div>
                    <div style="flex:1;color:#37474F;font-size:0.9rem;">
                        <b>วิธีอ่าน:</b> 
                        <span style="color:#4CAF50;">🟢 สีเขียว (↑)</span> = เพิ่มขึ้น · 
                        <span style="color:#F44336;">🔴 สีแดง (↓)</span> = ลดลง · 
                        <b>Delta</b> = เทียบกับเดือนก่อน · 
                        <span style="color:#1565C0;cursor:pointer;">คลิก <b>ⓘ</b> ข้าง KPI เพื่อดูรายละเอียด</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # ✅ เพิ่มตารางอ้างอิงสั้น ๆ (Optional - แสดงด้านบน KPI)
        col_ref1, col_ref2, col_ref3 = st.columns(3)
        
        with col_ref1:
            st.markdown("""
                <div style="background:#E8F5E9;padding:0.6rem 1rem;border-radius:6px;text-align:center;">
                    <div style="color:#2E7D32;font-size:0.75rem;font-weight:600;">✅ ยิ่งสูงยิ่งดี</div>
                    <div style="color:#546E7A;font-size:0.8rem;margin-top:0.2rem;">
                        Discharges · RW · Turnover
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_ref2:
            st.markdown("""
                <div style="background:#FFF3E0;padding:0.6rem 1rem;border-radius:6px;text-align:center;">
                    <div style="color:#E65100;font-size:0.75rem;font-weight:600;">⚖️ ควรอยู่ในช่วง</div>
                    <div style="color:#546E7A;font-size:0.8rem;margin-top:0.2rem;">
                        CMI: 1.0-1.5 · LOS: 3-5 วัน
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_ref3:
            st.markdown("""
                <div style="background:#FFEBEE;padding:0.6rem 1rem;border-radius:6px;text-align:center;">
                    <div style="color:#C62828;font-size:0.75rem;font-weight:600;">⚠️ ยิ่งต่ำยิ่งดี</div>
                    <div style="color:#546E7A;font-size:0.8rem;margin-top:0.2rem;">
                        Mortality · Readmit
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
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
                delta_color="normal",
                help="📊 **จำนวนผู้ป่วยที่จำหน่ายทั้งหมด**\n\nนับจากผู้ป่วยที่ออกจากโรงพยาบาล (Discharge) ในเดือนล่าสุด รวมทุกสถานะ (กลับบ้าน, ส่งต่อ, เสียชีวิต)\n\n🔹 **Delta:** เปรียบเทียบกับเดือนก่อนหน้า"  # ⬅️ เพิ่มบรรทัดนี้
            )
        
        with k2:
            delta_cmi = cmi_current - cmi_previous
            st.metric(
                "📈 CMI (Case Mix Index)",
                f"{cmi_current:.3f}",
                f"{delta_cmi:+.3f}",
                delta_color="normal",
                help="📈 **ดัชนีความหนักของโรค (Case Mix Index)**\n\nค่าเฉลี่ย Adjusted RW ของผู้ป่วยทั้งหมด บ่งบอกความซับซ้อนของผู้ป่วย\n\n🔹 **CMI สูง** = รักษาผู้ป่วยหนัก/ซับซ้อน\n🔹 **CMI ต่ำ** = รักษาผู้ป่วยเบา\n🔹 **เกณฑ์มาตรฐาน:** 1.0-1.5"  # ⬅️ เพิ่มบรรทัดนี้
            )
        
        with k3:
            delta_rw = total_rw_current - total_rw_previous
            st.metric(
                "💰 Total Adjusted RW",
                f"{total_rw_current:,.1f}",
                f"{delta_rw:+,.1f}",
                delta_color="normal",
                help="💰 **น้ำหนักสัมพัทธ์รวม (Total Adjusted Relative Weight)**\n\nผลรวมของ Adjusted RW ทั้งหมด ใช้คำนวณค่าตอบแทนจาก สปสช.\n\n🔹 **สูตร:** ΣadjRW ทุกราย\n🔹 **ใช้สำหรับ:** คำนวณรายได้จาก DRG Payment\n🔹 **หน่วย:** RW Points"  # ⬅️ เพิ่มบรรทัดนี้
            )
        
        with k4:
            delta_los = los_current - los_previous
            st.metric(
                "🛏️ Average LOS",
                f"{los_current:.1f} days",
                f"{delta_los:+.1f}",
                delta_color="inverse",  # LOS ต่ำกว่าดีกว่า
                help="🛏️ **ระยะเวลานอนโรงพยาบาลเฉลี่ย (Length of Stay)**\n\nจำนวนวันเฉลี่ยที่ผู้ป่วยนอนใน รพ. นับจากวันรับ (Admit) ถึงวันจำหน่าย (Discharge)\n\n🔹 **LOS ต่ำ** = ดีขึ้น (ประสิทธิภาพสูง)\n🔹 **LOS สูง** = ควรตรวจสอบ\n🔹 **เกณฑ์มาตรฐาน:** 3-5 วัน"  # ⬅️ เพิ่มบรรทัดนี้
            )
        
        with k5:
            delta_death_rate = death_rate_current - death_rate_previous
            st.metric(
                "💀 Mortality Rate",
                f"{death_rate_current:.2f}%",
                f"{delta_death_rate:+.2f}%",
                delta_color="inverse",
                help="💀 **อัตราการเสียชีวิต (Mortality Rate)**\n\nเปอร์เซ็นต์ของผู้ป่วยที่เสียชีวิตใน รพ. เทียบกับผู้ป่วยทั้งหมด\n\n🔹 **สูตร:** (จำนวนเสียชีวิต ÷ จำนวนจำหน่าย) × 100\n🔹 **ต่ำกว่า** = ดีขึ้น\n🔹 **เกณฑ์มาตรฐาน:** < 2%"  # ⬅️ เพิ่มบรรทัดนี้
            )
        
        with k6:
            # คำนวณ Bed Turnover Rate (ประมาณการ)
            turnover_current = total_current / 30  # สมมติ 30 เตียง
            st.metric(
                "🔄 Bed Turnover",
                f"{turnover_current:.1f}/day",
                help="🔄 **อัตราการหมุนเวียนเตียง (Bed Turnover Rate)**\n\nจำนวนผู้ป่วยเฉลี่ยที่จำหน่ายต่อวัน สะท้อนการใช้ประโยชน์จากเตียง\n\n🔹 **สูตร:** จำนวนจำหน่าย ÷ จำนวนวันในเดือน\n🔹 **สูงขึ้น** = ใช้เตียงคุ้มค่า\n🔹 **หมายเหตุ:** คำนวณจากจำนวนเตียงโดยประมาณ"  # ⬅️ เพิ่มบรรทัดนี้
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
                        box-shadow:0 4px 16px rgba(0,0,0,0.08);margin-bottom:1rem;">
                <h3 style="color:#1565C0;margin:0 0 0.5rem 0;font-size:1.4rem;font-weight:600;">
                    🎯 Operational Insights
                </h3>
                <p style="color:#546E7A;margin:0;font-size:0.95rem;">
                    ข้อมูลเชิงปฏิบัติการ สำหรับการตัดสินใจระดับหน้างาน
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # ✅ เพิ่มส่วนนี้ (Info Banner คำอธิบาย)
        st.markdown("""
            <div style="background:linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
                        padding:0.8rem 1.2rem;border-radius:8px;margin-bottom:1.5rem;
                        border-left:4px solid #FF9800;">
                <div style="display:flex;align-items:center;gap:0.8rem;">
                    <div style="font-size:1.5rem;">💡</div>
                    <div style="flex:1;color:#37474F;font-size:0.9rem;line-height:1.5;">
                        <b>3 ข้อมูลสำคัญ:</b> 
                        🏆 <b>Top 5 ผู้ป่วยที่มีมูลค่าสูง</b> (adjRW สูงสุด) · 
                        ⚠️ <b>ผู้ป่วยนอนนาน</b> (> 30 วัน ต้องติดตาม) · 
                        🏥 <b>Ward ที่มี CMI สูงสุด</b> (รักษาผู้ป่วยหนัก)
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        col_i1, col_i2, col_i3 = st.columns(3)
        
        with col_i1:
            # ✅ เพิ่มหัวข้อพร้อมคำอธิบาย
            st.markdown("""
                <div style="margin-bottom:0.8rem;">
                    <div style="display:flex;align-items:center;gap:0.5rem;">
                        <h4 style="margin:0;color:#1976D2;font-size:1.1rem;">🏆 Top 5 High-Value Cases</h4>
                    </div>
                    <p style="color:#757575;font-size:0.85rem;margin:0.3rem 0 0.8rem 0;">
                        ผู้ป่วย 5 รายที่มีค่า adjRW สูงสุดในเดือนนี้ (มูลค่างานสูง)
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # Top 5 High-RW Cases
            top_rw = df_current.nlargest(5, 'adjrw')[['pdx', 'adjrw', 'ward_name']]
            if not top_rw.empty:
                for idx, row in enumerate(top_rw.itertuples(), 1):
                    st.markdown(f"""
                        <div style="background:#F5F5F5;padding:0.8rem;border-radius:8px;
                                    margin-bottom:0.5rem;border-left:4px solid #1976D2;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
                                <b style="color:#1976D2;">#{idx}</b>
                                <span style="color:#1976D2;font-weight:600;font-size:1.1rem;">
                                    RW: {row.adjrw:.2f}
                                </span>
                            </div>
                            <div style="color:#37474F;font-size:0.9rem;">
                                <b>รหัสโรค:</b> {row.pdx}
                            </div>
                            <div style="color:#757575;font-size:0.85rem;">
                                <b>หอผู้ป่วย:</b> {row.ward_name}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("ไม่มีข้อมูล")
        
        with col_i2:
            # ✅ เพิ่มหัวข้อพร้อมคำอธิบาย
            st.markdown("""
                <div style="margin-bottom:0.8rem;">
                    <div style="display:flex;align-items:center;gap:0.5rem;">
                        <h4 style="margin:0;color:#FF6F00;font-size:1.1rem;">⚠️ Long Stay Alert (>30 days)</h4>
                    </div>
                    <p style="color:#757575;font-size:0.85rem;margin:0.3rem 0 0.8rem 0;">
                        ผู้ป่วยที่นอนเกิน 30 วัน ต้องติดตามและหาสาเหตุ
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # Alert: Long Stay Cases
            long_stay = df_current[df_current['length_of_stay'] > 30]
            if len(long_stay) > 0:
                st.markdown(f"""
                    <div style="background:#FFF3E0;padding:0.8rem 1rem;border-radius:8px;
                                margin-bottom:1rem;border-left:4px solid #FF6F00;text-align:center;">
                        <div style="color:#E65100;font-size:1.8rem;font-weight:700;">
                            🚨 {len(long_stay)} ราย
                        </div>
                        <div style="color:#757575;font-size:0.85rem;margin-top:0.3rem;">
                            ต้องตรวจสอบและติดตาม
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                for row in long_stay.head(5).itertuples():
                    st.markdown(f"""
                        <div style="background:#FFF3E0;padding:0.6rem;border-radius:6px;
                                    margin-bottom:0.4rem;border-left:3px solid #FF6F00;">
                            <div style="color:#37474F;font-size:0.9rem;margin-bottom:0.2rem;">
                                <b>AN:</b> {row.an} · 
                                <b style="color:#FF6F00;">นอน {row.length_of_stay:.0f} วัน</b>
                            </div>
                            <div style="color:#757575;font-size:0.85rem;">
                                {row.pdx} · {row.ward_name}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background:#E8F5E9;padding:1.5rem;border-radius:8px;
                                text-align:center;border-left:4px solid #4CAF50;">
                        <div style="font-size:2rem;margin-bottom:0.5rem;">✅</div>
                        <div style="color:#2E7D32;font-weight:600;font-size:1rem;">
                            ไม่มีผู้ป่วยนอนนาน
                        </div>
                        <div style="color:#757575;font-size:0.85rem;margin-top:0.3rem;">
                            ทุกรายนอนไม่เกิน 30 วัน
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        with col_i3:
            # ✅ เพิ่มหัวข้อพร้อมคำอธิบาย
            st.markdown("""
                <div style="margin-bottom:0.8rem;">
                    <div style="display:flex;align-items:center;gap:0.5rem;">
                        <h4 style="margin:0;color:#2E7D32;font-size:1.1rem;">🏥 Ward CMI Ranking</h4>
                    </div>
                    <p style="color:#757575;font-size:0.85rem;margin:0.3rem 0 0.8rem 0;">
                        หอผู้ป่วยที่มี CMI สูงสุด = รักษาผู้ป่วยหนัก/ซับซ้อน
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # Ward Performance
            ward_cmi = (df_current.groupby('ward_name')['adjrw']
                        .mean()
                        .sort_values(ascending=False)
                        .head(5))
            
            if not ward_cmi.empty:
                for idx, (ward, cmi) in enumerate(ward_cmi.items(), 1):
                    bar_width = int((cmi / ward_cmi.max()) * 100)
                    
                    # กำหนดสีตาม CMI
                    if cmi >= 2.0:
                        color = "#D32F2F"  # แดง - หนักมาก
                        badge = "🔴"
                    elif cmi >= 1.5:
                        color = "#F57C00"  # ส้m - หนักปานกลาง
                        badge = "🟠"
                    elif cmi >= 1.0:
                        color = "#2E7D32"  # เขียว - ปกติ
                        badge = "🟢"
                    else:
                        color = "#1976D2"  # น้ำเงิน - เบา
                        badge = "🔵"
                    
                    st.markdown(f"""
                        <div style="margin-bottom:1rem;">
                            <div style="display:flex;justify-content:space-between;
                                        align-items:center;margin-bottom:0.3rem;">
                                <div style="font-size:0.9rem;font-weight:500;color:#37474F;">
                                    {badge} #{idx} {ward}
                                </div>
                                <div style="color:{color};font-weight:700;font-size:1.1rem;">
                                    {cmi:.3f}
                                </div>
                            </div>
                            <div style="background:#ECEFF1;border-radius:4px;height:8px;">
                                <div style="background:{color};height:8px;width:{bar_width}%;
                                            border-radius:4px;transition:width 0.3s;"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("ไม่มีข้อมูล Ward")
        
        # ✅ เพิ่มคำอธิบายเพิ่มเติมด้านล่าง (Expandable)
        with st.expander("💡 คำอธิบายเพิ่มเติม - Operational Insights", expanded=False):
            st.markdown("""
            ### 📖 คู่มือการใช้งาน
            
            ---
            
            #### 🏆 Top 5 High-Value Cases คืออะไร?
            
            **ความหมาย:**  
            ผู้ป่วย 5 รายที่มีค่า **Adjusted RW สูงสุด** ในเดือนนี้
            
            **ใช้ประโยชน์:**
            - ✅ ตรวจสอบว่ารักษาถูกต้องตามมาตรฐานหรือไม่
            - ✅ ตรวจสอบ Coding ว่าถูกต้องหรือไม่
            - ✅ วางแผน Resource สำหรับผู้ป่วยหนัก
            - ✅ ทบทวน Outcome และ Complication
            
            **ตัวอย่างการตีความ:**
            - **RW > 20** = ผู้ป่วยหนักมาก (ICU, Surgery ซับซ้อน)
            - **RW 10-20** = ผู้ป่วยหนักปานกลาง
            - **RW 5-10** = ผู้ป่วยหนักเล็กน้อย
            
            ---
            
            #### ⚠️ Long Stay Alert (>30 days) คืออะไร?
            
            **ความหมาย:**  
            ผู้ป่วยที่นอนโรงพยาบาล **เกิน 30 วัน** ซึ่งถือว่า "นอนนานมาก"
            
            **ทำไมต้องติดตาม:**
            - 🔴 เสี่ยงต่อ Hospital-acquired infection (HAI)
            - 🔴 ค่าใช้จ่ายสูง (Cost per case ↑)
            - 🔴 เตียงเต็ม (Bed occupancy ↑)
            - 🔴 อาจมี Delay discharge
            
            **สาเหตุที่พบบ่อย:**
            1. **Medical:** Chronic disease, Complication, Slow recovery
            2. **Social:** ไม่มีผู้ดูแล, รอ Home care, รอ Hospice
            3. **Administrative:** รอประสานงาน, รอเตียง Long-term care
            
            **ควรทำอย่างไร:**
            - ✅ ประชุม MDT (Multi-Disciplinary Team)
            - ✅ Review discharge plan
            - ✅ ประสานงาน Social worker
            - ✅ พิจารณา Home care / Transfer
            
            ---
            
            #### 🏥 Ward CMI Ranking คืออะไร?
            
            **ความหมาย:**  
            หอผู้ป่วยที่มี **CMI (Case Mix Index) สูงสุด** 
            = หอที่รักษาผู้ป่วยหนัก/ซับซ้อนที่สุด
            
            **การตีความสี:**
            - 🔴 **CMI ≥ 2.0** = หนักมาก (ICU, CCU)
            - 🟠 **CMI 1.5-2.0** = หนักปานกลาง (Step-down, Specialty ward)
            - 🟢 **CMI 1.0-1.5** = ปกติ (General ward)
            - 🔵 **CMI < 1.0** = เบา (Observation, Same-day)
            
            **ใช้ประโยชน์:**
            - ✅ วางแผน Nurse-to-patient ratio
            - ✅ จัดสรร Budget และ Equipment
            - ✅ Training staff ตามความซับซ้อน
            - ✅ Benchmark ระหว่าง Ward
            
            **ตัวอย่าง:**
            - **หอผู้ป่วยหนัก ICU** → CMI สูง (2.5-4.0) ✅ ปกติ
            - **หอผู้ป่วยทั่วไป** → CMI ปานกลาง (1.0-1.5) ✅ ปกติ
            - **หอผู้ป่วยทั่วไป แต่ CMI สูง (> 2.0)** → ⚠️ ควรย้ายไป ICU?
            
             """)
             
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
