#!/usr/bin/env python3
import os
import json
import socket
import time
import threading
import uuid
import hashlib
import base64
import secrets
import gzip
import io
import sqlite3
import struct
from datetime import datetime, timedelta
from urllib.parse import unquote, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import cgi
import shutil
import mimetypes
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass


# Key generation for encryption purposes
KEY = base64.urlsafe_b64encode(os.urandom(32))
fernet = Fernet(KEY)

# Advanced Analytics Database
class AnalyticsDB:
    def __init__(self):
        self.db_path = 'analytics.db'
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                file_size INTEGER,
                file_type TEXT,
                upload_time TIMESTAMP,
                ip_address TEXT,
                compressed_size INTEGER,
                download_count INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def log_upload(self, filename, file_size, file_type, ip_address, compressed_size):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO uploads (filename, file_size, file_type, upload_time, ip_address, compressed_size)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, file_size, file_type, datetime.now(), ip_address, compressed_size))
        conn.commit()
        conn.close()
    
    def increment_download(self, filename):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE uploads SET download_count = download_count + 1 WHERE filename = ?', (filename,))
        conn.commit()
        conn.close()
    
    def get_stats(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total files and size
        cursor.execute('SELECT COUNT(*), SUM(file_size), SUM(compressed_size) FROM uploads')
        total_files, total_size, total_compressed = cursor.fetchone()
        
        # Today's uploads
        today = datetime.now().date()
        cursor.execute('SELECT COUNT(*) FROM uploads WHERE DATE(upload_time) = ?', (today,))
        today_uploads = cursor.fetchone()[0]
        
        # Popular file types
        cursor.execute('SELECT file_type, COUNT(*) FROM uploads GROUP BY file_type ORDER BY COUNT(*) DESC LIMIT 5')
        popular_types = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_files': total_files or 0,
            'total_size': total_size or 0,
            'total_compressed': total_compressed or 0,
            'today_uploads': today_uploads or 0,
            'popular_types': popular_types,
            'compression_ratio': round((1 - (total_compressed or 1) / (total_size or 1)) * 100, 1) if total_size else 0
        }

analytics = AnalyticsDB()

# A simple token generator for user session management
def generate_token():
    return secrets.token_urlsafe(16)

# Smart file compression
def compress_file_data(data, filename):
    """Compress file data if beneficial"""
    # Don't compress already compressed formats
    compressed_formats = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3', '.zip', '.rar', '.7z'}
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in compressed_formats:
        return data, len(data)  # Return original data and size
    
    # Compress for text files, documents, etc.
    compressed = gzip.compress(data)
    if len(compressed) < len(data) * 0.95:  # Only if compression saves >5%
        return compressed, len(compressed)
    else:
        return data, len(data)

def decompress_file_data(data, filename):
    """Decompress file data if it was compressed"""
    compressed_formats = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3', '.zip', '.rar', '.7z'}
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in compressed_formats:
        return data  # Not compressed
    
    try:
        return gzip.decompress(data)
    except:
        return data  # Fallback to original if decompression fails

def add_file_expiry(filepath, hours=24):
    expiry_time = datetime.now() + timedelta(hours=hours)
    os.utime(filepath, (expiry_time.timestamp(), expiry_time.timestamp()))

class FileCleaner(threading.Thread):
    def run(self):
        while True:
            try:
                now = time.time()
                if os.path.exists('uploads'):
                    for filename in os.listdir('uploads'):
                        filepath = os.path.join('uploads', filename)
                        if os.path.isfile(filepath):
                            # Check if file is older than 24 hours
                            file_age = now - os.path.getctime(filepath)
                            if file_age > 86400:  # 24 hours in seconds
                                os.remove(filepath)
                                # Also remove associated token file
                                token_path = f"{filepath}.token"
                                if os.path.exists(token_path):
                                    os.remove(token_path)
                                print(f"🗑️ Auto-deleted (24h): {filename}")
            except Exception as e:
                print(f"⚠️ Cleaner error: {e}")
            time.sleep(3600)  # Check every hour

# Start cleaner thread
cleaner = FileCleaner()
cleaner.daemon = True
cleaner.start()

class FileTransferHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.upload_dir = "uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to reduce console spam"""
        return
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_file('index.html', 'text/html')
        elif self.path == '/manifest.json':
            self.serve_file('manifest.json', 'application/json')
        elif self.path == '/sw.js':
            self.serve_file('sw.js', 'application/javascript')
        elif self.path == '/files':
            self.list_files()
        elif self.path == '/analytics':
            self.get_analytics()
        elif self.path == '/health':
            self.health_check()
        elif self.path.startswith('/download/'):
            filename = unquote(self.path[10:])  # Remove '/download/'
            self.download_file(filename)
        elif self.path.startswith('/preview/'):
            filename = unquote(self.path[9:])  # Remove '/preview/'
            self.preview_file(filename)
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/upload':
            self.upload_file()
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        if self.path.startswith('/delete/'):
            filename = unquote(self.path[8:])  # Remove '/delete/'
            self.delete_file(filename)
        else:
            self.send_error(404)
    
    def serve_file(self, filename, content_type):
        try:
            with open(filename, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)
    
    def upload_file(self):
        try:
            # Parse the multipart form data
            content_type = self.headers.get('Content-Type')
            if not content_type or not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Bad Request: Expected multipart/form-data")
                return
            
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Bad Request: No content")
                return
            
            # Parse form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers.get('Content-Type'),
                }
            )
            
            if 'file' not in form:
                self.send_error(400, "Bad Request: No file field")
                return
            
            file_item = form['file']
            if not file_item.filename:
                self.send_error(400, "Bad Request: No file selected")
                return
            
            # Save the file
            filename = file_item.filename
            # Sanitize filename
            filename = os.path.basename(filename)
            
            filepath = os.path.join(self.upload_dir, filename)
            
            # Handle duplicate filenames
            counter = 1
            original_filepath = filepath
            while os.path.exists(filepath):
                name, ext = os.path.splitext(original_filepath)
                filepath = f"{name}_{counter}{ext}"
                counter += 1
            
            # Write file in chunks to handle large files
            original_size = 0
            with open(filepath, 'wb') as f:
                while True:
                    chunk = file_item.file.read(8192)
                    if not chunk:
                        break
                    original_size += len(chunk)
                    f.write(chunk)

            # Smart compression and encryption
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            # Compress if beneficial
            compressed_data, compressed_size = compress_file_data(file_data, filename)
            was_compressed = len(compressed_data) < len(file_data)
            
            # Create metadata with compression info
            metadata = {
                'compressed': was_compressed,
                'original_size': len(file_data),
                'filename': filename
            }
            metadata_json = json.dumps(metadata).encode()
            
            # Combine metadata and data
            combined_data = len(metadata_json).to_bytes(4, 'big') + metadata_json + compressed_data
            
            # Encrypt the combined data
            encrypted_data = fernet.encrypt(combined_data)
            
            # Write encrypted data back
            with open(filepath, 'wb') as f:
                f.write(encrypted_data)

            # Generate unique owner token for this upload
            owner_token = generate_token()
            token_path = f"{filepath}.token"
            with open(token_path, 'w') as token_file:
                token_file.write(owner_token)
            
            # Log to analytics
            file_type = os.path.splitext(filename)[1].lower() or 'unknown'
            client_ip = self.client_address[0]
            analytics.log_upload(filename, original_size, file_type, client_ip, compressed_size)
            
            print(f"✅ File uploaded: {os.path.basename(filepath)} ({self.get_file_size(filepath)})")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('X-Owner-Token', owner_token)  # Return token to client
            self.end_headers()
            response = json.dumps({"status": "success", "filename": os.path.basename(filepath), "owner_token": owner_token})
            self.wfile.write(response.encode())
            
        except Exception as e:
            print(f"❌ Upload error: {str(e)}")
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def list_files(self):
        try:
            files = []
            for filename in os.listdir(self.upload_dir):
                filepath = os.path.join(self.upload_dir, filename)
                # Skip system files, hidden files, and token files
                if (os.path.isfile(filepath) and 
                    not filename.endswith('.token') and 
                    not filename.startswith('.') and 
                    filename not in ['.gitkeep', '.DS_Store', 'Thumbs.db']):
                    
                    # Read metadata to get original size
                    original_size = os.path.getsize(filepath) # Fallback to current size
                    try:
                        with open(filepath, 'rb') as f:
                            encrypted_data = f.read()
                            decrypted_data = fernet.decrypt(encrypted_data)
                            
                            # Extract metadata size
                            metadata_len = int.from_bytes(decrypted_data[:4], 'big')
                            # Extract metadata JSON
                            metadata_json = decrypted_data[4:4+metadata_len]
                            metadata = json.loads(metadata_json.decode())
                            original_size = metadata.get('original_size', original_size)

                    except Exception as e:
                        print(f"Could not read metadata for {filename}: {e}")

                    files.append({
                        'name': filename,
                        'size': original_size
                    })
            
            files.sort(key=lambda f: os.path.getmtime(os.path.join(self.upload_dir, f['name'])), reverse=True)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps(files)
            self.wfile.write(response.encode())
            
        except Exception as e:
            print(f"❌ List files error: {str(e)}")
            self.send_error(500)
    
    def download_file(self, filename):
        try:
            filepath = os.path.join(self.upload_dir, filename)
            if not os.path.exists(filepath) or not os.path.isfile(filepath):
                self.send_error(404, "File not found")
                return
            
            # First decrypt and extract data with metadata
            with open(filepath, 'rb') as f:
                encrypted_data = f.read()
                try:
                    # Decrypt first
                    decrypted_data = fernet.decrypt(encrypted_data)
                    
                    # Check if this is new format with metadata
                    try:
                        # Extract metadata length (first 4 bytes)
                        metadata_len = int.from_bytes(decrypted_data[:4], 'big')
                        # Extract metadata JSON
                        metadata_json = decrypted_data[4:4+metadata_len]
                        metadata = json.loads(metadata_json.decode())
                        # Extract file data
                        file_data = decrypted_data[4+metadata_len:]
                        
                        # Decompress only if it was compressed
                        if metadata.get('compressed', False):
                            final_data = gzip.decompress(file_data)
                        else:
                            final_data = file_data
                            
                    except (json.JSONDecodeError, ValueError, struct.error):
                        # Fallback to old format
                        final_data = decompress_file_data(decrypted_data, filename)
                    
                    # Update download counter
                    analytics.increment_download(filename)
                    
                    # Send correct headers with actual file size
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                    self.send_header('Content-Length', str(len(final_data)))
                    self.end_headers()
                    
                    # Send decompressed data in chunks
                    offset = 0
                    while offset < len(final_data):
                        chunk_size = min(8192, len(final_data) - offset)
                        chunk = final_data[offset:offset + chunk_size]
                        self.wfile.write(chunk)
                        offset += chunk_size
                        
                except Exception as e:
                    print(f"Decryption/decompression error: {e}")
                    # Fallback: send encrypted data as-is
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                    self.send_header('Content-Length', str(len(encrypted_data)))
                    self.end_headers()
                    self.wfile.write(encrypted_data)
            
            print(f"📥 File downloaded: {filename}")
            
        except Exception as e:
            print(f"❌ Download error: {str(e)}")
            self.send_error(500)
    
    def preview_file(self, filename):
        """Serve file for preview/streaming with proper MIME type detection"""
        try:
            filepath = os.path.join(self.upload_dir, filename)
            if not os.path.exists(filepath) or not os.path.isfile(filepath):
                self.send_error(404, "File not found")
                return
            
            # Decrypt and extract data with metadata
            with open(filepath, 'rb') as f:
                encrypted_data = f.read()
                try:
                    # Decrypt first
                    decrypted_data = fernet.decrypt(encrypted_data)
                    
                    # Check if this is new format with metadata
                    try:
                        # Extract metadata length (first 4 bytes)
                        metadata_len = int.from_bytes(decrypted_data[:4], 'big')
                        # Extract metadata JSON
                        metadata_json = decrypted_data[4:4+metadata_len]
                        metadata = json.loads(metadata_json.decode())
                        # Extract file data
                        file_data = decrypted_data[4+metadata_len:]
                        
                        # Decompress only if it was compressed
                        if metadata.get('compressed', False):
                            final_data = gzip.decompress(file_data)
                        else:
                            final_data = file_data
                            
                    except (json.JSONDecodeError, ValueError, struct.error):
                        # Fallback to old format
                        final_data = decompress_file_data(decrypted_data, filename)
                        
                except Exception as e:
                    print(f"Decryption/decompression error for preview: {e}")
                    self.send_error(500, "Failed to process file")
                    return
            
            # Detect MIME type based on file extension
            content_type, _ = mimetypes.guess_type(filename)
            if content_type is None:
                content_type = 'application/octet-stream'
            
            # Set appropriate headers for preview/streaming
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(final_data)))
            
            # Add headers for better media handling
            if content_type.startswith(('audio/', 'video/')):
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Cache-Control', 'no-cache')
            
            self.end_headers()
            
            # Send the file data
            self.wfile.write(final_data)
            
            print(f"👁️ File previewed: {filename}")
            
        except Exception as e:
            print(f"❌ Preview error: {str(e)}")
            self.send_error(500)
    
    def delete_file(self, filename):
        try:
            filepath = os.path.join(self.upload_dir, filename)
            if not os.path.exists(filepath) or not os.path.isfile(filepath):
                self.send_error(404, "File not found")
                return
            
            # Get owner token from request header
            owner_token = self.headers.get('X-Owner-Token')
            if not owner_token:
                self.send_error(403, "Forbidden: No owner token provided")
                return
            
            # Check if token matches
            token_path = f"{filepath}.token"
            if not os.path.exists(token_path):
                self.send_error(404, "Token file not found")
                return
                
            with open(token_path, 'r') as token_file:
                saved_token = token_file.read()
            if owner_token != saved_token:
                self.send_error(403, "Forbidden: Invalid owner token")
                return

            os.remove(filepath)
            os.remove(token_path)  # Remove the token file linked to the file
            print(f"🗑️ File manually deleted: {filename}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "success", "message": "File deleted successfully"})
            self.wfile.write(response.encode())
            
        except Exception as e:
            print(f"❌ Delete error: {str(e)}")
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def get_analytics(self):
        """Return analytics data as JSON"""
        try:
            stats = analytics.get_stats()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps(stats)
            self.wfile.write(response.encode())
            
        except Exception as e:
            print(f"❌ Analytics error: {str(e)}")
            self.send_error(500)
    
    def health_check(self):
        """Health check endpoint for monitoring"""
        try:
            # Check if uploads directory exists
            uploads_ok = os.path.exists('uploads')
            
            # Check database connection
            try:
                analytics.get_stats()
                db_ok = True
            except:
                db_ok = False
            
            health_status = {
                'status': 'healthy' if uploads_ok and db_ok else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'service': 'B-Transfer Pro by Balsim Productions',
                'checks': {
                    'uploads_directory': uploads_ok,
                    'database': db_ok,
                    'encryption': True  # Fernet is always available if server starts
                }
            }
            
            self.send_response(200 if health_status['status'] == 'healthy' else 503)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps(health_status, indent=2)
            self.wfile.write(response.encode())
            
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            self.send_error(500)
    
    def get_file_size(self, filepath):
        size_bytes = os.path.getsize(filepath)
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote address (doesn't actually connect)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    port = int(os.environ.get('PORT', 8081))  # Use Heroku's port or default to 8081
    local_ip = get_local_ip()
    
    print("📱 B-Transfer Server Starting...")
    print("=" * 60)
    print(f"📱 Access from your phone: http://{local_ip}:{port}")
    print(f"💻 Access from this computer: http://localhost:{port}")
    print("=" * 60)
    print("📁 Files encrypted and saved in 'uploads' folder")
    print("🔄 Server supports up to 5GB file transfers")
    print("🔐 Advanced security with owner authentication")
    print("⚡ Fast local network transfer - no internet needed!")
    print("🏢 Powered by Balsim Productions")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("")
    
    try:
        server = ThreadedHTTPServer(('0.0.0.0', port), FileTransferHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 B-Transfer server stopped. Thanks for using B-Transfer by Balsim Productions!")
        server.shutdown()

if __name__ == '__main__':
    main()
