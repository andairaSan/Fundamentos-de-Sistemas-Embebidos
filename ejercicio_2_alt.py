import RPi.GPIO as GPIO

from time import sleep

GPIO.setwarnings(False)

GPIO.setmode(GPIO.BOARD)

#iniciamos salidas en LOW
#lista para pines
pines_LED_out = [12,16,18,22,24,26,32,36,38,40,37]

GPIO.setup(pines_LED_out,GPIO.OUT,initial=GPIO.LOW)

def marquesina(num):
    GPIO.output(pines_LED_out[0], GPIO.HIGH if num & 0x00000001 else GPIO.LOW)
    GPIO.output(pines_LED_out[1], GPIO.HIGH if num & 0x00000002 else GPIO.LOW)
    GPIO.output(pines_LED_out[2], GPIO.HIGH if num & 0x00000004 else GPIO.LOW)
    GPIO.output(pines_LED_out[3], GPIO.HIGH if num & 0x00000008 else GPIO.LOW)
    GPIO.output(pines_LED_out[4], GPIO.HIGH if num & 0x00000010 else GPIO.LOW)
    GPIO.output(pines_LED_out[5], GPIO.HIGH if num & 0x00000020 else GPIO.LOW)
    GPIO.output(pines_LED_out[6], GPIO.HIGH if num & 0x00000040 else GPIO.LOW)
    
    GPIO.output(pines_LED_out[7], GPIO.HIGH if (num & 0x00000001) > 0 else GPIO.LOW)
    GPIO.output(pines_LED_out[8], GPIO.HIGH if (num & 0x00000002) > 0 else GPIO.LOW)
    GPIO.output(pines_LED_out[9], GPIO.HIGH if (num & 0x00000004) > 0 else GPIO.LOW)
    GPIO.output(pines_LED_out[10], GPIO.HIGH if (num & 0x00000008) > 0 else GPIO.LOW)
    
num=0x00000040
flag=True
while flag:
    try:
        marquesina(num)
        num = num>>1
        sleep(0.5)
        if(num<0x00000001):
            num=0x00000040
    except:
        flag = False
GPIO.cleanup()