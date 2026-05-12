const term = new Terminal({
  convertEol: true,
  scrollback: 1000,
  cursorBlink: true
});

term.open(document.getElementById("terminal"));

// 🔥 Perfect WebSocket (works everywhere)
const protocol = location.protocol === "https:" ? "wss" : "ws";
const ws = new WebSocket(`${protocol}://${location.host}/ws`);

ws.onopen = () => {
  console.log("WS CONNECTED");
  term.write("\r\n🟢 Connected to terminal\r\n");
};

ws.onmessage = (event) => {
  term.write(event.data);
};

ws.onerror = (err) => {
  console.log("WS ERROR:", err);
  term.write("\r\n🔴 WebSocket error\r\n");
};

ws.onclose = () => {
  console.log("WS CLOSED");
  term.write("\r\n👋 Session ended. Returning home...\r\n");

  setTimeout(() => {
    window.location.href = "/";
  }, 1500);
};

term.onData(data => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(data);
  }
});
