from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, redirect, url_for
import os
import uuid
import base64
import qrcode
from werkzeug.utils import secure_filename
from io import BytesIO
import json
import logging
import sqlite3
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Use environment variables for configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size for Vercel
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['DATABASE'] = os.path.join('data', 'files.db')
app.config['UPLOAD_FOLDER'] = os.path.join('data', 'uploads')

# Ensure directories exist
try:
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.mkdir(app.config['UPLOAD_FOLDER'])
except Exception as e:
    logger.error("Error creating directories: %s", str(e))
    raise

def init_db():
    """Initialize the SQLite database"""
    try:
        # Remove existing database if it's corrupted
        if os.path.exists(app.config['DATABASE']):
            try:
                conn = sqlite3.connect(app.config['DATABASE'])
                conn.execute('SELECT 1 FROM files')
                conn.close()
            except:
                os.remove(app.config['DATABASE'])
        
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                size INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized at: %s", os.path.abspath(app.config['DATABASE']))
    except Exception as e:
        logger.error("Error initializing database: %s", str(e))
        raise

# Initialize database
init_db()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error("Error rendering index: %s", str(e))
        return jsonify({'error': 'Internal server error'}), 500

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
    try:
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
    except Exception as e:
        logger.error("Error generating QR code: %s", str(e))
        return None

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        logger.info("Upload request received")
        
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("No selected file")
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            try:
                filename = secure_filename(file.filename)
            except:
                filename = sanitize_filename(file.filename)
            
            logger.info("Processing file: %s", filename)
            
            # Generate unique ID for the file
            file_id = str(uuid.uuid4())
            
            # Save file to disk
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            
            # Store file info in SQLite
            conn = get_db()
            try:
                now = datetime.utcnow()
                expires = now + timedelta(days=7)
                conn.execute(
                    'INSERT INTO files (id, filename, filepath, size, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (file_id, filename, file_path, file_size, now, expires)
                )
                conn.commit()
            finally:
                conn.close()
            
            # Generate share URL
            share_url = request.host_url.rstrip('/') + url_for('download_file', file_id=file_id)
            
            # Generate QR code
            qr_code = generate_qr_code(share_url)
            if qr_code is None:
                return jsonify({'error': 'Failed to generate QR code'}), 500
            
            response_data = {
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'share_url': share_url,
                'qr_code': base64.b64encode(qr_code.getvalue()).decode('utf-8'),
                'expires_at': expires.isoformat()
            }
            
            logger.info("File processed successfully: %s", file_id)
            return jsonify(response_data)
            
    except Exception as e:
        logger.error("Error in upload_file: %s", str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        conn = get_db()
        try:
            # Find file in database
            file = conn.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
            
            if not file:
                logger.error("File not found: %s", file_id)
                return jsonify({'error': 'File not found'}), 404
            
            # Check if file has expired
            if datetime.utcnow() > datetime.fromisoformat(file['expires_at']):
                # Delete file and database entry
                os.remove(file['filepath'])
                conn.execute('DELETE FROM files WHERE id = ?', (file_id,))
                conn.commit()
                return jsonify({'error': 'File has expired'}), 404
            
            return send_file(
                file['filepath'],
                as_attachment=True,
                attachment_filename=file['filename']
            )
        finally:
            conn.close()
    except Exception as e:
        logger.error("Error in download_file: %s", str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/file_info/<file_id>')
def file_info(file_id):
    try:
        conn = get_db()
        try:
            # Find file in database
            file = conn.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
            
            if not file:
                logger.error("File info not found: %s", file_id)
                return jsonify({'error': 'File not found'}), 404
            
            # Check if file has expired
            if datetime.utcnow() > datetime.fromisoformat(file['expires_at']):
                # Delete file and database entry
                os.remove(file['filepath'])
                conn.execute('DELETE FROM files WHERE id = ?', (file_id,))
                conn.commit()
                return jsonify({'error': 'File has expired'}), 404
            
            info = {
                'filename': file['filename'],
                'size': file['size'],
                'created_at': file['created_at'],
                'expires_at': file['expires_at']
            }
            return jsonify(info)
        finally:
            conn.close()
    except Exception as e:
        logger.error("Error in file_info: %s", str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/database')
def download_database():
    """Download the SQLite database file"""
    try:
        return send_file(
            app.config['DATABASE'],
            as_attachment=True,
            attachment_filename='files.db',
            mimetype='application/x-sqlite3'
        )
    except Exception as e:
        logger.error("Error downloading database: %s", str(e))
        return jsonify({'error': 'Database file not found'}), 404

# Cleanup task for expired files
@app.route('/cleanup', methods=['POST'])
def cleanup_expired_files():
    try:
        with get_db() as conn:
            # Get expired files
            expired_files = conn.execute(
                'SELECT filepath FROM files WHERE expires_at < ?', 
                (datetime.utcnow(),)
            ).fetchall()
            
            # Delete physical files
            for file in expired_files:
                try:
                    os.remove(file['filepath'])
                except:
                    pass
            
            # Delete database entries
            cursor = conn.execute('DELETE FROM files WHERE expires_at < ?', (datetime.utcnow(),))
            deleted_count = cursor.rowcount
            conn.commit()
            
            return jsonify({'message': 'Deleted %d expired files' % deleted_count})
    except Exception as e:
        logger.error("Error in cleanup: %s", str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413

@app.errorhandler(500)
def internal_error(error):
    logger.error("Internal server error: %s", str(error))
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error("Unhandled exception: %s", str(e))
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print(" * Running on http://127.0.0.1:5000/")
    app.run(host='127.0.0.1', port=5000)