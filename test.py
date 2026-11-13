#!/usr/bin/env python3
# Práctica 8 - Experimentos 2 y 4
# Línea 1: apellidos en marquesina (corrimiento infinito a la izquierda)
# Línea 2: temperatura del DS18B20 en grados centígrados
import glob
import threading
import time
import smbus2

ADDR = 0x27 # dirección que mostró i2cdetect
BL, EN, RW, RS = 0x08, 0x04, 0x02, 0x01 # Mapa A del PCF8574

# Apellidos paternos del equipo
APELLIDOS = ["Garcia", "Sanchez", "Zuniga"]
VELOCIDAD = 0.3 # segundos entre cada desplazamiento
MOSTRAR_TEMP = True # False = solo marquesina (experimento 2)

bus = smbus2.SMBus(1)
temperatura = None # la actualiza el hilo de lectura del sensor


def pcf_write(val):
    bus.write_byte(ADDR, val)

def pulse_en(val):
    pcf_write(val | EN); time.sleep(0.0005)
    pcf_write(val & ~EN); time.sleep(0.0001)

def send_byte(byte, rs):
    for nibble in (byte & 0xF0, (byte << 4) & 0xF0):# nibble alto y bajo
        pcf_write(BL | nibble | rs)
        pulse_en(BL | nibble | rs)

def lcd_cmd(cmd): send_byte(cmd, 0)
def lcd_dat(ch):  send_byte(ch, RS)

def init_lcd():
    time.sleep(0.05)
    for seq in (0x30, 0x30, 0x30, 0x20):# pasa a modo de 4 bits
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


def limpiar(s):
    return s.translate(str.maketrans("áéíóúÁÉÍÓÚñÑüÜ", "aeiouAEIOUnNuU"))

def leer_ds18b20():
    """Devuelve la temperatura en °C, o None si el sensor no responde."""
    try:
        ruta = glob.glob("/sys/bus/w1/devices/28-*/w1_slave")[0]
        with open(ruta) as f:
            lineas = f.read().splitlines()
        if lineas[0].strip().endswith("YES"):
            return int(lineas[1].split("t=")[1]) / 1000.0
    except (IndexError, OSError, ValueError):
        pass
    return None

def hilo_temperatura():
    global temperatura
    while True:
        temperatura = leer_ds18b20()
        time.sleep(2)

def texto_temp():
    if temperatura is None:
        return "Temp: sin sensor"
    return "Temp: %.1f %sC" % (temperatura, chr(0xDF)) # 0xDF = símbolo de grados


def main():
    init_lcd()
    texto = limpiar(" ".join(APELLIDOS)) + " "
    cinta = texto * (16 // len(texto) + 2)# cinta más larga que la ventana
    if MOSTRAR_TEMP:
        threading.Thread(target=hilo_temperatura, daemon=True).start()
    i = 0
    while True:
        try:
            set_cursor(0, 0)
            write_string(cinta[i:i + 16])
            if MOSTRAR_TEMP:
                set_cursor(1, 0)
                write_string(texto_temp())
        except OSError: # falla momentánea del bus I2C
            time.sleep(1)
            init_lcd()
            continue
        i = (i + 1) % len(texto)
        time.sleep(VELOCIDAD)

if __name__ == "__main__":
    main()
