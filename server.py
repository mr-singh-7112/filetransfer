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

# A simple token generator for user session management
def generate_token():
    return secrets.token_urlsafe(16)

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
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
            
            filepath = os.path.join(self.upload_dir, filename)
            
            # Handle duplicate filenames
            counter = 1
            original_filepath = filepath
            while os.path.exists(filepath):
                name, ext = os.path.splitext(original_filepath)
                filepath = f"{name}_{counter}{ext}"
                counter += 1
            
            # Write file in chunks to handle large files
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(file_item.file, f)

            # Generate unique owner token for this upload
            owner_token = generate_token()
            token_path = f"{filepath}.token"
            with open(token_path, 'w') as token_file:
                token_file.write(owner_token)

            # Optionally encrypt file content with Fernet
            with open(filepath, 'rb') as file_to_encrypt:
                encrypted_data = fernet.encrypt(file_to_encrypt.read())
            with open(filepath, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_data)
            
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
                if os.path.isfile(filepath) and not filename.endswith('.token'):
                    files.append({
                        'name': filename,
                        'size': os.path.getsize(filepath)
                    })
            
            files.sort(key=lambda x: x['name'])
            
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
            
            file_size = os.path.getsize(filepath)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(file_size))
            self.end_headers()
            
            # Decrypt and send file in chunks for large files
            with open(filepath, 'rb') as f:
                encrypted_data = f.read()
                try:
                    decrypted_data = fernet.decrypt(encrypted_data)
                    # Send decrypted data in chunks
                    offset = 0
                    while offset < len(decrypted_data):
                        chunk_size = min(8192, len(decrypted_data) - offset)
                        chunk = decrypted_data[offset:offset + chunk_size]
                        self.wfile.write(chunk)
                        offset += chunk_size
                except Exception as e:
                    print(f"Decryption error: {e}")
                    # Fallback: send as-is if decryption fails
                    self.wfile.write(encrypted_data)
            
            print(f"📥 File downloaded: {filename}")
            
        except Exception as e:
            print(f"❌ Download error: {str(e)}")
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
    
    print("🚀 Quick File Transfer Server Starting...")
    print("=" * 50)
    print(f"📱 Access from your phone: http://{local_ip}:{port}")
    print(f"💻 Access from this computer: http://localhost:{port}")
    print("=" * 50)
    print("📁 Files will be saved in the 'uploads' folder")
    print("🔄 Server supports up to 5GB file transfers")
    print("⚡ Fast local network transfer - no internet needed!")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print("")
    
    try:
        server = ThreadedHTTPServer(('0.0.0.0', port), FileTransferHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped. Thanks for using Quick Transfer!")
        server.shutdown()

if __name__ == '__main__':
    main()
