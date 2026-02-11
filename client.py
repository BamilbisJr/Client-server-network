
"""
Chat Client
Connects to the chat server and allows sending/receiving messages.
Uses threading to receive messages while waiting for user input.
Usage: python client.py <host> <port>
Example: python client.py 192.168.1.100 5000
"""

import socket
import threading
import sys

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.nickname = None
   
    def receive_messages(self):
        """Continuously receive messages from the server."""
        print(f"[DEBUG] receive_messages thread started")
        while self.running:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    print("\nDisconnected from server.")
                    self.running = False
                    break
                #Goes from byte to string
                message = data.decode('utf-8')
               
                # Handle nickname request from server
                if message == "NICKNAME_REQUEST":
                    #.strip removes whitespace to read-in
                    nickname = input("Enter your nickname: ").strip()
                    if not nickname:
                        nickname = "Anonymous"
                    self.nickname = nickname
                    #Sends nickname as a byte stream
                    self.client_socket.send(nickname.encode('utf-8'))
                else:
                    # Regular message - print it
                    print(f"\n{message}")
                    print("You: ", end="", flush=True)
                   
            except ConnectionResetError:
                print("\nConnection lost.")
                self.running = False
                break
            except OSError as e:
                if self.running:
                    print(f"OSError in receive: {e}")
                break
            except Exception as e:
                print(f"Error receiving: {e}")
                if self.running:
                    self.running = False
                break

   
    def send_messages(self):
        """Handle user input and send messages to the server."""
       
        # Wait a moment for nickname exchange to complete
        import time
        time.sleep(0.5)
       
        while self.running:
            try:
                message = input("You: ")
                #Handles connection errors
                if not self.running:
                    break
               
                if message.lower() == '/quit':
                    self.client_socket.send(message.encode('utf-8'))
                    self.running = False
                    break
               
                if message:
                    self.client_socket.send(message.encode('utf-8'))
                   
            except EOFError:
                print(f"\nEOFError, exiting")
                self.running = False
                break
            except Exception as e:
                print(f"Error sending: {e}")
                if self.running:
                    self.running = False
                break
    
   
    def connect(self):
        """Connect to the server and start communication."""
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Connected successfully to {self.host}:{self.port}")
           
            print(f"\n{'='*50}")
            print(f"Connected to server at {self.host}:{self.port}")
            print(f"Type '/quit' to exit")
            print(f"{'='*50}\n")
           
            # Start receive thread
            #Thread ends when program stops
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
           
            # Send messages in main thread
            self.send_messages()
           
        except ConnectionRefusedError:
            print(f"Error: Could not connect to server at {self.host}:{self.port}")
            print("Make sure the server is running and the address is correct.")
        except socket.timeout:
            print(f"Error: Connection timed out")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.running = False
            self.client_socket.close()
            print(f"Client socket closed")
            print("Goodbye!")

def print_usage():
    print("Usage: python client.py <host> <port>")
    print("Example: python client.py 192.168.1.100 5000")

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
   
    client = ChatClient(host=host, port=port)
    client.connect()
