import serial

src = serial.Serial("COM12", 115200, timeout=0.1)  # real NUCLEO
dst = serial.Serial("COM23", 115200, timeout=0.1)  # virtual port

print("Forwarding COM12 -> COM23")

while True:
    data = src.read(src.in_waiting or 1)
    if data:
        dst.write(data)
