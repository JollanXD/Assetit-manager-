from pathlib import Path
from PIL import Image, ImageDraw

out = Path("assets/assetit.ico")
out.parent.mkdir(parents=True, exist_ok=True)

# Draw one crisp master image; Pillow writes all requested Windows ICO sizes.
size = 256
image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
def points(values):
    return [(round(x * size / 64), round(y * size / 64)) for x, y in values]

draw.rounded_rectangle((2, 2, size - 3, size - 3), radius=round(size * 0.18), fill=(15, 24, 36, 255))
draw.polygon(points([(5, 55), (26, 10), (39, 10), (19, 55)]), fill=(20, 188, 233, 255))
draw.polygon(points([(28, 10), (42, 10), (60, 44), (45, 55)]), fill=(8, 121, 236, 255))
draw.polygon(points([(20, 55), (45, 55), (42, 49), (23, 49)]), fill=(40, 210, 255, 255))
image.save(out, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"Created multi-resolution Windows icon: {out}")
