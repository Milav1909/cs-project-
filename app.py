from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import os
import uuid
import base64
import qrcode
from werkzeug.utils import secure_filename
from io import BytesIO
import json

app = Flask(__name__)

# Use environment variables for configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size for Vercel
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Store file information (in-memory for serverless)
file_storage = {}

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
        
        # Read file into memory
        file_data = file.read()
        
        # Store file information
        file_storage[file_id] = {
            'filename': filename,
            'data': file_data,
            'size': len(file_data)
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
        BytesIO(file_info['data']),
        mimetype='application/octet-stream',
        as_attachment=True,
        attachment_filename=file_info['filename']
    )

@app.route('/file_info/<file_id>')
def file_info(file_id):
    if file_id not in file_storage:
        return jsonify({'error': 'File not found'}), 404
    
    info = file_storage[file_id].copy()
    del info['data']  # Remove binary data from response
    return jsonify(info)

app.debug = False

# This is required for Vercel
if __name__ == '__main__':
    app.run()