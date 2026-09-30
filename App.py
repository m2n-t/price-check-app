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
        'Exhibition Manager': 'مدير المعرض',
        'Department Supervisor': 'مشرف قسم',
        'Department Employee': 'موظف قسم',
        'مدير النظام': 'مدير النظام',
        'مدير المعرض': 'مدير المعرض',
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
    
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [col[1] for col in cursor.fetchall()]
    if 'emp_name' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN emp_name TEXT DEFAULT ''")
    if 'branch_name' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN branch_name TEXT DEFAULT ''")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            offer_price REAL,
            category TEXT
        )
    ''')
    
    cursor.execute("PRAGMA table_info(products)")
    prod_cols = [col[1] for col in cursor.fetchall()]
    if 'offer_price' not in prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN offer_price REAL DEFAULT 0.0")
    if 'category' not in prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'أخرى'")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            login_time TEXT
        )
    ''')
    
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role, emp_name, branch_name) VALUES ('admin', '12345', 'General Manager', 'المدير العام', 'الفرع الرئيسي')")
        
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = 'md'")
    if not cursor.fetchone():
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role, emp_name, branch_name) VALUES ('Md', '0904', 'Exhibition Manager', 'مسؤول المعرض', 'الفرع الرئيسي')")
        
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
    st.markdown("<p style='text-align: center;'>النظام محمي ومخصص للاستخدام التجاري.</p>", unsafe_allow_html=True)
    
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
        "📁 اسعار المنتجات (رفع إكسل)", 
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
        "📁 Import Prices (Excel)", 
        "📋 All Products"
    ]

if st.sidebar.button(logout_label):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

st.sidebar.markdown("---")

if user_role in ['مدير النظام', 'مدير المعرض', 'مسؤول الفرع', 'admin', 'General Manager', 'Exhibition Manager']:
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
    if user_role in ['مدير النظام', 'مدير المعرض', 'مسؤول الفرع', 'admin', 'General Manager', 'Exhibition Manager']:
        st.subheader("إدارة المستخدمين وصلاحيات النظام")
        
        with st.form("user_form"):
            new_u = st.text_input("اسم المستخدم الجديد")
            new_emp = st.text_input("اسم الموظف / الفرع الفرعي (اختياري)")
            new_branch = st.text_input("اسم الفرع الرئيسي")
            new_p = st.text_input("كلمة المرور", type="password")
            
            new_role = st.selectbox(
                "الصلاحية (الدور الوظيفي)", 
                [
                    "General Manager",
                    "Exhibition Manager", 
                    "Department Supervisor", 
                    "Department Employee"
                ],
                format_func=lambda x: translate_role_to_arabic(x)
            )
            
            create_user_btn = st.form_submit_button("إنشاء الحساب")
            
            if create_user_btn:
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
                        st.error("اسم المستخدم موجود مسبقاً، اختر اسماً آخر.")
                else:
                    st.error("الرجاء إدخال اسم المستخدم وكلمة المرور على الأقل.")
                    
        st.markdown("---")
        st.subheader("📋 المستخدمون المسجلون في النظام")
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, role, branch_name, emp_name FROM users")
        all_users = cursor.fetchall()
        conn.close()
        
        if all_users:
            table_data = []
            for index, (u_name, pwd, role_val, b_name, e_name) in enumerate(all_users, start=1):
                table_data.append({
                    "اسم الفرع": b_name if b_name else e_name,
                    "الصلاحية": translate_role_to_arabic(role_val),
                    "كلمة المرور": pwd,
                    "اسم الموظف": e_name,
                    "اسم المستخدم": u_name,
                    "العدد": index,
                    "حذف": "⊖"
                })
            
            df_users = pd.DataFrame(table_data)
            
            # ترتيب الأعمدة بالتسلسل المطلوب (من اليمين لليسار)
            df_users = df_users[["اسم الفرع", "الصلاحية", "كلمة المرور", "اسم الموظف", "اسم المستخدم", "العدد", "حذف"]]
            
            # السماح بالتعديل الكامل على كافة خصائص الجدول ما عدا العدد وحذف
            edited_df = st.data_editor(
                df_users,
                disabled=["العدد"],
                hide_index=True,
                use_container_width=True,
                key="unified_users_grid"
            )
            
            conn = get_connection()
            cursor = conn.cursor()
            needs_rerun = False
            
            for _, row in edited_df.iterrows():
                u_n = row['اسم المستخدم']
                p_w = row['كلمة المرور']
                r_v = row['الصلاحية']
                b_n = row['اسم الفرع']
                e_n = row['اسم الموظف']
                del_action = row['حذف']
                
                if del_action != "⊖":
                    if u_n.lower() in ["admin", "md"]:
                        st.error(f"⚠ لا يمكن حذف حساب الإدارة الأساسي ({u_n}).")
                    elif u_n.lower() == st.session_state.username.lower():
                        st.error("⚠ لا يمكنك حذف الحساب الذي تستخدمه حالياً.")
                    else:
                        cursor.execute("DELETE FROM users WHERE username = ?", (u_n,))
                        conn.commit()
                        needs_rerun = True
                else:
                    reverse_mapping = {
                        'مدير النظام': 'General Manager',
                        'مدير المعرض': 'Exhibition Manager',
                        'مسؤول الفرع': 'Exhibition Manager',
                        'مشرف قسم': 'Department Supervisor',
                        'موظف قسم': 'Department Employee'
                    }
                    db_role = reverse_mapping.get(r_v, r_v)
                    cursor.execute("""
                        UPDATE users 
                        SET password = ?, role = ?, branch_name = ?, emp_name = ? 
                        WHERE username = ?
                    """, (p_w, db_role, b_n, e_n, u_n))
                    conn.commit()
            
            conn.close()
            if needs_rerun:
                st.success("تم الحذف بنجاح!")
                st.rerun()

        else:
            st.info("لا يوجد مستخدمون مسجلون حالياً.")

    else:
        st.error("⚠ عذراً، لا تملك صلاحية الوصول إلى هذه الصفحة.")

