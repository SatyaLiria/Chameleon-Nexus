import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ============================================================
# SUPABASE CLIENT
# ============================================================
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# ============================================================
# CREATE TABLES USING SQL - SUPABASE VERSION
# ============================================================
def init_database():
    """Initialize database tables in Supabase using SQL"""
    
    print("=" * 50)
    print("🚀 INITIALIZING DATABASE (Supabase Version)")
    print("=" * 50)
    
    try:
        # ============================================================
        # USERS TABLE
        # ============================================================
        print("📋 Creating users table...")
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """
        supabase.table('users').execute()  # Placeholder - will check if table exists
        
        # ============================================================
        # ROLES TABLE
        # ============================================================
        print("📋 Creating roles table...")
        roles_sql = """
        CREATE TABLE IF NOT EXISTS roles (
            id BIGSERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        # ============================================================
        # PERMISSIONS TABLE
        # ============================================================
        print("📋 Creating permissions table...")
        permissions_sql = """
        CREATE TABLE IF NOT EXISTS permissions (
            id BIGSERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        # ============================================================
        # USER ROLES TABLE
        # ============================================================
        print("📋 Creating user_roles table...")
        user_roles_sql = """
        CREATE TABLE IF NOT EXISTS user_roles (
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
            UNIQUE(user_id, role_id)
        );
        """
        
        # ============================================================
        # ROLE PERMISSIONS TABLE
        # ============================================================
        print("📋 Creating role_permissions table...")
        role_permissions_sql = """
        CREATE TABLE IF NOT EXISTS role_permissions (
            id BIGSERIAL PRIMARY KEY,
            role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
            permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
            UNIQUE(role_id, permission_id)
        );
        """
        
        # ============================================================
        # STUDENTS TABLE
        # ============================================================
        print("📋 Creating students table...")
        students_sql = """
        CREATE TABLE IF NOT EXISTS students (
            id BIGSERIAL PRIMARY KEY,
            roll_number TEXT UNIQUE NOT NULL,
            student_name TEXT,
            program TEXT,
            major TEXT,
            lms_email TEXT,
            mobile_no TEXT,
            abc_id TEXT,
            deb_id TEXT,
            photo_url TEXT,
            dob DATE,
            aadhar TEXT,
            father_name TEXT,
            mother_name TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            pin_code TEXT,
            admission_date DATE,
            fee_status TEXT,
            pending_amount NUMERIC,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        # ============================================================
        # STUDENT FIELDS TABLE
        # ============================================================
        print("📋 Creating student_fields table...")
        student_fields_sql = """
        CREATE TABLE IF NOT EXISTS student_fields (
            id BIGSERIAL PRIMARY KEY,
            field_name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            field_type TEXT DEFAULT 'text',
            is_required BOOLEAN DEFAULT false,
            is_active BOOLEAN DEFAULT true,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        # ============================================================
        # USER FIELD PERMISSIONS TABLE
        # ============================================================
        print("📋 Creating user_field_permissions table...")
        user_field_permissions_sql = """
        CREATE TABLE IF NOT EXISTS user_field_permissions (
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            field_id INTEGER REFERENCES student_fields(id) ON DELETE CASCADE,
            can_view BOOLEAN DEFAULT false,
            can_edit BOOLEAN DEFAULT false,
            UNIQUE(user_id, field_id)
        );
        """
        
        # ============================================================
        # VERIFICATION TICKETS TABLE
        # ============================================================
        print("📋 Creating verification_tickets table...")
        verification_tickets_sql = """
        CREATE TABLE IF NOT EXISTS verification_tickets (
            id BIGSERIAL PRIMARY KEY,
            ticket_number TEXT UNIQUE NOT NULL,
            roll_number TEXT NOT NULL,
            student_name TEXT NOT NULL,
            declaration TEXT,
            status TEXT DEFAULT 'Pending',
            corrections TEXT,
            documents TEXT,
            correction_fields TEXT,
            submitted_by TEXT,
            submitted_at TIMESTAMP DEFAULT NOW(),
            reviewed_by TEXT,
            reviewed_at TIMESTAMP,
            review_notes TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        # ============================================================
        # VERIFICATION NOTIFICATIONS TABLE
        # ============================================================
        print("📋 Creating verification_notifications table...")
        verification_notifications_sql = """
        CREATE TABLE IF NOT EXISTS verification_notifications (
            id BIGSERIAL PRIMARY KEY,
            ticket_id INTEGER REFERENCES verification_tickets(id) ON DELETE CASCADE,
            roll_number TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT false,
            notification_type TEXT DEFAULT 'info',
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        # ============================================================
        # SETTINGS TABLE
        # ============================================================
        print("📋 Creating settings table...")
        settings_sql = """
        CREATE TABLE IF NOT EXISTS settings (
            id BIGSERIAL PRIMARY KEY,
            logo_url TEXT,
            logo_public_id TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        # ============================================================
        # CATEGORIES AND MAPPINGS TABLES
        # ============================================================
        print("📋 Creating field_categories table...")
        field_categories_sql = """
        CREATE TABLE IF NOT EXISTS field_categories (
            id BIGSERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        print("📋 Creating category_field_mapping table...")
        category_field_mapping_sql = """
        CREATE TABLE IF NOT EXISTS category_field_mapping (
            id BIGSERIAL PRIMARY KEY,
            category_id INTEGER REFERENCES field_categories(id) ON DELETE CASCADE,
            field_id INTEGER REFERENCES student_fields(id) ON DELETE CASCADE,
            display_order INTEGER DEFAULT 0,
            is_visible BOOLEAN DEFAULT true,
            UNIQUE(category_id, field_id)
        );
        """
        
        # ============================================================
        # EXECUTE ALL SQL QUERIES
        # ============================================================
        # Note: Supabase doesn't support executing raw SQL directly via client.
        # You need to use the SQL Editor in Supabase dashboard.
        
        print("""
        ⚠️ IMPORTANT: Supabase doesn't support creating tables via Python client.
        Please run the following SQL queries in Supabase SQL Editor:
        
        1. Go to Supabase Dashboard → SQL Editor
        2. Copy and paste the SQL statements above
        3. Run them one by one or all at once
        
        Or you can use the bootstrap.py script which creates everything.
        """)
        
        print("✅ Database initialization completed (manual SQL required)")
        
        # Check if tables exist
        check_tables()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Please use Supabase SQL Editor to create tables manually.")

# ============================================================
# CHECK IF TABLES EXIST
# ============================================================
def check_tables():
    """Check if tables exist in Supabase"""
    try:
        tables_to_check = ['users', 'roles', 'permissions', 'students', 'verification_tickets']
        
        print("\n🔍 Checking tables...")
        for table_name in tables_to_check:
            try:
                result = supabase.table(table_name).select('id', count='exact').limit(1).execute()
                print(f"✅ Table '{table_name}' exists")
            except Exception:
                print(f"❌ Table '{table_name}' does not exist")
                
    except Exception as e:
        print(f"⚠️ Error checking tables: {e}")

# ============================================================
# RUN INIT DATABASE
# ============================================================
if __name__ == "__main__":
    init_database()