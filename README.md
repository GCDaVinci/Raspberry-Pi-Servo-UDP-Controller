# RPi Servo UDP Controller

A UDP-based servo control system for Raspberry Pi that allows remote control of 4 servos within a LAN. Consists of two Python scripts: a client script and a servo controller script. The client script runs on a PC and sends user-input UDP messages containing the desired angles of each motor. The servo controller script runs on the Raspberry Pi, listens for and parses the UDP messages, and sets the motors to the received angles.

This a robotics learning project for me. This control system allows me to control/test/move a four-jointed robot arm. It also provides a basic control layer while I work out the inverse kinimatics to create a motion planning layer.

## Hardware Setup

### Servo RPI pinout
- **Servo 1**: GPIO 12
- **Servo 2**: GPIO 13
- **Servo 3**: GPIO 18
- **Servo 4**: GPIO 19

## Installation

### On Raspberry Pi

1. **Install pigpio and dependencies:**
   ```bash
   sudo apt update
   sudo apt install pigpio python3-pigpio
   ```

2. **Enable and start pigpio daemon:**
   ```bash
   sudo systemctl enable pigpiod
   sudo systemctl start pigpiod
   ```

3. **Install Python requirements:**
   ```bash
   pip install -r requirements_rpi.txt
   ```

## Usage

### Start the Servo Controller (Raspberry Pi)

```bash
# Start the UDP server
python rpi_servo_controller.py

# Show current servo positions
python rpi_servo_controller.py --status
```

### Send Commands (Client Computer)

```bash
# Interactive mode
python servo_upd_client.py

# Single command
python servo_upd_client.py 90,45, ,180
```

## Command Format

### Message Structure
```
angle1,angle2,angle3,angle4
```

### Examples
- `90,90,90,90` - Move all servos to 90 degrees (center)
- `45, ,135, ` - Move servo 1 to 45°, keep servo 2 current, move servo 3 to 135°, keep servo 4 current
- `0,45,90,135` - Move servos to 0°, 45°, 90°, and 135° respectively
- ` , , , ` - Keep all servos at their current positions
- `180,0,180,0` - Move servos to extreme positions (180°, 0°, 180°, 0°)

### Parameters
- **Position 1**: Servo 1 angle (GPIO 12) - 0-180 degrees or space to keep current
- **Position 2**: Servo 2 angle (GPIO 13) - 0-180 degrees or space to keep current  
- **Position 3**: Servo 3 angle (GPIO 18) - 0-180 degrees or space to keep current
- **Position 4**: Servo 4 angle (GPIO 19) - 0-180 degrees or space to keep current
- **Spaces**: Use spaces or empty values to keep the servo at its current position

## Configuration

### Network Settings
- **Server IP**: `0.0.0.0` (listens on all interfaces)
- **Port**: `5005`
- **Client IP**: Update `UDP_IP` in `servo_upd_client.py` to your Raspberry Pi's IP

### Servo Settings
You can modify servo parameters in `rpi_servo_controller.py`:

```python
SERVO_MIN_PULSE = 500   # Minimum pulse width in microseconds
SERVO_MAX_PULSE = 2500  # Maximum pulse width in microseconds
SERVO_MIN_ANGLE = 0     # Minimum angle in degrees
SERVO_MAX_ANGLE = 180   # Maximum angle in degrees
```

## Example Output

### Server (Raspberry Pi)
```
============================================================
RASPBERRY PI SERVO CONTROLLER
============================================================
✓ Connected to pigpio daemon
✓ Servo 1 (GPIO 12) initialized at 90°
✓ Servo 2 (GPIO 13) initialized at 90°
✓ Servo 3 (GPIO 18) initialized at 90°
✓ Servo 4 (GPIO 19) initialized at 90°
✓ UDP Server listening on 0.0.0.0:5005
✓ Ready to receive servo commands

Command format: 'angle1,angle2,angle3,angle4'
Example: '90,45, ,180' - moves servo 1 to 90°, servo 2 to 45°, keeps servo 3 current, servo 4 to 180°
Use spaces or empty values to keep current servo position
Valid angles: 0-180 degrees

Press Ctrl+C to stop
------------------------------------------------------------
[2024-01-15 14:30:25] From 192.168.1.100:54321 - Message: '90,45, ,180'
  ✓ Servo 1 (GPIO 12) moved to 90°
  ✓ Servo 2 (GPIO 13) moved to 45°
  • Servo 3 (GPIO 18) kept at 90°
  ✓ Servo 4 (GPIO 19) moved to 180°
```

### Client (Test Computer)
```
Servo Controller Test Client - Interactive Mode
Type 'quit' or 'exit' to stop
Target: 192.168.1.2:5005
Command format: 'angle1,angle2,angle3,angle4'
Example: '90,45, ,180' - moves servo 1 to 90°, servo 2 to 45°, keeps servo 3 current, servo 4 to 180°
Use spaces or empty values to keep current servo position
Valid angles: 0-180 degrees
----------------------------------------
Enter servo command: 45, ,135, 
Sent command: '45, ,135, ' to 192.168.1.2:5005
```

## Troubleshooting

### Common Issues

1. **"Failed to connect to pigpio daemon"**
   - Ensure pigpio daemon is running: `sudo systemctl status pigpiod`
   - Start daemon: `sudo systemctl start pigpiod`

2. **Servos not responding**
   - Check power connections
   - Verify GPIO pin connections
   - Check servo specifications and adjust pulse widths if needed

3. **Network connectivity issues**
   - Verify Raspberry Pi IP address
   - Check firewall settings
   - Ensure both devices are on the same network

4. **Permission errors**
   - Run with sudo if needed: `sudo python rpi_servo_controller.py`
   - Check pigpio daemon permissions

## Project Structure

```
rpi_servo_udp_controller/
├── rpi_servo_controller.py    # Main Raspberry Pi servo controller
├── servo_upd_client.py        # Test client for sending commands
├── requirements_rpi.txt       # Python dependencies
└── README.md                  # This file
```
## License

This project is open source and available under the MIT License.
