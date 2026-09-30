import streamlit as st
import sqlite3
import pandas as pd

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تشيك الأسعار - PriceCheck Pro", page_icon="🏷", layout="centered")

# --- 1. إعداد قاعدة البيانات المحلية (SQLite) لضمان حفظ البيانات ودائم ---
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
    
    # جدول المنتجات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            category TEXT
        )
    ''')
    
    # إنشاء حساب المدير الأساسي تلقائياً إذا لم يكن موجوداً
    cursor.execute("SELECT * FROM users WHERE username = 'mohammed'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES ('mohammed', '12345', 'admin')")
        
    conn.commit()
    conn.close()

init_db()

# دوال مساعدة للتعامل مع قاعدة البيانات
def get_connection():
    return sqlite3.connect('price_check.db', check_same_thread=False)

# --- 2. إدارة جلسة تسجيل الدخول ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

# شاشة تسجيل الدخول
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 تسجيل الدخول - تشيك الأسعار</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>النظام محمي ومخصص للاستخدام التجاري.</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        u_input = st.text_input("اسم المستخدم")
        p_input = st.text_input("كلمة المرور", type="password")
        submit_login = st.form_submit_button("دخول النظام")
        
        if submit_login:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT password, role FROM users WHERE username = ?", (u_input,))
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data and user_data[0] == p_input:
                st.session_state.logged_in = True
                st.session_state.username = u_input
                st.session_state.role = user_data[1]  # 'admin' أو 'user'
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("خطأ في اسم المستخدم أو كلمة المرور.")
    st.stop()

# --- 3. واجهة التطبيق الرئيسية بعد الدخول ---
st.title("🏷️ نظام تشيك الأسعار المعتمد")
st.sidebar.markdown(f"**المستخدم الحالي:** {st.session_state.username}")
st.sidebar.markdown(f"**الصلاحية:** {'مدير النظام (Admin)' if st.session_state.role == 'admin' else 'مستخدم (فحص فقط)'}")

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

st.sidebar.markdown("---")

# ترتيب القوائم بالترتيب المطلوب تماماً وتحت بعض على اليمين (Sidebar)
if st.session_state.role == 'admin':
    menu_selection = st.sidebar.radio(
        "📋 القائمة الرئيسية",
        [
            "👥 إدارة المستخدمين", 
            "🔍 فحص السعر", 
            "➕ إدارة المنتجات والأسعار", 
            "📁 اسعار المنتجات (رفع إكسل)", 
            "📋 كل المنتجات"
        ]
    )
else:
    menu_selection = st.sidebar.radio(
        "📋 القائمة الرئيسية",
        [
            "🔍 فحص السعر", 
            "📋 كل المنتجات"
        ]
    )

# --- 1. إدارة المستخدمين ---
if menu_selection == "👥 إدارة المستخدمين":
    st.subheader("إدارة المستخدمين الجدد والنظام")
    with st.form("user_form"):
        new_u = st.text_input("اسم المستخدم الجديد")
        new_p = st.text_input("كلمة المرور للمستخدم الجديد", type="password")
        new_role = st.selectbox("صلاحية المستخدم", ["user", "admin"])
        
        create_user_btn = st.form_submit_button("إنشاء الحساب")
        
        if create_user_btn:
            if new_u and new_p:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (new_u, new_p, new_role))
                    conn.commit()
                    conn.close()
                    st.success(f"تم إنشاء حساب المستخدم {new_u} بنجاح!")
                except sqlite3.IntegrityError:
                    st.error("اسم المستخدم موجود مسبقاً، اختر اسماً آخر.")
            else:
                st.error("أدخل اسم المستخدم وكلمة المرور.")
                
    st.markdown("---")
    st.write("### المستخدمون المسجلون في النظام:")
    conn = get_connection()
    users_df = pd.read_sql_query("SELECT username, role FROM users", conn)
    conn.close()
    st.dataframe(users_df, use_container_width=True)

# --- 2. فحص السعر ---
elif menu_selection == "🔍 فحص السعر":
    st.subheader("التحقق الفوري من أسعار المنتجات")
    
    search_method = st.radio("اختر طريقة البحث:", ["إدخال رقم الباركود يدوياً", "استخدام الكاميرا (QR / Barcode)"])
    
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
        cursor.execute("SELECT name, price, category FROM products WHERE barcode = ?", (barcode_to_search,))
        product = cursor.fetchone()
        conn.close()
        
        if product:
            st.success("تم العثور على المنتج بنجاح!")
            col1, col2 = st.columns(2)
            col1.metric("اسم الصنف", product[0])
            col2.metric("السعر", f"{product[1]} ر.س")
            st.info(f"القسم: {product[2]}")
        else:
            st.warning("⚠ هذا الصنف غير مسجل في النظام.")

# --- 3. إدارة المنتجات والأسعار ---
elif menu_selection == "➕ إدارة المنتجات والأسعار":
    st.subheader("إضافة أو تعديل منتج فردي")
    with st.form("product_form"):
        p_code = st.text_input("رقم الباركود")
        p_name = st.text_input("اسم الصنف")
        p_price = st.number_input("السعر بالريال", min_value=0.0, format="%.2f")
        p_cat = st.selectbox("القسم", ["أغذية", "مشروبات", "منظفات", "إلكترونيات", "أخرى"])
        
        save_product = st.form_submit_button("حفظ أو تحديث المنتج")
        
        if save_product:
            if p_code and p_name and p_price >= 0:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO products (barcode, name, price, category) 
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(barcode) 
                    DO UPDATE SET name=excluded.name, price=excluded.price, category=excluded.category
                ''', (p_code, p_name, p_price, p_cat))
                conn.commit()
                conn.close()
                st.success(f"تم حفظ الصنف ({p_name}) وتحديث سعره بنجاح!")
            else:
                st.error("الرجاء تعبئة الحقول الأساسية بشكل صحيح.")

# --- 4. اسعار المنتجات (رفع إكسل) ---
elif menu_selection == "📁 اسعار المنتجات (رفع إكسل)":
    st.subheader("استيراد اسعار المنتجات عبر ملف (CSV / Excel)")
    st.markdown("""
    **تعليمات الملف:**
    يجب أن يحتوي الملف على الأعمدة التالية باللغة الإنجليزية لضمان القراءة الصحيحة:
    - `barcode` (رقم الباركود)
    - `name` (اسم المنتج)
    - `price` (السعر)
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
                    p_cat = str(row.get('category', 'أخرى'))
                    
                    if b_code and p_name:
                        cursor.execute('''
                            INSERT INTO products (barcode, name, price, category) 
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(barcode) 
                            DO UPDATE SET name=excluded.name, price=excluded.price, category=excluded.category
                        ''', (b_code, p_name, p_price, p_cat))
                        success_count += 1
                        
                conn.commit()
                conn.close()
                st.success(f"تم بنجاح استيراد وتحديث {success_count} منتجاً في قاعدة البيانات!")
        except Exception as e:
            st.error(f"حدث خطأ أثناء قراءة الملف: {e}")

# --- 5. كل المنتجات ---
elif menu_selection == "📋 كل المنتجات":
    st.subheader("قائمة أصناف وسعار المنتجات المسجلة")
    conn = get_connection()
    prod_df = pd.read_sql_query("SELECT barcode AS 'الباركود', name AS 'اسم الصنف', price AS 'السعر (ر.س)', category AS 'القسم' FROM products", conn)
    conn.close()
    if not prod_df.empty:
        st.dataframe(prod_df, use_container_width=True)
    else:
        st.info("لا توجد أصناف مسجلة حتى الآن.")
