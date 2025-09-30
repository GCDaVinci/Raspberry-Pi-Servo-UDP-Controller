#!/usr/bin/env python3
"""
Servo UDP client for Raspberry Pi Servo Controller
Sends servo commands to the RPI servo controller
"""

import socket
import time
import sys

# UDP configuration
UDP_IP = "192.168.1.5"  # Raspberry Pi IP address
UDP_PORT = 5005

def send_servo_command(servo_angles, ip=UDP_IP, port=UDP_PORT):
    """
    Send servo commands to the Raspberry Pi
    
    Args:
        servo_angles (list): List of 4 values [angle1, angle2, angle3, angle4]
                            Use None, '', or ' ' to keep current position
        ip (str): Target IP address
        port (int): Target port number
    
    Returns:
        bool: True if command sent successfully, False otherwise
    """
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Format the command - convert to comma-separated string
        command_parts = []
        for angle in servo_angles:
            if angle is None or angle == '' or angle == ' ':
                command_parts.append(' ')
            else:
                command_parts.append(str(angle))
        
        command = ','.join(command_parts)
        
        # Send command
        sock.sendto(command.encode('utf-8'), (ip, port))
        print(f"Sent command: '{command}' to {ip}:{port}")
        
        # Close socket
        sock.close()
        return True
        
    except Exception as e:
        print(f"Error sending command: {e}")
        return False


def interactive_mode():
    """Interactive mode for sending custom servo commands"""
    print("Servo Controller Test Client - Interactive Mode")
    print("Type 'quit' or 'exit' to stop")
    print(f"Target: {UDP_IP}:{UDP_PORT}")
    print("Command format: 'angle1,angle2,angle3,angle4'")
    print("Example: '90,45, ,180' - moves servo 1 to 90°, servo 2 to 45°, keeps servo 3 current, servo 4 to 180°")
    print("Use spaces or empty values to keep current servo position")
    print("Valid angles: 0-180 degrees")
    print("-" * 40)
    
    while True:
        try:
            command = input("Enter servo command: ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if command:
                # Parse the command - split by comma
                parts = [part.strip() for part in command.split(',')]
                
                if len(parts) == 4:
                    # Convert to proper format
                    servo_angles = []
                    for part in parts:
                        if part == '' or part.isspace():
                            servo_angles.append(' ')
                        else:
                            try:
                                angle = float(part)
                                if 0 <= angle <= 180:
                                    servo_angles.append(angle)
                                else:
                                    print("Invalid angle range. Angles must be 0-180 degrees.")
                                    break
                            except ValueError:
                                print(f"Invalid angle '{part}'. Must be a number or space.")
                                break
                    else:
                        # All angles were valid
                        send_servo_command(servo_angles)
                else:
                    print("Invalid format. Use: angle1,angle2,angle3,angle4")
            else:
                print("Please enter a command")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_mode()
        else:
            # Send single command from command line
            command = " ".join(sys.argv[1:])
            # Handle the case where commas might be separated by spaces in argv
            command = command.replace(' ,', ',').replace(', ', ',').replace(' , ', ',')
            parts = [part.strip() for part in command.split(',')]
            
            if len(parts) == 4:
                # Convert to proper format
                servo_angles = []
                for part in parts:
                    if part == '' or part.isspace():
                        servo_angles.append(' ')
                    else:
                        try:
                            angle = float(part)
                            if 0 <= angle <= 180:
                                servo_angles.append(angle)
                            else:
                                print("Invalid angle range. Angles must be 0-180 degrees.")
                                break
                        except ValueError:
                            print(f"Invalid angle '{part}'. Must be a number or space.")
                            break
                else:
                    # All angles were valid
                    send_servo_command(servo_angles)
            else:
                print("Invalid format. Use: angle1,angle2,angle3,angle4")
    else:
        # Default to interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
