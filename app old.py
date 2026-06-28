import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from supabase import create_client, Client
import cloudinary
import cloudinary.uploader
import pandas as pd
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, date
import json

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# ============================================================
# SUPABASE CONFIGURATION
# ============================================================
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# ============================================================
# CLOUDINARY CONFIGURATION
# ============================================================
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

# ============================================================
# ALLOWED EXTENSIONS
# ============================================================
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# ============================================================
# HELPER FUNCTION: Convert datetime to string
# ============================================================
def convert_datetime_to_string(data):
    """Convert all datetime objects in a dictionary to ISO format strings"""
    for key, value in data.items():
        if isinstance(value, (datetime, date)):
            data[key] = value.isoformat()
        elif isinstance(value, pd.Timestamp):
            data[key] = value.isoformat()
        elif pd.isna(value):
            data[key] = None
    return data

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/student-verification')
def student_verification():
    # Fetch all students from Supabase
    try:
        result = supabase.table('students').select('*').order('created_at', desc=True).execute()
        students = result.data if result.data else []
    except Exception as e:
        students = []
        print(f"Error fetching students: {e}")
    return render_template('student_verification.html', students=students)

@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    if 'excel_file' not in request.files:
        flash('No file uploaded', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(filepath)
        
        try:
            # Process Excel file
            df = pd.read_excel(filepath)
            
            # Handle NaN values and convert datetime to string
            df = df.where(pd.notnull(df), None)
            
            # Upsert data to Supabase
            record_count = 0
            for _, row in df.iterrows():
                data = row.to_dict()
                
                # Convert all datetime objects to string
                data = convert_datetime_to_string(data)
                
                # Check if roll_number exists
                if 'roll_number' in data and data['roll_number']:
                    try:
                        # Check if student exists
                        existing = supabase.table('students').select('*').eq('roll_number', data['roll_number']).execute()
                        
                        if existing.data:
                            # Update existing
                            supabase.table('students').update(data).eq('roll_number', data['roll_number']).execute()
                        else:
                            # Insert new
                            supabase.table('students').insert(data).execute()
                        record_count += 1
                    except Exception as e:
                        print(f"Error processing row: {e}")
                        continue
            
            flash(f'✅ Excel file processed successfully! {record_count} records updated.', 'success')
            
        except Exception as e:
            flash(f'❌ Error processing file: {str(e)}', 'danger')
            print(f"Excel processing error: {e}")
        
        return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload Excel file.', 'danger')
        return redirect(url_for('index'))

@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo uploaded'}), 400
    
    file = request.files['photo']
    roll_number = request.form.get('roll_number', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not roll_number:
        return jsonify({'error': 'Roll number is required'}), 400
    
    if file and allowed_image_file(file.filename):
        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file,
                folder="chameleon_nexus/photos",
                public_id=f"student_{roll_number}",
                transformation=[
                    {'width': 400, 'height': 400, 'crop': 'fill'},
                    {'quality': 'auto'}
                ],
                overwrite=True
            )
            
            photo_url = upload_result['secure_url']
            public_id = upload_result['public_id']
            
            # Update student record with photo URL
            try:
                supabase.table('students').update({
                    'photo_url': photo_url
                }).eq('roll_number', roll_number).execute()
            except Exception as e:
                print(f"Error updating photo URL: {e}")
            
            return jsonify({
                'success': True,
                'url': photo_url,
                'public_id': public_id,
                'message': f'Photo uploaded successfully for {roll_number}'
            })
            
        except Exception as e:
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid image format. Please upload PNG, JPG, JPEG, or WEBP.'}), 400

@app.route('/student/<roll_number>')
def student_profile(roll_number):
    # Fetch student from Supabase
    try:
        result = supabase.table('students').select('*').eq('roll_number', roll_number).execute()
        if result.data:
            student = result.data[0]
            return render_template('student_profile.html', student=student)
        else:
            flash('Student not found', 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

# ============================================================
# RUN APP
# ============================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)