#!/usr/bin/env python3
"""TCP Proxy: transparently forwards all traffic from :25774 to backend.
Routs theme paths to galaxy-proxy, everything else (incl WebSocket) to komari."""
import socket
import threading
import sys

LISTEN_PORT = 25774
TARGET_HOST = "127.0.0.1"

# Route table: path prefix -> target port
ROUTES = {
    "/themes/": 25775,    # galaxy-proxy serves theme files
    "/": 25775,           # galaxy-proxy serves index.html
    "/instance/": 25775,  # galaxy-proxy serves instance pages
}

def get_target_port(data):
    """Read the HTTP path from raw request bytes and return target port."""
    try:
        first_line = data.split(b"\r\n")[0].decode("utf-8", errors="replace")
        parts = first_line.split(" ")
        if len(parts) >= 2:
            path = parts[1]
            for prefix, port in ROUTES.items():
                if path == prefix.rstrip("/") or path.startswith(prefix):
                    return port
    except:
        pass
    return 25776  # default: komari

def pipe(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        try:
            dst.close()
        except:
            pass

def handle_client(client_sock):
    try:
        client_sock.settimeout(30)
        data = client_sock.recv(65536)
        if not data:
            return
        target_port = get_target_port(data)
        backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend.settimeout(30)
        backend.connect((TARGET_HOST, target_port))
        backend.sendall(data)
        t1 = threading.Thread(target=pipe, args=(client_sock, backend), daemon=True)
        t2 = threading.Thread(target=pipe, args=(backend, client_sock), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        try:
            client_sock.close()
        except:
            pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", LISTEN_PORT))
    server.listen(100)
    print(f"TCP Proxy listening on :{LISTEN_PORT}")
    print(f"  /themes/ + / + /instance/ -> galaxy-proxy:25775")
    print(f"  everything else           -> komari:25776")
    while True:
        client, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(client,), daemon=True)
        t.start()

if __name__ == "__main__":
    main()
