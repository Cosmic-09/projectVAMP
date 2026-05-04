from fastapi import FastAPI, WebSocket, Request, Form, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import asyncio
import os
import pty
import subprocess
import shutil
import signal
import urllib.parse

from app_secrets import ADMIN_USERNAME, ADMIN_PASSWORD, SESSION_SECRET_KEY


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)
ROOT_DIR = "/home/akshith"

@app.get("/")
def home(req: Request):
    user = req.session.get("name")
    if user == ADMIN_USERNAME:
        return FileResponse("home.html")
    return FileResponse("index.html")

@app.post("/")
async def login(request:Request ,username: str = Form(...), password: str = Form(...)):

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["name"] = username
        return FileResponse("home.html")
        
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
            os.system("sudo shutdown now")
    return {"status": "ok", "command": cmd}

@app.get("/terminal")
def terminal_page(req: Request):
    user = req.session.get("name")
    if user != ADMIN_USERNAME:
            return RedirectResponse(url="/", status_code=302)
    return FileResponse("terminal.html")

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

def safe_path(path: str):
    if path is None:
        path = ""
    path = path.strip()
    if path in ("", "/"):
        normalized = ""
    else:
        normalized = path.lstrip("/")

    full_path = os.path.abspath(os.path.join(ROOT_DIR, normalized))
    if not full_path.startswith(ROOT_DIR):
        raise Exception("Access denied")
    return full_path

# 🎨 RESPONSIVE STYLE (MOBILE + LAPTOP)
STYLE = """
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Arial;
    background: #0f172a;
    color: #e2e8f0;
    padding: 10px;
}

.container {
    max-width: 1000px;
    margin: auto;
}

.box {
    background: #1e293b;
    padding: 12px;
    border-radius: 10px;
    margin-top: 10px;
}

a {
    color: #38bdf8;
    text-decoration: none;
    margin-right: 10px;
    display: inline-block;
}

.file {
    padding: 10px;
    border-bottom: 1px solid #334155;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

input, button {
    width: 100%;
    padding: 10px;
    border-radius: 6px;
    border: none;
    font-size: 16px;
    margin-top: 6px;
}

button {
    background: #38bdf8;
    cursor: pointer;
    font-weight: bold;
}

img {
    max-width: 100%;
    border-radius: 10px;
}

pre {
    white-space: pre-wrap;
    word-break: break-word;
}

/* 📱 MOBILE */
@media (max-width: 600px) {
    a {
        display: block;
        margin: 6px 0;
    }
}

/* 💻 DESKTOP */
@media (min-width: 768px) {
    .file {
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
    }

    input, button {
        width: auto;
        max-width: 300px;
    }
}
</style>
"""

# 🏠 HOME
@app.post("/filesystem", response_class=HTMLResponse)
async def filesystem(req: Request, password: str = Form(...)):
    user = req.session.get("name")
    if user != ADMIN_USERNAME:
        return RedirectResponse(url="/", status_code=302)
    
    if password != ADMIN_PASSWORD:
        return "Wrong password"
    
    return f"""
    <html>
    <head>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    {STYLE}
    </head>
    <body>
    <div class='container'>
        <h2>📁 File Manager</h2>

        <div class='box'>
            <a href='/'>🏠 Home</a>
            <a href='/browse?path=/'>📂 Open root</a>
            <a href='/'>🚪 Exit</a>
        </div>

        <div class='box'>
            <form action='/browse' method='get'>
                <input name='path' placeholder='Enter path like /Desktop'>
                <button type='submit'>Open</button>
            </form>
        </div>
    </div>
    </body>
    </html>
    """

# 📂 BROWSE
@app.get("/browse", response_class=HTMLResponse)
def browse(req: Request, path: str = "/"):
    user = req.session.get("name")
    if user != ADMIN_USERNAME:
        return RedirectResponse(url="/", status_code=302)
    
    full_path = safe_path(path)
    if not os.path.exists(full_path):
        return "Not found"

    items = os.listdir(full_path)

    html = f"""
    <html>
    <head>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    {STYLE}
    </head>
    <body>
    <div class='container'>
        <h3>📂 {path}</h3>

        <div class='box'>
            <a href='/'>🏠 Home</a>
            <a href='javascript:history.back()'>⬅ Back</a>
            <a href='/'>🚪 Exit</a>
        </div>

        <div class='box'>
    """

    for item in items:
        item_path = os.path.join(path, item)
        full_item = safe_path(item_path)
        item_query = urllib.parse.quote(item_path)

        if os.path.isdir(full_item):
            html += f"""
            <div class='file'>
                📁 <a href='/browse?path={item_query}'>{item}</a>
            </div>
            """
        else:
            html += f"""
            <div class='file'>
                📄 {item}
                <div class='actions'>
                    <a href='/download?path={item_query}'>⬇ Download</a>
                    <a href='/view?path={item_query}'>👁 View</a>
                </div>
            </div>
            """

    html += f"""
        </div>

        <div class='box'>
            <h3>📤 Upload</h3>
            <form action='/upload' method='post' enctype='multipart/form-data'>
                <input type='hidden' name='path' value='{path}'>
                <input type='file' name='file'>
                <button type='submit'>Upload</button>
            </form>
        </div>

    </div>
    </body>
    </html>
    """

    return html

# 👁 VIEW
@app.get("/view", response_class=HTMLResponse)
def view(req: Request, path: str):
    user = req.session.get("name")
    if user != ADMIN_USERNAME:
        return RedirectResponse(url="/", status_code=302)
    
    full_path = safe_path(path)
    if not os.path.exists(full_path):
        return "Not found"
    if os.path.isdir(full_path):
        return "Cannot view a directory"

    with open(full_path, "r", errors="ignore") as f:
        content = f.read(5000)

    return f"""
    <html>
    <head>{STYLE}</head>
    <body>
    <div class='container box'>
        <h3>{path}</h3>
        <pre>{content}</pre>
    </div>
    </body>
    </html>
    """

# ⬇ DOWNLOAD
@app.get("/download")
def download(req: Request, path: str):
    user = req.session.get("name")
    if user != ADMIN_USERNAME:
        return RedirectResponse(url="/", status_code=302)
    
    full_path = safe_path(path)
    if not os.path.exists(full_path):
        return RedirectResponse(url='/', status_code=302)
    return FileResponse(full_path, filename=os.path.basename(full_path))

# 📤 UPLOAD
@app.post("/upload")
async def upload(req: Request, path: str = Form(...), file: UploadFile = File(...)):
    user = req.session.get("name")
    if user != ADMIN_USERNAME:
        return RedirectResponse(url="/", status_code=302)
    
    target = safe_path(path)
    file_path = os.path.join(target, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return RedirectResponse(url=f"/browse?path={path}", status_code=303)        