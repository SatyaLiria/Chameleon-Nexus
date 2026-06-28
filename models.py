import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from flask_login import UserMixin

load_dotenv()

# ============================================================
# SUPABASE CLIENT
# ============================================================
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# ============================================================
# USER CLASS (For Flask-Login Compatibility)
# ============================================================
class User(UserMixin):
    """User class for Flask-Login compatibility with Supabase"""
    
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password = user_data.get('password')
        self.full_name = user_data.get('full_name')
        self.mobile = user_data.get('mobile')
        self.designation = user_data.get('designation')
        self.department = user_data.get('department')
        self.role = user_data.get('role', 'user')
        self.is_active = user_data.get('is_active', True)
        self.created_at = user_data.get('created_at')
        self.updated_at = user_data.get('updated_at')
        self._roles = []
        self._permissions = []
    
    @staticmethod
    def from_dict(data):
        return User(data)
    
    def get_id(self):
        return str(self.id)
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_roles(self):
        """Get roles for this user"""
        if not self._roles:
            try:
                result = supabase.table('user_roles')\
                    .select('*, roles(*)')\
                    .eq('user_id', self.id)\
                    .execute()
                if result.data:
                    self._roles = [item['roles'] for item in result.data if item.get('roles')]
            except Exception as e:
                print(f"Error fetching roles: {e}")
        return self._roles
    
    def get_permissions(self):
        """Get permissions for this user"""
        if not self._permissions:
            try:
                # Get role permissions
                role_perms = set()
                for role in self.get_roles():
                    role_id = role.get('id')
                    if role_id:
                        result = supabase.table('role_permissions')\
                            .select('*, permissions(*)')\
                            .eq('role_id', role_id)\
                            .execute()
                        if result.data:
                            for item in result.data:
                                if item.get('permissions'):
                                    role_perms.add(item['permissions']['name'])
                
                # Get user-specific permissions
                user_perms = set()
                result = supabase.table('user_permissions')\
                    .select('*, permissions(*)')\
                    .eq('user_id', self.id)\
                    .execute()
                if result.data:
                    for item in result.data:
                        if item.get('permissions'):
                            user_perms.add(item['permissions']['name'])
                
                self._permissions = list(role_perms.union(user_perms))
            except Exception as e:
                print(f"Error fetching permissions: {e}")
        return self._permissions
    
    def has_permission(self, permission_name):
        """Check if user has a specific permission"""
        return permission_name in self.get_permissions()
    
    def has_role(self, role_name):
        """Check if user has a specific role"""
        for role in self.get_roles():
            if role.get('name') == role_name:
                return True
        return False

# ============================================================
# ROLE CLASS
# ============================================================
class Role:
    """Role class for Supabase"""
    
    table_name = 'roles'
    
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.description = data.get('description')
        self.responsibilities = data.get('responsibilities')
        self.is_active = data.get('is_active', True)
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    @staticmethod
    def from_dict(data):
        return Role(data)
    
    @classmethod
    def get_all(cls):
        result = supabase.table(cls.table_name).select('*').eq('is_active', True).execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []
    
    @classmethod
    def get_by_id(cls, role_id):
        result = supabase.table(cls.table_name).select('*').eq('id', role_id).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def get_by_name(cls, name):
        result = supabase.table(cls.table_name).select('*').eq('name', name).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def create(cls, data):
        result = supabase.table(cls.table_name).insert(data).execute()
        return cls.from_dict(result.data[0]) if result.data else None

# ============================================================
# PERMISSION CLASS
# ============================================================
class Permission:
    """Permission class for Supabase"""
    
    table_name = 'permissions'
    
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.created_at = data.get('created_at')
    
    @staticmethod
    def from_dict(data):
        return Permission(data)
    
    @classmethod
    def get_all(cls):
        result = supabase.table(cls.table_name).select('*').execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []
    
    @classmethod
    def get_by_id(cls, perm_id):
        result = supabase.table(cls.table_name).select('*').eq('id', perm_id).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def get_by_name(cls, name):
        result = supabase.table(cls.table_name).select('*').eq('name', name).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def create(cls, name):
        result = supabase.table(cls.table_name).insert({'name': name}).execute()
        return cls.from_dict(result.data[0]) if result.data else None

# ============================================================
# STUDENT FIELD CLASS
# ============================================================
class StudentField:
    """Student Field class for Supabase"""
    
    table_name = 'student_fields'
    
    def __init__(self, data):
        self.id = data.get('id')
        self.field_name = data.get('field_name')
        self.display_name = data.get('display_name')
        self.field_type = data.get('field_type', 'text')
        self.is_required = data.get('is_required', False)
        self.is_active = data.get('is_active', True)
        self.sort_order = data.get('sort_order', 0)
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    @staticmethod
    def from_dict(data):
        return StudentField(data)
    
    @classmethod
    def get_all(cls, active_only=True):
        query = supabase.table(cls.table_name).select('*')
        if active_only:
            query = query.eq('is_active', True)
        result = query.order('sort_order').execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []
    
    @classmethod
    def get_by_id(cls, field_id):
        result = supabase.table(cls.table_name).select('*').eq('id', field_id).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def get_by_name(cls, field_name):
        result = supabase.table(cls.table_name).select('*').eq('field_name', field_name).execute()
        return cls.from_dict(result.data[0]) if result.data else None

