function sendCommand(cmd) {
  let password = null;
  if (cmd == "stop_server" || cmd == "shutdown") {
    password = prompt("enter your password:");
  }

  fetch("/run", {
    method: "POST",
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify({ command: cmd, password: password })
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      alert(data.error);
    }
  });
}

function goToTerminal() {
  window.location.href = "/terminal";
}

function filesystem() {
  let password = prompt("enter your password:");
  fetch("/filesystem", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    credentials: 'include',
    body: new URLSearchParams({ password: password })
  })
  .then(res => res.text())
  .then(html => {
    if (html.includes("Wrong password")) {
      alert("Wrong password");
    } else {
      document.open();
      document.write(html);
      document.close();
    }
  });
}

function logout() {
  fetch("/logout", {
    method: "POST",
    credentials: 'include'
  }).then(() => window.location.href = "/");
}

function showSystemStatus() {
  fetch('/system_status', {
    method: 'GET',
    credentials: 'include'
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      alert(data.error);
      return;
    }
    let statusDiv = document.getElementById('system-status');
    statusDiv.innerHTML = `
      <h3>System Status</h3>
      <p>CPU Usage: ${data.cpu_usage}%</p>
      <p>Memory Usage: ${data.memory_usage}% (${data.memory_used_gb} GB / ${data.memory_total_gb} GB)</p>
      <p>CPU Temperature: ${data.cpu_temp_celsius ? data.cpu_temp_celsius + ' °C' : 'N/A'}</p>
      <p>Disk Usage: ${data.disk_usage}% (${data.disk_used_gb} GB / ${data.disk_total_gb} GB)</p>
      <p>Battery: ${data.battery_percent ? data.battery_percent + '%' : 'N/A'}</p>
    `;
    statusDiv.style.display = 'block';
  });
}
