import os
import cloudinary
import cloudinary.uploader
from supabase import create_client, Client
from dotenv import load_dotenv
import time
import sys

# Load environment variables
load_dotenv()

# ============================================================
# SUPABASE SETUP
# ============================================================
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# ============================================================
# CLOUDINARY SETUP
# ============================================================
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

# ============================================================
# BULK UPLOAD FUNCTION
# ============================================================
def bulk_upload_photos(photo_folder_path, delay=0.5):
    """
    Upload all photos from a folder to Cloudinary and update Supabase
    
    Parameters:
    - photo_folder_path: Folder path containing student photos
    - delay: Time delay between uploads (seconds)
    """
    
    # Check if folder exists
    if not os.path.exists(photo_folder_path):
        print(f"❌ Error: Folder '{photo_folder_path}' does not exist!")
        return
    
    # Get all photo files
    photo_files = []
    for filename in os.listdir(photo_folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
            photo_files.append(filename)
    
    if not photo_files:
        print(f"❌ No photo files found in '{photo_folder_path}'")
        print("Supported formats: .png, .jpg, .jpeg, .webp, .gif")
        return
    
    print(f"📸 Found {len(photo_files)} photos to upload")
    print("=" * 50)
    
    uploaded_count = 0
    failed_count = 0
    skipped_count = 0
    
    for index, filename in enumerate(photo_files, 1):
        # Extract roll number from filename
        roll_number = os.path.splitext(filename)[0]
        
        try:
            print(f"🔄 [{index}/{len(photo_files)}] Uploading {roll_number}...", end=" ")
            
            # Check if student exists in Supabase
            student_exists = supabase.table('students')\
                .select('roll_number')\
                .eq('roll_number', roll_number)\
                .execute()
            
            if not student_exists.data:
                print(f"⚠️ Roll number '{roll_number}' not found in database. Skipping...")
                skipped_count += 1
                continue
            
            # Upload to Cloudinary
            file_path = os.path.join(photo_folder_path, filename)
            upload_result = cloudinary.uploader.upload(
                file_path,
                folder="chameleon_nexus/photos",
                public_id=f"student_{roll_number}",
                transformation=[
                    {'width': 400, 'height': 400, 'crop': 'fill'},
                    {'quality': 'auto'}
                ],
                overwrite=True
            )
            
            photo_url = upload_result['secure_url']
            
            # Update Supabase
            supabase.table('students')\
                .update({'photo_url': photo_url})\
                .eq('roll_number', roll_number)\
                .execute()
            
            print(f"✅ Uploaded successfully!")
            uploaded_count += 1
            
            # Delay between uploads (avoid rate limiting)
            time.sleep(delay)
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}...")
            failed_count += 1
    
    # Summary
    print("=" * 50)
    print("📊 UPLOAD SUMMARY")
    print(f"✅ Uploaded successfully: {uploaded_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⚠️ Skipped (Roll number not found): {skipped_count}")
    print(f"📸 Total photos processed: {len(photo_files)}")
    print("=" * 50)

# ============================================================
# RUN SCRIPT
# ============================================================
if __name__ == '__main__':
    print("🦎 CHAMELEON NEXUS - Bulk Photo Upload")
    print("=" * 50)
    
    # Get folder path from user
    folder_path = input("📁 Enter the path to your photos folder: ").strip()
    
    if not folder_path:
        print("❌ No folder path provided. Exiting...")
        sys.exit()
    
    # Remove quotes if present
    folder_path = folder_path.strip('"').strip("'")
    
    # Ask for delay
    delay_input = input("⏱️ Enter delay between uploads (default 0.5 seconds): ").strip()
    try:
        delay = float(delay_input) if delay_input else 0.5
    except:
        delay = 0.5
    
    print("\n🚀 Starting bulk upload...\n")
    
    # Run the upload
    bulk_upload_photos(folder_path, delay)
    
    print("\n✅ Bulk upload completed!")