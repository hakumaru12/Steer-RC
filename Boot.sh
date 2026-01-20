#!/bin/bash

TARGET_SSID="BF-HSKK-2.4G"
MOMO_DIR="/home/haku12/momo"

echo "=============================="
echo "Waiting for Wi-Fi - $TARGET_SSID"
echo "=============================="

while true; do
	SSID=$(iwgetid -r)

	[ "$SSID" = "$TARGET_SSID" ] && break
	sleep 2
done

IP_ADDR=$(hostname -I | awk '{print $1}')

echo "Wi-Fi connected!"

echo "=============================="
echo "SSID: $SSID"
echo "IP Address: $IP_ADDR"
echo "=============================="

echo "Starting streaming by momo"
cd "$MOMO_DIR"
if ! tmux has-session -t momo 2>/dev/null; then
	tmux new-session -d -s momo "./momo --no-audio-device p2p"
fi
echo "Streaming started!"
echo "Starting raspy.py (RC controll)"
python3 /home/haku12/raspi.py
