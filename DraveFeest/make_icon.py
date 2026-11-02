# Maakt assets/icon.png + assets/icon.ico voor DraveFeest (eigen ontwerp: pixelhuisje met feestlampjes, lampion en ster).
import os
from PIL import Image, ImageDraw

HIER = os.path.dirname(os.path.abspath(__file__))
P = 32  # pixelraster 32x32, daarna 16x zo groot
im = Image.new("RGBA", (P, P), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle((0, 0, 31, 31), radius=6, fill=(14, 16, 40, 255))
for x, y in ((4, 4), (26, 6), (20, 3), (8, 10), (28, 13)):
    d.point((x, y), fill=(220, 220, 255, 255))
d.polygon([(22, 3), (23, 5), (25, 5), (23, 6), (24, 8), (22, 7), (20, 8), (21, 6), (19, 5), (21, 5)], fill=(255, 205, 60, 255))
d.rectangle((7, 16, 24, 27), fill=(170, 60, 50, 255))
d.polygon([(5, 16), (15, 8), (16, 8), (26, 16)], fill=(90, 30, 35, 255))
d.line([(5, 16), (15, 8)], fill=(240, 245, 250, 255))
d.line([(16, 8), (26, 16)], fill=(240, 245, 250, 255))
d.rectangle((14, 21, 17, 27), fill=(60, 35, 25, 255))
for x0 in (9, 20):
    d.rectangle((x0, 19, x0 + 2, 21), fill=(255, 214, 110, 255))
for i, x in enumerate(range(7, 25, 2)):
    d.point((x, 17 + (i % 2)), fill=[(255, 60, 60, 255), (255, 220, 60, 255), (80, 200, 255, 255), (120, 255, 120, 255)][i % 4])
d.rounded_rectangle((1, 26, 30, 30), radius=4, fill=(230, 235, 245, 255))
d.rectangle((1, 26, 30, 27), fill=(230, 235, 245, 255))
d.rounded_rectangle((0, 0, 31, 31), radius=6, outline=(255, 179, 71, 255))
d.line([(28, 18), (28, 22)], fill=(110, 80, 50, 255))
d.ellipse((26, 22, 30, 26), fill=(255, 140, 40, 255))
d.point((28, 24), fill=(255, 240, 180, 255))
big = im.resize((512, 512), Image.NEAREST)
os.makedirs(os.path.join(HIER, "assets"), exist_ok=True)
big.save(os.path.join(HIER, "assets", "icon.png"))
big.save(os.path.join(HIER, "assets", "icon.ico"), format="ICO",
         sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icoon klaar")
