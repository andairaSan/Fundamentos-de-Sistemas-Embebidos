#!/usr/bin/env python3
import os
import time
import threading
import io
import smbus2
from collections import defaultdict
from flask import Flask, Response, render_template_string, request

# Forzar a matplotlib a no usar interfaz gráfica
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Importamos tu clase del sensor independiente
from one_wire_temp_config import one_wire_temp_config

# --- CONFIGURACIÓN GLOBAL ---
LOG_FILE     = './temp.log'
APP_PORT     = 8082
LOG_PERIOD   = 5.0   # Segundos entre registros en el archivo log
MAX_DAYS     = 30

# --- CONFIGURACIÓN LCD I2C ---
ADDR = 0x27
BUSN = 1
bus = smbus2.SMBus(BUSN)
PINMAPS = [
    {'BL':0x08,'EN':0x04,'RW':0x02,'RS':0x01,'hi_mask':0xF0,'lo_mask':0x0F,'nibble_high':True,'name':'MapA'},
    {'BL':0x01,'EN':0x08,'RW':0x04,'RS':0x02,'hi_mask':0xF0,'lo_mask':0x0F,'nibble_high':True,'name':'MapB'},
    {'BL':0x80,'EN':0x40,'RW':0x20,'RS':0x10,'hi_mask':0x0F,'lo_mask':0xF0,'nibble_high':False,'name':'MapC'},
]

# --- VARIABLES GLOBALES DE COMPARTICIÓN DE DATOS ---
# Guardamos la última temperatura leída para que el LCD y Flask la accedan al instante
ultima_temperatura = None
_stop_event = threading.Event()

# --- FUNCIONES LCD (IGUAL QUE ANTES) ---
def pcf_write(val): bus.write_byte(ADDR, val)
def pulse_en(val, EN):
    pcf_write(val | EN); time.sleep(0.0005)
    pcf_write(val & ~EN); time.sleep(0.0001)
def send_byte(byte, RS, RW, BL, mapdef):
    if mapdef['nibble_high']:
        hi = (byte & 0xF0)
        lo = (byte << 4) & 0xF0
    else:
        hi = (byte >> 4) & 0x0F
        lo = byte & 0x0F
    base = BL
    pcf_write(base | hi | RS)
    pulse_en(base | hi | RS, mapdef['EN'])
    pcf_write(base | lo | RS)
    pulse_en(base | lo | RS, mapdef['EN'])

def lcd_cmd(cmd, mapdef): send_byte(cmd, 0, 0, mapdef['BL'], mapdef)
def lcd_dat(ch, mapdef): send_byte(ch, mapdef['RS'], 0, mapdef['BL'], mapdef)
def init_lcd(mapdef):
    time.sleep(0.05)
    for seq in [0x30,0x30,0x30,0x20]:
        if mapdef['nibble_high']: val = (seq & 0xF0) | mapdef['BL']
        else: val = (seq >> 4) | mapdef['BL']
        pcf_write(val); pulse_en(val, mapdef['EN'])
        time.sleep(0.005 if seq==0x30 else 0.001)
    lcd_cmd(0x28, mapdef); lcd_cmd(0x0C, mapdef)
    lcd_cmd(0x01, mapdef); time.sleep(0.002); lcd_cmd(0x06, mapdef)
def set_cursor(row, col, mapdef):
    base = 0x80 if row == 0 else 0xC0
    lcd_cmd(base + col, mapdef)
def write_string(s, mapdef):
    for ch in s[:16]: lcd_dat(ord(ch), mapdef)

# --- TRABAJADOR 1: LOGGER EN BACKGROUND (MUESTRA EN LCD + GUARDA LOG) ---
def hardware_worker():
    global ultima_temperatura
    sensor = one_wire_temp_config()
    
    # Intentamos encontrar un mapa LCD válido
    lcd_mapeo = None
    for m in PINMAPS:
        try:
            pcf_write(0x00)
            pcf_write(m['BL'])
            init_lcd(m)
            lcd_mapeo = m
            print(f"** LCD listo con {m['name']} **")
            break
        except Exception:
            continue

    # Configuración carrusel continuo
    texto_original = "Zuniga Sanches Garcia "
    texto_carrusel = texto_original + texto_original[:16]
    indice_carrusel = 0
    limite_carrusel = len(texto_original)
    
    contador_ciclos = 0
    temp_lcd_str = "Cargando..."

    os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)

    while not _stop_event.is_set():
        # Cada 10 ciclos (~2 segundos), leemos hardware y escribimos log
        if contador_ciclos % 10 == 0:
            ultima_temperatura = sensor.read_temp()
            temp_fahr = (ultima_temperatura * 9 / 5) + 32
            if ultima_temperatura is not None:
                temp_lcd_str = f"{ultima_temperatura:.1f} C, {temp_fahr:.1f} F"
                # Registro con formato crudo en el archivo log
                with open(LOG_FILE, 'a') as fp:
                    fp.write(f"{time.time()} {ultima_temperatura:.2f}°C\n")
            else:
                temp_lcd_str = "Error Sensor    "

        # Si el LCD está conectado, pintamos carrusel y estático
        if lcd_mapeo:
            try:
                fragmento = texto_carrusel[indice_carrusel : indice_carrusel + 16]
                set_cursor(0, 0, lcd_mapeo)
                write_string(fragmento, lcd_mapeo)
                
                set_cursor(1, 0, lcd_mapeo)
                write_string(temp_lcd_str, lcd_mapeo)
                
                indice_carrusel = (indice_carrusel + 1) % limite_carrusel
            except Exception:
                pass

        contador_ciclos += 1
        _stop_event.wait(0.2) # Intervalo del carrusel

    # Al apagar el hilo, limpia la pantalla si existe
    if lcd_mapeo:
        try: lcd_cmd(0x01, lcd_mapeo)
        except: pass

