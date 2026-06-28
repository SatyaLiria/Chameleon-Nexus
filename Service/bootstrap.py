import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# ============================================================
# SUPABASE CLIENT
# ============================================================
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_or_create_role(role_name, description=None):
    """Get existing role or create new one in Supabase"""
    if not description:
        description = f"{role_name} Role"
    
    # Check if role exists
    result = supabase.table('roles').select('*').eq('name', role_name).execute()
    if result.data:
        return result.data[0]
    
    # Create new role
    data = {
        'name': role_name,
        'description': description,
        'is_active': True,
        'created_at': datetime.now().isoformat()
    }
    result = supabase.table('roles').insert(data).execute()
    return result.data[0] if result.data else None

def get_or_create_permission(perm_name):
    """Get existing permission or create new one in Supabase"""
    result = supabase.table('permissions').select('*').eq('name', perm_name).execute()
    if result.data:
        return result.data[0]
    
    data = {'name': perm_name}
    result = supabase.table('permissions').insert(data).execute()
    return result.data[0] if result.data else None

def get_or_create_user(username, email, password, full_name, role_name='user'):
    """Get existing user or create new one in Supabase"""
    result = supabase.table('users').select('*').eq('username', username).execute()
    if result.data:
        return result.data[0]
    
    data = {
        'username': username,
        'email': email,
        'password': generate_password_hash(password),
        'full_name': full_name,
        'role': role_name,
        'is_active': True,
        'created_at': datetime.now().isoformat()
    }
    result = supabase.table('users').insert(data).execute()
    return result.data[0] if result.data else None

def assign_user_role(user_id, role_id):
    """Assign role to user in Supabase"""
    result = supabase.table('user_roles').select('*').eq('user_id', user_id).eq('role_id', role_id).execute()
    if result.data:
        return result.data[0]
    
    data = {'user_id': user_id, 'role_id': role_id}
    result = supabase.table('user_roles').insert(data).execute()
    return result.data[0] if result.data else None

def assign_role_permission(role_id, permission_id):
    """Assign permission to role in Supabase"""
    result = supabase.table('role_permissions').select('*').eq('role_id', role_id).eq('permission_id', permission_id).execute()
    if result.data:
        return result.data[0]
    
    data = {'role_id': role_id, 'permission_id': permission_id}
    result = supabase.table('role_permissions').insert(data).execute()
    return result.data[0] if result.data else None

# ============================================================
# MAIN BOOTSTRAP FUNCTION
# ============================================================
def bootstrap_system():
    print("=" * 50)
    print("🚀 BOOTSTRAP STARTED (Supabase Version)")
    print("=" * 50)
    
    # =========================
    # CREATE ROLES
    # =========================
    roles = ["Super Admin", "Admin", "Faculty", "SME", "Support Team", "Learner"]
    role_ids = {}
    
    for role_name in roles:
        role = get_or_create_role(role_name)
        if role:
            role_ids[role_name] = role['id']
            print(f"✅ Role '{role_name}' ready")
    
    # =========================
    # CREATE PERMISSIONS
    # =========================
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
    
    permission_ids = {}
    
    for perm_name in permissions:
        perm = get_or_create_permission(perm_name)
        if perm:
            permission_ids[perm_name] = perm['id']
            print(f"✅ Permission '{perm_name}' ready")
    
    # =========================
    # CREATE ADMIN USER
    # =========================
    admin = get_or_create_user(
        username="admin",
        email="admin@chameleon.com",
        password="Admin@123",
        full_name="System Administrator",
        role_name="super_admin"
    )
    
    if admin:
        print(f"✅ Admin user created/updated: {admin['username']} (ID: {admin['id']})")
    
    # =========================
    # ASSIGN ADMIN TO SUPER ADMIN ROLE
    # =========================
    if admin and 'Super Admin' in role_ids:
        user_role = assign_user_role(admin['id'], role_ids['Super Admin'])
        print(f"✅ Admin assigned to Super Admin role")
    
    # =========================
    # ASSIGN ALL PERMISSIONS TO SUPER ADMIN ROLE
    # =========================
    if 'Super Admin' in role_ids:
        super_admin_role_id = role_ids['Super Admin']
        
        for perm_name, perm_id in permission_ids.items():
            assign_role_permission(super_admin_role_id, perm_id)
        
        print(f"✅ All permissions assigned to Super Admin role")
    
    # =========================
    # CHECK SETTINGS TABLE
    # =========================
    try:
        settings_result = supabase.table('settings').select('*').eq('id', 1).execute()
        if not settings_result.data:
            supabase.table('settings').insert({
                'id': 1,
                'logo_url': None,
                'logo_public_id': None,
                'created_at': datetime.now().isoformat()
            }).execute()
            print("✅ Settings table initialized")
    except Exception as e:
        print(f"⚠️ Settings table check: {e}")
    
    print("=" * 50)
    print("🎉 BOOTSTRAP COMPLETED")
    print("=" * 50)
    print("👤 Username: admin")
    print("🔑 Password: Admin@123")
    print("=" * 50)


# ============================================================
# RUN BOOTSTRAP
# ============================================================
if __name__ == "__main__":
    bootstrap_system()