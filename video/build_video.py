import os, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont
W, H = 1920, 1080
D = os.path.dirname(os.path.abspath(__file__)); S = f"{D}/shots"; T = f"{D}/frames"; os.makedirs(T, exist_ok=True)
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"; FR = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
BLUE, INK, MUT, GREEN, AMB, RED = (37,99,235), (15,27,61), (100,112,138), (22,163,74), (217,119,6), (220,38,38)

def bg(): 
    im = Image.new("RGB", (W, H), (244,247,252)); return im, ImageDraw.Draw(im)
def title(d, t, sub=None):
    d.text((W//2, 110), t, font=f(FB, 64), fill=INK, anchor="mm")
    if sub: d.text((W//2, 185), sub, font=f(FR, 32), fill=MUT, anchor="mm")
def card(d, box, fill="white"): d.rounded_rectangle(box, 28, fill=fill)
def caption(im, text):
    ov = Image.new("RGBA", (W, 130), (10, 18, 45, 225)); im = im.convert("RGBA"); im.alpha_composite(ov, (0, H-130))
    d = ImageDraw.Draw(im); lines = textwrap.wrap(text, 95)[:2]
    y = H-130+65-(len(lines)-1)*22
    for l in lines: d.text((W//2, y), l, font=f(FR, 36), fill="white", anchor="mm"); y += 44
    return im.convert("RGB")
def shot(name, text):
    im = Image.open(f"{S}/{name}").convert("RGB").resize((W, H), Image.LANCZOS); return caption(im, text)

scenes = []   # (image, seconds)

# 1 title
im, d = bg()
d.text((W//2, 380), "DocInt", font=f(FB, 150), fill=BLUE, anchor="mm")
d.text((W//2, 540), "Multimodal Document Intelligence", font=f(FB, 72), fill=INK, anchor="mm")
d.text((W//2, 650), "PDF / image in  →  classified, extracted, validated, structured JSON out", font=f(FR, 38), fill=MUT, anchor="mm")
scenes.append((caption(im, "Demo guide: an AI app that understands documents and returns structured, validated results."), 5))

# 2 requirements
im, d = bg(); title(d, "The task: 5 requirements, 3 success criteria")
card(d, (120, 250, 940, 900)); card(d, (980, 250, 1800, 900), (236,250,242))
d.text((170, 300), "Requirements", font=f(FB, 44), fill=BLUE)
for i, t in enumerate(["File / image input", "Information extraction", "Classification + summary", "Structured output (JSON)", "Validation: missing / uncertain"]):
    d.text((170, 390+i*95), "✔  " + t, font=f("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38), fill=INK)
d.text((1030, 300), "Success criteria", font=f(FB, 44), fill=GREEN)
for i, t in enumerate(["Outputs consistent & structured", "Uncertain fields are labeled", "Limitations are documented"]):
    d.text((1030, 390+i*120), "✔  " + t, font=f("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38), fill=INK)
scenes.append((caption(im, "I built the app against every requirement and success criterion on the task slide."), 6))

# 3 architecture
im, d = bg(); title(d, "How it works", "One pipeline, two interchangeable engines")
boxes = [("1  Input", "PDF · JPG · PNG\nup to 20 MB", BLUE), ("2  Loader", "text layer or\npage images", BLUE),
         ("3  Engine", "Claude vision  OR\nLocal OCR + rules", (124,58,237)), ("4  Validation", "normalise · label\nmissing / uncertain", AMB), ("5  Output", "same JSON schema\nevery time", GREEN)]
x = 90
for i, (h, b, c) in enumerate(boxes):
    card(d, (x, 360, x+310, 700)); d.rounded_rectangle((x, 360, x+310, 440), 28, fill=c); d.rectangle((x, 410, x+310, 440), fill=c)
    d.text((x+155, 400), h, font=f(FB, 36), fill="white", anchor="mm")
    for j, l in enumerate(b.split("\n")): d.text((x+155, 530+j*50), l, font=f(FR, 31), fill=INK, anchor="mm")
    if i < 4: d.text((x+335, 530), "➜", font=f("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44), fill=MUT, anchor="mm")
    x += 360
d.text((W//2, 830), "Validation is shared by both engines, so results look identical whichever one ran.", font=f(FR, 34), fill=MUT, anchor="mm")
scenes.append((caption(im, "Every file goes through the same five steps. The validation layer is what makes the output trustworthy."), 9))

# demo scenes
scenes += [
 (shot("0_empty.png" if False else "00_empty.png", "The web UI: drop a file, optionally type questions, choose an engine."), 4),
 (shot("1a_ready.png", "Demo 1: a clean PDF invoice, with two questions."), 3),
 (shot("1b_result.png", "Type, customer, date, total and status extracted with high confidence. Green means OK; the questions are answered too."), 7),
 (shot("2b_result.png", "Demo 2: a photo of a receipt. Text is read with OCR, then the same fields come out in the same structure."), 6),
 (shot("3a_ready.png", "Demo 3: a bad scan. It is blurry, skewed, and an ink stain hides the total."), 4),
 (shot("3b_result.png", "The app does not pretend. Ambiguous date, damaged total and weak status are labeled 'uncertain', and the file is flagged 'Needs human review'."), 9),
 (shot("4b_result.png", "Demo 4: not a document type we support. It is classified 'unknown' and every question answers 'Not found'. No hallucinated values."), 7),
 (shot("1c_json.png", "Under the UI is a stable JSON schema: value, confidence and status for every field, plus issues and documented limitations."), 6),
]

# tests
im, d = bg(); title(d, "Automated tests", "12 tests: parsing, every sample file, schema consistency, mocked Claude call, API fallback")
card(d, (160, 250, 1760, 900), (13,20,40))
lines = [l.strip() for l in open(f"{D}/tests_out.txt") if l.strip()]
for i, l in enumerate(lines[:13]):
    col = (110,231,160) if l.endswith("ok") or l == "OK" else (214,226,255)
    d.text((210, 285+i*44), l[:110], font=f(FM, 28), fill=col)
scenes.append((caption(im, "Everything is tested, including the case where the Claude API fails and the app falls back to the local engine."), 6))

# limitations
im, d = bg(); title(d, "Limitations (documented, not hidden)")
card(d, (140, 250, 1780, 930))
lims = ["Local engine: English text only. Use the Claude engine for Arabic.", "Handwriting, stamps, heavy skew, low resolution → lower accuracy.",
        "4 document types modelled: invoice, receipt, contract, letter.", "Multi-page files: first 5 pages are analysed.",
        "Confidence scores are estimates, not calibrated probabilities.", "Claude engine was tested with a mocked API; add your key to use it live."]
for i, l in enumerate(lims):
    d.text((200, 310+i*100), "•  " + l, font=f(FR, 38), fill=INK)
scenes.append((caption(im, "Honest limits are part of the deliverable, and they are returned inside every JSON result."), 8))

# deliverables / run
im, d = bg(); title(d, "Deliverables & how to run")
card(d, (120, 250, 1800, 640)); 
for i, (t, c) in enumerate([("Code repository", BLUE), ("Sample files (6)", GREEN), ("Output examples (JSON)", AMB), ("Demo video", RED)]):
    x = 170 + i*410; d.rounded_rectangle((x, 300, x+370, 400), 24, fill=c); d.text((x+185, 350), t, font=f(FB, 32), fill="white", anchor="mm")
d.text((170, 470), "pip install -r requirements.txt", font=f(FM, 34), fill=INK)
d.text((170, 530), "python server.py        →  http://localhost:8000", font=f(FM, 34), fill=INK)
d.text((170, 590), "python cli.py samples/*.pdf -q \"What is the total?\"", font=f(FM, 34), fill=INK)
d.text((W//2, 780), "export ANTHROPIC_API_KEY=...   to switch on the Claude vision engine", font=f(FM, 32), fill=MUT, anchor="mm")
scenes.append((caption(im, "Install, run the server, upload a document. Set an API key and the same pipeline uses Claude vision."), 7))

# render
clips = []
for i, (im, sec) in enumerate(scenes):
    p = f"{T}/s{i:02d}.png"; im.save(p)
    c = f"{T}/s{i:02d}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", str(sec), "-i", p, "-vf",
                    f"scale=1920:1080,fade=t=in:st=0:d=0.4,fade=t=out:st={sec-0.4}:d=0.4,format=yuv420p", "-r", "30",
                    "-c:v", "libx264", "-crf", "20", c], check=True)
    clips.append(c)
open(f"{T}/list.txt", "w").write("".join(f"file '{c}'\n" for c in clips))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{T}/list.txt", "-c", "copy",
                f"{D}/demo_video.mp4"], check=True)
print("total seconds:", sum(s for _, s in scenes))
