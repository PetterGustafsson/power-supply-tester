from PIL import Image, ImageDraw, ImageFont
D = "/workspace/psu-tester-case/cad_I9/_b7"; FP = "/usr/share/fonts/truetype/sand-box/google/Poppins/Poppins-"
fb, fr = ImageFont.truetype(FP + "Medium.ttf", 26), ImageFont.truetype(FP + "Regular.ttf", 19)
P = [("trench_top", "A  Base alone, top view", "One tie station at the trench mid-length (y -18.65; walls run y -45.3 to +8.0).\nBlind bed pocket under the jacket (gap in the ribs) and blind head pocket at +x."),
     ("trench_sec", "B  Section at the tie plane, base alone", "3.0 x 1.6 slots through both walls at mid-height (z 4.4-6.0),\ninner-wall grooves down to the bed pocket. Floor left under pockets 1.2; underside flat."),
     ("trench_sec_tie", "C  Same section with jacket and tie", "Band: head -> +x slot -> groove -> under the jacket -> -x slot -> over the top -> head.\nTie top z 10.8, 2.15 below the J1/J2 THT pin tips."),
     ("trench_tie", "D  Tie in place", "2.5 mm tie, head on the tray floor right of the +x wall.\nCores run beside the trench (0.38 from the tie).")]
W, H, CAP = 1200, 1000, 130
out = Image.new("RGB", (2*W, 2*(H + CAP)), (236, 236, 232)); d = ImageDraw.Draw(out)
for i, (f, t, s) in enumerate(P):
    x, y = (i % 2)*W, (i//2)*(H + CAP)
    out.paste(Image.open(f"{D}/{f}.png").convert("RGB"), (x, y))
    d.text((x + 30, y + H + 14), t, font=fb, fill=(26, 26, 28)); d.multiline_text((x + 30, y + H + 52), s, font=fr, fill=(60, 60, 64), spacing=6)
out.save("/workspace/psu-tester-case/renders/I7b_zip_trench.png"); print("saved")
