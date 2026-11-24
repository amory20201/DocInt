#!/usr/bin/env python3
"""Generates the fictional sample documents in ./samples (re-runnable)."""
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
os.makedirs(OUT, exist_ok=True)
F = "/usr/share/fonts/truetype/dejavu/"

def font(name, size): return ImageFont.truetype(F + name, size)

# ---------- 1. invoice.pdf (text PDF) ----------
def invoice_pdf():
    c = canvas.Canvas(f"{OUT}/invoice_nile_trading.pdf", pagesize=A4); w, h = A4
    c.setFont("Helvetica-Bold", 22); c.drawString(50, h-70, "Nile Trading Supplies")
    c.setFont("Helvetica", 10); c.drawString(50, h-88, "12 Corniche Road, Alexandria, Egypt")
    c.setFont("Helvetica-Bold", 28); c.drawRightString(w-50, h-70, "INVOICE")
    c.setFont("Helvetica", 11)
    y = h-140
    for l in ["Invoice No: INV-2026-0417", "Invoice Date: 14 March 2026", "Due Date: 13 April 2026"]:
        c.drawString(50, y, l); y -= 18
    c.setFont("Helvetica-Bold", 11); c.drawString(50, y-10, "Bill To:"); c.setFont("Helvetica", 11)
    c.drawString(50, y-28, "Delta Logistics LLC"); c.drawString(50, y-44, "45 Industrial Zone, Cairo")
    y -= 100
    c.setFont("Helvetica-Bold", 10)
    for x, t in ((50, "Description"), (330, "Qty"), (390, "Unit price"), (480, "Amount")): c.drawString(x, y, t)
    c.line(50, y-4, w-50, y-4); c.setFont("Helvetica", 10); y -= 22
    for d, q, u, a in (("Packaging boxes (large)", "200", "$3.50", "$700.00"), ("Pallet wrap rolls", "40", "$10.00", "$400.00")):
        c.drawString(50, y, d); c.drawString(330, y, q); c.drawString(390, y, u); c.drawString(480, y, a); y -= 18
    y -= 10
    for l, v in (("Subtotal", "$1,100.00"), ("VAT (14%)", "$154.00")):
        c.drawString(390, y, l); c.drawString(480, y, v); y -= 16
    c.setFont("Helvetica-Bold", 12); c.drawString(390, y-4, "Total"); c.drawString(480, y-4, "$1,254.00")
    c.setFont("Helvetica-Bold", 26); c.setFillColorRGB(0.1, 0.6, 0.3); c.drawString(50, y-10, "PAID")
    c.setFillColorRGB(0, 0, 0); c.setFont("Helvetica", 9); c.drawString(50, 60, "Payment received by bank transfer on 20 March 2026. Thank you for your business.")
    c.save()

# ---------- 2. contract.pdf ----------
def contract_pdf():
    c = canvas.Canvas(f"{OUT}/contract_service_agreement.pdf", pagesize=A4); w, h = A4
    c.setFont("Helvetica-Bold", 18); c.drawCentredString(w/2, h-70, "SERVICE AGREEMENT")
    c.setFont("Helvetica", 11)
    lines = [
        'This Agreement is made between Horizon Labs Ltd. (the "Provider") and Cairo Logistics SAE (the "Client").',
        "",
        "Effective Date: 1 September 2026",
        "Contract Value: USD 48,000.00",
        "",
        "1. Services. The Provider will build and maintain a shipment-tracking platform for the Client.",
        "2. Payment. The Client shall pay the Contract Value in four equal quarterly instalments.",
        "3. Confidentiality. Both parties shall keep all project information confidential.",
        "4. Governing law. This Agreement is governed by the laws of the Arab Republic of Egypt.",
        "5. Term. The Agreement runs for twelve (12) months from the Effective Date.",
        "",
        "Signed by: Mona Adel, CEO, Horizon Labs Ltd.  /s/ Mona Adel",
        "Signed by: Tarek Samy, COO, Cairo Logistics SAE  /s/ Tarek Samy",
    ]
    y = h-120
    for l in lines:
        c.drawString(50, y, l); y -= 20
    c.save()

# ---------- 3. letter.pdf ----------
def letter_pdf():
    c = canvas.Canvas(f"{OUT}/letter_university.pdf", pagesize=A4); w, h = A4
    c.setFont("Helvetica-Bold", 14); c.drawString(50, h-70, "Nile Valley University - Admissions Office")
    c.setFont("Helvetica", 11)
    c.drawString(50, h-110, "Date: 5 October 2026")
    lines = ["Dear Mr. Karim Hassan,", "",
             "We are pleased to inform you that your application to the MSc in Data Science",
             "programme has been accepted. Classes begin on 15 January 2027.", "",
             "Please confirm your place by replying to this letter within two weeks.", "",
             "Kind regards,", "Dr. Laila Mansour", "Head of Admissions"]
    y = h-150
    for l in lines:
        c.drawString(50, y, l); y -= 20
    c.save()

