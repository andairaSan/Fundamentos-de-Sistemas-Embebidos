import vlc
import time

player = vlc.MediaPlayer() #reproducimos el video con vlc
video = vlc.Media('/home/pi/videos/video.mp4')
player.set_media(video)
player.audio_set_volume(0)# Inicia con el volumen en 0
player.play()

for v in range(0, 101, 5):  #sube el volumen de 0 a 100 en 5 segundos
    player.audio_set_volume(v)
    time.sleep(5/20)  #20 pasos -> 5 s total
time.sleep(10) #Mantiene el 100% por 10 segundos

#baja el volumen de 100 a 0 en 5 segundos
for v in range(100, -1, -5):
    player.audio_set_volume(v)
    time.sleep(5/20)  # 20 pasos -> 5 s total
player.stop()# se detiene después de 20 s
