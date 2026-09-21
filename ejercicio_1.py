import RPi.GPIO as GPIO

from time import sleep

GPIO.setwarnings(False)

GPIO.setmode(GPIO.BOARD)

pines_LED_sal = [12,16,18,22,24,26,32]

#iniciamos salidas de los led en low
GPIO.setup(pines_LED_sal,GPIO.OUT,initial=GPIO.LOW)

while True:
    GPIO.output(pines_LED_sal,GPIO.HIGH)
    sleep(0.5)
    GPIO.output(pines_LED_sal,GPIO.LOW)
    sleep(0.5)