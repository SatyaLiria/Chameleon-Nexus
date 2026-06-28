import os
import json
import pandas as pd
from datetime import datetime
from flask import current_app
from supabase import create_client, Client
import random
import string

# ============================================================
# SUPABASE CLIENT (Will be initialized from app)
# ============================================================
supabase = None

def init_supabase_client(supabase_client):
    """Initialize Supabase client from app"""
    global supabase
    supabase = supabase_client

# ============================================================
# GENERATE TICKET NUMBER
# ============================================================
def generate_ticket_number():
    """Generate unique ticket number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TKT-{timestamp}-{random_str}"

# ============================================================
# CREATE VERIFICATION TICKET - SUPABASE VERSION
# ============================================================
def create_verification_ticket(data):
    """Create a new verification ticket in Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        ticket_data = {
            'ticket_number': generate_ticket_number(),
            'roll_number': data.get('roll_number'),
            'student_name': data.get('student_name'),
            'declaration': data.get('declaration'),
            'corrections': json.dumps(data.get('corrections', [])),
            'documents': json.dumps(data.get('documents', [])),
            'submitted_by': data.get('submitted_by'),
            'submitted_at': datetime.now().isoformat(),
            'status': 'Pending',
            'is_active': True
        }
        
        # Insert ticket into Supabase
        result = supabase.table('verification_tickets').insert(ticket_data).execute()
        
        if not result.data:
            raise Exception("Failed to create ticket")
        
        ticket = result.data[0]
        
        # Create notification
        notification_data = {
            'ticket_id': ticket.get('id'),
            'roll_number': data.get('roll_number'),
            'message': f"New verification ticket {ticket.get('ticket_number')} created for {data.get('student_name')}",
            'notification_type': 'info',
            'is_read': False
        }
        supabase.table('verification_notifications').insert(notification_data).execute()
        
        return ticket
        
    except Exception as e:
        print(f"Error creating ticket: {e}")
        raise

