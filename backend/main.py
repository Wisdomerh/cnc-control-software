from flask import Flask, jsonify, request
from flask_socketio import SocketIO
import serial
import time
import serial.tools.list_ports
import threading  # Added for running GRBL response reading in a separate thread

app = Flask(__name__)
socketio = SocketIO(app)

# Check available COM ports
def get_available_port():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    return ports[0] if ports else None  # Return the first available port, or None if no ports are found

# Attempt to establish a serial connection
serial_port = get_available_port()
if serial_port:
    try:
        ser = serial.Serial(serial_port, 115200, timeout=1)  # Set timeout to prevent freezing
        print(f"Connected to {serial_port}")
    except serial.SerialException as e:
        print(f"Serial connection failed: {e}")
        ser = None
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

# Read GRBL responses in real-time
def read_grbl_responses():
    while True:
        if ser:
            try:
                response = ser.readline().decode().strip()
                if response:
                    socketio.emit('grbl_response', response)
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break
        else:
            time.sleep(1)  # Prevents excessive CPU usage when no device is connected

# API endpoint to send G-code
@app.route('/send_gcode', methods=['POST'])
def send_gcode_endpoint():
    data = request.json
    command = data.get('command')
    if not command:
        return jsonify({"error": "No command provided"}), 400
    response = send_gcode(command)
    return jsonify({"response": response})

# API endpoint to home the machine
@app.route('/home', methods=['POST'])
def home_machine():
    response = send_gcode('$H')
    return jsonify({"response": response})

# API endpoint to jog the machine
@app.route('/jog', methods=['POST'])
def jog_machine():
    data = request.json
    x = data.get('x', 0)
    y = data.get('y', 0)
    z = data.get('z', 0)
    feed_rate = data.get('feed_rate', 1000)
    command = f"$J=G91 X{x} Y{y} Z{z} F{feed_rate}"
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
    # Start a thread to read GRBL responses
    threading.Thread(target=read_grbl_responses, daemon=True).start()
    socketio.run(app, port=5000)