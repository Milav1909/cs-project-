from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import os
import uuid
import base64
import qrcode
from werkzeug import secure_filename
from io import BytesIO
import json

app = Flask(__name__)

# Use environment variables for configuration
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  # Use /tmp for serverless
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB max file size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', base64.b64encode(os.urandom(24)))

# Store file information (in-memory for serverless)
file_storage = {}

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/cookie')
def cookie():
    return render_template('cookie.html')

def sanitize_filename(filename):
    """Sanitize the filename manually if secure_filename is not available"""
    return "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '-', '_', '.')]).rstrip()

def generate_qr_code(data):
    """Generate QR code from data"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code to bytes
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        try:
            filename = secure_filename(file.filename)
        except:
            filename = sanitize_filename(file.filename)
        
        # Generate unique ID for the file
        file_id = str(uuid.uuid4())
        
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        file.save(file_path)
        
        # Store file information
        file_storage[file_id] = {
            'filename': filename,
            'path': file_path,
            'size': os.path.getsize(file_path)
        }
        
        # Generate share URL
        share_url = "{0}download/{1}".format(request.host_url, file_id)
        
        # Generate QR code
        qr_code = generate_qr_code(share_url)
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'share_url': share_url,
            'qr_code': base64.b64encode(qr_code.getvalue()).decode('utf-8')
        })

@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id not in file_storage:
        return jsonify({'error': 'File not found'}), 404
    
    file_info = file_storage[file_id]
    return send_file(
        file_info['path'],
        as_attachment=True,
        attachment_filename=file_info['filename']
    )

@app.route('/file_info/<file_id>')
def file_info(file_id):
    if file_id not in file_storage:
        return jsonify({'error': 'File not found'}), 404
    
    return jsonify(file_storage[file_id])

# This is required for Vercel
if __name__ == '__main__':
    app.run()
else:
    # This is required for Vercel
    handler = app