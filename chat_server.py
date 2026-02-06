
"""
Multi-Client Chat Server
Handles multiple clients simultaneously and broadcasts messages to all connected clients.
To use (must be in terminal): python chat_server.py <host> <port> (e.g python chat_server.py 0.0.0.0 5000)
"""

import socket
import threading
import sys

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  # {socket: nickname}
        self.lock = threading.Lock()
        print(f"[DEBUG] Server object created with host={host}, port={port}")
   
    def broadcast(self, message, sender_socket=None):
        """Send a message to all connected clients except the sender."""
        print(f"[DEBUG] Broadcasting message: {message}")
        with self.lock:
            client_count = len(self.clients)
            print(f"[DEBUG] Number of connected clients: {client_count}")
            for client_socket in list(self.clients.keys()):
                if client_socket != sender_socket:
                    try:
                        client_socket.send(message.encode('utf-8'))
                        print(f"[DEBUG] Sent to {self.clients[client_socket]}")
                    except Exception as e:
                        print(f"[DEBUG] Failed to send to client: {e}")
                        self.remove_client(client_socket)
   
    def remove_client(self, client_socket):
        """Remove a client from the server."""
        print(f"[DEBUG] Attempting to remove client")
        with self.lock:
            if client_socket in self.clients:
                nickname = self.clients[client_socket]
                del self.clients[client_socket]
                client_socket.close()
                print(f"[DEBUG] Removed client: {nickname}")
                return nickname
        return None
   
    def handle_client(self, client_socket, client_address):
        """Handle messages from a single client."""
        print(f"[DEBUG] handle_client started for {client_address}")
        try:
            # Get client nickname
            client_socket.send("NICKNAME_REQUEST".encode('utf-8'))
            print(f"[DEBUG] Sent nickname request to {client_address}")
           
            nickname = client_socket.recv(1024).decode('utf-8').strip()
            print(f"[DEBUG] Received nickname: '{nickname}' from {client_address}")
           
            if not nickname:
                nickname = f"User_{client_address[1]}"
                print(f"[DEBUG] Empty nickname, assigned: {nickname}")
           
            with self.lock:
                self.clients[client_socket] = nickname
                print(f"[DEBUG] Added {nickname} to clients dict. Total clients: {len(self.clients)}")
           
            welcome_msg = f"Welcome {nickname}! You are now connected. Type messages to chat."
            client_socket.send(welcome_msg.encode('utf-8'))
            print(f"[DEBUG] Sent welcome message to {nickname}")
           
            join_msg = f"*** {nickname} has joined the chat ***"
            print(join_msg)
            self.broadcast(join_msg, client_socket)
           
            # Handle messages
            while True:
                print(f"[DEBUG] Waiting for message from {nickname}...")
                data = client_socket.recv(1024)
               
                if not data:
                    print(f"[DEBUG] No data received from {nickname}, client disconnected")
                    break
               
                message = data.decode('utf-8').strip()
                print(f"[DEBUG] Received from {nickname}: '{message}'")
               
                if message.lower() == '/quit':
                    print(f"[DEBUG] {nickname} requested quit")
                    break
               
                formatted_msg = f"[{nickname}] {message}"
                print(formatted_msg)
                self.broadcast(formatted_msg, client_socket)
               
        except ConnectionResetError:
            print(f"[DEBUG] Connection reset by client {client_address}")
        except Exception as e:
            print(f"[DEBUG] Error handling client {client_address}: {e}")
        finally:
            nickname = self.remove_client(client_socket)
            if nickname:
                leave_msg = f"*** {nickname} has left the chat ***"
                print(leave_msg)
                self.broadcast(leave_msg)
   
    def start(self):
        """Start the chat server."""
        try:
            print(f"[DEBUG] Attempting to bind to {self.host}:{self.port}")
            self.server_socket.bind((self.host, self.port))
            print(f"[DEBUG] Bind successful")
           
            self.server_socket.listen(10)
            print(f"[DEBUG] Listening with backlog of 10")
           
            print(f"\n{'='*50}")
            print(f"Chat server started on {self.host}:{self.port}")
            print(f"Waiting for clients to connect...")
            print(f"{'='*50}\n")
           
            while True:
                print(f"[DEBUG] Waiting for new connection...")
                client_socket, client_address = self.server_socket.accept()
                print(f"[DEBUG] Accepted connection from {client_address}")
                print(f"New connection from {client_address}")
               
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                thread.start()
                print(f"[DEBUG] Started thread for {client_address}, thread ID: {thread.ident}")
               
        except KeyboardInterrupt:
            print("\n[DEBUG] KeyboardInterrupt received")
            print("Server shutting down...")
        except OSError as e:
            print(f"[DEBUG] OSError: {e}")
            print(f"Error: {e}")
        finally:
            print(f"[DEBUG] Cleaning up...")
            with self.lock:
                for client_socket in list(self.clients.keys()):
                    client_socket.close()
            self.server_socket.close()
            print(f"[DEBUG] Server socket closed")

def print_usage():
    print("Usage: python chat_server.py <host> <port>")
    print("Example: python chat_server.py 192.168.1.100 5000")
    print("         python chat_server.py 0.0.0.0 5000  (listen on all interfaces)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Error: Host and port are required!")
        print_usage()
        sys.exit(1)
   
    host = sys.argv[1]
    try:
        port = int(sys.argv[2])
    except ValueError:
        print(f"Error: Port must be a number, got '{sys.argv[2]}'")
        print_usage()
        sys.exit(1)
   
    print(f"[DEBUG] Starting server with host={host}, port={port}")
    server = ChatServer(host=host, port=port)
    server.start()
