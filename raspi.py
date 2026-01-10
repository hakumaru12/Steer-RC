#raspberry pi 側のコード
import socket
import struct
import time
from adafruit_pca9685 import PCA9685 # type: ignore
from adafruit_motor import servo, motor # type: ignore
import board # type: ignore
import busio # type: ignore

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # 50Hz

ESC_Default_Duty = 0.075  # ESCのニュートラル位置

servo_channel = pca.channels[0]  # サーボモータ用
esc_channel = pca.channels[1]    # ESC用

servo_motor = servo.Servo(servo_channel, min_pulse=500, max_pulse=2500)

# ダブルバック用の状態管理
reverse_ready = False

def initialize_esc():
    """ESCの初期化"""
    print("ESC初期化開始")
    esc_channel.duty_cycle = int(0.095 * 65535)
    time.sleep(2)
    print("ESC初期化完了")

def set_neutral():
    """ニュートラルに設定"""
    esc_channel.duty_cycle = int(0.095 * 65535)

def set_esc_speed(throttle_percent, direction):
    """
    ESCの速度を設定（0-100%）
    direction: 1=前進, -1=後退
    """
    if throttle_percent == 0:
        duty_percent = ESC_Default_Duty
    else:
        if direction == 1:  # 前進
            duty_percent = ESC_Default_Duty + (throttle_percent / 100.0) * 0.025
        else:  # 後退
            duty_percent = ESC_Default_Duty - (throttle_percent / 100.0) * 0.025
    
    duty_cycle = int(duty_percent * 65535)
    esc_channel.duty_cycle = duty_cycle
    return duty_percent * 100

def do_double_back():
    """ダブルバック操作を実行"""
    print("ダブルバック実行中...")
    set_esc_speed(30, -1)
    time.sleep(0.15)
    set_neutral()
    time.sleep(0.15)
    print("ダブルバック完了 - 後退可能")

def main():
    global reverse_ready
    
    initialize_esc()
    
    print("UDP通信待機中...")
    sock.settimeout(0.5)
    
    try:
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                steering_angle, throttle_value, direction = struct.unpack('ffi', data)
                
                servo_motor.angle = steering_angle + 90
                
                if direction == 1:
                    reverse_ready = False
                
                if direction == -1 and not reverse_ready:
                    do_double_back()
                    reverse_ready = True
                
                actual_duty = set_esc_speed(throttle_value, direction)
                status = "Reverse READY" if reverse_ready else "Forward"
                print(f"Throttle: {throttle_value:.1f}%, Direction: {'Forward' if direction == 1 else 'Reverse'}, Duty: {actual_duty:.2f}%, {status}")
                
            except socket.timeout:
                set_esc_speed(0, 1)
                reverse_ready = False
                continue
            
    except KeyboardInterrupt:
        print("\nプログラムを終了します")
    finally:
        set_esc_speed(0, 1)
        time.sleep(0.5)
        pca.deinit()
        sock.close()

if __name__ == "__main__":
    main()
