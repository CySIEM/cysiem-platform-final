import platform
import socket
import uuid
import os
import getpass


def _detect_ip_address():
    """
    socket.gethostbyname(socket.gethostname()) resolves to 127.0.0.1 on a
    lot of real machines (containers, multi-NIC hosts, /etc/hosts mapping
    the hostname to loopback) - confirmed during testing, not a hypothetical.
    Opening a UDP "connection" to a public address never sends a packet
    (UDP is connectionless) but makes the OS pick the real outbound
    interface, which getsockname() then reports. This is the standard
    trick for this and is far more reliable than the hostname lookup.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(2)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def _detect_current_user():
    try:
        return os.getlogin()
    except Exception:
        pass
    try:
        # Checks LOGNAME/USER/LNAME/USERNAME env vars, then falls back to
        # the password database entry for the real uid - works even
        # without a controlling terminal (services, containers), unlike
        # os.getlogin().
        return getpass.getuser()
    except Exception:
        return "unknown"


def get_sys_info():
    """
    Real system info, no hardcoded/placeholder values.
    Called on registration AND on every heartbeat, so Agent Details in the
    dashboard reflects the current machine state, not just a one-time
    snapshot from install.
    """
    ip_address = _detect_ip_address()
    current_user = _detect_current_user()

    return {
        "hostname": socket.gethostname(),
        "ip_address": ip_address,
        "os_name": platform.system(),
        "os_version": platform.release(),
        "architecture": platform.machine(),
        "mac_address": ':'.join(
            ['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8 * 6, 8)][::-1]
        ),
        "current_user": current_user,
    }
