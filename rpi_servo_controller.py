#!/usr/bin/env python3
"""
Raspberry Pi Servo Controller via UDP with Smooth Movement
Listens for UDP messages to control 4 servos connected to GPIO pins 12, 13, 18, and 19
Features smooth, gradual movement to prevent abrupt servo jumps
Message format: "angle1,angle2,angle3,angle4"
Example: "90,45, ,180" - moves servo 1 to 90°, servo 2 to 45°, keeps servo 3 current, servo 4 to 180°
"""

import socket
import time
import sys
import re
import pigpio

# UDP configuration
UDP_IP = "0.0.0.0"  # Listen on all interfaces
UDP_PORT = 5005

# Servo configuration
SERVO_PINS = {
    1: 12,  # Servo 1 on GPIO 12
    2: 13,  # Servo 2 on GPIO 13
    3: 18,  # Servo 3 on GPIO 18
    4: 19   # Servo 4 on GPIO 19
}

# Servo parameters (adjust these based on your servo specifications)
SERVO_MIN_PULSE = 500   # Minimum pulse width in microseconds
SERVO_MAX_PULSE = 2500  # Maximum pulse width in microseconds
SERVO_MIN_ANGLE = 0     # Minimum angle in degrees
SERVO_MAX_ANGLE = 180   # Maximum angle in degrees

# Smooth movement parameters
SMOOTH_MOVEMENT = True   # Enable smooth movement by default
STEP_DELAY = 0.02        # Delay between steps in seconds (20ms)
MIN_STEP_SIZE = 1        # Minimum degrees per step

