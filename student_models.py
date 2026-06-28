import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# SUPABASE CLIENT
# ============================================================
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# ============================================================
# STUDENT MASTER CLASS
# ============================================================
class StudentMaster:
    """Student Master class for Supabase"""
    
    table_name = 'students'
    
    def __init__(self, data):
        self.id = data.get('id')
        self.roll_number = data.get('roll_number')
        self.abc_id = data.get('abc_id')
        self.deb_id = data.get('deb_id')
        self.student_name = data.get('student_name')
        self.program = data.get('program')
        self.major = data.get('major')
        self.mobile_number = data.get('mobile_no')
        self.email = data.get('lms_email')
        self.address = data.get('address')
        self.fee_status = data.get('fee_status')
        self.pending_amount = data.get('pending_amount')
        self.photo_url = data.get('photo_url')
        self.dob = data.get('dob')
        self.aadhar = data.get('aadhar')
        self.father_name = data.get('father_name')
        self.mother_name = data.get('mother_name')
        self.city = data.get('city')
        self.state = data.get('state')
        self.country = data.get('country')
        self.pin_code = data.get('pin_code')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        self.last_synced = data.get('last_synced')
    
    @staticmethod
    def from_dict(data):
        return StudentMaster(data)
    
    @classmethod
    def get_all(cls, limit=None):
        """Get all students from Supabase"""
        query = supabase.table(cls.table_name).select('*')
        if limit:
            query = query.limit(limit)
        result = query.order('created_at', desc=True).execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []
    
    @classmethod
    def get_by_roll_number(cls, roll_number):
        """Get student by roll number"""
        result = supabase.table(cls.table_name).select('*').eq('roll_number', roll_number).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def get_by_id(cls, student_id):
        """Get student by ID"""
        result = supabase.table(cls.table_name).select('*').eq('id', student_id).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def search(cls, query):
        """Search students by roll number or name"""
        result = supabase.table(cls.table_name).select('*').or_(
            f'roll_number.ilike.%{query}%,student_name.ilike.%{query}%'
        ).limit(20).execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []
    
    @classmethod
    def get_count(cls):
        """Get total number of students"""
        result = supabase.table(cls.table_name).select('id', count='exact').execute()
        return result.count or 0
    
    @classmethod
    def create(cls, data):
        """Create a new student"""
        result = supabase.table(cls.table_name).insert(data).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    def update(self, data):
        """Update this student"""
        result = supabase.table(self.table_name).update(data).eq('id', self.id).execute()
        if result.data:
            for key, value in result.data[0].items():
                setattr(self, key, value)
        return self
    
    @classmethod
    def update_by_roll_number(cls, roll_number, data):
        """Update student by roll number"""
        result = supabase.table(cls.table_name).update(data).eq('roll_number', roll_number).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def delete(cls, roll_number):
        """Delete student by roll number"""
        result = supabase.table(cls.table_name).delete().eq('roll_number', roll_number).execute()
        return result.data
    
    @classmethod
    def upsert(cls, data):
        """Insert or update student"""
        roll_number = data.get('roll_number')
        if not roll_number:
            return None
        
        existing = cls.get_by_roll_number(roll_number)
        if existing:
            # Update existing
            existing.update(data)
            return existing
        else:
            # Create new
            return cls.create(data)
    
    def get_extra_data(self):
        """Get extra data for this student (from student_data table)"""
        result = supabase.table('student_data').select('*').eq('student_id', self.id).execute()
        return result.data if result.data else []
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'roll_number': self.roll_number,
            'abc_id': self.abc_id,
            'deb_id': self.deb_id,
            'student_name': self.student_name,
            'program': self.program,
            'major': self.major,
            'mobile_no': self.mobile_number,
            'lms_email': self.email,
            'address': self.address,
            'fee_status': self.fee_status,
            'pending_amount': self.pending_amount,
            'photo_url': self.photo_url,
            'dob': self.dob,
            'aadhar': self.aadhar,
            'father_name': self.father_name,
            'mother_name': self.mother_name,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'pin_code': self.pin_code,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