# --- 2. سجلات دخول المستخدمين ---
elif menu_selection in ["📊 سجلات دخول المستخدمين", "📊 Login Logs"]:
    if user_role in ['مدير النظام', 'مدير المعرض', 'مسؤول الفرع', 'admin', 'General Manager', 'Exhibition Manager']:
        st.subheader("📊 سجلات دخول المشرفين والمستخدمين إلى النظام")
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, login_time FROM login_logs ORDER BY id DESC")
        logs = cursor.fetchall()
        conn.close()
        
        if logs:
            for index, (log_id, u_name, l_time) in enumerate(logs, start=1):
                col_num, col_row1, col_row2 = st.columns([1, 4, 4])
                with col_num:
                    if st.button(f"⊖ {index}", key=f"del_log_{log_id}"):
                        conn = get_connection()
                        conn.cursor().execute("DELETE FROM login_logs WHERE id = ?", (log_id,))
                        conn.commit()
                        conn.close()
                        st.success("تم حذف السجل بنجاح!")
                        st.rerun()
                with col_row1:
                    st.markdown(f"**{u_name}**")
                with col_row2:
                    st.markdown(f"**{l_time}**")
                st.markdown("---")
        else:
            st.info("لا توجد سجلات دخول مسجلة حالياً.")
    else:
        st.error("⚠ عذراً، هذه الصفحة مخصصة لمدير النظام ومدير المعرض فقط.")

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
    if user_role in ['مدير النظام', 'مدير المعرض', 'مسؤول الفرع', 'مشرف قسم', 'admin', 'General Manager', 'Exhibition Manager', 'Department Supervisor']:
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
    if user_role in ['مدير النظام', 'مدير المعرض', 'مسؤول الفرع', 'مشرف قسم', 'admin', 'General Manager', 'Exhibition Manager', 'Department Supervisor']:
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
