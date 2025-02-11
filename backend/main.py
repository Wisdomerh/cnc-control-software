from flask import Flask, jsonify
from flask_socketio import SocketIO
import serial
import time

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
    ser.write((command + '\n').encode())
    response = ser.readline().decode().strip()
    return response

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