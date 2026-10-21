from pathlib import Path
from PIL import Image, ImageDraw

out = Path("assets/assetit.ico")
out.parent.mkdir(parents=True, exist_ok=True)
images = []
for size in (16, 24, 32, 48, 64, 128, 256):
    scale = size / 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    def p(points):
        return [(round(x * scale), round(y * scale)) for x, y in points]
    draw.polygon(p([(5, 55), (26, 10), (39, 10), (19, 55)]), fill=(20, 188, 233, 255))
    draw.polygon(p([(28, 10), (42, 10), (60, 44), (45, 55)]), fill=(8, 121, 236, 255))
    draw.polygon(p([(20, 55), (45, 55), (42, 49), (23, 49)]), fill=(40, 210, 255, 255))
    images.append(image)
images[-1].save(out, format="ICO", sizes=[(i.size[0], i.size[1]) for i in images], append_images=images[:-1])
print(f"Created {out}")
