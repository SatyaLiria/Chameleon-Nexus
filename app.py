import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, request, url_for, flash, send_file, render_template_string, send_from_directory, jsonify, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import time
import pandas as pd
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import io
import csv

# Import cloudinary for photo uploads
import cloudinary
import cloudinary.uploader

# Import auto_setup
from auto_setup import auto_setup

# Load environment variables
load_dotenv()

# ============================================================
# PRODUCTION CONFIGURATION
# ============================================================
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
PORT = int(os.getenv('PORT', 5000))

# ============================================================
# SUPABASE CLIENT
# ============================================================
from supabase import create_client, Client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# ============================================================
# AUTO SETUP ON STARTUP
# ============================================================
def check_and_setup():
    """Check if setup is needed and run it"""
    try:
        # Check if users table exists
        supabase.table('users').select('*').limit(1).execute()
        print("✅ Database already setup")
        return True
    except Exception as e:
        print(f"⚠️ Database not setup or error: {e}")
        print("🔄 Running auto setup...")
        try:
            auto_setup()
            print("✅ Auto setup completed successfully!")
            return True
        except Exception as setup_error:
            print(f"❌ Auto setup failed: {setup_error}")
            return False

# Run setup check
check_and_setup()

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'ChameleonNexusSecretKey')

# Production settings
if not DEBUG:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ============================================================
# CONFIGURATION
# ============================================================
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xlsx', 'xls'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# ============================================================
# COLUMN MAPPING - Excel to Supabase
# ============================================================
COLUMN_MAPPING = {
    # Personal Information
    'Roll Number': 'roll_number',
    'Roll No': 'roll_number',
    'Roll No.': 'roll_number',
    'Student Name': 'student_name',
    'Personal Email': 'personal_email',
    'LMS Email': 'lms_email',
    'LMS Email I’d': 'lms_email',
    'Mobile Number': 'mobile_no',
    'Mobile No': 'mobile_no',
    'Mobile No.': 'mobile_no',
    'Date of Birth': 'dob',
    'DOB': 'dob',
    'Aadhaar': 'aadhaar',
    'Aadhar': 'aadhaar',
    
    # Academic Information
    'Program': 'program',
    'Major': 'major',
    'Program Code': 'program_code',
    'Final Status': 'final_status',
    'LMS Status': 'lms_status',
    'Source': 'source',
    
    # IDs
    'ABC ID': 'abc_id',
    'DEB ID': 'deb_id',
    
    # Family
    "Father's Name": 'father_name',
    'Father Name': 'father_name',
    "Mother's Name": 'mother_name',
    'Mother Name': 'mother_name',
    
    # Address
    'Address': 'address',
    'Communication Address': 'address',
    'City': 'city',
    'State': 'state',
    'Country': 'country',
    'PIN Code': 'pin_code',
    'Pincode': 'pin_code',
    
    # Admission
    'Admission Date': 'admission_date',
    'Intake': 'intake',
    'Year': 'year',
    'Current Semester': 'current_semester',
    'Semester Completed': 'semester_completed',
    'Semester Pending': 'semester_pending',
    
    # Academic Performance
    'Total Subjects': 'total_subjects',
    'Supplementary Subjects': 'supplementary_subjects',
    'Current CGPA': 'current_cgpa',
    'Degree Status': 'degree_status',
    'Degree Completion Date': 'degree_completion_date',
    
    # Fee
    'Student Category': 'student_category',
    'Fee Status': 'fee_status',
    'Fee Type': 'fee_type',
    'Total Fee': 'total_fee',
    'Paid Amount': 'paid_amount',
    'Pending Amount': 'pending_amount',
    'Scholarship': 'scholarship',
    'Loan Status': 'loan_status',
    'Payment History': 'payment_history',
    'Last Payment Date': 'last_payment_date',
    
    # Documents
    'Aadhaar Card': 'aadhaar_card',
    '10th Certificate': 'tenth_certificate',
    '12th Certificate': 'twelfth_certificate',
    'Graduation Certificate': 'graduation_certificate',
    
    # Verification
    'Verification Sent Mail': 'verification_sent_mail',
    'Student Confirmed Call': 'student_confirmed_call',
    'Pending Documents WhatsApp': 'pending_documents_whatsapp',
    
    # Social Media
    'LinkedIn Status': 'linkedin_status',
    'Coursera Status': 'coursera_status',
    'HBP Status': 'hbp_status',
    'EY Status': 'ey_status',
    'LinkedIn URL': 'linkedin_url',
    'Facebook URL': 'facebook_url',
    'Instagram URL': 'instagram_url',
    'Twitter URL': 'twitter_url',
    
    # Professional
    'Student Type': 'student_type',
    'Current Company': 'current_company',
    'Designation': 'designation',
    'Experience In Years': 'experience_in_years',
    'Annual CTC In Lac': 'annual_ctc_in_lac',
    'After MBA Accepted': 'after_mba_accepted',
    'Promotion History': 'promotion_history'
}

# ============================================================
# LOGIN MANAGER
# ============================================================
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

class User:
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password = user_data.get('password')
        self.full_name = user_data.get('full_name')
        self.mobile = user_data.get('mobile')
        self.designation = user_data.get('designation')
        self.role = user_data.get('role', 'user')
        self.is_active = user_data.get('is_active', True)
    
    @staticmethod
    def from_dict(data):
        return User(data)
    
    def get_id(self):
        return str(self.id)
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False

@login_manager.user_loader
def load_user(user_id):
    try:
        result = supabase.table('users').select('*').eq('id', str(user_id)).execute()
        if result.data:
            return User.from_dict(result.data[0])
        return None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_logo_url():
    try:
        result = supabase.table('settings').select('logo_url').eq('id', 1).execute()
        if result.data and result.data[0].get('logo_url'):
            return result.data[0]['logo_url']
    except:
        pass
    return None

def convert_to_dict(data):
    """Convert pandas Series to dict with proper types"""
    result = {}
    for key, value in data.items():
        if pd.isna(value):
            result[key] = None
        elif hasattr(value, 'isoformat'):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result

# ============================================================
# REQUIRE PERMISSION DECORATOR - UPDATED
# ============================================================
def require_permission(permission_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please login first!", "warning")
                return redirect(url_for("login"))
            
            # For Super Admin, bypass permission check
            if current_user.role == 'super_admin':
                return func(*args, **kwargs)
            
            # Check if user has permission
            try:
                # Get user roles
                user_roles_result = supabase.table('user_roles').select('*, roles(*)').eq('user_id', current_user.id).execute()
                
                # Get all role ids
                role_ids = [ur['role_id'] for ur in user_roles_result.data] if user_roles_result.data else []
                
                if not role_ids:
                    flash("Access Denied! No roles assigned.", "danger")
                    return "Access Denied", 403
                
                # Check if any role has the required permission
                role_perms_result = supabase.table('role_permissions').select('*, permissions(*)').in_('role_id', role_ids).execute()
                
                if role_perms_result.data:
                    for rp in role_perms_result.data:
                        if rp.get('permissions') and rp['permissions'].get('name') == permission_name:
                            return func(*args, **kwargs)
                
                flash(f"Access Denied! Missing permission: {permission_name}", "danger")
                return "Access Denied", 403
                
            except Exception as e:
                print(f"Permission check error: {e}")
                flash(f"Permission check error: {str(e)}", "danger")
                return "Access Denied", 403
                
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# ============================================================
# CONTEXT PROCESSOR
# ============================================================
@app.context_processor
def inject_logo():
    return dict(logo_url=get_logo_url())

# ============================================================
# ROUTES - AUTHENTICATION
# ============================================================

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        try:
            result = supabase.table('users').select('*').eq('username', username).execute()
            
            if not result.data:
                flash("❌ User not found!", "danger")
                return render_template("login.html")
            
            user_data = result.data[0]
            
            if check_password_hash(user_data['password'], password):
                user = User.from_dict(user_data)
                login_user(user)
                flash(f"✅ Welcome back, {user.full_name or user.username}!", "success")
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for("dashboard"))
            else:
                flash("❌ Invalid Password!", "danger")
                
        except Exception as e:
            flash(f"❌ Login error: {str(e)}", "danger")
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("✅ You have been logged out.", "info")
    return redirect(url_for("login"))

