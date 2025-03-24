import dotenv
from socket_server import SocketIOServer
import threading

def run_socket_server(ready_event):
    # Initialize socket server instance with port 3001
    socket_server = SocketIOServer(port=3001, ready_event=ready_event)
    socket_server.run()

if __name__ == "__main__":
    dotenv.load_dotenv()

    # Create an event to signal when the socket server is ready
    socket_ready = threading.Event()

    # Start Socket.IO server in a separate thread
    socket_thread = threading.Thread(target=run_socket_server, args=(socket_ready,))
    socket_thread.daemon = True  # This ensures the thread will exit when the main program exits
    socket_thread.start()

    # Wait for the socket server to be ready
    print("Waiting for Socket.IO server to start...")
    socket_ready.wait()
    print("Socket.IO server is ready!")

    # Keep the main thread alive
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nShutting down server...")
