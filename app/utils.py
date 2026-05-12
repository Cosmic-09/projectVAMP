"""
Utility functions for the application
"""
import os
import psutil


def get_system_status():
    """Get current system status including CPU, memory, disk, and battery info"""
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_used = memory.used / (1024**3)  # GB
    memory_total = memory.total / (1024**3)  # GB
    
    # CPU temperature (Linux specific)
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp_raw = int(f.read().strip())
            cpu_temp = temp_raw / 1000.0  # Convert from millidegrees to degrees
    except:
        cpu_temp = None
    
    # Disk usage
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    disk_used = disk.used / (1024**3)  # GB
    disk_total = disk.total / (1024**3)  # GB
    
    # Battery (if laptop)
    try:
        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else None
    except:
        battery_percent = None
    
    return {
        "cpu_usage": cpu_percent,
        "memory_usage": memory_percent,
        "memory_used_gb": round(memory_used, 2),
        "memory_total_gb": round(memory_total, 2),
        "cpu_temp_celsius": cpu_temp,
        "disk_usage": disk_percent,
        "disk_used_gb": round(disk_used, 2),
        "disk_total_gb": round(disk_total, 2),
        "battery_percent": battery_percent
    }


def safe_path(path: str, root_dir: str):
    """
    Validate and normalize file path to prevent directory traversal attacks
    
    Args:
        path: The requested path
        root_dir: The root directory to restrict access to
        
    Returns:
        The validated absolute path
        
    Raises:
        Exception: If path tries to escape root directory
    """
    if path is None:
        path = ""
    path = path.strip()
    if path in ("", "/"):
        normalized = ""
    else:
        normalized = path.lstrip("/")

    full_path = os.path.abspath(os.path.join(root_dir, normalized))
    if not full_path.startswith(root_dir):
        raise Exception("Access denied")
    return full_path


# HTML Template for file manager styling
FILESYSTEM_STYLE = """
<link rel="stylesheet" href="/static/css/filesystem.css">
"""
