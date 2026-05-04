from fastapi import FastAPI, WebSocket, Request, Form
from fastapi.responses import FileResponse, RedirectResponse
import asyncio
import os
import pty
import subprocess
import signal

app = FastAPI()

@app.get("/")
def home():
    return FileResponse("index.html")

@app.post("/")
async def login(username: str = Form(...), password: str = Form(...)):

    global main_password
    if username == "admin" and password == "akshith@123":
        main_password = password
        return FileResponse("home.html")
    else:
        return RedirectResponse(url="/", status_code=303)

@app.post("/run")
async def run_command(req: Request):
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
        if cmd_password != "akshith@123":
            return {"error":"wrong password"}
        os.kill(os.getpid(), signal.SIGTERM)

    elif cmd == "shutdown":
        if cmd_password != "akshith@123":
            return {"error":"wrong password"}
        else:
            os.system("shutdown now")
    return {"status": "ok", "command": cmd}

@app.get("/terminal")
def terminal_page():
    if main_password == "akshith@123":
        return FileResponse("terminal.html")
    else:
        return {"error": "you haven't loged in"}

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