# ============================================================
# ROUTES - DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("admin_dashboard"))

@app.route("/admin")
@login_required
def admin_dashboard():
    try:
        users_result = supabase.table('users').select('*').execute()
        roles_result = supabase.table('roles').select('*').execute()
        permissions_result = supabase.table('permissions').select('*').execute()
        students_result = supabase.table('students').select('id', count='exact').execute()
        
        return render_template(
            "admin/dashboard.html",
            user=current_user,
            users=users_result.data if users_result.data else [],
            roles=roles_result.data if roles_result.data else [],
            permissions=permissions_result.data if permissions_result.data else [],
            total_students=students_result.count or 0
        )
    except Exception as e:
        flash(f"Error loading admin dashboard: {str(e)}", "danger")
        return render_template("admin/dashboard.html", user=current_user)

# ============================================================
# ROUTES - USER MANAGEMENT
# ============================================================

@app.route("/admin/users")
@login_required
@require_permission("manage_users")
def admin_users():
    try:
        # Fetch users
        users_result = supabase.table('users').select('*').execute()
        users = users_result.data if users_result.data else []
        
        # Fetch roles
        roles_result = supabase.table('roles').select('*').execute()
        roles = roles_result.data if roles_result.data else []
        
        # Fetch user_roles for each user
        for user in users:
            try:
                user_roles_result = supabase.table('user_roles').select('*, roles(*)').eq('user_id', user['id']).execute()
                user['roles'] = [r['roles'] for r in user_roles_result.data] if user_roles_result.data else []
            except Exception as e:
                print(f"Error fetching roles for user {user.get('username')}: {e}")
                user['roles'] = []
        
        return render_template("admin/users.html", users=users, roles=roles)
    except Exception as e:
        flash(f"Error loading users: {str(e)}", "danger")
        return render_template("admin/users.html", users=[], roles=[])

@app.route("/admin/users/create", methods=["POST"])
@login_required
def create_user():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    full_name = request.form.get("full_name")
    mobile = request.form.get("mobile")
    designation = request.form.get("designation")
    
    try:
        existing = supabase.table('users').select('*').eq('username', username).execute()
        if existing.data:
            flash("❌ Username already exists!", "danger")
            return redirect(url_for("admin_users"))
        
        existing_email = supabase.table('users').select('*').eq('email', email).execute()
        if existing_email.data:
            flash("❌ Email already exists!", "danger")
            return redirect(url_for("admin_users"))
        
        data = {
            'username': username,
            'email': email,
            'password': generate_password_hash(password),
            'full_name': full_name,
            'mobile': mobile,
            'designation': designation,
            'is_active': True
        }
        result = supabase.table('users').insert(data).execute()
        
        if result.data:
            flash(f"✅ User {username} created successfully!", "success")
        else:
            flash("❌ Failed to create user!", "danger")
            
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
    
    return redirect(url_for("admin_users"))

@app.route("/admin/users/assign-role", methods=["POST"])
@login_required
def assign_role():
    user_id = request.form.get("user_id")
    role_id = request.form.get("role_id")
    
    try:
        existing = supabase.table('user_roles').select('*').eq('user_id', user_id).eq('role_id', role_id).execute()
        if not existing.data:
            supabase.table('user_roles').insert({'user_id': user_id, 'role_id': role_id}).execute()
            flash("✅ Role assigned successfully!", "success")
        else:
            flash("⚠️ Role already assigned!", "warning")
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
    
    return redirect(url_for("admin_users"))

@app.route("/admin/users/remove-role", methods=["POST"])
@login_required
def remove_role():
    user_id = request.form.get("user_id")
    role_id = request.form.get("role_id")
    
    try:
        result = supabase.table('user_roles').delete().eq('user_id', user_id).eq('role_id', role_id).execute()
        if result.data:
            flash("✅ Role removed successfully!", "success")
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
    
    return redirect(url_for("admin_users"))

# ============================================================
# ROUTES - ROLE MANAGEMENT
# ============================================================

@app.route("/admin/roles")
@login_required
def admin_roles():
    try:
        roles_result = supabase.table('roles').select('*').execute()
        permissions_result = supabase.table('permissions').select('*').execute()
        role_permissions_result = supabase.table('role_permissions').select('*').execute()
        
        return render_template(
            "admin/roles.html",
            roles=roles_result.data if roles_result.data else [],
            permissions=permissions_result.data if permissions_result.data else [],
            role_permissions=role_permissions_result.data if role_permissions_result.data else []
        )
    except Exception as e:
        flash(f"Error loading roles: {str(e)}", "danger")
        return render_template("admin/roles.html", roles=[], permissions=[], role_permissions=[])

@app.route("/admin/roles/create", methods=["POST"])
@login_required
def create_role():
    role_name = request.form.get("role_name")
    description = request.form.get("description")
    responsibilities = request.form.get("responsibilities")
    
    try:
        existing = supabase.table('roles').select('*').eq('name', role_name).execute()
        if existing.data:
            flash("❌ Role already exists!", "danger")
            return redirect(url_for("admin_roles"))
        
        data = {
            'name': role_name,
            'description': description,
            'responsibilities': responsibilities,
            'is_active': True
        }
        result = supabase.table('roles').insert(data).execute()
        
        if result.data:
            flash(f"✅ Role {role_name} created successfully!", "success")
        else:
            flash("❌ Failed to create role!", "danger")
            
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
    
    return redirect(url_for("admin_roles"))

@app.route("/admin/roles/assign-permission", methods=["POST"])
@login_required
def assign_permission():
    role_id = request.form.get("role_id")
    permission_id = request.form.get("permission_id")
    
    try:
        existing = supabase.table('role_permissions').select('*').eq('role_id', role_id).eq('permission_id', permission_id).execute()
        if not existing.data:
            supabase.table('role_permissions').insert({'role_id': role_id, 'permission_id': permission_id}).execute()
            flash("✅ Permission assigned successfully!", "success")
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
    
    return redirect(url_for("admin_roles"))

# ============================================================
# ROUTES - COLUMN PERMISSIONS
# ============================================================

