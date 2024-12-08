from django.core.exceptions import ValidationError
import magic
import os

def validate_file_type(file):
    # Get MIME type
    file_type = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)  # Reset file pointer
    
    # Define allowed types
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif']
    
    if file_type not in ALLOWED_TYPES:
        raise ValidationError('Unsupported file type.')

def validate_file_size(file):
    # 5MB limit
    MAX_SIZE = 5 * 1024 * 1024
    
    if file.size > MAX_SIZE:
        raise ValidationError('File too large. Size should not exceed 5 MB.') 