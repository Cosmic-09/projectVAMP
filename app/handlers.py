"""
File and filesystem handlers
"""
import os
import urllib.parse
import mimetypes
import json
from datetime import datetime
from app.utils import safe_path, FILESYSTEM_STYLE


def render_filesystem_page(path: str = "/"):
    """Render the file manager welcome page"""
    return f"""
    <html>
    <head>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    {FILESYSTEM_STYLE}
    </head>
    <body>
    <div class='container'>
        <div class='header'>
            <h1>📁 File Explorer</h1>
            <p>Browse, view, and manage your files</p>
        </div>

        <div class='welcome-box'>
            <div class='quick-action'>
                <a href='/browse?path=/' class='btn-large'>📂 Open File Explorer</a>
            </div>

            <div class='path-form'>
                <form action='/browse' method='get'>
                    <input type='text' name='path' placeholder='Enter path like /Desktop' required>
                    <button type='submit'>Navigate</button>
                </form>
            </div>

            <div class='info-box'>
                <h3>Features</h3>
                <ul>
                    <li>📷 View images (JPG, PNG, GIF, etc.)</li>
                    <li>🎬 Play videos (MP4, WebM, etc.)</li>
                    <li>🎵 Play audio (MP3, OGG, WAV, etc.)</li>
                    <li>📄 View PDFs and documents</li>
                    <li>⬇️ Download files and folders</li>
                    <li>➕ Upload files</li>
                    <li>🗑️ Delete with password protection</li>
                </ul>
            </div>
        </div>
    </div>
    </body>
    </html>
    """


def get_file_icon(filename: str) -> str:
    """Get icon based on file type"""
    ext = os.path.splitext(filename)[1].lower()
    icons = {
        # Images
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.bmp': '🖼️', '.svg': '🖼️', '.webp': '🖼️',
        # Videos
        '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬', '.mkv': '🎬', '.webm': '🎬', '.flv': '🎬', '.wmv': '🎬',
        # Audio
        '.mp3': '🎵', '.wav': '🎵', '.ogg': '🎵', '.flac': '🎵', '.aac': '🎵', '.wma': '🎵',
        # PDF
        '.pdf': '📕',
        # Documents
        '.doc': '📄', '.docx': '📄', '.txt': '📝', '.md': '📝', '.xlsx': '📊', '.csv': '📊', '.xls': '📊',
        # Archives
        '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
        # Code
        '.py': '🐍', '.js': '🟨', '.ts': '🔵', '.html': '🌐', '.css': '🎨', '.json': '{ }',
        # Default
    }
    return icons.get(ext, '📄')


def get_file_size_str(file_path: str) -> str:
    """Get human-readable file size"""
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except:
        return "?"


def get_mod_time_str(file_path: str) -> str:
    """Get modification time as formatted string"""
    try:
        mod_time = os.path.getmtime(file_path)
        dt = datetime.fromtimestamp(mod_time)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return "?"


