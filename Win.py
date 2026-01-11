# Windows PC side code
import pygame # type: ignore
import socket
import struct
import time

UDP_IP = "192.168.11.2"  # Raspberry Pi IP address
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

Steer_val_range = 23 
Throttle_range = 50 # Throttle value
Brake_range = 50 # Brake value

# Throttle adjustment settings
THROTTLE_STEP = 5  # Change amount per button press
THROTTLE_MIN = 30
THROTTLE_MAX = 100

# Driving Force button numbers (change as needed)
# To check button numbers, see the print statement below for button_id
BUTTON_THROTTLE_UP = 4    # Right paddle (throttle up)
BUTTON_THROTTLE_DOWN = 5  # Left paddle (throttle down)

# Direction toggle button (steering center button)
BUTTON_DIRECTION_TOGGLE = 19  # Center button to toggle Forward/Reverse


def init_controller():
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        raise Exception("GT Force Pro is not connected")
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Controller name: {joystick.get_name()}")
    print(f"Number of buttons: {joystick.get_numbuttons()}")
    return joystick

def map_range(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def apply_throttle_curve(value):

    return (value / 100) ** 2 * 100

def apply_deadzone(value, deadzone=0.02):

    if abs(value) < deadzone:
        return 0
    return value

def main():
    global Throttle_range, Brake_range
    
    joystick = init_controller()
    print("GT Force Pro connected")
    print(f"Current throttle range: {Throttle_range}%")
    print(f"Throttle: Button {BUTTON_THROTTLE_UP} to increase, Button {BUTTON_THROTTLE_DOWN} to decrease")
    print(f"Direction: Button {BUTTON_DIRECTION_TOGGLE} to toggle Forward/Reverse")
    print("Brake pedal: Immediate stop")
    
    # Track button press state (prevent continuous input)
    button_up_pressed = False
    button_down_pressed = False
    
    # Direction state (1=Forward, -1=Reverse)
    current_direction = 1
    
    try:
        while True:
            # Adjust throttle/brake range with button input
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    print(f"Button {event.button} pressed")  # Debug
                    
                    # Direction toggle
                    if event.button == BUTTON_DIRECTION_TOGGLE:
                        current_direction = -current_direction
                        dir_str = "Forward" if current_direction == 1 else "Reverse"
                        print(f">>> Direction changed to: {dir_str} <<<")
                    
                    # Throttle adjustment
                    elif event.button == BUTTON_THROTTLE_UP:
                        Throttle_range = min(Throttle_range + THROTTLE_STEP, THROTTLE_MAX)
                        print(f"▲ Throttle range: {Throttle_range}%")
                    
                    elif event.button == BUTTON_THROTTLE_DOWN:
                        Throttle_range = max(Throttle_range - THROTTLE_STEP, THROTTLE_MIN)
                        print(f"▼ Throttle range: {Throttle_range}%")
            
            steering = joystick.get_axis(0)
            raw_throttle = -joystick.get_axis(1)
            raw_brake = -joystick.get_axis(2)
            
            print(f"Raw throttle value: {raw_throttle:.3f}, Raw brake value: {raw_brake:.3f}")
            
            steering = apply_deadzone(steering)
            throttle = apply_deadzone(raw_throttle)
            brake = apply_deadzone(raw_brake)
            
            steering_angle = map_range(steering, -1.0, 1.0, -Steer_val_range, Steer_val_range)
            
            # Brake pedal pressed - immediate stop
            if raw_brake > -0.99:
                throttle_value = 0
                direction = current_direction
            # Throttle pedal
            elif raw_throttle > -0.99:
                raw_throttle_value = map_range(throttle, -0.99, 1.0, 0, Throttle_range)
                throttle_value = apply_throttle_curve(raw_throttle_value)
                direction = current_direction
            # No pedal pressed
            else:
                throttle_value = 0
                direction = current_direction
            
            dir_display = "Forward" if direction == 1 else "Reverse"
            brake_status = " [BRAKE]" if raw_brake > -0.99 else ""
            print(f"Throttle value: {throttle_value:.1f}%, Direction: {dir_display}{brake_status}")
            
            data = struct.pack('ffi', steering_angle, throttle_value, direction)
            
            sock.sendto(data, (UDP_IP, UDP_PORT))
            
            time.sleep(0.02)
            
    except KeyboardInterrupt:
        print("Exiting program")
    finally:
        pygame.quit()
        sock.close()

if __name__ == "__main__":
    main()