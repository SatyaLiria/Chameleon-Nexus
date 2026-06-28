import os
from datetime import datetime
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
# INIT PERMISSIONS - SUPABASE VERSION
# ============================================================
def init_permissions():
    """Initialize roles and permissions in Supabase"""
    
    print("=" * 50)
    print("🔧 Initializing Roles & Permissions (Supabase Version)")
    print("=" * 50)
    
    try:
        # =========================
        # CREATE DEFAULT PERMISSIONS
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
            # Check if permission exists
            result = supabase.table('permissions').select('*').eq('name', perm_name).execute()
            
            if result.data:
                permission_ids[perm_name] = result.data[0]['id']
                print(f"✅ Permission '{perm_name}' already exists")
            else:
                # Create new permission
                data = {'name': perm_name}
                result = supabase.table('permissions').insert(data).execute()
                if result.data:
                    permission_ids[perm_name] = result.data[0]['id']
                    print(f"✅ Permission '{perm_name}' created")
        
        # =========================
        # CREATE SUPER ADMIN ROLE
        # =========================
        role_result = supabase.table('roles').select('*').eq('name', 'Super Admin').execute()
        
        if role_result.data:
            role = role_result.data[0]
            print(f"✅ Super Admin role already exists (ID: {role['id']})")
        else:
            role_data = {
                'name': 'Super Admin',
                'description': 'Super Administrator with full system access',
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            role_result = supabase.table('roles').insert(role_data).execute()
            role = role_result.data[0]
            print(f"✅ Super Admin role created (ID: {role['id']})")
        
        # =========================
        # ASSIGN ALL PERMISSIONS TO SUPER ADMIN
        # =========================
        super_admin_role_id = role['id']
        assigned_count = 0
        
        for perm_name, perm_id in permission_ids.items():
            # Check if permission already assigned
            existing = supabase.table('role_permissions')\
                .select('*')\
                .eq('role_id', super_admin_role_id)\
                .eq('permission_id', perm_id)\
                .execute()
            
            if not existing.data:
                # Assign permission
                data = {
                    'role_id': super_admin_role_id,
                    'permission_id': perm_id
                }
                supabase.table('role_permissions').insert(data).execute()
                assigned_count += 1
                print(f"✅ Permission '{perm_name}' assigned to Super Admin")
            else:
                print(f"⚠️ Permission '{perm_name}' already assigned to Super Admin")
        
        print("=" * 50)
        print("✅ Permissions Initialized Successfully!")
        print(f"📊 Total Permissions: {len(permissions)}")
        print(f"📊 New Assignments: {assigned_count}")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error initializing permissions: {str(e)}")
        raise


# ============================================================
# CREATE ADDITIONAL ROLES
# ============================================================
def create_roles():
    """Create additional default roles in Supabase"""
    
    print("\n🔧 Creating default roles...")
    
    roles = [
        ("Admin", "Administrator with limited permissions"),
        ("Faculty", "Faculty member"),
        ("SME", "Subject Matter Expert"),
        ("Support Team", "Support Team Member"),
        ("Learner", "Student/Learner")
    ]
    
    for role_name, description in roles:
        result = supabase.table('roles').select('*').eq('name', role_name).execute()
        
        if not result.data:
            data = {
                'name': role_name,
                'description': description,
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            supabase.table('roles').insert(data).execute()
            print(f"✅ Role '{role_name}' created")
        else:
            print(f"⚠️ Role '{role_name}' already exists")


# ============================================================
# RUN INIT PERMISSIONS
# ============================================================
if __name__ == "__main__":
    init_permissions()
    
    # Optional: Create additional roles
    # Uncomment to create more roles
    # create_roles()