def render_browse_page(path: str, items: list, root_dir: str):
    """Render file browser page with modern file explorer UI"""
    html = f"""
    <html>
    <head>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    {FILESYSTEM_STYLE}
    </head>
    <body>
    <div class='container'>
        <div class='breadcrumb'>
            <a href='/'>🏠 Home</a> /
            <span class='path-display'>{path}</span>
        </div>

        <div class='toolbar'>
            <h2>📁 {path}</h2>
            <button class='btn-nav' onclick='history.back()'>⬅ Back</button>
        </div>

        <div class='file-list'>
    """

    # Sort items with folders first
    folders = []
    files = []
    for item in items:
        item_path = os.path.join(path, item)
        full_item = safe_path(item_path, root_dir)
        if os.path.isdir(full_item):
            folders.append((item, item_path, full_item))
        else:
            files.append((item, item_path, full_item))

    folders.sort(key=lambda x: x[0].lower())
    files.sort(key=lambda x: x[0].lower())

    # Display folders
    for item, item_path, full_item in folders:
        item_query = urllib.parse.quote(item_path)
        item_path_json = json.dumps(item_path)
        file_count = len(os.listdir(full_item))
        html += f"""
            <div class='file-item folder-item'>
                <div class='file-info'>
                    <div class='file-name'>📁 <a href='/browse?path={item_query}'>{item}</a></div>
                    <div class='file-meta'>{file_count} items</div>
                </div>
                <div class='file-actions'>
                    <a href='/download_folder?path={item_query}' class='btn-small'>⬇ Download</a>
                    <button class='btn-small btn-delete' onclick='deleteItem({item_path_json}, true, {json.dumps(item)})'>🗑️ Delete</button>
                </div>
            </div>
        """

    # Display files
    for item, item_path, full_item in files:
        item_query = urllib.parse.quote(item_path)
        item_path_json = json.dumps(item_path)
        icon = get_file_icon(item)
        size = get_file_size_str(full_item)
        mod_time = get_mod_time_str(full_item)
        
        html += f"""
            <div class='file-item'>
                <div class='file-info'>
                    <div class='file-name'>{icon} <a href='/view?path={item_query}'>{item}</a></div>
                    <div class='file-meta'>{size} • {mod_time}</div>
                </div>
                <div class='file-actions'>
                    <a href='/download?path={item_query}' class='btn-small'>⬇ Download</a>
                    <button class='btn-small btn-delete' onclick='deleteItem({item_path_json}, false, {json.dumps(item)})'>🗑️ Delete</button>
                </div>
            </div>
        """

    html += """
        </div>

        <div class='upload-section'>
            <div class='upload-box'>
                <h3>📤 Upload File</h3>
                <form action='/upload' method='post' enctype='multipart/form-data'>
    """
    html += f"                <input type='hidden' name='path' value='{path}'>"
    html += """
                    <input type='file' name='file' required>
                    <button type='submit' class='btn-upload'>Upload</button>
                </form>
            </div>

            <div class='upload-box'>
                <h3>📁 Upload Multiple Files</h3>
                <form action='/upload_folder' method='post' enctype='multipart/form-data'>
    """
    html += f"                <input type='hidden' name='path' value='{path}'>"
    html += """
                    <input type='file' name='files' multiple required>
                    <button type='submit' class='btn-upload'>Upload</button>
                </form>
            </div>
        </div>
    </div>

    <!-- Delete Modal -->
    <div id='deleteModal' class='modal'>
        <div class='modal-content'>
            <h2>Delete File?</h2>
            <p id='deleteFileName'></p>
            <input type='password' id='deletePassword' placeholder='Enter admin password' />
            <div class='modal-buttons'>
                <button onclick='confirmDelete()' class='btn-confirm'>Delete</button>
                <button onclick='closeDeleteModal()' class='btn-cancel'>Cancel</button>
            </div>
        </div>
    </div>

    <script>
    let deleteItemPath = '';
    let isFolder = false;

    function deleteItem(itemPath, folder, itemName) {
        deleteItemPath = itemPath;
        isFolder = folder;
        document.getElementById('deleteFileName').textContent = (folder ? '📁 ' : '📄 ') + itemName;
        document.getElementById('deletePassword').value = '';
        document.getElementById('deleteModal').style.display = 'block';
    }

    function closeDeleteModal() {
        document.getElementById('deleteModal').style.display = 'none';
    }

    function confirmDelete() {
        const password = document.getElementById('deletePassword').value;
        if (!password) {
            alert('Please enter password');
            return;
        }
        
        fetch('/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: deleteItemPath,
                password: password
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                alert('Deleted successfully');
                location.reload();
            }
        })
        .catch(err => alert('Error: ' + err));
    }

    window.onclick = function(event) {
        const modal = document.getElementById('deleteModal');
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
    </script>

    </body>
    </html>
    """

    return html


