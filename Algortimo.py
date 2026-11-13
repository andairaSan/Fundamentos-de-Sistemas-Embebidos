#!/usr/bin/env python3
# Práctica 8 - Experimento 1: apellido en la primera línea del LCD 1602
import time
import smbus2

ADDR = 0x27                                # dirección que mostró i2cdetect
BL, EN, RW, RS = 0x08, 0x04, 0x02, 0x01    # Mapa A del PCF8574
NOMBRE = "Ariadna"

bus = smbus2.SMBus(1)

def pcf_write(val):
    bus.write_byte(ADDR, val)

def pulse_en(val):
    pcf_write(val | EN); time.sleep(0.0005)
    pcf_write(val & ~EN); time.sleep(0.0001)

def send_byte(byte, rs):
    for nibble in (byte & 0xF0, (byte << 4) & 0xF0):   # nibble alto y bajo
        pcf_write(BL | nibble | rs)
        pulse_en(BL | nibble | rs)

def lcd_cmd(cmd): send_byte(cmd, 0)
def lcd_dat(ch):  send_byte(ch, RS)

def init_lcd():
    time.sleep(0.05)
    for seq in (0x30, 0x30, 0x30, 0x20): # pasa a modo de 4 bits
        val = (seq & 0xF0) | BL
        pcf_write(val); pulse_en(val)
        time.sleep(0.005 if seq == 0x30 else 0.001)
    lcd_cmd(0x28) # 2 líneas 5x8
    lcd_cmd(0x0C) # display ON sin cursor
    lcd_cmd(0x01); time.sleep(0.002) # borra
    lcd_cmd(0x06) # cursor incrementa

def set_cursor(row, col):
    lcd_cmd((0x80 if row == 0 else 0xC0) + col)

def write_string(s):
    for ch in s.ljust(16)[:16]:
        lcd_dat(ord(ch))

def main():
    init_lcd()
    set_cursor(0, 0)
    write_string(NOMBRE)

if __name__ == "__main__":
    main()