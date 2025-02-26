from flask import Flask, jsonify, request
from flask_socketio import SocketIO
import serial
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app)

# Serial connection to GRBL
ser = serial.Serial('COM3', 115200)  # Update COM port and baud rate as needed

# GRBL initialization
def initialize_grbl():
    ser.write(b"\r\n\r\n")
    time.sleep(2)
    ser.flushInput()

# Send G-code to GRBL
def send_gcode(command):
    try:
        ser.write((command + '\n').encode())
        response = ser.readline().decode().strip()
        if "error" in response.lower():
            raise ValueError(f"GRBL error: {response}")
        return response
    except Exception as e:
        return str(e)

# Read GRBL responses in real-time
def read_grbl_responses():
    while True:
        response = ser.readline().decode().strip()
        if response:
            socketio.emit('grbl_response', response)

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