@app.route("/admin/column-permissions", methods=["GET", "POST"])
@login_required
def column_permissions():
    try:
        users_result = supabase.table('users').select('*').execute()
        users = users_result.data if users_result.data else []
        
        fields_result = supabase.table('student_fields').select('*').eq('is_active', True).order('sort_order').execute()
        fields = fields_result.data if fields_result.data else []
        
        if request.method == "POST":
            user_id = request.form.get("user_id")
            
            if not user_id:
                flash("⚠️ Please select a user!", "warning")
                return redirect(url_for("column_permissions"))
            
            # Clear existing permissions
            supabase.table('user_field_permissions').delete().eq('user_id', user_id).execute()
            
            # Save new permissions
            for field in fields:
                can_view = request.form.get(f"view_{field['id']}") == "on"
                can_edit = request.form.get(f"edit_{field['id']}") == "on"
                
                if can_view or can_edit:
                    supabase.table('user_field_permissions').insert({
                        'user_id': user_id,
                        'field_id': field['id'],
                        'can_view': can_view,
                        'can_edit': can_edit
                    }).execute()
            
            flash("✅ Column permissions updated successfully!", "success")
            return redirect(url_for("column_permissions"))
        
        # GET request
        user_permissions = {}
        for user in users:
            perms_result = supabase.table('user_field_permissions').select('*').eq('user_id', user['id']).execute()
            perm_dict = {}
            for p in perms_result.data if perms_result.data else []:
                perm_dict[p['field_id']] = {'can_view': p.get('can_view', False), 'can_edit': p.get('can_edit', False)}
            user_permissions[user['id']] = perm_dict
        
        return render_template(
            "admin/column_permissions.html",
            users=users,
            fields=fields,
            user_permissions=user_permissions,
            selected_user_id=None
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return render_template("admin/column_permissions.html", users=[], fields=[], user_permissions={})

# ============================================================
# ROUTES - CATEGORY MANAGEMENT
# ============================================================

@app.route("/admin/categories")
@login_required
def admin_categories():
    try:
        categories_result = supabase.table('field_categories').select('*').order('sort_order').execute()
        categories = categories_result.data if categories_result.data else []
        
        fields_result = supabase.table('student_fields').select('*').eq('is_active', True).execute()
        fields = fields_result.data if fields_result.data else []
        
        return render_template(
            "admin/categories.html",
            categories=categories,
            fields=fields
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return render_template("admin/categories.html", categories=[], fields=[])

@app.route("/admin/categories/create", methods=["POST"])
@login_required
def create_category():
    name = request.form.get("name")
    description = request.form.get("description")
    
    try:
        existing = supabase.table('field_categories').select('*').eq('name', name).execute()
        if existing.data:
            flash("❌ Category already exists!", "danger")
            return redirect(url_for("admin_categories"))
        
        count_result = supabase.table('field_categories').select('id', count='exact').execute()
        sort_order = (count_result.count or 0) + 1
        
        data = {
            'name': name,
            'description': description,
            'sort_order': sort_order,
            'is_active': True
        }
        result = supabase.table('field_categories').insert(data).execute()
        
        if result.data:
            flash(f"✅ Category '{name}' created successfully!", "success")
        else:
            flash("❌ Failed to create category!", "danger")
            
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
    
    return redirect(url_for("admin_categories"))

@app.route("/admin/categories/assign-multiple-fields", methods=["POST"])
@login_required
def assign_multiple_fields_to_category():
    category_id = request.form.get("category_id")
    field_ids = request.form.getlist("field_ids")
    
    if not category_id:
        flash("⚠️ Please select a category!", "warning")
        return redirect(url_for("admin_categories"))
    
    if not field_ids:
        flash("⚠️ Please select at least one field!", "warning")
        return redirect(url_for("admin_categories"))
    
    added = 0
    skipped = 0
    
    try:
        for field_id in field_ids:
            existing = supabase.table('category_field_mapping').select('*').eq('category_id', category_id).eq('field_id', field_id).execute()
            if existing.data:
                skipped += 1
                continue
            
            count_result = supabase.table('category_field_mapping').select('id', count='exact').eq('category_id', category_id).execute()
            display_order = (count_result.count or 0) + 1
            
            supabase.table('category_field_mapping').insert({
                'category_id': category_id,
                'field_id': field_id,
                'display_order': display_order,
                'is_visible': True
            }).execute()
            added += 1
        
        if added > 0:
            flash(f"✅ {added} fields assigned to category! ({skipped} already existed)", "success")
        else:
            flash(f"⚠️ No new fields assigned. {skipped} fields already existed.", "warning")
            
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
    
    return redirect(url_for("admin_categories"))

@app.route("/admin/categories/remove-field", methods=["POST"])
@login_required
def remove_field_from_category():
    mapping_id = request.form.get("mapping_id")
    
    try:
        result = supabase.table('category_field_mapping').delete().eq('id', mapping_id).execute()
        if result.data:
            flash("✅ Field removed from category!", "success")
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
    
    return redirect(url_for("admin_categories"))

@app.route("/admin/categories/delete/<int:category_id>")
@login_required
def delete_category(category_id):
    try:
        # Delete mappings first
        supabase.table('category_field_mapping').delete().eq('category_id', category_id).execute()
        # Delete category
        result = supabase.table('field_categories').delete().eq('id', category_id).execute()
        if result.data:
            flash(f"✅ Category deleted successfully!", "success")
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
    
    return redirect(url_for("admin_categories"))

# ============================================================
# ROUTES - STUDENT VERIFICATION
# ============================================================

@app.route("/admin/student-verification")
@login_required
def admin_student_verification():
    try:
        students_result = supabase.table('students').select('*').execute()
        students = students_result.data if students_result.data else []
        
        tickets_result = supabase.table('verification_tickets').select('*').execute()
        tickets = tickets_result.data if tickets_result.data else []
        
        ticket_count = supabase.table('verification_tickets').select('id', count='exact').eq('is_active', True).execute().count or 0
        notification_count = supabase.table('verification_notifications').select('id', count='exact').eq('is_read', False).execute().count or 0
        
        return render_template(
            "admin/Student_Profile_Verification_Form.html",
            students=students,
            student=None,
            tickets=tickets,
            all_fields=[],
            notification_count=notification_count,
            ticket_count=ticket_count,
            student_data={},
            ticket_status=None,
            ticket_number=None
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("admin_dashboard"))

@app.route("/student-verification/<roll_number>")
@login_required
def student_verification(roll_number):
    try:
        student_result = supabase.table('students').select('*').eq('roll_number', roll_number).execute()
        student = student_result.data[0] if student_result.data else None
        
        if not student:
            flash("Student not found!", "danger")
            return redirect(url_for("admin_dashboard"))
        
        tickets_result = supabase.table('verification_tickets').select('*').eq('roll_number', roll_number).order('submitted_at', desc=True).execute()
        tickets = tickets_result.data if tickets_result.data else []
        
        ticket_status = None
        ticket_number = None
        if tickets:
            ticket_status = tickets[0].get('status')
            ticket_number = tickets[0].get('ticket_number')
        
        # Get correction fields
        fields_result = supabase.table('student_fields').select('*').eq('is_active', True).order('sort_order').execute()
        all_fields = fields_result.data if fields_result.data else []
        
        return render_template(
            'admin/Student_Profile_Verification_Form.html',
            student=student,
            student_data=student,
            all_fields=all_fields,
            tickets=tickets,
            ticket_status=ticket_status,
            ticket_number=ticket_number,
            notification_count=0,
            ticket_count=0,
            students=[]
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("admin_dashboard"))

# ============================================================
# ROUTES - EXCEL UPLOAD
# ============================================================

@app.route("/admin/upload-verification-excel", methods=["POST"])
@login_required
def upload_verification_excel():
    try:
        if 'excel_file' not in request.files:
            flash("⚠️ No file selected!", "warning")
            return redirect(url_for("admin_student_verification"))
        
        file = request.files['excel_file']
        if file.filename == '':
            flash("⚠️ No file selected!", "warning")
            return redirect(url_for("admin_student_verification"))
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash("⚠️ Please upload a valid Excel file (.xlsx or .xls)!", "warning")
            return redirect(url_for("admin_student_verification"))
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read Excel file
        df = pd.read_excel(filepath)
        df.columns = df.columns.str.strip()
        
        # Apply column mapping
        df.rename(columns=COLUMN_MAPPING, inplace=True)
        
        # Get existing columns from Supabase table
        try:
            sample = supabase.table('students').select('*').limit(1).execute()
            existing_columns = list(sample.data[0].keys()) if sample.data else []
        except:
            existing_columns = []
        
        # Filter only valid columns
        valid_columns = [col for col in df.columns if col in existing_columns]
        df = df[valid_columns]
        
        # Process each row
        success_count = 0
        for _, row in df.iterrows():
            try:
                data = convert_to_dict(row)
                
                if data.get('roll_number'):
                    existing = supabase.table('students').select('*').eq('roll_number', data['roll_number']).execute()
                    if existing.data:
                        supabase.table('students').update(data).eq('roll_number', data['roll_number']).execute()
                    else:
                        supabase.table('students').insert(data).execute()
                    success_count += 1
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
        
        # Clean up
        os.remove(filepath)
        flash(f"✅ Excel file processed successfully! {success_count} records updated.", "success")
        return redirect(url_for("admin_student_verification"))
        
    except Exception as e:
        flash(f"❌ Error uploading file: {str(e)}", "danger")
        return redirect(url_for("admin_student_verification"))

# ============================================================
# ROUTES - SEARCH STUDENTS
# ============================================================

@app.route("/search-students")
@login_required
def search_students():
    query = request.args.get('q', '').strip()
    
    if len(query) < 1:
        return jsonify([])
    
    try:
        result = supabase.table('students').select('*').or_(
            f'roll_number.ilike.%{query}%,student_name.ilike.%{query}%'
        ).limit(20).execute()
        
        results = []
        for s in result.data if result.data else []:
            results.append({
                'id': s.get('id'),
                'roll_number': s.get('roll_number'),
                'student_name': s.get('student_name'),
                'lms_email': s.get('lms_email', ''),
                'mobile_no': s.get('mobile_no', ''),
                'program': s.get('program', ''),
                'major': s.get('major', ''),
                'abc_id': s.get('abc_id', ''),
                'deb_id': s.get('deb_id', '')
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/global-search")
@login_required
def global_search():
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    if len(query) < 1:
        flash("⚠️ Please enter a search term.", "warning")
        return redirect(request.referrer or url_for("dashboard"))
    
    results = {'students': [], 'tickets': [], 'notifications': []}
    
    if search_type in ['all', 'students']:
        try:
            result = supabase.table('students').select('*').or_(
                f'roll_number.ilike.%{query}%,student_name.ilike.%{query}%'
            ).limit(50).execute()
            
            for s in result.data if result.data else []:
                results['students'].append({
                    'id': s.get('id'),
                    'roll_number': s.get('roll_number'),
                    'student_name': s.get('student_name'),
                    'lms_email': s.get('lms_email', ''),
                    'mobile_no': s.get('mobile_no', ''),
                    'program': s.get('program', ''),
                    'major': s.get('major', '')
                })
        except:
            pass
    
    if search_type in ['all', 'tickets']:
        try:
            result = supabase.table('verification_tickets').select('*').or_(
                f'roll_number.ilike.%{query}%,student_name.ilike.%{query}%,ticket_number.ilike.%{query}%'
            ).limit(50).execute()
            results['tickets'] = result.data if result.data else []
        except:
            pass
    
    if search_type in ['all', 'notifications']:
        try:
            result = supabase.table('verification_notifications').select('*').or_(
                f'roll_number.ilike.%{query}%,message.ilike.%{query}%'
            ).limit(50).execute()
            results['notifications'] = result.data if result.data else []
        except:
            pass
    
    return render_template(
        "global_search_results.html",
        query=query,
        results=results,
        search_type=search_type
    )

# ============================================================
# ROUTES - STUDENT FORM
# ============================================================

@app.route("/student-form")
@login_required
def student_form():
    student_id = request.args.get('student_id')
    student = None
    student_data = {}
    photo_url = None
    
    if student_id:
        result = supabase.table('students').select('*').eq('id', student_id).execute()
        if result.data:
            student = result.data[0]
            student_data = student
            photo_url = student.get('photo_url')
    
    # Get all students for search
    all_students_result = supabase.table('students').select('*').execute()
    all_students = all_students_result.data if all_students_result.data else []
    
    students_list = []
    for s in all_students:
        students_list.append({
            'id': s.get('id'),
            'roll_number': s.get('roll_number'),
            'student_name': s.get('student_name'),
            'lms_email': s.get('lms_email', ''),
            'mobile_no': s.get('mobile_no', ''),
            'program': s.get('program', ''),
            'major': s.get('major', ''),
            'abc_id': s.get('abc_id', ''),
            'deb_id': s.get('deb_id', '')
        })
    
    # Get categories
    try:
        categories_result = supabase.table('field_categories').select('*').eq('is_active', True).order('sort_order').execute()
        categories = categories_result.data if categories_result.data else []
    except:
        categories = []
    
    category_fields = {}
    for category in categories:
        try:
            mappings_result = supabase.table('category_field_mapping').select('*, student_fields(*)').eq('category_id', category['id']).eq('is_visible', True).order('display_order').execute()
            fields = []
            for item in mappings_result.data if mappings_result.data else []:
                if item.get('student_fields'):
                    fields.append(item['student_fields'])
            category_fields[category['id']] = fields
        except:
            category_fields[category['id']] = []
    
    return render_template(
        "student_form.html",
        student=student,
        student_data=student_data,
        photo_url=photo_url,
        categories=categories,
        category_fields=category_fields,
        students_json=json.dumps(students_list)
    )

# ============================================================
# ROUTES - STUDENT RESULT
# ============================================================

@app.route("/student-result/<int:student_id>")
@login_required
def student_result(student_id):
    try:
        result = supabase.table('students').select('*').eq('id', student_id).execute()
        if not result.data:
            flash("❌ Student not found!", "danger")
            return redirect(url_for("dashboard"))
        
        student = result.data[0]
        
        # Get subject results (if table exists)
        try:
            subjects_result = supabase.table('student_subject_results').select('*').eq('student_id', student_id).order('semester').execute()
            subjects = subjects_result.data if subjects_result.data else []
        except:
            subjects = []
        
        semester_summary = {}
        semester_subjects = {}
        supplementary_list = []
        
        for sub in subjects:
            semester = sub.get('semester', 1)
            if semester not in semester_summary:
                semester_summary[semester] = {'subjects': 0, 'credits': 0, 'total_marks': 0, 'count': 0}
            semester_summary[semester]['subjects'] += 1
            semester_summary[semester]['credits'] += 4
            semester_summary[semester]['total_marks'] += sub.get('marks', 0)
            semester_summary[semester]['count'] += 1
            
            if semester not in semester_subjects:
                semester_subjects[semester] = []
            semester_subjects[semester].append(sub)
            
            if sub.get('is_supplementary', False):
                supplementary_list.append(sub)
        
        semester_results = []
        for sem, data in sorted(semester_summary.items()):
            avg_marks = data['total_marks'] / data['count'] if data['count'] > 0 else 0
            cgpa = round(avg_marks / 10, 2)
            semester_results.append({
                'semester': sem,
                'subjects': data['subjects'],
                'credits': data['credits'],
                'cgpa': cgpa
            })
        
        return render_template(
            "student_result.html",
            student=student,
            student_data=student,
            semester_results=semester_results,
            semester_subjects=semester_subjects,
            supplementary_list=supplementary_list,
            current_semester=max(semester_summary.keys()) if semester_summary else 1
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("dashboard"))

# ============================================================
# ROUTES - VIEW STUDENT
# ============================================================

@app.route("/student/<int:student_id>")
@login_required
def view_student(student_id):
    try:
        result = supabase.table('students').select('*').eq('id', student_id).execute()
        if not result.data:
            flash("❌ Student not found!", "danger")
            return redirect(url_for("dashboard"))
        
        student = result.data[0]
        return render_template("student_view.html", student=student)
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("dashboard"))

# ============================================================
# ROUTES - STUDENT VERIFICATION SUBMIT
# ============================================================

@app.route("/student-verification/submit", methods=["POST"])
@login_required
def submit_verification():
    try:
        roll_number = request.form.get('roll_number')
        declaration = request.form.get('declaration')
        agree = request.form.get('agree')
        
        if not roll_number:
            flash("❌ Roll number is required!", "danger")
            return redirect(url_for("admin_dashboard"))
        
        if not agree:
            flash("⚠️ Please agree to the Terms & Conditions!", "warning")
            return redirect(url_for("student_verification", roll_number=roll_number))
        
        # Get student data
        student_result = supabase.table('students').select('*').eq('roll_number', roll_number).execute()
        if not student_result.data:
            flash("❌ Student not found!", "danger")
            return redirect(url_for("admin_dashboard"))
        
        student = student_result.data[0]
        
        # Process corrections
        corrections = []
        correction_fields = []
        
        if declaration == 'correction':
            field_names = request.form.getlist('field_name[]')
            existing_details = request.form.getlist('existing_detail[]')
            correct_details = request.form.getlist('correct_detail[]')
            
            for i in range(len(field_names)):
                if field_names[i] and correct_details[i]:
                    corrections.append({
                        'field_name': field_names[i],
                        'existing_detail': existing_details[i] if i < len(existing_details) else '',
                        'correct_detail': correct_details[i]
                    })
                    correction_fields.append(field_names[i])
        
        # Process documents
        uploaded_files = []
        if 'documents' in request.files:
            files = request.files.getlist('documents')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    student_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(roll_number))
                    if not os.path.exists(student_folder):
                        os.makedirs(student_folder)
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    name, ext = os.path.splitext(filename)
                    filename = f"{name}_{timestamp}{ext}"
                    
                    file_path = os.path.join(student_folder, filename)
                    file.save(file_path)
                    uploaded_files.append(file_path)
        
        # Create ticket
        import random
        import string
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        ticket_number = f"TKT-{timestamp}-{random_str}"
        
        ticket_data = {
            'ticket_number': ticket_number,
            'roll_number': roll_number,
            'student_name': student.get('student_name'),
            'declaration': declaration,
            'corrections': json.dumps(corrections),
            'correction_fields': json.dumps(correction_fields),
            'documents': json.dumps(uploaded_files),
            'status': 'Pending',
            'is_active': True
        }
        supabase.table('verification_tickets').insert(ticket_data).execute()
        
        # Create notification
        supabase.table('verification_notifications').insert({
            'roll_number': roll_number,
            'message': f"New verification ticket {ticket_number} created",
            'notification_type': 'info'
        }).execute()
        
        flash(f"✅ Verification submitted successfully! Ticket: {ticket_number}", "success")
        return redirect(url_for("student_verification", roll_number=roll_number))
        
    except Exception as e:
        flash(f"❌ Error submitting verification: {str(e)}", "danger")
        return redirect(url_for("student_verification", roll_number=roll_number))

# ============================================================
# ROUTES - ADMIN TICKETS
# ============================================================

@app.route("/admin/verification-tickets")
@login_required
def admin_verification_tickets():
    try:
        tickets_result = supabase.table('verification_tickets').select('*').eq('is_active', True).order('submitted_at', desc=True).execute()
        tickets = tickets_result.data if tickets_result.data else []
        
        ticket_count = len(tickets)
        
        return render_template(
            "admin/verification_tickets.html",
            tickets=tickets,
            ticket_count=ticket_count
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return render_template("admin/verification_tickets.html", tickets=[], ticket_count=0)

@app.route("/admin/verification-ticket/<int:ticket_id>")
@login_required
def admin_verification_ticket(ticket_id):
    try:
        result = supabase.table('verification_tickets').select('*').eq('id', ticket_id).execute()
        if not result.data:
            flash("❌ Ticket not found!", "danger")
            return redirect(url_for("admin_verification_tickets"))
        
        ticket = result.data[0]
        corrections = json.loads(ticket.get('corrections', '[]')) if ticket.get('corrections') else []
        documents = json.loads(ticket.get('documents', '[]')) if ticket.get('documents') else []
        
        return render_template(
            "admin/verification_ticket_detail.html",
            ticket=ticket,
            corrections=corrections,
            documents=documents
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("admin_verification_tickets"))

@app.route("/admin/verification-ticket/<int:ticket_id>/review", methods=["POST"])
@login_required
def admin_review_ticket(ticket_id):
    try:
        action = request.form.get('action')
        notes = request.form.get('notes')
        
        if action not in ['approve', 'reject', 'close']:
            flash("❌ Invalid action!", "danger")
            return redirect(url_for("admin_verification_ticket", ticket_id=ticket_id))
        
        supabase.table('verification_tickets').update({
            'status': action.capitalize(),
            'review_notes': notes,
            'reviewed_at': datetime.now().isoformat()
        }).eq('id', ticket_id).execute()
        
        flash(f"✅ Ticket {action}d successfully!", "success")
        return redirect(url_for("admin_verification_tickets"))
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("admin_verification_tickets"))

# ============================================================
# ROUTES - ADMIN NOTIFICATIONS
# ============================================================

@app.route("/admin/verification-notifications")
@login_required
def admin_verification_notifications():
    try:
        notifications_result = supabase.table('verification_notifications').select('*').order('created_at', desc=True).execute()
        notifications = notifications_result.data if notifications_result.data else []
        
        notification_count = supabase.table('verification_notifications').select('id', count='exact').eq('is_read', False).execute().count or 0
        
        return render_template(
            "admin/verification_notifications.html",
            notifications=notifications,
            notification_count=notification_count
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return render_template("admin/verification_notifications.html", notifications=[], notification_count=0)

# ============================================================
# ROUTES - MY STUDENTS
# ============================================================

@app.route("/admin/my-students")
@login_required
def my_students():
    try:
        students_result = supabase.table('students').select('*').execute()
        students = students_result.data if students_result.data else []
        
        return render_template(
            "admin/my_students.html",
            students=students,
            visible_fields=[],
            total_students=len(students)
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return render_template("admin/my_students.html", students=[], visible_fields=[], total_students=0)

# ============================================================
# ROUTES - ASSIGN STUDENTS
# ============================================================

@app.route("/admin/assign-students", methods=["GET", "POST"])
@login_required
def assign_students():
    try:
        users_result = supabase.table('users').select('*').execute()
        users = users_result.data if users_result.data else []
        
        students_result = supabase.table('students').select('*').execute()
        students = students_result.data if students_result.data else []
        
        assigned_student_ids = {}
        for user in users:
            assigned_result = supabase.table('employee_students').select('student_id').eq('user_id', user['id']).execute()
            assigned_student_ids[user['id']] = [a['student_id'] for a in assigned_result.data] if assigned_result.data else []
        
        if request.method == "POST":
            user_id = request.form.get("user_id")
            student_ids = request.form.getlist("student_ids")
            notes = request.form.get("notes")
            
            if not student_ids:
                flash("⚠️ Please select at least one student!", "warning")
                return redirect(url_for("assign_students"))
            
            for sid in student_ids:
                existing = supabase.table('employee_students').select('*').eq('user_id', user_id).eq('student_id', sid).execute()
                if not existing.data:
                    supabase.table('employee_students').insert({
                        'user_id': user_id,
                        'student_id': sid,
                        'notes': notes,
                        'is_active': True
                    }).execute()
            
            flash(f"✅ {len(student_ids)} students assigned successfully!", "success")
            return redirect(url_for("assign_students"))
        
        return render_template(
            "admin/assign_students.html",
            users=users,
            students=students,
            assigned_student_ids=assigned_student_ids
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("admin_dashboard"))

# ============================================================
# ROUTES - LOGO MANAGEMENT
# ============================================================

@app.route("/admin/logo", methods=["GET"])
@login_required
def admin_logo():
    logo_url = get_logo_url()
    return render_template("admin/admin_logo.html", logo_url=logo_url)

@app.route("/admin/upload-logo", methods=["POST"])
@login_required
def upload_logo():
    if 'logo' not in request.files:
        flash('No file uploaded', 'danger')
        return redirect(url_for('admin_logo'))
    
    file = request.files['logo']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('admin_logo'))
    
    if not allowed_image_file(file.filename):
        flash('Invalid file type. Please upload PNG, JPG, or JPEG.', 'danger')
        return redirect(url_for('admin_logo'))
    
    try:
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET'),
            secure=True
        )
        
        upload_result = cloudinary.uploader.upload(
            file,
            folder="chameleon_nexus/logo",
            transformation=[
                {'width': 200, 'height': 80, 'crop': 'fill'},
                {'quality': 'auto'}
            ],
            overwrite=True
        )
        
        logo_url = upload_result['secure_url']
        public_id = upload_result['public_id']
        
        existing = supabase.table('settings').select('*').eq('id', 1).execute()
        
        if existing.data:
            old_public_id = existing.data[0].get('logo_public_id')
            if old_public_id:
                cloudinary.uploader.destroy(old_public_id)
            
            supabase.table('settings').update({
                'logo_url': logo_url,
                'logo_public_id': public_id,
                'updated_at': datetime.now().isoformat()
            }).eq('id', 1).execute()
        else:
            supabase.table('settings').insert({
                'id': 1,
                'logo_url': logo_url,
                'logo_public_id': public_id,
                'created_at': datetime.now().isoformat()
            }).execute()
        
        flash('✅ Logo uploaded successfully!', 'success')
        
    except Exception as e:
        flash(f'Error uploading logo: {str(e)}', 'danger')
    
    return redirect(url_for('admin_logo'))

@app.route("/admin/remove-logo", methods=["POST"])
@login_required
def remove_logo():
    try:
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET'),
            secure=True
        )
        
        result = supabase.table('settings').select('*').eq('id', 1).execute()
        if result.data and result.data[0].get('logo_public_id'):
            cloudinary.uploader.destroy(result.data[0]['logo_public_id'])
            supabase.table('settings').update({
                'logo_url': None,
                'logo_public_id': None,
                'updated_at': datetime.now().isoformat()
            }).eq('id', 1).execute()
            flash('✅ Logo removed successfully!', 'success')
        else:
            flash('No logo found to remove.', 'warning')
    except Exception as e:
        flash(f'Error removing logo: {str(e)}', 'danger')
    
    return redirect(url_for('admin_logo'))

# ============================================================
# ROUTES - DATA UPLOAD (UPDATED WITH AUTO-SYNC - FIXED)
# ============================================================

@app.route("/admin/data-upload")
@login_required
def data_upload():
    """Display the data upload page"""
    return render_template("admin/data_upload.html")

@app.route("/admin/upload-database", methods=["POST"])
@login_required
def upload_database():
    """Upload and auto-sync database file to Supabase"""
    try:
        if 'db_file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(url_for('data_upload'))
        
        file = request.files['db_file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('data_upload'))
        
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in ['csv', 'xlsx', 'xls', 'json']:
            flash('Unsupported file format. Please upload CSV or Excel files.', 'danger')
            return redirect(url_for('data_upload'))
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read file based on extension
        df = None
        
        if file_ext == 'csv':
            # Try different encodings for CSV
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'windows-1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    print(f"✅ CSV read with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Error with encoding {encoding}: {e}")
                    continue
            
            if df is None:
                try:
                    df = pd.read_csv(filepath, encoding='utf-8', engine='python')
                    print("✅ CSV read with utf-8 and python engine")
                except Exception as e:
                    flash(f'Cannot read CSV file: {str(e)}', 'danger')
                    return redirect(url_for('data_upload'))
        
        elif file_ext in ['xlsx', 'xls']:
            try:
                df = pd.read_excel(filepath)
                print("✅ Excel read successfully")
            except Exception as e:
                flash(f'Cannot read Excel file: {str(e)}', 'danger')
                return redirect(url_for('data_upload'))
        
        elif file_ext == 'json':
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
                print("✅ JSON read successfully")
            except Exception as e:
                flash(f'Cannot read JSON file: {str(e)}', 'danger')
                return redirect(url_for('data_upload'))
        
        if df is None or df.empty:
            flash('File is empty or could not be read', 'danger')
            return redirect(url_for('data_upload'))
        
        # Auto-sync schema to Supabase
        table_name = request.form.get('table_name', 'students')
        pk_column = request.form.get('primary_key', 'id')
        
        # Upload data with auto-schema sync
        upload_result = upload_dataframe_to_supabase(df, table_name, pk_column)
        
        try:
            os.remove(filepath)
        except:
            pass
        
        if upload_result.get('success'):
            flash(f"✅ {upload_result.get('message', 'File processed successfully!')}", "success")
            if upload_result.get('added_columns'):
                flash(f"📋 Added new columns: {', '.join(upload_result['added_columns'])}", "info")
        else:
            flash(f"❌ {upload_result.get('error', 'Unknown error')}", "danger")
            
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "danger")
    
    return redirect(url_for('data_upload'))

# ============================================================
# AUTO SCHEMA SYNC FUNCTIONS (UPDATED)
# ============================================================

def auto_sync_schema(table_name, df, pk_column='id'):
    """Automatically sync schema - create table and add missing columns"""
    try:
        added_columns = []
        existing_columns = []
        
        print(f"🔍 Checking table: {table_name}")
        print(f"📋 File columns: {list(df.columns)}")
        
        # Check if table exists and get existing columns
        try:
            # Try to get columns from information_schema using exec_sql
            col_query = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            col_result = supabase.rpc('exec_sql', {'query': col_query}).execute()
            
            if col_result.data:
                existing_columns = [c['column_name'] for c in col_result.data]
                print(f"✅ Table '{table_name}' exists with {len(existing_columns)} columns")
                print(f"📋 Existing columns: {existing_columns[:10]}...")
            else:
                # Try fallback method
                try:
                    sample = supabase.table(table_name).select('*').limit(1).execute()
                    if sample.data:
                        existing_columns = list(sample.data[0].keys())
                    else:
                        existing_columns = []
                except:
                    existing_columns = []
                    
        except Exception as e:
            print(f"⚠️ Could not get columns from information_schema: {e}")
            # Try fallback method
            try:
                sample = supabase.table(table_name).select('*').limit(1).execute()
                if sample.data:
                    existing_columns = list(sample.data[0].keys())
                else:
                    existing_columns = []
            except Exception as e2:
                print(f"❌ Table '{table_name}' may not exist: {e2}")
                return create_table_from_dataframe(table_name, df, pk_column)
        
        # If no existing columns found, create table
        if not existing_columns:
            print(f"⚠️ No columns found for '{table_name}'. Creating table...")
            return create_table_from_dataframe(table_name, df, pk_column)
        
        # Check for new columns
        file_columns = list(df.columns)
        new_columns = [col for col in file_columns if col not in existing_columns]
        
        if not new_columns:
            print(f"✅ No new columns to add. All {len(file_columns)} columns already exist.")
            return {'success': True, 'added_columns': [], 'existing_columns': existing_columns}
        
        print(f"📋 Found {len(new_columns)} new columns to add: {new_columns}")
        
        # Add each new column
        for col in new_columns:
            try:
                # Detect column type from data
                col_type = detect_column_type(df[col])
                print(f"🔧 Adding column: {col} with type: {col_type}")
                
                # Try to add column
                add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col} {col_type};"
                print(f"SQL: {add_column_sql}")
                
                result = supabase.rpc('exec_sql', {'query': add_column_sql}).execute()
                print(f"✅ Added column: {col} ({col_type})")
                added_columns.append(col)
                
            except Exception as e:
                print(f"⚠️ Failed to add column {col} with type {col_type}: {e}")
                # Try with TEXT type as fallback
                try:
                    add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col} TEXT;"
                    print(f"SQL (fallback): {add_column_sql}")
                    result = supabase.rpc('exec_sql', {'query': add_column_sql}).execute()
                    print(f"✅ Added column: {col} (TEXT - fallback)")
                    added_columns.append(col)
                except Exception as e2:
                    print(f"❌ Failed to add column {col} even with TEXT: {e2}")
        
        if added_columns:
            print(f"✅ Successfully added {len(added_columns)} new columns: {added_columns}")
        else:
            print(f"⚠️ No new columns were added. Please check the logs above.")
        
        return {'success': True, 'added_columns': added_columns, 'existing_columns': existing_columns}
        
    except Exception as e:
        print(f"❌ auto_sync_schema error: {str(e)}")
        return {'success': False, 'error': str(e)}

