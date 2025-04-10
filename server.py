import socket
import threading

# Server configuration
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5000       # Change this if needed

clients = []      # List to track active client sockets
lock = threading.Lock()  # Thread-safe access to clients list

def broadcast(message, sender_sock):
    """Send the message to all clients except the sender."""
    with lock:
        for client in clients:
            if client != sender_sock:
                try:
                    client.sendall(message)
                except Exception:
                    client.close()
                    clients.remove(client)

def handle_client(client_sock, client_addr):
    print(f"[+] New connection from {client_addr}")
    with lock:
        clients.append(client_sock)

    try:
        while True:
            data = client_sock.recv(1024)
            if not data:
                break  # Client disconnected
            broadcast(data, client_sock)
    except Exception as e:
        print(f"[!] Error with {client_addr}: {e}")
    finally:
        with lock:
            if client_sock in clients:
                clients.remove(client_sock)
        client_sock.close()
        print(f"[-] Connection closed: {client_addr}")

def start_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen()
    print(f"[SERVER] Chat server listening on {HOST}:{PORT}")

    try:
        while True:
            client_sock, client_addr = server_sock.accept()
            thread = threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    finally:
        server_sock.close()
        with lock:
            for client in clients:
                client.close()

if __name__ == "__main__":
    start_server()