def render_view_page(path: str, full_path: str, mime_type: str = None):
    """Render file view page with support for multiple file types"""
    
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(full_path)
    
    filename = os.path.basename(path)
    file_size = get_file_size_str(full_path)
    mod_time = get_mod_time_str(full_path)

    # Image files
    if mime_type and mime_type.startswith('image/'):
        return f"""
        <html>
        <head>{FILESYSTEM_STYLE}</head>
        <body>
        <div class='view-container'>
            <div class='view-header'>
                <h2>🖼️ {filename}</h2>
                <div class='view-meta'>{file_size} • {mod_time}</div>
                <div class='view-actions'>
                    <a href='/download?path={urllib.parse.quote(path)}' class='btn-view'>⬇ Download</a>
                    <a href='javascript:history.back()' class='btn-view'>⬅ Back</a>
                </div>
            </div>
            <div class='view-content'>
                <img src='/download?path={urllib.parse.quote(path)}' class='media-content'>
            </div>
        </div>
        </body>
        </html>
        """

    # Video files
    elif mime_type and mime_type.startswith('video/'):
        return f"""
        <html>
        <head>{FILESYSTEM_STYLE}</head>
        <body>
        <div class='view-container'>
            <div class='view-header'>
                <h2>🎬 {filename}</h2>
                <div class='view-meta'>{file_size} • {mod_time}</div>
                <div class='view-actions'>
                    <a href='/download?path={urllib.parse.quote(path)}' class='btn-view'>⬇ Download</a>
                    <a href='javascript:history.back()' class='btn-view'>⬅ Back</a>
                </div>
            </div>
            <div class='view-content'>
                <video controls class='media-content'>
                    <source src='/download?path={urllib.parse.quote(path)}' type='{mime_type}'>
                    Your browser does not support the video tag.
                </video>
            </div>
        </div>
        </body>
        </html>
        """

    # Audio files
    elif mime_type and mime_type.startswith('audio/'):
        return f"""
        <html>
        <head>{FILESYSTEM_STYLE}</head>
        <body>
        <div class='view-container'>
            <div class='view-header'>
                <h2>🎵 {filename}</h2>
                <div class='view-meta'>{file_size} • {mod_time}</div>
                <div class='view-actions'>
                    <a href='/download?path={urllib.parse.quote(path)}' class='btn-view'>⬇ Download</a>
                    <a href='javascript:history.back()' class='btn-view'>⬅ Back</a>
                </div>
            </div>
            <div class='view-content audio-content'>
                <audio controls class='media-content'>
                    <source src='/download?path={urllib.parse.quote(path)}' type='{mime_type}'>
                    Your browser does not support the audio tag.
                </audio>
            </div>
        </div>
        </body>
        </html>
        """

    # PDF files
    elif mime_type == 'application/pdf' or filename.lower().endswith('.pdf'):
        return f"""
        <html>
        <head>{FILESYSTEM_STYLE}</head>
        <body>
        <div class='view-container'>
            <div class='view-header'>
                <h2>📕 {filename}</h2>
                <div class='view-meta'>{file_size} • {mod_time}</div>
                <div class='view-actions'>
                    <a href='/download?path={urllib.parse.quote(path)}' class='btn-view'>⬇ Download</a>
                    <a href='javascript:history.back()' class='btn-view'>⬅ Back</a>
                </div>
            </div>
            <div class='view-content'>
                <iframe src='/download?path={urllib.parse.quote(path)}' class='pdf-viewer'></iframe>
            </div>
        </div>
        </body>
        </html>
        """

    # Text/Code files
    else:
        try:
            with open(full_path, "r", errors="ignore") as f:
                content = f.read(50000)
        except:
            content = "[Unable to read file]"

        # Detect language for syntax highlighting
        ext = os.path.splitext(filename)[1].lower()
        language_map = {{
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.html': 'html',
            '.css': 'css', '.json': 'json', '.xml': 'xml', '.sql': 'sql',
            '.cpp': 'cpp', '.c': 'c', '.java': 'java', '.go': 'go',
            '.rb': 'ruby', '.php': 'php', '.sh': 'bash', '.md': 'markdown'
        }}
        lang = language_map.get(ext, 'plaintext')
        
        return f"""
        <html>
        <head>
            {FILESYSTEM_STYLE}
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
        </head>
        <body>
        <div class='view-container'>
            <div class='view-header'>
                <h2>📄 {filename}</h2>
                <div class='view-meta'>{file_size} • {mod_time}</div>
                <div class='view-actions'>
                    <a href='/download?path={urllib.parse.quote(path)}' class='btn-view'>⬇ Download</a>
                    <a href='javascript:history.back()' class='btn-view'>⬅ Back</a>
                </div>
            </div>
            <div class='view-content code-content'>
                <pre><code class='language-{lang}'>{content}</code></pre>
            </div>
        </div>
        <script>
            document.querySelectorAll('code').forEach(el => {{
                hljs.highlightElement(el);
            }});
        </script>
        </body>
        </html>
        """