# ============================================================
# STUDENT DATA CLASS (Extra Fields)
# ============================================================
class StudentData:
    """Student Extra Data class for Supabase"""
    
    table_name = 'student_data'
    
    def __init__(self, data):
        self.id = data.get('id')
        self.student_id = data.get('student_id')
        self.field_name = data.get('field_name')
        self.field_value = data.get('field_value')
        self.created_at = data.get('created_at')
    
    @staticmethod
    def from_dict(data):
        return StudentData(data)
    
    @classmethod
    def get_by_student_id(cls, student_id):
        """Get all extra data for a student"""
        result = supabase.table(cls.table_name).select('*').eq('student_id', student_id).execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []
    
    @classmethod
    def get_by_field(cls, student_id, field_name):
        """Get specific field value for a student"""
        result = supabase.table(cls.table_name).select('*')\
            .eq('student_id', student_id)\
            .eq('field_name', field_name)\
            .execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def create(cls, data):
        """Create new extra data entry"""
        result = supabase.table(cls.table_name).insert(data).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def update_or_create(cls, student_id, field_name, field_value):
        """Update existing field or create new"""
        existing = cls.get_by_field(student_id, field_name)
        if existing:
            result = supabase.table(cls.table_name)\
                .update({'field_value': field_value})\
                .eq('id', existing.id)\
                .execute()
            return cls.from_dict(result.data[0]) if result.data else None
        else:
            data = {
                'student_id': student_id,
                'field_name': field_name,
                'field_value': field_value
            }
            return cls.create(data)

# ============================================================
# SYNC LOG CLASS
# ============================================================
class SyncLog:
    """Sync Log class for Supabase"""
    
    table_name = 'sync_logs'
    
    def __init__(self, data):
        self.id = data.get('id')
        self.file_name = data.get('file_name')
        self.total_records = data.get('total_records', 0)
        self.success_records = data.get('success_records', 0)
        self.failed_records = data.get('failed_records', 0)
        self.status = data.get('status', 'SUCCESS')
        self.created_at = data.get('created_at')
    
    @staticmethod
    def from_dict(data):
        return SyncLog(data)
    
    @classmethod
    def create(cls, data):
        """Create new sync log entry"""
        data['created_at'] = datetime.now().isoformat()
        result = supabase.table(cls.table_name).insert(data).execute()
        return cls.from_dict(result.data[0]) if result.data else None
    
    @classmethod
    def get_all(cls, limit=50):
        """Get all sync logs"""
        result = supabase.table(cls.table_name).select('*').order('created_at', desc=True).limit(limit).execute()
        return [cls.from_dict(item) for item in result.data] if result.data else []

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def sync_students_from_excel(df):
    """Sync students from Excel DataFrame to Supabase"""
    success_count = 0
    failed_count = 0
    failed_rows = []
    
    for idx, row in df.iterrows():
        try:
            data = row.to_dict()
            
            # Clean data
            for key, value in data.items():
                if pd.isna(value):
                    data[key] = None
            
            # Upsert student
            student = StudentMaster.upsert(data)
            
            if student:
                success_count += 1
            else:
                failed_count += 1
                failed_rows.append(idx)
                
        except Exception as e:
            failed_count += 1
            failed_rows.append(idx)
            print(f"Error syncing row {idx}: {e}")
    
    return {
        'total': len(df),
        'success': success_count,
        'failed': failed_count,
        'failed_rows': failed_rows
    }

def get_student_with_extra_data(roll_number):
    """Get student with all extra data"""
    student = StudentMaster.get_by_roll_number(roll_number)
    if not student:
        return None
    
    extra_data = student.get_extra_data()
    extra_dict = {item.field_name: item.field_value for item in extra_data}
    
    result = student.to_dict()
    result.update(extra_dict)
    
    return result