import vlc
import time
import os
import pyudev
import subprocess as sp
from threading import Thread

#Funciones de ayuda
def get_images(path): #Devuelve lista de imágenes .jpg y .png en la ruta dada
    if not os.path.exists(path):
        return []
    return [os.path.join(path, f)
            for f in os.listdir(path)
            if f.lower().endswith(".jpg") or f.lower().endswith(".png")]

def auto_mount(path):#Monta la partición USB usando udisksctl
    args = ["udisksctl", "mount", "-b", path]
    sp.run(args)

def get_mount_point(path):#punto de montaje 
    args = ["findmnt", "-unl", "-S", path]
    cp = sp.run(args, capture_output=True, text=True)
    out = cp.stdout.strip().split(" ")[0]
    return out

video_path = "/home/pi/videos/video.mp4" #ruta para encontrar el video
local_pictures_path = "/home/pi/pictures"

player = vlc.MediaPlayer() #utilizamos vlc
pictures_path = local_pictures_path #variable global de ruta de imágenes

#Hilo para detectar la usb cuando se utilice en la raspberry
def usb_monitor():
    global pictures_path
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="block", device_type="partition")
    for action, device in monitor:
        if action != "add":
            continue
        dev_path = "/dev/" + device.sys_name
        print(f"USB detectada en {dev_path}, montando...")
        auto_mount(dev_path)
        mp = get_mount_point(dev_path)
        print(f"Punto de montaje: {mp}")
        pictures_path = mp  # Cambiar carpeta a USB

#Reproducir video por 10 segundos
if os.path.exists(video_path):
    video = vlc.Media(video_path)
    player.set_media(video)
    player.play()
    time.sleep(10)
    player.stop()
else:
    print("No existe archivo", video_path)

thread = Thread(target=usb_monitor, daemon=True) #Inicia hilo de monitoreo USB
thread.start()

#Mostrar imágenes tanto locales como de la USB
while True:
    images = get_images(pictures_path)

    if not images:
        print("No hay imágenes en", pictures_path)
        time.sleep(5)
        continue

    for img in images:
        media = vlc.Media(img)
        player.set_media(media)
        player.play()
        print("Mostrando:", img)
        time.sleep(3)
        player.stop()
