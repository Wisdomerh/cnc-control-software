from flask import Flask, jsonify
from flask_socketio import SocketIO
import serial
import time
import serial.tools.list_ports

app = Flask(__name__)
socketio = SocketIO(app)

# Check available COM ports
def get_available_port():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    return ports[0] if ports else None  # Return the first available port, or None if no ports are found

# Attempt to establish a serial connection
serial_port = get_available_port()
if serial_port:
    ser = serial.Serial(serial_port, 115200, timeout=1)  # Set timeout to prevent freezing
    print(f"Connected to {serial_port}")
else:
    ser = None
    print("No serial devices found. Running without GRBL connection.")

# GRBL initialization
def initialize_grbl():
    if ser:
        ser.write(b"\r\n\r\n")
        time.sleep(2)
        ser.flushInput()
    else:
        print("GRBL not initialized. No device connected.")

# Send G-code to GRBL
def send_gcode(command):
    if ser:
        ser.write((command + '\n').encode())
        response = ser.readline().decode().strip()
        return response
    return "No device connected"

# API endpoint to send G-code
@app.route('/send_gcode/<command>', methods=['GET'])
def send_gcode_endpoint(command):
    response = send_gcode(command)
    return jsonify({"response": response})

# WebSocket for real-time communication
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    initialize_grbl()
    socketio.run(app, port=5000)
