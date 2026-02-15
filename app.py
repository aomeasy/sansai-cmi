import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io

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
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3eG5zdXNmeWRyaHRmcWRjc3FuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk0NjM0NjUsImV4cCI6MjA1NTAzOTQ2NX0.kJOrd2rQeb1yNYFW"  # ใช้ anon/public key

@st.cache_resource
def init_supabase():
    """เชื่อมต่อ Supabase"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

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

def validate_and_prepare_data(df):
    """ตรวจสอบและเตรียมข้อมูลก่อนนำเข้า"""
    errors = []
    warnings = []
    
    # คอลัมน์ที่จำเป็น
    required_columns = ['an', 'hn', 'month_year']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        errors.append(f"ขาดคอลัมน์ที่จำเป็น: {', '.join(missing_cols)}")
        return None, errors, warnings
    
    # ทำสำเนาข้อมูล
    df_clean = df.copy()
    
    # แปลงวันที่
    date_columns = ['month_year', 'birth_date', 'admit_date', 'discharge_date']
    for col in date_columns:
        if col in df_clean.columns:
            try:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
            except:
                warnings.append(f"ไม่สามารถแปลงวันที่ในคอลัมน์ {col} บางรายการ")
    
    # คำนวณปีงบประมาณ
    if 'month_year' in df_clean.columns:
        df_clean['fiscal_year'] = df_clean['month_year'].apply(get_fiscal_year)
    
    # คำนวณจำนวนวันนอน
    if 'admit_date' in df_clean.columns and 'discharge_date' in df_clean.columns:
        df_clean['length_of_stay'] = df_clean.apply(
            lambda row: calculate_length_of_stay(row['admit_date'], row['discharge_date']),
            axis=1
        )
    
    # แปลงตัวเลข
    if 'age' in df_clean.columns:
        df_clean['age'] = pd.to_numeric(df_clean['age'], errors='coerce')
    
    if 'adjrw' in df_clean.columns:
        df_clean['adjrw'] = pd.to_numeric(df_clean['adjrw'], errors='coerce')
    
    # เพิ่มข้อมูลการนำเข้า
    df_clean['imported_by'] = st.session_state.get('username', 'system')
    df_clean['created_at'] = datetime.now().isoformat()
    df_clean['updated_at'] = datetime.now().isoformat()
    
    # ตรวจสอบข้อมูลซ้ำ (AN + month_year)
    duplicates = df_clean[df_clean.duplicated(subset=['an', 'month_year'], keep=False)]
    if not duplicates.empty:
        warnings.append(f"พบข้อมูลซ้ำ {len(duplicates)} รายการ (AN + month_year ซ้ำ)")
    
    # แทนที่ NaN ด้วย None สำหรับ Supabase
    df_clean = df_clean.where(pd.notna(df_clean), None)
    
    return df_clean, errors, warnings

def import_to_supabase(df, batch_size=100):
    """นำเข้าข้อมูลไปยัง Supabase"""
    supabase = init_supabase()
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
            response = supabase.table('ipd_monthly').insert(batch_data).execute()
            success_count += len(batch_data)
            
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
        supabase = init_supabase()
        
        # นับจำนวนรายการทั้งหมด
        response = supabase.table('ipd_monthly').select('id', count='exact').execute()
        total_records = response.count if hasattr(response, 'count') else 0
        
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
    
    # คำแนะนำ
    with st.expander("📖 คำแนะนำการนำเข้าข้อมูล", expanded=True):
        st.markdown("""
        ### รูปแบบไฟล์ที่รองรับ:
        - Excel (.xlsx, .xls)
        - CSV (.csv)
        
        ### คอลัมน์ที่จำเป็นต้องมี:
        - **an** (Admission Number) - รหัสผู้ป่วยใน
        - **hn** (Hospital Number) - รหัสผู้ป่วย
        - **month_year** - เดือน/ปี ที่รายงาน
        
        ### คอลัมน์เสริม (ถ้ามี):
        - vn, birth_date, age, sex
        - admit_date, discharge_date, length_of_stay
        - ward_code, ward_name, clinic_code, clinic_name
        - pttype_code, pttype_name
        - pdx, dx0-dx10 (รหัสโรค ICD-10)
        - op0-op11 (รหัสหัตถการ)
        - adjrw, drg_code
        - discharge_status, discharge_type
        
        ### หมายเหตุ:
        - ระบบจะคำนวณ fiscal_year และ length_of_stay ให้อัตโนมัติ
        - ข้อมูลที่มี AN และ month_year ซ้ำจะไม่สามารถนำเข้าได้
        """)
    
    st.markdown("---")
    
    # อัพโหลดไฟล์
    uploaded_file = st.file_uploader(
        "เลือกไฟล์ข้อมูล",
        type=['xlsx', 'xls', 'csv'],
        help="อัพโหลดไฟล์ Excel หรือ CSV"
    )
    
    if uploaded_file is not None:
        try:
            # อ่านไฟล์
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ อ่านไฟล์สำเร็จ: **{uploaded_file.name}**")
            
            # แสดงข้อมูลตัวอย่าง
            st.markdown("### 👀 ตัวอย่างข้อมูล")
            st.dataframe(df.head(10), use_container_width=True)
            
            # แสดงสถิติ
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 จำนวนแถว", f"{len(df):,}")
            with col2:
                st.metric("📋 จำนวนคอลัมน์", f"{len(df.columns):,}")
            with col3:
                st.metric("🔍 ขนาดไฟล์", f"{uploaded_file.size/1024:.2f} KB")
            
            st.markdown("---")
            
            # ตรวจสอบและเตรียมข้อมูล
            st.markdown("### 🔍 ตรวจสอบข้อมูล")
            
            with st.spinner("กำลังตรวจสอบข้อมูล..."):
                df_clean, errors, warnings = validate_and_prepare_data(df)
            
            # แสดงข้อผิดพลาด
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
                st.stop()
            
            # แสดงคำเตือน
            if warnings:
                for warning in warnings:
                    st.warning(f"⚠️ {warning}")
            
            if df_clean is not None:
                st.success("✅ ข้อมูลผ่านการตรวจสอบเรียบร้อย")
                
                # แสดงข้อมูลที่จะนำเข้า
                with st.expander("📋 ดูข้อมูลที่เตรียมนำเข้า"):
                    st.dataframe(df_clean.head(20), use_container_width=True)
                
                st.markdown("---")
                
                # ปุ่มนำเข้าข้อมูล
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🚀 เริ่มนำเข้าข้อมูล", type="primary", use_container_width=True):
                        st.session_state.confirm_import = True
                
                # ยืนยันการนำเข้า
                if st.session_state.get('confirm_import', False):
                    st.markdown("### 📤 กำลังนำเข้าข้อมูล")
                    
                    with st.spinner("กรุณารอสักครู่..."):
                        success_count, error_count, error_details = import_to_supabase(df_clean)
                    
                    # แสดงผลลัพธ์
                    if error_count == 0:
                        st.balloons()
                        st.success(f"🎉 นำเข้าข้อมูลสำเร็จ **{success_count:,}** รายการ!")
                    else:
                        st.warning(f"⚠️ นำเข้าสำเร็จ **{success_count:,}** รายการ, ล้มเหลว **{error_count:,}** รายการ")
                        
                        if error_details:
                            with st.expander("🔍 รายละเอียดข้อผิดพลาด"):
                                for detail in error_details:
                                    st.error(detail)
                    
                    # รีเซ็ตสถานะ
                    st.session_state.confirm_import = False
                    
                    # ปุ่มนำเข้าข้อมูลใหม่
                    if st.button("📥 นำเข้าข้อมูลชุดใหม่"):
                        st.rerun()
        
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}")
            st.exception(e)

# เรียกใช้งาน
if __name__ == "__main__":
    main()