# ---------- 4. receipt.jpg ----------
def receipt_jpg():
    img = Image.new("RGB", (520, 760), "white"); d = ImageDraw.Draw(img)
    f, fb = font("DejaVuSansMono.ttf", 22), font("DejaVuSansMono-Bold.ttf", 26)
    y = 30
    d.text((260, y), "CAIRO COFFEE HOUSE", font=fb, fill="black", anchor="ma"); y += 42
    d.text((260, y), "Tahrir Square, Cairo", font=f, fill="black", anchor="ma"); y += 30
    d.text((260, y), "RECEIPT #CC-88213", font=f, fill="black", anchor="ma"); y += 50
    for l in ["Date: 2026-10-02  14:32", "Cashier: Omar"]:
        d.text((30, y), l, font=f, fill="black"); y += 30
    y += 15; d.line((30, y, 490, y), fill="black", width=2); y += 15
    for it, p in (("2x Cappuccino", "60.00"), ("1x Cheesecake", "20.00"), ("1x Water", "6.50")):
        d.text((30, y), it, font=f, fill="black"); d.text((490, y), p, font=f, fill="black", anchor="ra"); y += 32
    y += 10; d.line((30, y, 490, y), fill="black", width=2); y += 15
    d.text((30, y), "TOTAL EGP", font=fb, fill="black"); d.text((490, y), "86.50", font=fb, fill="black", anchor="ra"); y += 45
    d.text((30, y), "VISA ****1234", font=f, fill="black"); y += 60
    d.text((260, y), "THANK YOU!", font=fb, fill="black", anchor="ma")
    img.save(f"{OUT}/receipt_cairo_coffee.jpg", quality=92)

# ---------- 5. poor-quality scanned invoice ----------
def invoice_scan_poor():
    img = Image.new("RGB", (900, 1100), "white"); d = ImageDraw.Draw(img)
    f, fb, fh = font("DejaVuSans.ttf", 26), font("DejaVuSans-Bold.ttf", 28), font("DejaVuSans-Bold.ttf", 46)
    d.text((60, 50), "Sphinx Office Supplies", font=fb, fill="black")
    d.text((840, 50), "INVOICE", font=fh, fill="black", anchor="ra")
    y = 170
    for l in ["Invoice No: SOS-5521", "Date: 03/04/2026", "Due Date: 03/05/2026"]:
        d.text((60, y), l, font=f, fill="black"); y += 40
    d.text((60, y+20), "Bill To:", font=fb, fill="black"); d.text((60, y+60), "Giza Print Shop", font=f, fill="black")
    y += 170
    for t, p in (("Printer paper A4 x 50", "$ 400.00"), ("Toner cartridges x 6", "$ 540.00")):
        d.text((60, y), t, font=f, fill="black"); d.text((840, y), p, font=f, fill="black", anchor="ra"); y += 46
    y += 30
    d.text((500, y), "Total Due:", font=fb, fill="black"); d.text((840, y), "$ 940.00", font=fb, fill="black", anchor="ra")
    # ink stain hides part of the total + "scan" damage
    stain = Image.new("RGBA", img.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(stain)
    sd.ellipse((560, y-25, 900, y+60), fill=(60, 40, 20, 235))
    img = Image.alpha_composite(img.convert("RGBA"), stain).convert("RGB")
    random.seed(7)
    px = img.load()
    for _ in range(60000):
        x, yy = random.randrange(img.width), random.randrange(img.height)
        v = random.randrange(0, 255); px[x, yy] = (v, v, v)
    img = img.filter(ImageFilter.GaussianBlur(1.7)).rotate(2.6, expand=True, fillcolor="white", resample=Image.BICUBIC)
    img = img.resize((600, 760))   # low resolution
    img.save(f"{OUT}/invoice_scan_poor_quality.jpg", quality=35)

# ---------- 6. unknown document ----------
def flyer_png():
    img = Image.new("RGB", (800, 500), (255, 235, 150)); d = ImageDraw.Draw(img)
    d.text((400, 120), "SUMMER SALE", font=font("DejaVuSans-Bold.ttf", 70), fill=(180, 30, 30), anchor="ma")
    d.text((400, 260), "Up to 50% off everything in store", font=font("DejaVuSans.ttf", 32), fill="black", anchor="ma")
    d.text((400, 340), "This weekend only - bring a friend!", font=font("DejaVuSans.ttf", 28), fill="black", anchor="ma")
    img.save(f"{OUT}/flyer_unknown.png")

if __name__ == "__main__":
    for fn in (invoice_pdf, contract_pdf, letter_pdf, receipt_jpg, invoice_scan_poor, flyer_png):
        fn(); print("created", fn.__name__)
