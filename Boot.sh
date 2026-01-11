#!/bin/bash

TARGET_SSID="BF-HSKK-2.4G"
MOMO_DIR="/home/usr/momo"

echo "=============================="
echo "Waiting for Wi-Fi - $TARGET_SSID"
echo "=============================="

while true; do
	SSID=$(iwgetid -r)

	[ "$SSID" = "$TARGET_SSID" ] && break
	sleep 2
done

echo "Wi-Fi connected!"
echo "Starting streaming by momo"
cd "$MOMO_DIR"
if ! tmuc has-session -t momo 2>/dev/null; then
	tmux new-session -d -s momo "./momo --no-audio-device p2p"
fi
echo "Streaming started!"
echo "Starting raspy.py (RC controll)"
python3 /home/usr/raspi.py
