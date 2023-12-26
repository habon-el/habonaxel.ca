import socket

def scan_target(target_ip, start_port, end_port):
    print(f"Scanning target: {target_ip}")
    
    for port in range(start_port, end_port + 1):
        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)  # Set a timeout for the connection attempt

        # Attempt to connect to the target's IP address and port
        result = sock.connect_ex((target_ip, port))

        # Check if the connection attempt was successful (result == 0)
        if result == 0:
            print(f"Port {port} is open")
        else:
            print(f"Port {port} is closed")

        # Close the socket
        sock.close()

if __name__ == "__main__":
    # Replace these values with your target's IP address and the range of ports to scan
    target_ip = "127.0.0.1"
    start_port = 1
    end_port = 1024

    scan_target(target_ip, start_port, end_port)