def detect_column_type(series):
    """Detect appropriate SQL column type from pandas Series"""
    # Remove NaN/None values for detection
    clean_series = series.dropna()
    
    if len(clean_series) == 0:
        return 'TEXT'
    
    sample = clean_series.iloc[0]
    
    # Check if it's a number
    try:
        if pd.api.types.is_numeric_dtype(series):
            if pd.api.types.is_integer_dtype(series):
                return 'INTEGER'
            else:
                return 'NUMERIC'
    except:
        pass
    
    # Check if it's a date
    try:
        pd.to_datetime(series, errors='raise')
        return 'DATE'
    except:
        pass
    
    # Check for boolean
    if set(clean_series.unique()).issubset({True, False, 1, 0, 'True', 'False', 'true', 'false'}):
        return 'BOOLEAN'
    
    # Default to TEXT
    return 'TEXT'

def create_table_from_dataframe(table_name, df, pk_column='id'):
    """Create a new table in Supabase from DataFrame"""
    try:
        # Build CREATE TABLE SQL
        columns = []
        for col in df.columns:
            col_type = detect_column_type(df[col])
            if col == pk_column:
                columns.append(f"{col} {col_type} PRIMARY KEY")
            else:
                columns.append(f"{col} {col_type}")
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(columns)}
        );
        """
        
        # Add id column if not present
        if pk_column not in df.columns:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id BIGSERIAL PRIMARY KEY,
                {', '.join(columns)}
            );
            """
        
        print(f"📋 Creating table: {table_name}")
        print(f"SQL: {create_sql}")
        
        try:
            supabase.rpc('exec_sql', {'query': create_sql}).execute()
            print(f"✅ Table '{table_name}' created successfully")
            
            # Grant permissions
            grant_sql = f"""
            GRANT ALL ON {table_name} TO anon;
            GRANT ALL ON {table_name} TO authenticated;
            GRANT ALL ON {table_name} TO service_role;
            ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
            """
            try:
                supabase.rpc('exec_sql', {'query': grant_sql}).execute()
            except:
                pass
            
            # Get created columns
            sample = supabase.table(table_name).select('*').limit(1).execute()
            existing_columns = list(sample.data[0].keys()) if sample.data else []
            
            return {'success': True, 'added_columns': existing_columns, 'existing_columns': existing_columns}
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to create table: {str(e)}'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def clean_date_value(value):
    """Clean date values before inserting into Supabase"""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        invalid_keywords = ['not available', 'na', 'n/a', 'null', 'none', 'not availabe', 'not applicable', 'unknown', 'nill']
        if value.lower() in invalid_keywords or value.lower().startswith('not'):
            return None
        try:
            from dateutil import parser
            parsed_date = parser.parse(value, fuzzy=False)
            return parsed_date.date().isoformat()
        except:
            return None
    return value

