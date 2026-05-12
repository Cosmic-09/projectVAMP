from fastapi import FastAPI, WebSocket, Request, Form, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import asyncio
import os
import pty
import subprocess
import shutil
import signal
import zipfile
import tempfile
from datetime import datetime
import mimetypes
import time

from app_secrets import ADMIN_USERNAME, ADMIN_PASSWORD, SESSION_SECRET_KEY
from app.utils import get_system_status, safe_path
from app.handlers import render_filesystem_page, render_browse_page, render_view_page


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")
ROOT_DIR = "/home/akshith"

def check_session(req: Request):
    user = req.session.get("name")
    if not user:
        return None
    last_active = req.session.get("last_active")
    if last_active and time.time() - last_active > 3600:  # 1 hour timeout
        req.session.clear()
        return None
    req.session["last_active"] = time.time()
    return user

@app.get("/")
def home(req: Request):
    user = req.session.get("name")
    if user == ADMIN_USERNAME:
        return FileResponse("templates/home.html")
    return FileResponse("templates/index.html")

@app.post("/")
async def login(request:Request ,username: str = Form(...), password: str = Form(...)):

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["name"] = username
        request.session["last_active"] = time.time()
        return FileResponse("templates/home.html")
        
    else:
        return RedirectResponse(url="/", status_code=303)

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@app.post("/run")
async def run_command(req: Request):
    user = req.session.get("name")
    if user != ADMIN_USERNAME:
        return {"error": "not logged in"}

    data = await req.json()
    cmd = data.get("command")
    cmd_password = data.get("password")
    if cmd == "vsc":
        open_app = "code"
        output = os.popen(f"ps aux | grep {open_app} | grep -v grep").read()
        if not (open_app in output):
            subprocess.Popen(["code"])
        else:
            return{"error":"already opened"}
            
    elif cmd == "firefox":
        output = os.popen(f"ps aux | grep {cmd} | grep -v grep").read()
        if not (cmd in output):
            subprocess.Popen(["firefox"])
        else:
            return{"error":"already opened"}

    elif cmd == "stop_server":
        if cmd_password != ADMIN_PASSWORD:
            return {"error":"wrong password"}
        os.kill(os.getpid(), signal.SIGTERM)

    elif cmd == "shutdown":
        if cmd_password != ADMIN_PASSWORD:
            return {"error":"wrong password"}
        else:
            os.system("shutdown now")
    return {"status": "ok", "command": cmd}

@app.get("/system_status")
def system_status(req: Request):
    user = check_session(req)
    if not user:
        return {"error": "not logged in"}
    return get_system_status()

@app.get("/terminal")
def terminal_page(req: Request):
    user = check_session(req)
    if not user:
        return RedirectResponse(url="/", status_code=302)
    return FileResponse("templates/terminal.html")

@app.websocket("/ws")
async def terminal(ws: WebSocket):
    await ws.accept()

    pid, fd = pty.fork()

    if pid == 0:
        os.environ["TERM"] = "xterm"
        os.execvp("bash", ["bash"])
    else:
        loop = asyncio.get_event_loop()

        async def read_shell():
            while True:
                try:
                    data = await loop.run_in_executor(None, os.read, fd, 1024)
                    if not data:
                        break
                    await ws.send_text(data.decode(errors="ignore"))
                except:
                    break

            await ws.close()

        async def write_shell():
            while True:
                try:
                    msg = await ws.receive_text()

                    if msg.strip() == "exit":
                        await ws.send_text("\r\n👋 Closing terminal...\r\n")
                        await ws.close()
                        break

                    os.write(fd, msg.encode())
                except:
                    break

        await asyncio.gather(read_shell(), write_shell())




@app.post("/filesystem", response_class=HTMLResponse)
async def filesystem(req: Request, password: str = Form(...)):
    user = check_session(req)
    if not user:
        return RedirectResponse(url="/", status_code=302)
    
    if password != ADMIN_PASSWORD:
        return "Wrong password"
    
    return render_filesystem_page()

# 📂 BROWSE
@app.get("/browse", response_class=HTMLResponse)
def browse(req: Request, path: str = "/"):
    user = check_session(req)
    if not user:
        return RedirectResponse(url="/", status_code=302)
    
    full_path = safe_path(path, ROOT_DIR)
    if not os.path.exists(full_path):
        return "Not found"

    items = os.listdir(full_path)
    return render_browse_page(path, items, ROOT_DIR)

# 👁 VIEW
@app.get("/view", response_class=HTMLResponse)
def view(req: Request, path: str):
    user = check_session(req)
    if not user:
        return RedirectResponse(url="/", status_code=302)
    
    full_path = safe_path(path, ROOT_DIR)
    if not os.path.exists(full_path):
        return "Not found"
    if os.path.isdir(full_path):
        return "Cannot view a directory"

    mime_type, _ = mimetypes.guess_type(full_path)
    
    return render_view_page(path, full_path, mime_type)

# ⬇ DOWNLOAD
@app.get("/download")
def download(req: Request, path: str):
    user = check_session(req)
    if not user:
        return RedirectResponse(url="/", status_code=302)
    
    full_path = safe_path(path, ROOT_DIR)
    if not os.path.exists(full_path):
        return RedirectResponse(url='/', status_code=302)
    return FileResponse(full_path, filename=os.path.basename(full_path))

# ⬇ DOWNLOAD FOLDER
@app.get("/download_folder")
def download_folder(req: Request, path: str):
    user = check_session(req)
    if not user:
        return RedirectResponse(url="/", status_code=302)
    
    full_path = safe_path(path, ROOT_DIR)
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return RedirectResponse(url='/', status_code=302)
    
    # Create a temporary zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        zip_path = tmp.name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(full_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(full_path))
                zipf.write(file_path, arcname)
    
    folder_name = os.path.basename(full_path)
    return FileResponse(zip_path, filename=f"{folder_name}.zip", media_type='application/zip')

# 📤 UPLOAD
@app.post("/upload")
async def upload(req: Request, path: str = Form(...), file: UploadFile = File(...)):
    user = check_session(req)
    if not user:
        return RedirectResponse(url="/", status_code=302)
    
    target = safe_path(path, ROOT_DIR)
    filename = file.filename.rstrip('/')  # Remove trailing slash if present
    file_path = os.path.join(target, filename)

    if os.path.exists(file_path) and os.path.isdir(file_path):
        return "Cannot overwrite a directory with a file"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return RedirectResponse(url=f"/browse?path={path}", status_code=303)

# 📁 UPLOAD FOLDER
@app.post("/upload_folder")
async def upload_folder(req: Request, path: str = Form(...), files: list[UploadFile] = File(...)):
    user = check_session(req)
    if not user:
        return RedirectResponse(url="/", status_code=302)
    
    target = safe_path(path, ROOT_DIR)
    
    # Create a new folder with timestamp
    folder_name = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    folder_path = os.path.join(target, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    for file in files:
        filename = file.filename
        if not filename:
            continue
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    
    return RedirectResponse(url=f"/browse?path={path}", status_code=303)

# 🗑️ DELETE
@app.post("/delete")
async def delete_file(req: Request):
    user = check_session(req)
    if not user:
        return {"error": "not logged in"}
    
    data = await req.json()
    path = data.get("path", "")
    password = data.get("password", "")
    
    if password != ADMIN_PASSWORD:
        return {"error": "wrong password"}
    
    full_path = safe_path(path, ROOT_DIR)
    if not os.path.exists(full_path):
        return {"error": "file not found"}
    
    try:
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        return {"status": "deleted"}
    except Exception as e:
        return {"error": str(e)}