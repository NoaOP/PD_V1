#!/usr/bin/env python3
"""
MAVLink TCP Server - Simulates a drone/autopilot listening on localhost:5763
This allows DashboardAll.py in local mode to connect without needing a real drone.
"""

import socket
import threading
import time
from pymavlink import mavutil
import sys

class MAVLinkTCPServer:
    def __init__(self, host='127.0.0.1', port=5763):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = True

    def start(self):
        """Start the MAVLink TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"✓ MAVLink Server listening on {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    print(f"✓ Client connected from {client_addr}")
                    threading.Thread(target=self._handle_client, args=(client_socket, client_addr), daemon=True).start()
                except Exception as e:
                    if self.running:
                        print(f"Error accepting connection: {e}")
                    break
        except Exception as e:
            print(f"✗ Error starting MAVLink server: {e}")
            sys.exit(1)

    def _handle_client(self, client_socket, client_addr):
        """Handle a single client connection"""
        print(f"  → Handling client {client_addr}")
        try:
            # Create a MAVLink heartbeat message
            from pymavlink.dialects.v10 import ardupilotmega as mavlink_module

            msg = mavlink_module.MAVLink_heartbeat_message(
                type=1,  # MAV_TYPE_FIXED_WING
                autopilot=12,  # MAV_AUTOPILOT_PX4
                base_mode=81,
                custom_mode=0,
                system_status=3,  # MAV_STATE_ACTIVE
                mavlink_version=3
            )

            # Send heartbeat periodically
            while self.running:
                try:
                    # Send heartbeat every second
                    packed = msg.pack(mavlink_module.MAVLink(0, 1))
                    client_socket.sendall(packed)
                    time.sleep(1.0)
                except Exception as e:
                    print(f"  ✗ Error sending to {client_addr}: {e}")
                    break
        except Exception as e:
            print(f"  ✗ Handler error for {client_addr}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            print(f"  ✗ Client {client_addr} disconnected")

    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("✓ MAVLink Server stopped")

if __name__ == "__main__":
    server = MAVLinkTCPServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()

