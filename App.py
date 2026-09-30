import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعدادات صفحة التطبيق (توسيع العرض لتغطية الشاشة بالكامل)
st.set_page_config(page_title="تشيك الأسعار - PriceCheck Pro", page_icon="🏷", layout="wide")

# --- تنسيق CSS لتكبير الخطوط، جعل الواجهة من اليمين لليسار (RTL)، وتنسيق الجداول ---
st.markdown("""
    <style>
    html, body, [class*="css"] {
        direction: rtl;
        text-align: right;
        font-size: 18px !important;
    }
    h1 { font-size: 2.5rem !important; font-weight: bold; }
    h2 { font-size: 2.0rem !important; }
    h3 { font-size: 1.5rem !important; }
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        font-size: 18px !important;
    }
    table {
        direction: rtl;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

# --- دالة مساعدة لترجمة الصلاحيات إلى العربية ---
def translate_role_to_arabic(role):
    mapping = {
        'admin': 'مدير النظام',
        'General Manager': 'مدير النظام',
        'Exhibition Manager': 'مسؤول المعرض',
        'Branch Manager': 'مدير الفرع',
        'Department Supervisor': 'مشرف قسم',
        'Department Employee': 'موظف قسم',
        'مدير النظام': 'مدير النظام',
        'مسؤول المعرض': 'مسؤول المعرض',
        'مدير المعرض': 'مسؤول المعرض',
        'مدير الفرع': 'مدير الفرع',
        'مشرف قسم': 'مشرف قسم',
        'موظف قسم': 'موظف قسم'
    }
    return mapping.get(role, role)

# --- 1. إعداد قاعدة البيانات المحلية (SQLite) ---
def init_db():
    conn = sqlite3.connect('price_check.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            emp_name TEXT DEFAULT '',
            branch_name TEXT DEFAULT ''
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            offer_price REAL,
            category TEXT,
            last_updated TEXT
        )
    ''')
    
    cursor.execute("PRAGMA table_info(products)")
    prod_cols = [col[1] for col in cursor.fetchall()]
    if 'offer_price' not in prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN offer_price REAL DEFAULT 0.0")
    if 'category' not in prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'أخرى'")
    if 'last_updated' not in prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN last_updated TEXT")

    cursor.execute("DROP TABLE IF EXISTS login_logs")
    cursor.execute('''
        CREATE TABLE login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT
        )
    ''')
    
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role, emp_name, branch_name) VALUES ('admin', '12345', 'General Manager', 'المدير العام', 'الفرع الرئيسي')")
        
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = 'md'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role, emp_name, branch_name) VALUES ('Md', '0904', 'Exhibition Manager', 'مسؤول المعرض', 'الفرع الرئيسي')")
    
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect('price_check.db', check_same_thread=False)

# --- 2. إدارة جلسة تسجيل الدخول ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 تسجيل الدخول - نظام فحص الأسعار</h2>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("login_form"):
            u_input = st.text_input("اسم المستخدم")
            p_input = st.text_input("كلمة المرور", type="password")
            submit_login = st.form_submit_button("دخول النظام")
            
            if submit_login:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT username, password, role FROM users WHERE LOWER(username) = LOWER(?)", (u_input.strip(),))
                user_data = cursor.fetchone()
                
                if user_data and user_data[1] == p_input:
                    st.session_state.logged_in = True
                    st.session_state.username = user_data[0]
                    st.session_state.role = user_data[2]
                    
                    cursor.execute("INSERT INTO login_logs (username, role) VALUES (?, ?)", 
                                   (user_data[0], user_data[2]))
                    conn.commit()
                    conn.close()
                    st.rerun()
                else:
                    conn.close()
                    st.error("خطأ في اسم المستخدم أو كلمة المرور.")
    st.stop()

selected_lang = st.sidebar.selectbox("", ["العربية", "English"], label_visibility="collapsed")
user_role = st.session_state.role
arabic_role_display = translate_role_to_arabic(user_role)

if selected_lang == "العربية":
    st.title("🏷️ نظام فحص وتدقيق الأسعار المعتمد")
    st.sidebar.markdown(f"**👤 المستخدم الحالي:** {st.session_state.username}")
    st.sidebar.markdown(f"**📌 الصلاحية:** {arabic_role_display}")
    
    logout_label = "تسجيل الخروج"
    menu_title = "📋 القائمة الرئيسية"
    menu_options = [
        "👥 إدارة المستخدمين", 
        "📊 سجلات دخول المستخدمين",
        "🔍 فحص السعر", 
        "➕ إدارة المنتجات والأسعار", 
        "🔗 ربط نظام الشركة (API التلقائي)", 
        "📋 كل المنتجات"
    ]
else:
    st.title("🏷️ Price Check & Audit System")
    st.sidebar.markdown(f"**👤 Current User:** {st.session_state.username}")
    st.sidebar.markdown(f"**📌 Role:** {arabic_role_display}")
    
    logout_label = "Logout"
    menu_title = "📋 Main Menu"
    menu_options = [
        "👥 User Management", 
        "📊 Login Logs",
        "🔍 Price Checker", 
        "➕ Product Management", 
        "🔗 Company System Integration (API)", 
        "📋 All Products"
    ]

if st.sidebar.button(logout_label):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

st.sidebar.markdown("---")
admin_roles = ['مدير النظام', 'مسؤول المعرض', 'مدير المعرض', 'مدير الفرع', 'admin', 'General Manager', 'Exhibition Manager', 'Branch Manager']

if user_role in admin_roles:
    menu_selection = st.sidebar.radio(menu_title, menu_options)
else:
    if selected_lang == "العربية":
        menu_selection = st.sidebar.radio(menu_title, ["🔍 فحص السعر", "📋 كل المنتجات"])
    else:
        menu_selection = st.sidebar.radio(menu_title, ["🔍 Price Checker", "📋 All Products"])

# --- إدارة المستخدمين ---
if menu_selection in ["👥 إدارة المستخدمين", "👥 User Management"]:
    if user_role in admin_roles:
        st.subheader("إدارة المستخدمين وصلاحيات النظام")
        with st.form("user_form", clear_on_submit=True):
            new_u = st.text_input("اسم المستخدم الجديد")
            new_emp = st.text_input("اسم الموظف / الفرع الفرعي (اختياري)")
            new_branch = st.text_input("اسم الفرع الرئيسي")
            new_p = st.text_input("كلمة المرور", type="password")
            new_role = st.selectbox("الصلاحية", ["General Manager", "Exhibition Manager", "Branch Manager", "Department Supervisor", "Department Employee"], format_func=lambda x: translate_role_to_arabic(x))
            
            if st.form_submit_button("إنشاء الحساب"):
                if new_u and new_p:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users (username, password, role, emp_name, branch_name) VALUES (?, ?, ?, ?, ?)", 
                                       (new_u.strip(), new_p, new_role, new_emp.strip(), new_branch.strip()))
                        conn.commit()
                        conn.close()
                        st.success(f"تم إنشاء حساب المستخدم ({new_u}) بنجاح!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("اسم المستخدم موجود مسبقاً.")
                else:
                    st.error("الرجاء إدخال الحقول المطلوبة.")
    else:
        st.error("⚠ عذراً، لا تملك صلاحية الوصول.")

# --- سجلات الدخول ---
elif menu_selection in ["📊 سجلات دخول المستخدمين", "📊 Login Logs"]:
    if user_role in admin_roles:
        st.subheader("📊 سجلات دخول المستخدمين")
        conn = get_connection()
        logs = conn.cursor().execute("SELECT id, username, role FROM login_logs ORDER BY id DESC").fetchall()
        conn.close()
        for idx, (l_id, u, r) in enumerate(logs, 1):
            st.markdown(f"**{idx}. المستخدم:** {u} | **الدور:** {translate_role_to_arabic(r)}")
    else:
        st.error("⚠ غير مسموح بالدخول.")

# --- فحص السعر ---
elif menu_selection in ["🔍 فحص السعر", "🔍 Price Checker"]:
    st.subheader("التحقق الفوري من أسعار المنتجات")
    barcode_to_search = st.text_input("أدخل رقم الباركود للمنتج:")
    if barcode_to_search:
        conn = get_connection()
        product = conn.cursor().execute("SELECT name, price, offer_price, category, last_updated FROM products WHERE barcode = ?", (barcode_to_search.strip(),)).fetchone()
        conn.close()
        if product:
            st.success("تم العثور على المنتج بنجاح!")
            col1, col2, col3 = st.columns(3)
            col1.metric("اسم الصنف", product[0])
            col2.metric("السعر الأساسي", f"{product[1]} ر.س")
            col3.metric("🔥 سعر العرض", f"{product[2]} ر.س" if product[2] else "لا يوجد عرض")
            st.info(f"القسم: {product[3]} | آخر تحديث آلي: {product[4] or 'غير محدد'}")
        else:
            st.warning("⚠ هذا الصنف غير مسجل في النظام.")

# --- إدارة المنتجات والأسعار ---
elif menu_selection in ["➕ إدارة المنتجات والأسعار", "➕ Product Management"]:
    st.subheader("إضافة أو تعديل منتج فردي")
    with st.form("product_form"):
        p_code = st.text_input("رقم الباركود")
        p_name = st.text_input("اسم الصنف")
        p_price = st.number_input("السعر الأساسي بالريال", min_value=0.0, format="%.2f")
        p_offer = st.number_input("سعر العرض (اختياري)", min_value=0.0, format="%.2f")
        p_cat = st.selectbox("القسم", ["أغذية", "مشروبات", "منظفات", "إلكترونيات", "أخرى"])
        
        if st.form_submit_button("حفظ أو تحديث المنتج"):
            if p_code and p_name:
                now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = get_connection()
                conn.cursor().execute('''
                    INSERT INTO products (barcode, name, price, offer_price, category, last_updated) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(barcode) 
                    DO UPDATE SET name=excluded.name, price=excluded.price, offer_price=excluded.offer_price, category=excluded.category, last_updated=excluded.last_updated
                ''', (p_code.strip(), p_name, p_price, p_offer, p_cat, now_time))
                conn.commit()
                conn.close()
                st.success("تم تحديث المنتج وحفظه بنجاح!")

# --- 🔗 ربط نظام الشركة (API التلقائي) ---
elif menu_selection in ["🔗 ربط نظام الشركة (API التلقائي)", "🔗 Company System Integration (API)"]:
    st.subheader("🔗 ربط نظام الشركة (ERP / POS) للتحديث اللحظي التلقائي")
    st.markdown("""
    لربط نظام شركتك الأساسي بهذا التطبيق بحيث يتم تحديث أو إضافة المنتجات تلقائياً دون أي تدخل بشري:
    
    1. **استخدام رابط برمجي (Webhook / API Endpoint):**
       يمكنك ربط النظام الخاص بكم بإرسال بيانات المنتجات بصيغة **JSON** مباشرة إلى رابط سيرفر التطبيق.
    2. **كود مثال لربط نظام شركتك (Python Requests):**
       يمكن لمبرمج الشركة استخدام الكود التالي في نظام ERP لديك لإرسال أي منتج يتم تعديله أو إضافته فوراً:
    """)
    
    sample_code = """
import requests

url = "https://your-streamlit-app-domain.com/update_product"  # رابط نظامك
payload = {
    "barcode": "6281001234567",
    "name": "عصير برتقال طازج 1لتر",
    "price": 12.50,
    "offer_price": 10.00,
    "category": "مشروبات"
}
response = requests.post(url, json=payload)
print(response.json())
    """
    st.code(sample_code, language="python")
    
    st.markdown("---")
    st.info("💡 **طريقة بديلة (قاعدة بيانات سحابية مركزية):** إذا كان نظام شركتك وقاعدة بيانات هذا التطبيق يشتركان في نفس قاعدة البيانات السحابية (مثل Supabase أو MySQL على السيرفر)، فلن تحتاج لأي كود إضافي؛ فكل تعديل في برنامج الشركة سينعكس هنا بشكل فوري تلقائياً.")

# --- كل المنتجات ---
elif menu_selection in ["📋 كل المنتجات", "📋 All Products"]:
    st.subheader("قائمة أصناف و أسعار المنتجات المسجلة")
    conn = get_connection()
    prod_df = pd.read_sql_query("SELECT barcode AS 'الباركود', name AS 'اسم الصنف', price AS 'السعر الأساسي (ر.س)', offer_price AS 'سعر العرض (ر.س)', category AS 'القسم', last_updated AS 'آخر تحديث' FROM products", conn)
    conn.close()
    if not prod_df.empty:
        st.dataframe(prod_df, use_container_width=True)
    else:
        st.info("لا توجد أصناف مسجلة حتى الآن.")
