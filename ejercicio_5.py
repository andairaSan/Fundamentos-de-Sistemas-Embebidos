import RPi.GPIO as GPIO
from time import sleep
import threading

GPIO.setwarnings(False)

GPIO.setmode(GPIO.BOARD)

GPIO.setup(32,GPIO.OUT,initial=GPIO.LOW)

pwm = GPIO.PWM(32,1000)

thread_lock = threading.Lock()

hilos_ON = True

dutyCycle = 0

pwm.start(dutyCycle)
flag = True

def sec_cambia_pwm():
    global dutyCycle
    up_flag = True
    
    while hilos_ON:
        with thread_lock:
            if up_flag == True:
                dutyCycle = dutyCycle + 1
            if dutyCycle > 100:
                up_flag = False
            if up_flag == False:
                dutyCycle = dutyCycle - 1
            if dutyCycle < 1:
                up_flag = True
        sleep(0.1)
        
def sec_led():
    global dutyCycle
    
    while hilos_ON:
        with thread_lock:
            pwm.ChangeDutyCycle(dutyCycle)

hilo_pwm = threading.Thread(target = sec_cambia_pwm)
hilo_led = threading.Thread(target = sec_led)

hilo_pwm.start()
hilo_led.start()

while flag:
    try:
        sleep(0.01)
    except:
        flag = False
        pwm.ChangeDutyCycle(0)
        hilo_pwm.join()
        hilo_led.join()
        GPIO.cleanup()
        pwm.stop()
