from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# SUPABASE CLIENT (Will be initialized from app)
# ============================================================
supabase = None

def init_supabase_client(supabase_client):
    """Initialize Supabase client from app"""
    global supabase
    supabase = supabase_client

# ============================================================
# GET USER ROLES - SUPABASE VERSION
# ============================================================
def get_user_roles(user_id):
    """Get all role names for a user from Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        # Get user_roles with role details
        result = supabase.table('user_roles')\
            .select('*, roles(name)')\
            .eq('user_id', user_id)\
            .execute()
        
        if not result.data:
            return []
        
        roles = []
        for item in result.data:
            if item.get('roles') and item['roles'].get('name'):
                roles.append(item['roles']['name'])
        
        return roles
        
    except Exception as e:
        print(f"Error getting user roles: {e}")
        return []

# ============================================================
# GET ROLE PERMISSIONS - SUPABASE VERSION
# ============================================================
def get_role_permissions(user_id):
    """Get all permissions from user's roles from Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        # First get user's roles
        user_roles_result = supabase.table('user_roles')\
            .select('role_id')\
            .eq('user_id', user_id)\
            .execute()
        
        if not user_roles_result.data:
            return set()
        
        role_ids = [item['role_id'] for item in user_roles_result.data]
        
        if not role_ids:
            return set()
        
        # Get permissions for these roles
        role_perms_result = supabase.table('role_permissions')\
            .select('*, permissions(name)')\
            .in_('role_id', role_ids)\
            .execute()
        
        if not role_perms_result.data:
            return set()
        
        permissions = set()
        for item in role_perms_result.data:
            if item.get('permissions') and item['permissions'].get('name'):
                permissions.add(item['permissions']['name'])
        
        return permissions
        
    except Exception as e:
        print(f"Error getting role permissions: {e}")
        return set()

# ============================================================
# GET USER EXTRA PERMISSIONS - SUPABASE VERSION
# ============================================================
def get_user_permissions(user_id):
    """Get user-specific permissions from Supabase (not role-based)"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        result = supabase.table('user_permissions')\
            .select('*, permissions(name)')\
            .eq('user_id', user_id)\
            .execute()
        
        if not result.data:
            return set()
        
        permissions = set()
        for item in result.data:
            if item.get('permissions') and item['permissions'].get('name'):
                permissions.add(item['permissions']['name'])
        
        return permissions
        
    except Exception as e:
        print(f"Error getting user permissions: {e}")
        return set()

# ============================================================
# COMBINE ALL PERMISSIONS - SUPABASE VERSION
# ============================================================
def get_all_permissions(user_id):
    """Get all permissions (role-based + user-specific) from Supabase"""
    role_perms = get_role_permissions(user_id)
    user_perms = get_user_permissions(user_id)
    return role_perms.union(user_perms)

# ============================================================
# CHECK PERMISSION - SUPABASE VERSION
# ============================================================
def has_permission(user_id, permission_name):
    """Check if user has a specific permission"""
    return permission_name in get_all_permissions(user_id)

# ============================================================
# GET VISIBLE STUDENT FIELDS - SUPABASE VERSION
# ============================================================
def get_visible_fields(user_id):
    """Get list of field IDs that a user can see from Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        # Super Admin sees everything
        roles = get_user_roles(user_id)
        if "Super Admin" in roles:
            return "ALL"
        
        # Get field permissions for this user
        result = supabase.table('user_field_permissions')\
            .select('field_id')\
            .eq('user_id', user_id)\
            .eq('can_view', True)\
            .execute()
        
        if not result.data:
            return []
        
        return [item['field_id'] for item in result.data]
        
    except Exception as e:
        print(f"Error getting visible fields: {e}")
        return []