class ServoController:
    def __init__(self):
        """Initialize the servo controller with pigpio and smooth movement capabilities"""
        self.pi = None
        self.current_angles = {1: 0, 2: 0, 3: 0, 4: 0}  # Default to 0° position
        
    def initialize(self):
        """Initialize pigpio connection and setup servo pins"""
        try:
            # Connect to pigpio daemon
            self.pi = pigpio.pi()
            
            if not self.pi.connected:
                raise Exception("Failed to connect to pigpio daemon")
            
            print("✓ Connected to pigpio daemon")
            
            # Initialize all servo pins
            for servo_num, gpio_pin in SERVO_PINS.items():
                # Set servo to 0 degrees starting position
                self.set_servo_angle(servo_num, 0, smooth=False)
                print(f"✓ Servo {servo_num} (GPIO {gpio_pin}) initialized at 0°")
            
            return True
            
        except Exception as e:
            print(f"✗ Error initializing servo controller: {e}")
            return False
    
    def angle_to_pulse_width(self, angle):
        """Convert angle (0-180) to pulse width in microseconds"""
        if angle < SERVO_MIN_ANGLE or angle > SERVO_MAX_ANGLE:
            raise ValueError(f"Angle {angle} is out of range ({SERVO_MIN_ANGLE}-{SERVO_MAX_ANGLE})")
        
        # Linear interpolation between min and max pulse widths
        pulse_width = SERVO_MIN_PULSE + (angle / SERVO_MAX_ANGLE) * (SERVO_MAX_PULSE - SERVO_MIN_PULSE)
        return int(pulse_width)
    
    def set_servo_angle(self, servo_num, angle, smooth=True, step_delay=0.02):
        """
        Set servo to specified angle with optional smooth movement
        
        Args:
            servo_num (int): Servo number (1-4)
            angle (float): Target angle in degrees (0-180)
            smooth (bool): Enable smooth movement (default: True)
            step_delay (float): Delay between steps in seconds (default: 0.02)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if servo_num not in SERVO_PINS:
                raise ValueError(f"Invalid servo number: {servo_num}. Valid servos: {list(SERVO_PINS.keys())}")
            
            # Validate angle range
            if angle < SERVO_MIN_ANGLE or angle > SERVO_MAX_ANGLE:
                raise ValueError(f"Angle {angle} is out of range ({SERVO_MIN_ANGLE}-{SERVO_MAX_ANGLE})")
            
            current_angle = self.current_angles[servo_num]
            
            if smooth and abs(angle - current_angle) > MIN_STEP_SIZE:  # Only smooth if movement > minimum step size
                # Calculate number of steps (1 degree per step for smooth movement)
                steps = int(abs(angle - current_angle))
                step_size = (angle - current_angle) / steps
                
                # Move in gradual steps to prevent abrupt movement
                for i in range(steps):
                    intermediate_angle = current_angle + (i + 1) * step_size
                    pulse_width = self.angle_to_pulse_width(intermediate_angle)
                    gpio_pin = SERVO_PINS[servo_num]
                    self.pi.set_servo_pulsewidth(gpio_pin, pulse_width)
                    time.sleep(step_delay)  # Small delay between steps for smooth motion
            else:
                # Direct movement for small changes (no smoothing needed)
                pulse_width = self.angle_to_pulse_width(angle)
                gpio_pin = SERVO_PINS[servo_num]
                self.pi.set_servo_pulsewidth(gpio_pin, pulse_width)
            
            # Update current angle
            self.current_angles[servo_num] = angle
            
            return True
            
        except Exception as e:
            print(f"✗ Error setting servo {servo_num}: {e}")
            return False
    
    def get_servo_angle(self, servo_num):
        """Get current angle of specified servo"""
        return self.current_angles.get(servo_num, None)
    
    def get_all_angles(self):
        """Get current angles of all servos"""
        return self.current_angles.copy()
    
    def move_servos_synchronized(self, target_angles_by_servo, step_delay=0.02):
        """
        Move multiple servos simultaneously using linear interpolation per step.
        
        Args:
            target_angles_by_servo (dict[int, float]): Mapping of servo_num -> target angle
            step_delay (float): Delay between interpolation steps
        """
        # Determine current and delta for each servo
        deltas = {}
        max_delta = 0.0
        for servo_num, target_angle in target_angles_by_servo.items():
            current_angle = self.current_angles[servo_num]
            delta = target_angle - current_angle
            deltas[servo_num] = (current_angle, target_angle, delta)
            max_delta = max(max_delta, abs(delta))

        # Number of steps: 1 degree per step based on the largest movement
        steps = int(max_delta)
        if steps <= 0:
            # Nothing significant to do; still ensure final set
            for servo_num, (_, target_angle, _) in deltas.items():
                pulse_width = self.angle_to_pulse_width(target_angle)
                gpio_pin = SERVO_PINS[servo_num]
                self.pi.set_servo_pulsewidth(gpio_pin, pulse_width)
                self.current_angles[servo_num] = target_angle
            return True

        # Interpolate all together
        for i in range(1, steps + 1):
            for servo_num, (start_angle, target_angle, delta) in deltas.items():
                intermediate = start_angle + (delta * i / steps)
                pulse_width = self.angle_to_pulse_width(intermediate)
                gpio_pin = SERVO_PINS[servo_num]
                self.pi.set_servo_pulsewidth(gpio_pin, pulse_width)
            time.sleep(step_delay)

        # Ensure final exact target angles recorded
        for servo_num, (_, target_angle, _) in deltas.items():
            self.current_angles[servo_num] = target_angle
        return True
    
    def cleanup(self):
        """Clean up pigpio connection and stop all servos"""
        if self.pi and self.pi.connected:
            # Stop all servos
            for servo_num, gpio_pin in SERVO_PINS.items():
                self.pi.set_servo_pulsewidth(gpio_pin, 0)
                print(f"✓ Servo {servo_num} stopped")
            
            self.pi.stop()
            print("✓ Pigpio connection closed")

class UDPServoServer:
    def __init__(self):
        self.servo_controller = ServoController()
        self.sock = None
        
    def parse_message(self, message):
        """Parse UDP message to extract servo commands"""
        try:
            # Remove extra whitespace
            message = message.strip()
            
            # Expected format: "angle1,angle2,angle3,angle4" or "angle1, ,angle3,angle4" (spaces for current angle)
            # Split by comma
            parts = [part.strip() for part in message.split(',')]
            
            if len(parts) != 4:
                raise ValueError(f"Expected 4 comma-separated values, got {len(parts)}")
            
            servo_commands = []
            
            for i, part in enumerate(parts):
                servo_num = i + 1  # Servo numbers are 1-4
                
                if part == '' or part.isspace():
                    # Keep current angle for this servo
                    current_angle = self.servo_controller.get_servo_angle(servo_num)
                    servo_commands.append((servo_num, current_angle, True))  # True indicates "keep current"
                else:
                    try:
                        angle = float(part)
                        
                        # Validate angle range
                        if angle < SERVO_MIN_ANGLE or angle > SERVO_MAX_ANGLE:
                            raise ValueError(f"Angle {angle} for servo {servo_num} is out of range ({SERVO_MIN_ANGLE}-{SERVO_MAX_ANGLE})")
                        
                        servo_commands.append((servo_num, angle, False))  # False indicates "set new angle"
                        
                    except ValueError as e:
                        raise ValueError(f"Invalid angle '{part}' for servo {servo_num}: {e}")
            
            return servo_commands
            
        except Exception as e:
            raise ValueError(f"Message parsing error: {e}")
    
    def process_commands(self, servo_commands):
        """Process multiple servo movement commands with smooth and synchronized movement"""
        results = []

        # Build targets for servos that should move
        targets = {}
        for servo_num, angle, is_keep_current in servo_commands:
            if is_keep_current:
                gpio_pin = SERVO_PINS[servo_num]
                results.append(f"• Servo {servo_num} (GPIO {gpio_pin}) kept at {angle}°")
            else:
                targets[servo_num] = angle

        # If more than one servo is moving, synchronize movement
        try:
            if len(targets) > 1 and SMOOTH_MOVEMENT:
                self.servo_controller.move_servos_synchronized(targets, step_delay=STEP_DELAY)
                for servo_num, angle in targets.items():
                    gpio_pin = SERVO_PINS[servo_num]
                    results.append(f"✓ Servo {servo_num} (GPIO {gpio_pin}) moved to {angle}° (synchronized)")
            else:
                # Move individually (still smooth if enabled)
                for servo_num, angle in targets.items():
                    success = self.servo_controller.set_servo_angle(
                        servo_num, angle, smooth=SMOOTH_MOVEMENT, step_delay=STEP_DELAY
                    )
                    gpio_pin = SERVO_PINS[servo_num]
                    if success:
                        results.append(f"✓ Servo {servo_num} (GPIO {gpio_pin}) moved to {angle}°")
                    else:
                        results.append(f"✗ Failed to move servo {servo_num} to {angle}°")

        except Exception as e:
            results.append(f"✗ Error during synchronized movement: {e}")

        return results
    
    def start_server(self):
        """Start UDP server to listen for servo commands"""
        print("=" * 60)
        print("RASPBERRY PI SERVO CONTROLLER WITH SMOOTH MOVEMENT")
        print("=" * 60)
        
        # Initialize servo controller
        if not self.servo_controller.initialize():
            print("Failed to initialize servo controller. Exiting.")
            return
        
        try:
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Bind socket to IP and port
            self.sock.bind((UDP_IP, UDP_PORT))
            
            print(f"✓ UDP Server listening on {UDP_IP}:{UDP_PORT}")
            print(f"✓ Ready to receive servo commands")
            print()
            print("Command format: 'angle1,angle2,angle3,angle4'")
            print("Example: '90,45, ,180' - moves servo 1 to 90°, servo 2 to 45°, keeps servo 3 current, servo 4 to 180°")
            print("Use spaces or empty values to keep current servo position")
            print("Valid angles: 0-180 degrees")
            print("Smooth movement: Enabled (gradual movement prevents abrupt jumps)")
            print()
            print("Press Ctrl+C to stop")
            print("-" * 60)
            
            while True:
                # Receive message and sender address
                data, addr = self.sock.recvfrom(1024)
                
                # Decode the message
                message = data.decode('utf-8')
                
                # Get current timestamp
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"[{timestamp}] From {addr[0]}:{addr[1]} - Message: '{message}'")
                
                try:
                    # Parse the message
                    servo_commands = self.parse_message(message)
                    
                    # Process the commands
                    results = self.process_commands(servo_commands)
                    for result in results:
                        print(f"  {result}")
                    
                except ValueError as e:
                    error_msg = f"  ✗ Invalid command: {e}"
                    print(error_msg)
                    
                except Exception as e:
                    error_msg = f"  ✗ Unexpected error: {e}"
                    print(error_msg)
                
                print()  # Add blank line for readability
                
        except KeyboardInterrupt:
            print("\n\nServer stopped by user")
            
        except Exception as e:
            print(f"\n✗ Server error: {e}")
            
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.sock:
            self.sock.close()
            print("✓ UDP socket closed")
        
        self.servo_controller.cleanup()

def show_status():
    """Show current status of all servos"""
    controller = ServoController()
    if controller.initialize():
        print("Current servo positions:")
        for servo_num in SERVO_PINS.keys():
            angle = controller.get_servo_angle(servo_num)
            gpio_pin = SERVO_PINS[servo_num]
            print(f"  Servo {servo_num} (GPIO {gpio_pin}): {angle}°")
        controller.cleanup()
    else:
        print("Failed to initialize servo controller")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            show_status()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Available options: --status")
    else:
        # Start the UDP server
        server = UDPServoServer()
        server.start_server()

if __name__ == "__main__":
    main()
