from PIL import Image, ImageDraw, ImageFont
import os
D=os.path.dirname(os.path.abspath(__file__))
F6=ImageFont.truetype(f"{D}/fonts/Poppins-600.ttf", 28)
def label(text, out):
    pad_x, pad_y = 28, 16
    tw = F6.getlength(text); bbox = F6.getbbox("Hg"); th = bbox[3]-bbox[1]
    w = int(tw + pad_x*2 + 10); h = int(th + pad_y*2 + 6)
    im = Image.new("RGBA", (1920, 1080), (0,0,0,0)); d = ImageDraw.Draw(im)
    x0, y0 = 56, 1080-56-h
    d.rounded_rectangle([x0, y0, x0+w, y0+h], radius=12, fill=(11,31,58,228))
    d.rectangle([x0, y0+10, x0+5, y0+h-10], fill=(201,162,75,255))
    d.text((x0+pad_x+6, y0+pad_y-bbox[1]+2), text, font=F6, fill=(244,241,234,255))
    im.save(out)
def phone_caption(title, sub, out):
    im = Image.new("RGBA", (1920,1080), (0,0,0,0)); d = ImageDraw.Draw(im)
    d.text((260,440), title, font=ImageFont.truetype(f"{D}/fonts/Poppins-600.ttf", 64), fill=(244,241,234,255))
    d.text((262,540), sub, font=ImageFont.truetype(f"{D}/fonts/Poppins-500.ttf", 30), fill=(201,162,75,255))
    im.save(out)
