import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash
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
# CREATE SUPER ADMIN - SUPABASE VERSION
# ============================================================
def create_super_admin():
    """Create Super Admin user in Supabase"""
    
    try:
        # =========================
        # CHECK IF ADMIN EXISTS
        # =========================
        admin_result = supabase.table('users').select('*').eq('username', 'admin').execute()
        
        if admin_result.data:
            print("⚠️ Admin Already Exists")
            print(f"👤 Username: admin")
            print(f"🔑 Password: Admin@123")
            return
        
        # =========================
        # CHECK/CREATE SUPER ADMIN ROLE
        # =========================
        role_result = supabase.table('roles').select('*').eq('name', 'Super Admin').execute()
        
        if role_result.data:
            role = role_result.data[0]
            print("✅ Super Admin role found")
        else:
            # Create Super Admin role
            role_data = {
                'name': 'Super Admin',
                'description': 'Super Administrator with full system access',
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            role_result = supabase.table('roles').insert(role_data).execute()
            role = role_result.data[0]
            print("✅ Super Admin role created")
        
        # =========================
        # CREATE ADMIN USER
        # =========================
        admin_data = {
            'username': 'admin',
            'email': 'admin@chameleon.com',
            'password': generate_password_hash('Admin@123'),
            'full_name': 'System Administrator',
            'role': 'super_admin',
            'is_active': True,
            'created_at': datetime.now().isoformat()
        }
        
        admin_result = supabase.table('users').insert(admin_data).execute()
        admin = admin_result.data[0]
        
        print(f"✅ Admin user created with ID: {admin['id']}")
        
        # =========================
        # ASSIGN ADMIN TO SUPER ADMIN ROLE
        # =========================
        # Check if already assigned
        user_role_result = supabase.table('user_roles')\
            .select('*')\
            .eq('user_id', admin['id'])\
            .eq('role_id', role['id'])\
            .execute()
        
        if not user_role_result.data:
            # Assign role
            user_role_data = {
                'user_id': admin['id'],
                'role_id': role['id']
            }
            supabase.table('user_roles').insert(user_role_data).execute()
            print("✅ Admin assigned to Super Admin role")
        else:
            print("✅ Admin already assigned to Super Admin role")
        
        # =========================
        # CHECK/INSERT DEFAULT SETTINGS
        # =========================
        settings_result = supabase.table('settings').select('*').eq('id', 1).execute()
        if not settings_result.data:
            settings_data = {
                'id': 1,
                'logo_url': None,
                'logo_public_id': None,
                'created_at': datetime.now().isoformat()
            }
            supabase.table('settings').insert(settings_data).execute()
            print("✅ Default settings created")
        
        print("=" * 50)
        print("🎉 SUPER ADMIN CREATED SUCCESSFULLY")
        print("=" * 50)
        print("👤 Username: admin")
        print("🔑 Password: Admin@123")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error Creating Admin: {str(e)}")


# ============================================================
# CREATE PERMISSIONS (Optional - Add if needed)
# ============================================================
def create_default_permissions():
    """Create default permissions in Supabase"""
    permissions = [
        "view_dashboard",
        "manage_users",
        "manage_roles",
        "manage_permissions",
        "assign_students",
        "view_students",
        "edit_students",
        "delete_students",
        "import_excel",
        "export_excel",
        "view_reports"
    ]
    
    for perm_name in permissions:
        result = supabase.table('permissions').select('*').eq('name', perm_name).execute()
        if not result.data:
            supabase.table('permissions').insert({'name': perm_name}).execute()
            print(f"✅ Permission '{perm_name}' created")
    
    print("✅ All default permissions created")


# ============================================================
# RUN CREATE ADMIN
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🔧 CREATING SUPER ADMIN (Supabase Version)")
    print("=" * 50)
    create_super_admin()