# --- MANEJO DE GRÁFICAS Y LOG (IGUAL QUE ANTES) ---
def read_log_window(hours=24):
    if not os.path.exists(LOG_FILE): return []
    cutoff = time.time() - hours*3600
    rows = []
    with open(LOG_FILE, 'r') as fp:
        for line in fp:
            parts = line.strip().split()
            if len(parts) < 2: continue
            try:
                ts = float(parts[0])
                temp = float(parts[1].replace('°C',''))
            except ValueError: continue
            if ts >= cutoff: rows.append((ts, temp))
    return rows

def bucket_by_minute(rows):
    buckets = defaultdict(list)
    for ts, t in rows:
        m = int(ts // 60) * 60
        buckets[m].append(t)
    return sorted((m, sum(v)/len(v)) for m, v in buckets.items())

def make_plot(hours=24):
    rows = read_log_window(hours)
    fig = plt.figure(figsize=(9,4))
    if not rows:
        plt.title(f"Sin datos en las últimas {hours} h")
        plt.grid(True)
    else:
        series = bucket_by_minute(rows)
        t0 = series[0][0]
        xs = [(m - t0)/60.0 for m,_ in series]
        ys = [v for _,v in series]
        plt.plot(xs, ys, marker='o', linestyle='-', color='#007BFF')
        plt.title(f"Histórico de temperatura (últimas {hours} h)")
        plt.xlabel("Tiempo (minutos desde ventana)")
        plt.ylabel("Temperatura (°C)")
        plt.ylim(0,50)
        plt.grid(True)
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf.read()

# --- INTERFAZ WEB HTML (FLASK) ---
app = Flask(__name__)
HTML_TEMPLATE = """<!doctype html><html lang="es"><head>
<meta charset="utf-8"><title>Panel Raspberry Pi AP</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:24px auto;padding:0 12px;background:#f8f9fa;color:#333}
.card{background:#fff;border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0;box-shadow:0 2px 6px rgba(0,0,0,.04)}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.temp-display{font-size:2.5rem;font-weight:bold;color:#ff5722;margin:8px 0}
label{font-weight:600} input,select{padding:.4rem .6rem;border:1px solid #ccc;border-radius:8px}
button{padding:.5rem 1rem;border-radius:8px;border:none;background:#007BFF;color:#fff;cursor:pointer}
img{max-width:100%;height:auto;display:block;margin:20px auto;border-radius:8px}
</style></head><body>
<h1>Panel de Monitoreo - Servidor Local</h1>
<div class="card">
  <h2>Lectura Actual</h2>
  <div class="temp-display">{{ temp_actual }}</div>
</div>
<div class="card">
  <form class="controls" onsubmit="reloadPlot();return false">
    <div>
      <label>Ventana:</label>
      <select id="hours">
        <option value="1">Última 1 h</option>
        <option value="3">Últimas 3 h</option>
        <option value="24" selected>Últimas 24 h</option>
        <option value="72">Últimas 72 h</option>
      </select>
    </div>
    <div>
      <label>Auto-actualizar (s):</label>
      <input id="interval" type="number" value="10" min="5">
    </div>
    <button type="button" onclick="reloadPlot()">Actualizar</button>
  </form>
</div>
<div class="card">
  <img id="plot" src="/plot.png?h=24&rand={{ ts }}" alt="Gráfica">
</div>
<script>
let timer=null;
function reloadPlot(){
  const h = document.getElementById('hours').value;
  const img = document.getElementById('plot');
  img.src = `/plot.png?h=${h}&rand=${Date.now()}`;
  const sec = parseInt(document.getElementById('interval').value||"10");
  if (timer) clearInterval(timer);
  if (sec>0){ timer = setInterval(()=>window.location.reload(), sec*1000); }
}
if(!timer) { timer = setInterval(()=>window.location.reload(), 10000); }
</script>
</body></html>"""

@app.route("/")
def index():
    t_str = f"{ultima_temperatura:.1f} °C" if ultima_temperatura is not None else "Leyendo..."
    return render_template_string(HTML_TEMPLATE, temp_actual=t_str, ts=int(time.time()))

@app.route("/plot.png")
def plot_png():
    try:
        hours = int(request.args.get('h', '24'))
        hours = max(1, min(24*MAX_DAYS, hours))
    except: hours = 24
    png = make_plot(hours)
    return Response(png, mimetype='image/png')

# --- INICIO GENERAL ---
def main():
    # Iniciamos el bucle del LCD y muestreo en un hilo paralelo
    th = threading.Thread(target=hardware_worker, daemon=True)
    th.start()
    try:
        # Escucha en todas las interfaces de red locales en el puerto configurado
        app.run(host="0.0.0.0", port=APP_PORT, debug=False)
    finally:
        _stop_event.set()
        th.join(timeout=2)

if __name__ == "__main__":
    main()
