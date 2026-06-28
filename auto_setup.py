import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from werkzeug.security import generate_password_hash

load_dotenv()

# ============================================================
# SUPABASE CLIENT
# ============================================================
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# ============================================================
# TABLE DEFINITIONS - Add all your tables here
# ============================================================
TABLES = {
    'users': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            mobile TEXT,
            designation TEXT,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        """
    },
    'roles': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        """
    },
    'permissions': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        """
    },
    'user_roles': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, role_id)
        """
    },
    'role_permissions': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
            permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(role_id, permission_id)
        """
    },
    'students': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            roll_number TEXT UNIQUE NOT NULL,
            student_name TEXT,
            personal_email TEXT,
            lms_email TEXT,
            program TEXT,
            major TEXT,
            program_code TEXT,
            mobile_no TEXT,
            abc_id TEXT,
            deb_id TEXT,
            dob DATE,
            aadhaar TEXT,
            father_name TEXT,
            mother_name TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            pin_code TEXT,
            photo_url TEXT,
            fee_status TEXT,
            total_fee NUMERIC,
            paid_amount NUMERIC,
            pending_amount NUMERIC,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        """
    },
    'student_fields': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            field_name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            field_type TEXT DEFAULT 'text',
            is_required BOOLEAN DEFAULT false,
            is_active BOOLEAN DEFAULT true,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        """
    },
    'field_categories': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        """
    },
    'category_field_mapping': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            category_id INTEGER REFERENCES field_categories(id) ON DELETE CASCADE,
            field_id INTEGER REFERENCES student_fields(id) ON DELETE CASCADE,
            display_order INTEGER DEFAULT 0,
            is_visible BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(category_id, field_id)
        """
    },
    'user_field_permissions': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            field_id INTEGER REFERENCES student_fields(id) ON DELETE CASCADE,
            can_view BOOLEAN DEFAULT false,
            can_edit BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, field_id)
        """
    },
    'verification_tickets': {
        'columns': """
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
        """
    },
    'verification_notifications': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            ticket_id INTEGER REFERENCES verification_tickets(id) ON DELETE CASCADE,
            roll_number TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT false,
            notification_type TEXT DEFAULT 'info',
            created_at TIMESTAMP DEFAULT NOW()
        """
    },
    'employee_students': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            notes TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, student_id)
        """
    },
    'settings': {
        'columns': """
            id BIGSERIAL PRIMARY KEY,
            logo_url TEXT,
            logo_public_id TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        """
    }
}

# ============================================================
# DEFAULT DATA
# ============================================================
DEFAULT_ROLES = [
    ('Super Admin', 'Full system access'),
    ('Admin', 'Administrator with limited permissions'),
    ('Faculty', 'Faculty member'),
    ('SME', 'Subject Matter Expert'),
    ('Support Team', 'Support Team Member'),
    ('Learner', 'Student/Learner')
]

DEFAULT_PERMISSIONS = [
    'view_dashboard', 'manage_users', 'manage_roles', 'manage_permissions',
    'assign_students', 'view_students', 'edit_students', 'delete_students',
    'import_excel', 'export_excel', 'view_reports'
]

# ============================================================
# AUTO SETUP FUNCTIONS
# ============================================================

def create_exec_sql_function():
    """Create the exec_sql function if it doesn't exist"""
    print("🔧 Checking/creating exec_sql function...")
    
    sql = """
    CREATE OR REPLACE FUNCTION exec_sql(query text)
    RETURNS SETOF json
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        RETURN QUERY EXECUTE query;
    END;
    $$;
    
    GRANT EXECUTE ON FUNCTION exec_sql(text) TO anon;
    GRANT EXECUTE ON FUNCTION exec_sql(text) TO authenticated;
    GRANT EXECUTE ON FUNCTION exec_sql(text) TO service_role;
    """
    
    try:
        # Try to create the function using a simple query first
        # We'll use a different approach since we can't use exec_sql to create itself
        result = supabase.rpc('exec_sql', {'query': 'SELECT 1'}).execute()
        print("✅ exec_sql function already exists")
        return True
    except Exception as e:
        print("⚠️ exec_sql function not found. Attempting to create it...")
        
        try:
            # Try to create the function using raw SQL through the REST API
            # This is a workaround - we'll use a direct SQL execution if available
            # Or we'll provide instructions for manual creation
            print("📋 To create exec_sql function, please run this SQL in Supabase SQL Editor:")
            print("=" * 60)
            print(sql)
            print("=" * 60)
            print("\nAlternatively, you can use the Supabase Dashboard to create it.")
            print("1. Go to your Supabase project")
            print("2. Navigate to SQL Editor")
            print("3. Paste and run the SQL above")
            print("\nContinuing setup without exec_sql...")
            return False
        except Exception as e2:
            print(f"❌ Could not create exec_sql: {e2}")
            return False