def clean_string_value(value):
    """Clean string values before inserting into Supabase"""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        if value.lower() in ['nan', 'none', 'null', '']:
            return None
    return value

def upload_dataframe_to_supabase(df, table_name='students', pk_column='id'):
    """Upload DataFrame to Supabase with auto-schema sync and proper upsert"""
    try:
        # First sync schema
        schema_result = auto_sync_schema(table_name, df, pk_column)
        
        if not schema_result['success']:
            return {'success': False, 'error': f'Schema sync failed: {schema_result["error"]}'}
        
        # Get existing columns after sync
        sample = supabase.table(table_name).select('*').limit(1).execute()
        existing_columns = list(sample.data[0].keys()) if sample.data else []
        
        # Filter columns
        valid_columns = [col for col in df.columns if col in existing_columns]
        
        if not valid_columns:
            return {'success': False, 'error': 'No matching columns found in the file'}
        
        # Keep only valid columns
        df_filtered = df[valid_columns].copy()
        
        # Clean data before conversion
        for col in df_filtered.columns:
            # Check if column might be a date column
            date_keywords = ['dob', 'date', 'birth', 'admission', 'completion', 'payment', 'created', 'updated']
            is_date_column = any(keyword in col.lower() for keyword in date_keywords)
            
            if is_date_column:
                df_filtered[col] = df_filtered[col].apply(clean_date_value)
            else:
                df_filtered[col] = df_filtered[col].apply(clean_string_value)
        
        # Convert to records
        records = df_filtered.to_dict('records')
        
        # Clean records
        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                if pd.isna(value) or value == 'nan' or value == '' or value == 'None':
                    cleaned_record[key] = None
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)
        
        if not cleaned_records:
            return {'success': False, 'error': 'No valid records to upload'}
        
        # IMPORTANT: Use UPSERT instead of INSERT for all operations
        try:
            # Use roll_number as the unique key for upsert
            upsert_column = 'roll_number' if 'roll_number' in existing_columns else pk_column
            
            print(f"📤 Upserting {len(cleaned_records)} records using column: {upsert_column}")
            
            result = supabase.table(table_name).upsert(
                cleaned_records, 
                on_conflict=upsert_column
            ).execute()
            
            return {
                'success': True, 
                'message': f'Upserted {len(cleaned_records)} records into {table_name}', 
                'added_columns': schema_result.get('added_columns', [])
            }
            
        except Exception as e:
            # If upsert fails, try one by one
            print(f"⚠️ Bulk upsert failed: {e}")
            print("🔄 Trying individual upserts...")
            
            success_count = 0
            failed_count = 0
            
            for record in cleaned_records:
                try:
                    roll_number = record.get('roll_number')
                    if roll_number:
                        existing = supabase.table(table_name).select('*').eq('roll_number', roll_number).execute()
                        if existing.data:
                            supabase.table(table_name).update(record).eq('roll_number', roll_number).execute()
                        else:
                            supabase.table(table_name).insert(record).execute()
                        success_count += 1
                    else:
                        supabase.table(table_name).insert(record).execute()
                        success_count += 1
                except Exception as e2:
                    failed_count += 1
                    print(f"⚠️ Failed for record: {e2}")
            
            if success_count > 0:
                return {
                    'success': True, 
                    'message': f'Processed {success_count} records successfully (failed: {failed_count})',
                    'added_columns': schema_result.get('added_columns', [])
                }
            else:
                return {'success': False, 'error': f'All {failed_count} records failed to upload'}
                
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ============================================================
# ROUTES - PHOTO UPLOAD (ENHANCED)
# ============================================================