# ============================================================
# GET EDITABLE STUDENT FIELDS - SUPABASE VERSION
# ============================================================
def get_editable_fields(user_id):
    """Get list of field IDs that a user can edit from Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        result = supabase.table('user_field_permissions')\
            .select('field_id')\
            .eq('user_id', user_id)\
            .eq('can_edit', True)\
            .execute()
        
        if not result.data:
            return []
        
        return [item['field_id'] for item in result.data]
        
    except Exception as e:
        print(f"Error getting editable fields: {e}")
        return []

# ============================================================
# SET USER FIELD PERMISSION - SUPABASE VERSION
# ============================================================
def set_user_field_permission(user_id, field_id, can_view=False, can_edit=False):
    """Set or update field permission for a user in Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        # Check if permission exists
        result = supabase.table('user_field_permissions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('field_id', field_id)\
            .execute()
        
        if result.data:
            # Update existing
            supabase.table('user_field_permissions')\
                .update({
                    'can_view': can_view,
                    'can_edit': can_edit
                })\
                .eq('user_id', user_id)\
                .eq('field_id', field_id)\
                .execute()
        else:
            # Insert new
            supabase.table('user_field_permissions')\
                .insert({
                    'user_id': user_id,
                    'field_id': field_id,
                    'can_view': can_view,
                    'can_edit': can_edit
                })\
                .execute()
        
        return True
        
    except Exception as e:
        print(f"Error setting field permission: {e}")
        return False

# ============================================================
# BULK SET USER FIELD PERMISSIONS - SUPABASE VERSION
# ============================================================
def bulk_set_field_permissions(user_id, field_permissions):
    """Bulk set permissions for a user in Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        # Clear existing permissions
        supabase.table('user_field_permissions')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        
        # Add new permissions
        for perm in field_permissions:
            supabase.table('user_field_permissions')\
                .insert({
                    'user_id': user_id,
                    'field_id': perm['field_id'],
                    'can_view': perm.get('can_view', False),
                    'can_edit': perm.get('can_edit', False)
                })\
                .execute()
        
        return True
        
    except Exception as e:
        print(f"Error bulk setting field permissions: {e}")
        return False

# ============================================================
# FILTER STUDENT DATA - SUPABASE VERSION
# ============================================================
def filter_student_data(user_id, student_id):
    """Filter student data based on user's field permissions from Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        # Get student data
        student_result = supabase.table('students')\
            .select('*')\
            .eq('id', student_id)\
            .execute()
        
        if not student_result.data:
            return None
        
        student = student_result.data[0]
        visible_field_ids = get_visible_fields(user_id)
        
        # Super Admin sees everything
        if visible_field_ids == "ALL":
            return student
        
        # Get all student fields
        fields_result = supabase.table('student_fields')\
            .select('*')\
            .eq('is_active', True)\
            .execute()
        
        fields = fields_result.data if fields_result.data else []
        
        # Filter data based on visible fields
        filtered_data = {
            'id': student.get('id'),
            'roll_number': student.get('roll_number'),
            'student_name': student.get('student_name')
        }
        
        for field in fields:
            field_id = field.get('id')
            field_name = field.get('field_name')
            if field_id in visible_field_ids:
                filtered_data[field_name] = student.get(field_name, '')
        
        return filtered_data
        
    except Exception as e:
        print(f"Error filtering student data: {e}")
        return None

# ============================================================
# DECORATOR FOR ROUTES - SUPABASE VERSION
# ============================================================
def require_permission(permission_name):
    """Decorator to check if user has permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask_login import current_user
            if not current_user.is_authenticated:
                return "Access Denied - Please Login", 403
            if not has_permission(current_user.id, permission_name):
                return f"Access Denied - Missing permission: {permission_name}", 403
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# ============================================================
# CHECK USER PERMISSION BY NAME - SUPABASE VERSION
# ============================================================
def user_has_permission(user_id, permission_name):
    """Direct check if user has a specific permission"""
    return has_permission(user_id, permission_name)

# ============================================================
# GET USER ROLE NAMES - SUPABASE VERSION
# ============================================================
def get_user_role_names(user_id):
    """Get list of role names for a user"""
    return get_user_roles(user_id)

# ============================================================
# GET ALL PERMISSION NAMES - SUPABASE VERSION
# ============================================================
def get_all_permission_names(user_id):
    """Get all permission names for a user (combined)"""
    return get_all_permissions(user_id)