# ============================================================
# UPDATE VERIFICATION EXCEL - SUPABASE VERSION
# ============================================================
def update_verification_excel(roll_number, data):
    """Update verification records in Excel (local file)"""
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        'data', 
        'Verification_Records.xlsx'
    )
    
    # Ensure data folder exists
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    
    # Load existing data
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path)
    else:
        # Create new dataframe with columns
        df = pd.DataFrame(columns=[
            'Roll No.', 'Student Name', 'LMS Email I’d', 'Program', 'Major',
            'ABC ID', 'DEB ID', 'Date of Birth', 'Aadhar', 'Mobile No',
            "Father's Name", "Mother's Name", 'Communication Address',
            'City', 'State', 'Country', 'PIN Code',
            'Declaration', 'Verified Date & Time',
            'Correction Required', 'Field Names for Correction', 'Details for Correction',
            'Ticket Number', 'Status'
        ])
    
    # Check if student already exists
    try:
        roll_no_int = int(roll_number)
        existing_idx = df[df['Roll No.'] == roll_no_int].index
    except:
        existing_idx = df[df['Roll No.'] == roll_number].index
    
    if len(existing_idx) > 0:
        # Update existing record
        idx = existing_idx[0]
        df.at[idx, 'Declaration'] = data.get('declaration')
        df.at[idx, 'Verified Date & Time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df.at[idx, 'Correction Required'] = 'Yes' if data.get('corrections') else 'No'
        df.at[idx, 'Field Names for Correction'] = json.dumps(data.get('correction_fields', []))
        df.at[idx, 'Details for Correction'] = json.dumps(data.get('corrections', []))
        df.at[idx, 'Ticket Number'] = data.get('ticket_number')
        df.at[idx, 'Status'] = data.get('status', 'Pending')
    else:
        # Add new record
        new_row = {
            'Roll No.': int(roll_number) if str(roll_number).isdigit() else roll_number,
            'Student Name': data.get('student_name'),
            'LMS Email I’d': data.get('lms_email'),
            'Program': data.get('program'),
            'Major': data.get('major'),
            'ABC ID': data.get('abc_id'),
            'DEB ID': data.get('deb_id'),
            'Date of Birth': data.get('dob'),
            'Aadhar': data.get('aadhar'),
            'Mobile No': data.get('mobile_no'),
            "Father's Name": data.get('father_name'),
            "Mother's Name": data.get('mother_name'),
            'Communication Address': data.get('address'),
            'City': data.get('city'),
            'State': data.get('state'),
            'Country': data.get('country'),
            'PIN Code': data.get('pin_code'),
            'Declaration': data.get('declaration'),
            'Verified Date & Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Correction Required': 'Yes' if data.get('corrections') else 'No',
            'Field Names for Correction': json.dumps(data.get('correction_fields', [])),
            'Details for Correction': json.dumps(data.get('corrections', [])),
            'Ticket Number': data.get('ticket_number'),
            'Status': data.get('status', 'Pending')
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Save to Excel
    df.to_excel(excel_path, index=False)
    return True

# ============================================================
# UPDATE TICKET STATUS - SUPABASE VERSION
# ============================================================
def update_ticket_status(ticket_id, status, reviewed_by=None, review_notes=None):
    """Update ticket status in Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        update_data = {
            'status': status,
            'reviewed_at': datetime.now().isoformat()
        }
        if reviewed_by:
            update_data['reviewed_by'] = reviewed_by
        if review_notes:
            update_data['review_notes'] = review_notes
        
        result = supabase.table('verification_tickets')\
            .update(update_data)\
            .eq('id', ticket_id)\
            .execute()
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"Error updating ticket status: {e}")
        raise

# ============================================================
# GET STUDENT VERIFICATION HISTORY - SUPABASE VERSION
# ============================================================
def get_student_verification_history(roll_number):
    """Get verification history for a student from Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        result = supabase.table('verification_tickets')\
            .select('*')\
            .eq('roll_number', roll_number)\
            .eq('is_active', True)\
            .order('submitted_at', desc=True)\
            .execute()
        
        tickets = result.data if result.data else []
        
        history = []
        for ticket in tickets:
            history.append({
                'ticket_number': ticket.get('ticket_number'),
                'declaration': ticket.get('declaration'),
                'status': ticket.get('status'),
                'submitted_at': ticket.get('submitted_at'),
                'reviewed_at': ticket.get('reviewed_at'),
                'review_notes': ticket.get('review_notes')
            })
        
        return history
        
    except Exception as e:
        print(f"Error getting verification history: {e}")
        return []

# ============================================================
# GET TICKET BY ID - SUPABASE VERSION
# ============================================================
def get_ticket_by_id(ticket_id):
    """Get ticket by ID from Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        result = supabase.table('verification_tickets')\
            .select('*')\
            .eq('id', ticket_id)\
            .execute()
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"Error getting ticket: {e}")
        return None

# ============================================================
# GET ALL TICKETS - SUPABASE VERSION
# ============================================================
def get_all_tickets(status=None):
    """Get all tickets from Supabase with optional status filter"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        query = supabase.table('verification_tickets').select('*').eq('is_active', True)
        if status:
            query = query.eq('status', status)
        result = query.order('submitted_at', desc=True).execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error getting tickets: {e}")
        return []

# ============================================================
# CREATE NOTIFICATION - SUPABASE VERSION
# ============================================================
def create_notification(roll_number, message, notification_type='info', ticket_id=None):
    """Create a notification in Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        data = {
            'roll_number': roll_number,
            'message': message,
            'notification_type': notification_type,
            'is_read': False,
            'ticket_id': ticket_id
        }
        result = supabase.table('verification_notifications').insert(data).execute()
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None

# ============================================================
# GET UNREAD NOTIFICATIONS - SUPABASE VERSION
# ============================================================
def get_unread_notifications(roll_number):
    """Get unread notifications for a student from Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        result = supabase.table('verification_notifications')\
            .select('*')\
            .eq('roll_number', roll_number)\
            .eq('is_read', False)\
            .order('created_at', desc=True)\
            .execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return []

# ============================================================
# MARK NOTIFICATION AS READ - SUPABASE VERSION
# ============================================================
def mark_notification_read(notification_id):
    """Mark a notification as read in Supabase"""
    if not supabase:
        raise Exception("Supabase client not initialized")
    
    try:
        result = supabase.table('verification_notifications')\
            .update({'is_read': True})\
            .eq('id', notification_id)\
            .execute()
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return None