@app.route("/admin/upload-photos", methods=["POST"])
@login_required
def upload_photos():
    """Upload multiple photos to Cloudinary"""
    try:
        if 'photos' not in request.files:
            flash('No files uploaded', 'danger')
            return redirect(url_for('data_upload'))
        
        files = request.files.getlist('photos')
        if not files or files[0].filename == '':
            flash('No files selected', 'danger')
            return redirect(url_for('data_upload'))
        
        folder = request.form.get('folder', 'chameleon_nexus/photos')
        upload_type = request.form.get('upload_type', 'student')
        
        uploaded_count = 0
        failed_count = 0
        
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET'),
            secure=True
        )
        
        for file in files:
            if file and allowed_image_file(file.filename):
                try:
                    if upload_type == 'student':
                        roll_number = os.path.splitext(file.filename)[0]
                        public_id = f"student_{roll_number}"
                    else:
                        public_id = os.path.splitext(file.filename)[0]
                    
                    upload_result = cloudinary.uploader.upload(
                        file,
                        folder=folder,
                        public_id=public_id,
                        transformation=[
                            {'width': 400, 'height': 400, 'crop': 'fill'},
                            {'quality': 'auto'}
                        ],
                        overwrite=True
                    )
                    
                    photo_url = upload_result['secure_url']
                    
                    if upload_type == 'student':
                        roll_number = os.path.splitext(file.filename)[0]
                        supabase.table('students').update({
                            'photo_url': photo_url
                        }).eq('roll_number', roll_number).execute()
                    
                    uploaded_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    print(f"Error uploading {file.filename}: {e}")
            else:
                failed_count += 1
        
        if uploaded_count > 0:
            flash(f"✅ {uploaded_count} photos uploaded successfully! ({failed_count} failed)", "success")
        else:
            flash(f"⚠️ No photos uploaded. {failed_count} failed.", "warning")
            
    except Exception as e:
        flash(f"❌ Error uploading photos: {str(e)}", "danger")
    
    return redirect(url_for('data_upload'))

