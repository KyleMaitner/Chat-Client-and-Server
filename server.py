import socket
import threading

# Server configuration
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5000       # Change this if needed

clients = []      # List to track active client sockets
lock = threading.Lock()  # Thread-safe access to clients list

"""
    Relays a message to all connected clients except the sender.
    
    Args:
        message (str): The message to be sent to other clients.
        sender_sock (socket.socket): The socket of the client who sent the message. The message will not be sent to this client.
        
    Outputs:
        None. The message is sent to all other connected clients except the sender.
"""
def broadcast(message, sender_sock):
    """Send the message to all clients except the sender."""
    with lock:
        for client in clients:
            if client != sender_sock:# Exclude the sender from receiving the message
                try:
                    client.sendall(message)# Send the message to the client
                except Exception:  # If sending fails (client might have disconnected)
                    client.close()  # Close the connection
                    clients.remove(client)  # Remove the client from the list

"""
    Handles a single client connection. Receives and broadcasts messages sent by the client.
    
    Args:
        client_sock (socket.socket): The socket object representing the client.
        client_addr (tuple): The address (IP, port) of the client.
        
    Outputs:
        None. This function runs in a separate thread and handles client communication.
"""
def handle_client(client_sock, client_addr):
    print(f"[+] New connection from {client_addr}")
    with lock:  # Ensure thread-safe access to the clients list
        clients.append(client_sock)  # Add the new client to the list

    try:
        while True:
            data = client_sock.recv(1024)  # Receive data from the client
            if not data:  # If the client disconnects or sends no data
                break  # Client disconnected
            broadcast(data, client_sock)  # Broadcast the received message to all clients
    except Exception as e:
        print(f"[!] Error with {client_addr}: {e}")
    finally:
        # After the connection ends, safely remove the client from the list and close the connection
        with lock:
            if client_sock in clients:
                clients.remove(client_sock)
        client_sock.close()
        print(f"[-] Connection closed: {client_addr}")

"""
    Starts the server, listens for incoming connections, and starts a new thread for each connection.
    
    Args:
        None.
        
    Outputs:
        None. This function runs the server and waits for client connections.
"""
def start_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse address to avoid bind issues
    server_sock.bind((HOST, PORT))  # Bind the socket to the specified host and port
    server_sock.listen()  # Start listening for incoming connections
    print(f"[SERVER] Chat server listening on {HOST}:{PORT}")

    try:
        while True:
            client_sock, client_addr = server_sock.accept()  # Accept new client connections
            thread = threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True)  # Create a new thread for each client
            thread.start()  # Start the client handling thread
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    finally:
        server_sock.close()
        with lock:
            for client in clients:
                client.close()  # Close all client connections when the server shuts down

if __name__ == "__main__":
    start_server()
