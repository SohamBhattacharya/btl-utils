#!/usr/bin/env python3

import socket

ESP32_IP = "192.168.0.184"  # Replace with your ESP32 IP
ESP32_PORT = 1234

def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)  # Add timeout
        try:
            s.connect((ESP32_IP, ESP32_PORT))
            s.sendall(command.encode())
            response = s.recv(1024)
            print("Received from ESP32:", response.decode())
        except socket.timeout:
            print("Timed out waiting for response.")
        except Exception as e:
            print("Socket error:", e)

# Example usage
send_command("SWITCH")