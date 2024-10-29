import socket

def udp_client(server_ip='192.168.1.63', server_port=61556):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        # Ask for user input
        user_input = input("Enter message to send (or type 'exit' to quit): ")
        
        # Check if the user wants to exit
        if user_input.lower() == 'exit':
            print("Exiting the client.")
            break
        
        # Encode the message as bytes
        message = user_input.encode()  # Convert to byte string
        sock.sendto(message, (server_ip, server_port))
        print(f"Sent message to {server_ip}:{server_port}: {user_input}")

udp_client()
