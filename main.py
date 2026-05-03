from fastapi import FastAPI, WebSocket, Request, Form
from fastapi.responses import FileResponse, RedirectResponse
import asyncio
import os
import pty

app = FastAPI()

# 🏠 Home page
@app.get("/")
def home():
    return FileResponse("index.html")

@app.post("/")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "1234":
        return FileResponse("home.html")
    else:
        return RedirectResponse(url="/", status_code=303)

@app.post("/run")
async def run_command(req: Request):
    data = await req.json()
    cmd = data.get("command")

    if cmd == "vsc":
        os.system("code &")
    if cmd == "firefox":
        os.system("firefox &")

    return {"status": "ok", "command": cmd}

# 🖥 Terminal page
@app.get("/terminal")
def terminal_page():
    return FileResponse("terminal.html")


# 🔌 WebSocket terminal
@app.websocket("/ws")
async def terminal(ws: WebSocket):
    await ws.accept()

    pid, fd = pty.fork()

    if pid == 0:
        # 🔥 Proper shell (IMPORTANT)
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

                    # 🚪 exit command
                    if msg.strip() == "exit":
                        await ws.send_text("\r\n👋 Closing terminal...\r\n")
                        await ws.close()
                        break

                    os.write(fd, msg.encode())
                except:
                    break

        await asyncio.gather(read_shell(), write_shell())