# Junta os PNGs de fappzap/ico-fontes/ nos .ico do Windows (roda depois do gerar-marca.mjs).
from pathlib import Path
from PIL import Image

AQUI = Path(__file__).parent
FONTES = AQUI / "ico-fontes"
MARCA = AQUI / "marca"

def ico(destino, tamanhos):
    imgs = [Image.open(FONTES / f"{t}.png").convert("RGBA") for t in tamanhos]
    p = MARCA / destino
    p.parent.mkdir(parents=True, exist_ok=True)
    imgs[-1].save(p, format="ICO", sizes=[(t, t) for t in tamanhos], append_images=imgs[:-1])

ico("res/icon.ico", [16, 24, 32, 48, 64, 128, 256])
ico("flutter/windows/runner/resources/app_icon.ico", [16, 24, 32, 48, 64, 128, 256])
ico("res/tray-icon.ico", [16, 24, 32])
print("ico ok")
