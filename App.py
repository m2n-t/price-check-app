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

# تبويبات النظام بناءً على الصلاحيات
if st.session_state.role == 'admin':
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 فحص السعر", "➕ إدارة المنتجات والأسعار", "👥 إدارة المستخدمين", "📋 كل المنتجات"])
else:
    tab1, tab4 = st.tabs(["🔍 فحص السعر", "📋 كل المنتجات"])
    tab2 = None
    tab3 = None

# --- التبويب الأول: فحص السعر (متاح للجميع) ---
with tab1:
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

# --- التبويب الثاني: إدارة المنتجات (للمشرفين فقط) ---
if tab2:
    with tab2:
        st.subheader("إضافة أو تعديل أسعار المنتجات")
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

# --- التبويب الثالث: إدارة المستخدمين (للمشرف الأساسي/المدير فقط) ---
if tab3:
    with tab3:
        st.subheader("إضافة مستخدمين جدد للنظام (بدون حدود)")
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

# --- التبويب الرابع: استعراض جميع الأصناف (للجميع) ---
with tab4:
    st.subheader("قائمة أصناف السوبرماركت المسجلة")
    conn = get_connection()
    prod_df = pd.read_sql_query("SELECT barcode AS 'الباركود', name AS 'اسم الصنف', price AS 'السعر (ر.س)', category AS 'القسم' FROM products", conn)
    conn.close()
    if not prod_df.empty:
        st.dataframe(prod_df, use_container_width=True)
    else:
        st.info("لا توجد أصناف مسجلة حتى الآن.")
