"""Gera os ícones do app (android-recursos/icone/*). Uso: python3 ferramentas/icone.py"""
import os
from PIL import Image, ImageDraw, ImageFont
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, 'android-recursos', 'icone')
FONTE = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
AZUL, BRANCO, GRIFO = (36, 70, 196), (255, 255, 255), (255, 210, 0)

def desenha(n, redondo):
    s = 4  # supersampling
    N = n * s
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if redondo: d.ellipse([0, 0, N - 1, N - 1], fill=AZUL)
    else: d.rounded_rectangle([0, 0, N - 1, N - 1], radius=int(N * .22), fill=AZUL)
    f = ImageFont.truetype(FONTE, int(N * .36))
    t = '201'
    bx = d.textbbox((0, 0), t, font=f)
    w, h = bx[2] - bx[0], bx[3] - bx[1]
    x, y = (N - w) / 2 - bx[0], (N - h) / 2 - bx[1] - N * .02
    # traço de marca-texto atrás da parte de baixo do número
    d.rounded_rectangle([x - N * .04, y + h * .58 + bx[1], x + w + N * .04, y + h * 1.02 + bx[1]], radius=int(N * .03), fill=GRIFO)
    d.text((x, y), t, font=f, fill=BRANCO, stroke_width=int(N * .012), stroke_fill=AZUL)
    return img.resize((n, n), Image.LANCZOS)

for dens, n in {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}.items():
    pasta = os.path.join(OUT, 'mipmap-' + dens); os.makedirs(pasta, exist_ok=True)
    desenha(n, False).save(os.path.join(pasta, 'ic_launcher.png'))
    desenha(n, True).save(os.path.join(pasta, 'ic_launcher_round.png'))
desenha(512, False).save(os.path.join(OUT, 'icone-512.png'))
print('ok')
