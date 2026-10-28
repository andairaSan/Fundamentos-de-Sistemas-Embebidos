#!/usr/bin/env python3
import time, smbus2
from one_wire_temp_config import one_wire_temp_config

ADDR = 0x27   # cambiar a 0x3F si el i2cdetect lo muestra así
BUSN = 1
bus = smbus2.SMBus(BUSN)

#pines:BL, EN, RW, RS, data_shift, bl_bit
# data_shift = desplazar nibble alto al puerto (4 bits altos en P7..P4 o P3..P0)
PINMAPS = [
    # Mapa A: P7..P4=D7..D4, P3=BL, P2=EN, P1=RW, P0=RS  (muy común)
    {'BL':0x08,'EN':0x04,'RW':0x02,'RS':0x01,'hi_mask':0xF0,'lo_mask':0x0F,'nibble_high':True,'name':'MapA'},

    # Mapa B: P7..P4=D7..D4, P0=BL, P3=EN, P2=RW, P1=RS
    {'BL':0x01,'EN':0x08,'RW':0x04,'RS':0x02,'hi_mask':0xF0,'lo_mask':0x0F,'nibble_high':True,'name':'MapB'},
    # Mapa Q: P3..P0=D7..D4, P7=BL, P6=EN, P5=RW, P4=RS  (algunos módulos “invertidos”)
    {'BL':0x80,'EN':0x40,'RW':0x20,'RS':0x10,'hi_mask':0x0F,'lo_mask':0xF0,'nibble_high':False,'name':'MapC'},
]

def pcf_write(val):
    bus.write_byte(ADDR, val)
#end def

def pulse_en(val, EN):
    pcf_write(val | EN); time.sleep(0.0005)
    pcf_write(val & ~EN); time.sleep(0.0001)
#end def

def send_byte(byte, RS, RW, BL, mapdef):
    if mapdef['nibble_high']:
        hi = (byte & 0xF0)
        lo = (byte << 4) & 0xF0
    else:
        hi = (byte >> 4) & 0x0F
        lo = byte & 0x0F
    base = BL  # backlight ON
    # hi nibble
    pcf_write(base | hi | RS)           # RS=0 cmd, RS=1 data
    pulse_en(base | hi | RS, mapdef['EN'])
    # lo nibble
    pcf_write(base | lo | RS)
    pulse_en(base | lo | RS, mapdef['EN'])
#end def

def lcd_cmd(cmd, mapdef):
    send_byte(cmd, 0, 0, mapdef['BL'], mapdef)
#edn def

def lcd_dat(ch, mapdef):
    send_byte(ch, mapdef['RS'], 0, mapdef['BL'], mapdef)
#end def

def init_lcd(mapdef):
    # Secuencia estándar init 4-bit
    time.sleep(0.05)
    # Forzar 8-bit tres veces, luego 4-bit (en el puerto según mapa)
    for seq in [0x30,0x30,0x30,0x20]:
        if mapdef['nibble_high']:
            val = (seq & 0xF0) | mapdef['BL']
        else:
            val = (seq >> 4) | mapdef['BL']
        pcf_write(val); pulse_en(val, mapdef['EN'])
        time.sleep(0.005 if seq==0x30 else 0.001)
    # Function set: 4-bit, 2 lines, 5x8
    lcd_cmd(0x28, mapdef)
    # Display ON, cursor OFF, blink OFF
    lcd_cmd(0x0C, mapdef)
    # Clear
    lcd_cmd(0x01, mapdef); time.sleep(0.002)
    # Entry mode: increment
    lcd_cmd(0x06, mapdef)
#end def

def set_cursor(row, col, mapdef):
    base = 0x80 if row == 0 else 0xC0
    lcd_cmd(base + col, mapdef)
#end def

def write_string(s, mapdef):
    for ch in s[:16]:
        lcd_dat(ord(ch), mapdef)
#end def

def try_map(m):
    try:
        # backlight ON
        pcf_write(m['BL'])
        init_lcd(m)
        set_cursor(0,0,m)
        write_string("Zuniga,Sanchez,Garcia", m)  # <-- cambia a tu apellido
        time.sleep(0.4)
        #set_cursor(1,0,m)
        #write_string("Garcia",m)
        #time.sleep(0.4)
        return True
    except Exception as e:
        print(f"Error en {m['name']}: {e}")
        return False
#end def

def main():
    sensor = one_wire_temp_config()

    for m in PINMAPS:
        # Clear any residual
        try:
            pcf_write(0x00)
        except:
            pass
        ok = try_map(m)
        if ok:
            print(f"** OK con {m['name']} ** (deja texto en pantalla)")
            # Deja el display con texto y se queda vivo
            try:
                while True:
                    temperat = sensor.read_temp()
                    temp_fahren = (float(temperat) * 9 / 5) + 32
                    set_cursor(1,0,m)
                    if temperat  is not None:
                        #print("temp ok")
                        write_string(f"{temperat:.1f}C {temp_fahren:.1f}F",m)
                    else:
                        write_string("Error sensor",m)
                    time.sleep(1)
            except KeyboardInterrupt:
                lcd_cmd(0x01, m)
            return
        else:
            print(f"No hubo texto con {m['name']}. Probando siguiente...")
            time.sleep(0.5)
    print("Ningún mapeo funcionó. Revisa contraste, backlight, VCC/GND y dirección.")
#end def

if __name__ == "__main__":
    main()