# ============================================================
# ROUTES - EXPORT
# ============================================================

@app.route("/export/form-data")
@login_required
def export_form_data():
    try:
        tickets_result = supabase.table('verification_tickets').select('*').eq('is_active', True).execute()
        tickets = tickets_result.data if tickets_result.data else []
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Ticket Number', 'Roll Number', 'Student Name', 'LMS Email',
            'Program', 'Major', 'ABC ID', 'DEB ID', 'Date of Birth',
            'Aadhar', 'Mobile Number', "Father's Name", "Mother's Name",
            'Address', 'City', 'State', 'Country', 'PIN Code',
            'Declaration', 'Status', 'Submitted At'
        ])
        
        for ticket in tickets:
            writer.writerow([
                ticket.get('ticket_number', ''),
                ticket.get('roll_number', ''),
                ticket.get('student_name', ''),
                '',
                '', '', '', '', '',
                '', '', '', '',
                '', '', '', '', '',
                ticket.get('declaration', ''),
                ticket.get('status', ''),
                ticket.get('submitted_at', '')
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=verification_form_data_{datetime.now().strftime("%Y%m%d")}.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
        
    except Exception as e:
        flash(f"❌ Error exporting form data: {str(e)}", "danger")
        return redirect(request.referrer or url_for("admin_dashboard"))

@app.route("/export/tickets")
@login_required
def export_tickets():
    try:
        tickets_result = supabase.table('verification_tickets').select('*').eq('is_active', True).execute()
        tickets = tickets_result.data if tickets_result.data else []
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Ticket Number', 'Roll Number', 'Student Name', 'Declaration',
            'Status', 'Submitted At', 'Reviewed At', 'Review Notes'
        ])
        
        for ticket in tickets:
            writer.writerow([
                ticket.get('ticket_number', ''),
                ticket.get('roll_number', ''),
                ticket.get('student_name', ''),
                ticket.get('declaration', ''),
                ticket.get('status', ''),
                ticket.get('submitted_at', ''),
                ticket.get('reviewed_at', ''),
                ticket.get('review_notes', '')
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=tickets_{datetime.now().strftime("%Y%m%d")}.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
        
    except Exception as e:
        flash(f"❌ Error exporting tickets: {str(e)}", "danger")
        return redirect(request.referrer or url_for("admin_dashboard"))

@app.route("/export/notifications")
@login_required
def export_notifications():
    try:
        notifications_result = supabase.table('verification_notifications').select('*').order('created_at', desc=True).execute()
        notifications = notifications_result.data if notifications_result.data else []
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Notification ID', 'Roll Number', 'Message', 'Type', 'Is Read', 'Created At'
        ])
        
        for n in notifications:
            writer.writerow([
                n.get('id', ''),
                n.get('roll_number', ''),
                n.get('message', ''),
                n.get('notification_type', 'info'),
                'Yes' if n.get('is_read', False) else 'No',
                n.get('created_at', '')
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=notifications_{datetime.now().strftime("%Y%m%d")}.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
        
    except Exception as e:
        flash(f"❌ Error exporting notifications: {str(e)}", "danger")
        return redirect(request.referrer or url_for("admin_dashboard"))

# ============================================================
# ROUTES - API
# ============================================================

@app.route("/api/notification-count")
@login_required
def api_notification_count():
    try:
        count = supabase.table('verification_notifications').select('id', count='exact').eq('is_read', False).execute().count or 0
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'count': 0, 'error': str(e)})

# ============================================================
# RUN APP (Modified for Production)
# ============================================================

if __name__ == "__main__":
    # For production, use gunicorn instead of Flask's built-in server
    if DEBUG:
        app.run(debug=True, host='0.0.0.0', port=PORT)
    else:
        # For Render, they will use gunicorn
        app.run(host='0.0.0.0', port=PORT)