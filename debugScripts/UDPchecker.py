import socket

def udp_server(host='0.0.0.0', port=61557, buffer_size=1024):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"Listening for UDP packets on {host}:{port}...")
    
    while True:
        data, addr = sock.recvfrom(buffer_size)
        print(f"Received message from {addr}: {data}")

udp_server()
