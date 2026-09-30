import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعدادات صفحة التطبيق (توسيع العرض لتغطية الشاشة بالكامل)
st.set_page_config(page_title="تشيك الأسعار - PriceCheck Pro", page_icon="🏷", layout="wide")

# --- تنسيق CSS لتكبير الخطوط وجعل الواجهة من اليمين لليسار (RTL) ---
st.markdown("""
    <style>
    /* تكبير الخطوط العامة وتوجيه النص لليمين */
    html, body, [class*="css"] {
        direction: rtl;
        text-align: right;
        font-size: 18px !important;
    }
    /* تكبير العناوين */
    h1 { font-size: 2.5rem !important; font-weight: bold; }
    h2 { font-size: 2rem !important; }
    h3 { font-size: 1.5rem !important; }
    /* تنسيق الحقول والجداول */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        font-size: 18px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. إعداد قاعدة البيانات المحلية (SQLite) ---
def init_db():
    conn = sqlite3.connect('price_check.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    ''')
    
    # جدول المنتجات (يتضمن عمود `offer_price` لسعر العرض)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            offer_price REAL,
            category TEXT
        )
    ''')
    
    # جدول سجلات الدخول
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            login_time TEXT
        )
    ''')
    
    # إنشاء حساب المدير الأساسي (admin / 12345)
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES ('admin', '12345', 'مدير النظام')")
        
    # إنشاء حساب مسؤول المعرض (Md / 0904)
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = 'md'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES ('Md', '0904', 'مسؤول المعرض')")
        
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

# شاشة تسجيل الدخول
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 تسجيل الدخول - نظام فحص الأسعار</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>النظام محمي ومخصص للاستخدام التجاري.</p>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("login_form"):
            u_input = st.text_input("اسم المستخدم (لا يشترط التقيد بحالة الحروف الكبيرة/الصغيرة)")
            p_input = st.text_input("كلمة المرور", type="password")
            submit_login = st.form_submit_button("دخول النظام")
            
            if submit_login:
                conn = get_connection()
                cursor = conn.cursor()
                # البحث بغض النظر عن حالة الحروف الكبيرة والصغيرة (Lower)
                cursor.execute("SELECT username, password, role FROM users WHERE LOWER(username) = LOWER(?)", (u_input.strip(),))
                user_data = cursor.fetchone()
                
                if user_data and user_data[1] == p_input:
                    st.session_state.logged_in = True
                    st.session_state.username = user_data[0] # حفظ الاسم بالشكل الأصلي
                    st.session_state.role = user_data[2]     # الدور بالعربي
                    
                    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                    cursor.execute("INSERT INTO login_logs (username, login_time) VALUES (?, ?)", (user_data[0], current_time))
                    conn.commit()
                    conn.close()
                    
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                else:
                    conn.close()
                    st.error("خطأ في اسم المستخدم أو كلمة المرور.")
    st.stop()

# --- 3. خيار اختيار لغة الواجهة في الشريط الجانبي ---
st.sidebar.markdown("### 🌐 إعدادات اللغة / Language")
selected_lang = st.sidebar.selectbox("اختر لغة الواجهة / Select Language", ["العربية", "English"])

# --- واجهة التطبيق الرئيسية بعد الدخول ---
if selected_lang == "العربية":
    st.title("🏷️ نظام فحص وتدقيق الأسعار المعتمد")
    st.sidebar.markdown(f"**👤 المستخدم الحالي:** {st.session_state.username}")
    st.sidebar.markdown(f"**📌 الصلاحية:** {st.session_state.role}")
    
    logout_label = "تسجيل الخروج"
    menu_title = "📋 القائمة الرئيسية"
    menu_options = [
        "👥 إدارة المستخدمين", 
        "📊 سجلات دخول المستخدمين",
        "🔍 فحص السعر", 
        "➕ إدارة المنتجات والأسعار", 
        "📁 اسعار المنتجات (رفع إكسل)", 
        "📋 كل المنتجات"
    ]
else:
    st.title("🏷️ Price Check & Audit System")
    st.sidebar.markdown(f"**👤 Current User:** {st.session_state.username}")
    st.sidebar.markdown(f"**📌 Role:** {st.session_state.role}")
    
    logout_label = "Logout"
    menu_title = "📋 Main Menu"
    menu_options = [
        "👥 User Management", 
        "📊 Login Logs",
        "🔍 Price Checker", 
        "➕ Product Management", 
        "📁 Import Prices (Excel)", 
        "📋 All Products"
    ]

if st.sidebar.button(logout_label):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

st.sidebar.markdown("---")

user_role = st.session_state.role

# تصفية القوائم بناءً على الدور الوظيفي بالعربي
if user_role in ['مدير النظام', 'مسؤول المعرض', 'admin', 'Exhibition Manager']:
    menu_selection = st.sidebar.radio(menu_title, menu_options)
elif user_role in ['مشرف قسم', 'Department Supervisor']:
    if selected_lang == "العربية":
        menu_selection = st.sidebar.radio(menu_title, ["🔍 فحص السعر", "➕ إدارة المنتجات والأسعار", "📁 اسعار المنتجات (رفع إكسل)", "📋 كل المنتجات"])
    else:
        menu_selection = st.sidebar.radio(menu_title, ["🔍 Price Checker", "➕ Product Management", "📁 Import Prices (Excel)", "📋 All Products"])
else:  
    if selected_lang == "العربية":
        menu_selection = st.sidebar.radio(menu_title, ["🔍 فحص السعر", "📋 كل المنتجات"])
    else:
        menu_selection = st.sidebar.radio(menu_title, ["🔍 Price Checker", "📋 All Products"])

# --- 1. إدارة المستخدمين ---
if menu_selection in ["👥 إدارة المستخدمين", "👥 User Management"]:
    if user_role in ['مدير النظام', 'مسؤول المعرض', 'admin', 'Exhibition Manager']:
        st.subheader("إدارة المستخدمين وصلاحيات النظام")
        
        with st.form("user_form"):
            new_u = st.text_input("اسم المستخدم الجديد (يقبل حروف كبيرة أو صغيرة)")
            new_p = st.text_input("كلمة المرور للمستخدم الجديد", type="password")
            new_role = st.selectbox(
                "الصلاحية (الدور الوظيفي)", 
                [
                    "مدير النظام", 
                    "مسؤول المعرض", 
                    "مشرف قسم", 
                    "موظف قسم"
                ]
            )
            
            create_user_btn = st.form_submit_button("إنشاء الحساب")
            
            if create_user_btn:
                if new_u and new_p:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (new_u.strip(), new_p, new_role))
                        conn.commit()
                        conn.close()
                        st.success(f"تم إنشاء حساب المستخدم ({new_u}) بنجاح!")
                    except sqlite3.IntegrityError:
                        st.error("اسم المستخدم موجود مسبقاً، اختر اسماً آخر.")
                else:
                    st.error("الرجاء أدخال اسم المستخدم وكلمة المرور.")
                    
        st.markdown("---")
        st.write("### المستخدمون المسجلون في النظام:")
        
        conn = get_connection()
        users_df = pd.read_sql_query("SELECT username AS 'اسم المستخدم', role AS 'الصلاحية (الدور)' FROM users", conn)
        conn.close()
        
        st.dataframe(users_df, use_container_width=True)
        
        st.markdown("#### 🗑️ حذف مستخدم مسجل:")
        with st.form("delete_user_form"):
            user_to_delete = st.selectbox("اختر اسم المستخدم للحذف", users_df['اسم المستخدم'].tolist())
            delete_btn = st.form_submit_button("حذف المستخدم المحدد")
            
            if delete_btn:
                if user_to_delete.lower() in ["admin", "md"]:
                    st.error("⚠ لا يمكن حذف حسابات الإدارة الأساسية.")
                elif user_to_delete.lower() == st.session_state.username.lower():
                    st.error("⚠ لا يمكنك حذف الحساب الذي تستخدمه حالياً.")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM users WHERE username = ?", (user_to_delete,))
                    conn.commit()
                    conn.close()
                    st.success(f"تم حذف المستخدم ({user_to_delete}) بنجاح!")
                    st.rerun()
    else:
        st.error("⚠ عذراً، لا تملك صلاحية الوصول إلى هذه الصفحة.")

# --- 2. سجلات دخول المستخدمين ---
elif menu_selection in ["📊 سجلات دخول المستخدمين", "📊 Login Logs"]:
    if user_role in ['مدير النظام', 'مسؤول المعرض', 'admin', 'Exhibition Manager']:
        st.subheader("📊 سجلات دخول المشرفين والمستخدمين إلى النظام")
        
        conn = get_connection()
        logs_df = pd.read_sql_query("SELECT id AS 'م', username AS 'اسم المستخدم', login_time AS 'وقت تسجيل الدخول' FROM login_logs ORDER BY id DESC", conn)
        conn.close()
        
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.info("لا توجد سجلات دخول مسجلة حتى الآن.")
    else:
        st.error("⚠ عذراً، لا تملك صلاحية الوصول إلى هذه الصفحة.")

# --- 3. فحص السعر ---
elif menu_selection in ["🔍 فحص السعر", "🔍 Price Checker"]:
    st.subheader("التحقق الفوري من أسعار المنتجات")
    
    search_method = st.radio("اختر طريقة البحث:", ["إدخال رقم الباركود يدوياً", "استخدام الكاميرا (Barcode)"])
    
    barcode_to_search = ""
    if search_method == "إدخال رقم الباركود يدوياً":
        barcode_to_search = st.text_input("أدخل رقم الباركود للمنتج:")
    else:
        st.info("قم بتوجيه الكاميرا نحو باركود المنتج والتقاط الصورة:")
        img_file = st.camera_input("التقاط صورة الباركود")
        if img_file:
            st.warning("تم التقاط الصورة بنجاح. إذا لم يتم التعرف تلقائياً، أدخل الرقم يدوياً أدناه:")
            barcode_to_search = st.text_input("أكد رقم الباركود:")

    if barcode_to_search:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, offer_price, category FROM products WHERE barcode = ?", (barcode_to_search.strip(),))
        product = cursor.fetchone()
        conn.close()
        
        if product:
            st.success("تم العثور على المنتج بنجاح!")
            col1, col2, col3 = st.columns(3)
            col1.metric("اسم الصنف", product[0])
            col2.metric("السعر الأساسي", f"{product[1]} ر.س")
            
            if product[2] and product[2] > 0:
                col3.metric("🔥 سعر العرض", f"{product[2]} ر.س", delta="عرض خاص", delta_color="inverse")
            else:
                col3.metric("🔥 سعر العرض", "لا يوجد عرض")
                
            st.info(f"القسم: {product[3]}")
        else:
            st.warning("⚠ هذا الصنف غير مسجل في النظام.")

# --- 4. إدارة المنتجات والأسعار ---
elif menu_selection in ["➕ إدارة المنتجات والأسعار", "➕ Product Management"]:
    if user_role in ['مدير النظام', 'مسؤول المعرض', 'مشرف قسم', 'admin', 'Exhibition Manager', 'Department Supervisor']:
        st.subheader("إضافة أو تعديل منتج فردي (مع خيار العروض)")
        with st.form("product_form"):
            p_code = st.text_input("رقم الباركود")
            p_name = st.text_input("اسم الصنف")
            p_price = st.number_input("السعر الأساسي بالريال", min_value=0.0, format="%.2f")
            p_offer = st.number_input("سعر العرض (اختياري - اتركه 0 إذا لم يوجد عرض)", min_value=0.0, format="%.2f")
            p_cat = st.selectbox("القسم", ["أغذية", "مشروبات", "منظفات", "إلكترونيات", "أخرى"])
            
            save_product = st.form_submit_button("حفظ أو تحديث المنتج")
            
            if save_product:
                if p_code and p_name and p_price >= 0:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO products (barcode, name, price, offer_price, category) 
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(barcode) 
                        DO UPDATE SET name=excluded.name, price=excluded.price, offer_price=excluded.offer_price, category=excluded.category
                    ''', (p_code.strip(), p_name, p_price, p_offer, p_cat))
                    conn.commit()
                    conn.close()
                    st.success(f"تم حفظ الصنف ({p_name}) وتحديث سعره بنجاح!")
                else:
                    st.error("الرجاء تعبئة الحقول الأساسية بشكل صحيح.")
    else:
        st.error("⚠ عذراً، لا تملك صلاحية تعديل أو إضافة المنتجات.")

# --- 5. اسعار المنتجات (رفع إكسل) ---
elif menu_selection in ["📁 اسعار المنتجات (رفع إكسل)", "📁 Import Prices (Excel)"]:
    if user_role in ['مدير النظام', 'مسؤول المعرض', 'مشرف قسم', 'admin', 'Exhibition Manager', 'Department Supervisor']:
        st.subheader("استيراد اسعار المنتجات عبر ملف (CSV / Excel)")
        st.markdown("""
        **تعليمات الملف:**
        يجب أن يحتوي الملف على الأعمدة التالية باللغة الإنجليزية لضمان القراءة الصحيحة:
        - `barcode` (رقم الباركود)
        - `name` (اسم المنتج)
        - `price` (السعر الأساسي)
        - `offer_price` (سعر العرض - اختياري)
        - `category` (القسم)
        """)
        
        uploaded_file = st.file_uploader("اختر ملف CSV أو Excel", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                
                st.write("معاينة البيانات المرفوعة:", df_upload.head())
                
                if st.button("اعتماد وحفظ جميع المنتجات في النظام"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    success_count = 0
                    
                    for _, row in df_upload.iterrows():
                        b_code = str(row.get('barcode', ''))
                        p_name = str(row.get('name', ''))
                        p_price = float(row.get('price', 0.0))
                        p_offer = float(row.get('offer_price', 0.0)) if pd.notna(row.get('offer_price')) else 0.0
                        p_cat = str(row.get('category', 'أخرى'))
                        
                        if b_code and p_name:
                            cursor.execute('''
                                INSERT INTO products (barcode, name, price, offer_price, category) 
                                VALUES (?, ?, ?, ?, ?)
                                ON CONFLICT(barcode) 
                                DO UPDATE SET name=excluded.name, price=excluded.price, offer_price=excluded.offer_price, category=excluded.category
                            ''', (b_code.strip(), p_name, p_price, p_offer, p_cat))
                            success_count += 1
                            
                    conn.commit()
                    conn.close()
                    st.success(f"تم بنجاح استيراد وتحديث {success_count} منتجاً في قاعدة البيانات!")
            except Exception as e:
                st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
    else:
        st.error("⚠ عذراً، لا تملك صلاحية رفع الملفات.")

# --- 6. كل المنتجات ---
elif menu_selection in ["📋 كل المنتجات", "📋 All Products"]:
    st.subheader("قائمة أصناف و أسعار المنتجات المسجلة")
    conn = get_connection()
    prod_df = pd.read_sql_query("SELECT barcode AS 'الباركود', name AS 'اسم الصنف', price AS 'السعر الأساسي (ر.س)', offer_price AS 'سعر العرض (ر.س)', category AS 'القسم' FROM products", conn)
    conn.close()
    if not prod_df.empty:
        st.dataframe(prod_df, use_container_width=True)
    else:
        st.info("لا توجد أصناف مسجلة حتى الآن.")
        
