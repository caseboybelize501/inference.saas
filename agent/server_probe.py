import socket

def probe_servers(ports=[8000, 11434, 5000, 7860, 1234]):
    servers = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) == 0:
                servers.append(port)
    return servers