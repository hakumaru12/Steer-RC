#Windows PC 側のコード
import pygame # type: ignore
import socket
import struct
import time

UDP_IP = "192.168.11.2"  # Raspberry PiのIPアドレス
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

Steer_val_range = 23 
Throttle_range = 50 # スロットル値
Brake_range = 50 # ブレーキ値


def init_controller():
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        raise Exception("GT Force Proが接続されていません")
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
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
    joystick = init_controller()
    print("GT Force Pro接続完了")
    
    try:
        while True:
            pygame.event.pump()
            
            steering = joystick.get_axis(0)
            raw_throttle = -joystick.get_axis(1)
            raw_brake = -joystick.get_axis(2)
            
            print(f"Raw throttle value: {raw_throttle:.3f}, Raw brake value: {raw_brake:.3f}")
            
            steering = apply_deadzone(steering)
            throttle = apply_deadzone(raw_throttle)
            brake = apply_deadzone(raw_brake)
            
            steering_angle = map_range(steering, -1.0, 1.0, -Steer_val_range, Steer_val_range)
            
            if raw_throttle <= -0.99 and raw_brake <= -0.99:
                throttle_value = 0
                direction = 1  # 前
            elif raw_throttle > -0.99:  
                raw_throttle_value = map_range(throttle, -0.99, 1.0, 0, Throttle_range)
                throttle_value = apply_throttle_curve(raw_throttle_value)
                direction = 1  # 前進
            elif raw_brake > -0.99:  
                raw_brake_value = map_range(brake, -0.99, 1.0, 0, Brake_range)
                throttle_value = apply_throttle_curve(raw_brake_value)
                direction = -1  # 後
            
            print(f"Throttle value: {throttle_value:.1f}%, Direction: {'Forward' if direction == 1 else 'Reverse'}")
            
            data = struct.pack('ffi', steering_angle, throttle_value, direction)
            
            sock.sendto(data, (UDP_IP, UDP_PORT))
            
            time.sleep(0.02)
            
    except KeyboardInterrupt:
        print("プログラムを終了します")
    finally:
        pygame.quit()
        sock.close()

if __name__ == "__main__":
    main()