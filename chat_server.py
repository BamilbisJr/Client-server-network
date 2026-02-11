"""
Multi-Client Chat Server
Handles multiple clients simultaneously and broadcasts messages to all connected clients.
Usage: python chat_server.py <host> <port>
Example: python chat_server.py 192.168.1.100 5000
"""

import socket
import threading
import sys

class ChatServer:
    """Constructor (sets host, port, TCP & IP, reuse options, default clients, sets lock)"""
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  
        self.lock = threading.Lock()
        print(f"Server object created with host={host}, port={port}")
   
    """Send a message to all connected clients except the sender."""
    def broadcast(self, message, sender_socket=None):
        with self.lock:
            client_count = len(self.clients)
            print(f"Number of connected clients: {client_count}")
            for client_socket in list(self.clients.keys()):
                if client_socket != sender_socket:
                    try:
                        #Sockets only send bytes, not strings
                        client_socket.send(message.encode('utf-8'))
                        print(f"Sent to {self.clients[client_socket]}")
                    except Exception as e:
                        print(f"Failed to send to client: {e}")
                        self.remove_client(client_socket)
   
    def remove_client(self, client_socket):
        """Remove a client from the server."""
        with self.lock:
            if client_socket in self.clients:
                nickname = self.clients[client_socket]
                del self.clients[client_socket]
                client_socket.close()
                print(f"Removed client: {nickname}")
                return nickname
        return None
   
    def handle_client(self, client_socket, client_address):
        """Handle messages from a single client."""
        try:
            #Get client nickname
            client_socket.send("NICKNAME_REQUEST".encode('utf-8'))
            #Reads 1024 bytes (strip removes whitespace)
            nickname = client_socket.recv(1024).decode('utf-8').strip()
            print(f"Received nickname: '{nickname}' from {client_address}")
           
            if not nickname:
                nickname = f"User_{client_address[1]}"
           
            with self.lock:
                self.clients[client_socket] = nickname
                print(f"Added {nickname} to clients dict. Total clients: {len(self.clients)}")
           
            welcome_msg = f"Welcome {nickname}! You are now connected. Type messages to chat."
            client_socket.send(welcome_msg.encode('utf-8'))
           
            join_msg = f"*** {nickname} has joined the chat ***"
            print(join_msg)
            #Send to all except new client
            self.broadcast(join_msg, client_socket)
           
            # Handle messages
            while True:
                print(f"Waiting for message from {nickname}...")
                data = client_socket.recv(1024)
                #Client disconnects
                if not data:
                    print(f"No data received from {nickname}, client disconnected")
                    break
               
                message = data.decode('utf-8').strip()
               
                if message.lower() == '/quit':
                    break
               
                formatted_msg = f"[{nickname}] {message}"
                print(formatted_msg)
                self.broadcast(formatted_msg, client_socket)
               
        except ConnectionResetError:
            print(f"Connection reset by client {client_address}")
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            nickname = self.remove_client(client_socket)
            if nickname:
                leave_msg = f"*** {nickname} has left the chat ***"
                print(leave_msg)
                self.broadcast(leave_msg)
   
    def start(self):
        """Start the chat server."""
        try:
            self.server_socket.bind((self.host, self.port))
            print(f"Bind successful")
           
            #Listens for connection attempts (up to 10 in queue)
            self.server_socket.listen(10)
           
            print(f"\n{'='*50}")
            print(f"Chat server started on {self.host}:{self.port}")
            print(f"Waiting for clients to connect...")
            print(f"{'='*50}\n")
           
            while True:
                #Waits for client to connect and stores their info
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address}")
               
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    #Thread ends when program stops
                    daemon=True
                )
                thread.start()
               
        #Allows ending with Ctrl+C
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received")
            print("Server shutting down...")
        except OSError as e:
            print(f"OSError: {e}")
            print(f"Error: {e}")
        finally:
            with self.lock:
                for client_socket in list(self.clients.keys()):
                    client_socket.close()
            self.server_socket.close()
            print(f"Server socket closed")

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