import RPi.GPIO as GPIO
from time import sleep
import threading

#variable para velocidad del parpadeo
blink_t = 0.5
#lock para evitar acceso simultaneo a la vraiable
thread_lock = threading.Lock()
#para apagar los hilos
hilos_ON= True

#
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
pines_led_out = [12,16,18,22,24,26,32]

def marquesina_hilos(num):
    GPIO.output(pines_led_out[6],GPIO.HIGH if num & 0x00000001 else GPIO.LOW)
    GPIO.output(pines_led_out[5],GPIO.HIGH if num & 0x00000002 else GPIO.LOW)
    GPIO.output(pines_led_out[4],GPIO.HIGH if num & 0x00000004 else GPIO.LOW)
    GPIO.output(pines_led_out[3],GPIO.HIGH if num & 0x00000008 else GPIO.LOW)
    GPIO.output(pines_led_out[2],GPIO.HIGH if num & 0x00000010 else GPIO.LOW)
    GPIO.output(pines_led_out[1],GPIO.HIGH if num & 0x00000020 else GPIO.LOW)
    GPIO.output(pines_led_out[0],GPIO.HIGH if num & 0x00000040 else GPIO.LOW)

def secuencia_var_blink():
    global blink_t

    while hilos_ON:
        inpt_blink = float(input("Defina la velocidad del parpadeo en [ms]: "))
        with thread_lock:
            blink_t = inpt_blink/1000
        
def secuencia_led():
    global blink_t
    GPIO.setup(pines_led_out, GPIO.OUT,initial=GPIO.LOW)
    num = 0x00000001
    
    while hilos_ON:
        with thread_lock:
            blink_refresh = blink_t
        marquesina_hilos(num)
        num = num << 1
        sleep(blink_refresh)
        if num > 0x00000040:
            num= 0x00000001
            
hilo_led = threading.Thread(target = secuencia_led)
hilo_var_blink = threading.Thread(target = secuencia_var_blink)

hilo_led.start()
hilo_var_blink.start()

try:
    while True:
        sleep(0.01)
except:
    hilos_ON = False
    hilo_led.join()
    hilo_var_blink.join()
    GPIO.cleanup()