# ============================================================
# FIELD CATEGORY CLASS
# ============================================================
class FieldCategory:
    """Field Category class for Supabase"""
    
    table_name = 'field_categories'
    
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.description = data.get('description')
        self.sort_order = data.get('sort_order', 0)
        self.is_active = data.get('is_active', True)
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        self._fields = []
    
    @staticmethod
    def from_dict(data):
        return FieldCategory(data)
    
    @classmethod
    def get_all(cls, active_only=True):
        query = supabase.table(cls.table_name).select('*')
        if active_only:
            query = query.eq('is_active', True)
        result = query.order('sort_order').execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []
    
    @classmethod
    def get_by_id(cls, category_id):
        result = supabase.table(cls.table_name).select('*').eq('id', category_id).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    def get_fields(self):
        """Get fields for this category"""
        if not self._fields:
            try:
                result = supabase.table('category_field_mapping')\
                    .select('*, student_fields(*)')\
                    .eq('category_id', self.id)\
                    .eq('is_visible', True)\
                    .order('display_order')\
                    .execute()
                if result.data:
                    self._fields = [item['student_fields'] for item in result.data if item.get('student_fields')]
            except Exception as e:
                print(f"Error fetching category fields: {e}")
        return self._fields

# ============================================================
# VERIFICATION TICKET CLASS
# ============================================================
class VerificationTicket:
    """Verification Ticket class for Supabase"""
    
    table_name = 'verification_tickets'
    
    def __init__(self, data):
        self.id = data.get('id')
        self.ticket_number = data.get('ticket_number')
        self.roll_number = data.get('roll_number')
        self.student_name = data.get('student_name')
        self.declaration = data.get('declaration')
        self.status = data.get('status', 'Pending')
        self.corrections = data.get('corrections')
        self.documents = data.get('documents')
        self.correction_fields = data.get('correction_fields')
        self.submitted_by = data.get('submitted_by')
        self.submitted_at = data.get('submitted_at')
        self.reviewed_by = data.get('reviewed_by')
        self.reviewed_at = data.get('reviewed_at')
        self.review_notes = data.get('review_notes')
        self.is_active = data.get('is_active', True)
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    @staticmethod
    def from_dict(data):
        return VerificationTicket(data)
    
    @classmethod
    def get_all(cls, status=None):
        query = supabase.table(cls.table_name).select('*').eq('is_active', True)
        if status:
            query = query.eq('status', status)
        result = query.order('submitted_at', desc=True).execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []
    
    @classmethod
    def get_by_id(cls, ticket_id):
        result = supabase.table(cls.table_name).select('*').eq('id', ticket_id).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def get_by_roll_number(cls, roll_number):
        result = supabase.table(cls.table_name).select('*')\
            .eq('roll_number', roll_number)\
            .eq('is_active', True)\
            .order('submitted_at', desc=True)\
            .execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []
    
    @classmethod
    def create(cls, data):
        result = supabase.table(cls.table_name).insert(data).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    def update(self, data):
        result = supabase.table(self.table_name).update(data).eq('id', self.id).execute()
        if result.data:
            for key, value in result.data[0].items():
                setattr(self, key, value)
        return self

# ============================================================
# VERIFICATION NOTIFICATION CLASS
# ============================================================
class VerificationNotification:
    """Verification Notification class for Supabase"""
    
    table_name = 'verification_notifications'
    
    def __init__(self, data):
        self.id = data.get('id')
        self.ticket_id = data.get('ticket_id')
        self.roll_number = data.get('roll_number')
        self.message = data.get('message')
        self.is_read = data.get('is_read', False)
        self.notification_type = data.get('notification_type', 'info')
        self.created_at = data.get('created_at')
    
    @staticmethod
    def from_dict(data):
        return VerificationNotification(data)
    
    @classmethod
    def get_by_roll_number(cls, roll_number, unread_only=False):
        query = supabase.table(cls.table_name).select('*').eq('roll_number', roll_number)
        if unread_only:
            query = query.eq('is_read', False)
        result = query.order('created_at', desc=True).execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []
    
    @classmethod
    def create(cls, data):
        result = supabase.table(cls.table_name).insert(data).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    def mark_as_read(self):
        result = supabase.table(self.table_name).update({'is_read': True}).eq('id', self.id).execute()
        if result.data:
            self.is_read = True
        return self

# ============================================================
# SETTINGS CLASS
# ============================================================
class Settings:
    """Settings class for Supabase"""
    
    table_name = 'settings'
    
    @classmethod
    def get_logo(cls):
        result = supabase.table(cls.table_name).select('logo_url, logo_public_id').eq('id', 1).execute()
        if result.data:
            return result.data[0].get('logo_url')
        return None
    
    @classmethod
    def update_logo(cls, logo_url, public_id):
        data = {
            'logo_url': logo_url,
            'logo_public_id': public_id,
            'updated_at': datetime.now().isoformat()
        }
        result = supabase.table(cls.table_name).update(data).eq('id', 1).execute()
        return result.data[0] if result.data else None

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_user_by_username(username):
    """Get user by username from Supabase"""
    result = supabase.table('users').select('*').eq('username', username).execute()
    return User.from_dict(result.data[0]) if result.data else None

def get_user_by_email(email):
    """Get user by email from Supabase"""
    result = supabase.table('users').select('*').eq('email', email).execute()
    return User.from_dict(result.data[0]) if result.data else None

def get_user_by_id(user_id):
    """Get user by ID from Supabase"""
    result = supabase.table('users').select('*').eq('id', user_id).execute()
    return User.from_dict(result.data[0]) if result.data else None