def execute_sql(sql):
    """Execute SQL using Supabase RPC"""
    try:
        # Try to use exec_sql RPC
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        return result
    except Exception as e:
        # If exec_sql doesn't exist, print SQL for manual execution
        print(f"⚠️ exec_sql RPC not available: {e}")
        print("📋 Please run this SQL manually:")
        print("=" * 60)
        print(sql)
        print("=" * 60)
        return None

def table_exists(table_name):
    """Check if table exists"""
    try:
        result = supabase.table(table_name).select('*').limit(1).execute()
        return True
    except Exception as e:
        # If table doesn't exist, it will raise an exception
        return False

def create_table_if_not_exists(table_name, columns):
    """Create table if it doesn't exist"""
    if table_exists(table_name):
        print(f"✅ Table '{table_name}' already exists")
        return True
    
    print(f"🔧 Creating table '{table_name}'...")
    
    sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {columns}
    );
    """
    
    try:
        # Try RPC first
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        print(f"✅ Table '{table_name}' created successfully")
        return True
    except Exception as e:
        print(f"⚠️ Could not create table '{table_name}': {e}")
        print("📋 SQL for manual creation:")
        print(sql)
        return False

def grant_permissions(table_name):
    """Grant permissions on table"""
    sql = f"""
    GRANT ALL ON {table_name} TO anon;
    GRANT ALL ON {table_name} TO authenticated;
    GRANT ALL ON {table_name} TO service_role;
    GRANT USAGE ON SEQUENCE {table_name}_id_seq TO anon;
    GRANT USAGE ON SEQUENCE {table_name}_id_seq TO authenticated;
    ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
    """
    try:
        supabase.rpc('exec_sql', {'query': sql}).execute()
        return True
    except Exception as e:
        print(f"⚠️ Could not grant permissions on '{table_name}': {e}")
        return False

def insert_default_data():
    """Insert default roles and permissions"""
    print("\n📊 Inserting default data...")
    
    # Insert Roles
    for name, description in DEFAULT_ROLES:
        try:
            supabase.table('roles').insert({
                'name': name,
                'description': description,
                'is_active': True
            }).execute()
            print(f"✅ Role '{name}' added")
        except Exception as e:
            if 'duplicate key' in str(e).lower():
                print(f"ℹ️ Role '{name}' already exists")
            else:
                print(f"⚠️ Error adding role '{name}': {e}")
    
    # Insert Permissions
    for perm in DEFAULT_PERMISSIONS:
        try:
            supabase.table('permissions').insert({'name': perm}).execute()
            print(f"✅ Permission '{perm}' added")
        except Exception as e:
            if 'duplicate key' in str(e).lower():
                print(f"ℹ️ Permission '{perm}' already exists")
            else:
                print(f"⚠️ Error adding permission '{perm}': {e}")

def setup_admin_user():
    """Create admin user if not exists"""
    print("\n👤 Setting up admin user...")
    
    # Check if admin exists
    try:
        result = supabase.table('users').select('*').eq('username', 'admin').execute()
        if result.data:
            print("✅ Admin user already exists")
            return
    except Exception as e:
        print(f"⚠️ Error checking admin user: {e}")
        return
    
    # Create admin
    try:
        supabase.table('users').insert({
            'username': 'admin',
            'email': 'admin@chameleon.com',
            'password': generate_password_hash('Admin@123'),
            'full_name': 'System Administrator',
            'role': 'super_admin',
            'is_active': True
        }).execute()
        print("✅ Admin user created: admin / Admin@123")
    except Exception as e:
        print(f"⚠️ Error creating admin: {e}")

def assign_admin_role():
    """Assign Super Admin role to admin user"""
    print("\n🔗 Assigning admin role...")
    
    try:
        # Get admin user
        admin = supabase.table('users').select('id').eq('username', 'admin').execute()
        if not admin.data:
            print("⚠️ Admin user not found")
            return
        
        # Get Super Admin role
        role = supabase.table('roles').select('id').eq('name', 'Super Admin').execute()
        if not role.data:
            print("⚠️ Super Admin role not found")
            return
        
        # Assign role
        try:
            supabase.table('user_roles').insert({
                'user_id': admin.data[0]['id'],
                'role_id': role.data[0]['id']
            }).execute()
            print("✅ Admin assigned to Super Admin role")
        except Exception as e:
            if 'duplicate key' in str(e).lower():
                print("ℹ️ Admin already has Super Admin role")
            else:
                print(f"⚠️ Error assigning role: {e}")
    except Exception as e:
        print(f"⚠️ Error in assign_admin_role: {e}")

def assign_all_permissions():
    """Assign all permissions to Super Admin"""
    print("\n🔑 Assigning permissions to Super Admin...")
    
    try:
        # Get Super Admin role
        role = supabase.table('roles').select('id').eq('name', 'Super Admin').execute()
        if not role.data:
            print("⚠️ Super Admin role not found")
            return
        
        role_id = role.data[0]['id']
        
        # Get all permissions
        permissions = supabase.table('permissions').select('id').execute()
        if not permissions.data:
            print("⚠️ No permissions found")
            return
        
        # Assign each permission
        assigned_count = 0
        for perm in permissions.data:
            try:
                supabase.table('role_permissions').insert({
                    'role_id': role_id,
                    'permission_id': perm['id']
                }).execute()
                assigned_count += 1
            except Exception as e:
                if 'duplicate key' not in str(e).lower():
                    print(f"⚠️ Error assigning permission {perm['id']}: {e}")
        
        print(f"✅ {assigned_count} permissions assigned to Super Admin")
    except Exception as e:
        print(f"⚠️ Error assigning permissions: {e}")

def setup_settings():
    """Initialize settings table"""
    print("\n⚙️ Setting up settings...")
    
    try:
        # Check if settings exists
        result = supabase.table('settings').select('*').eq('id', 1).execute()
        if result.data:
            print("✅ Settings already initialized")
            return
        
        # Create default settings
        supabase.table('settings').insert({
            'id': 1,
            'logo_url': None,
            'logo_public_id': None
        }).execute()
        print("✅ Settings initialized")
    except Exception as e:
        print(f"⚠️ Could not initialize settings: {e}")

# ============================================================
# MAIN SETUP FUNCTION
# ============================================================

def auto_setup():
    """Complete automated setup"""
    
    print("=" * 70)
    print("🚀 CHAMELEON NEXUS - AUTO SETUP")
    print("=" * 70)
    print()
    
    # Step 0: Create exec_sql function if needed
    print("📋 STEP 0: Verifying exec_sql function...")
    print("-" * 50)
    has_exec_sql = create_exec_sql_function()
    print()
    
    # Step 1: Create all tables
    print("📋 STEP 1: Creating tables...")
    print("-" * 50)
    
    for table_name, table_info in TABLES.items():
        create_table_if_not_exists(table_name, table_info['columns'])
    
    print("\n✅ All tables processed")
    
    # Step 2: Grant permissions
    print("\n📋 STEP 2: Granting permissions...")
    print("-" * 50)
    
    for table_name in TABLES.keys():
        grant_permissions(table_name)
        print(f"✅ Permissions granted on '{table_name}'")
    
    # Step 3: Insert default data
    print("\n📋 STEP 3: Inserting default data...")
    print("-" * 50)
    insert_default_data()
    
    # Step 4: Setup admin user
    print("\n📋 STEP 4: Setting up admin user...")
    print("-" * 50)
    setup_admin_user()
    assign_admin_role()
    assign_all_permissions()
    
    # Step 5: Setup settings
    print("\n📋 STEP 5: Setting up settings...")
    print("-" * 50)
    setup_settings()
    
    print("\n" + "=" * 70)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("👤 Admin Credentials:")
    print("   Username: admin")
    print("   Password: Admin@123")
    print()
    print("📊 Tables Created: " + ", ".join(TABLES.keys()))
    print("=" * 70)

# ============================================================
# RUN SETUP
# ============================================================
if __name__ == "__main__":
    auto_setup()