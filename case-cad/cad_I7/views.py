"""Re-render the 5 closed-case review views (I6 exterior: vents removed, grommet feet) with preview.py."""
import subprocess
BL = "/workspace/blender-4.2.3-linux-x64/blender"; O = "/workspace/psu-tester-case/cad_I7"; S = f"{O}/stl"
F = [f"{S}/I7_top_world.stl:D9D3C3", f"{S}/I7_base_world.stl:2A2A2C", f"{S}/I7_crown_world.stl:FF6A13", f"{S}/REF_cable_12pin_7mm.stl:111111",
     f"{S}/REF_grommet_foot_x4.stl:151515", f"{S}/REF_display_ESP32-S3-LCD-1.28.stl:1B2238"]
V = [("v_iso", -35, 28, 0.19), ("v_front", 0, 0, 0.158), ("v_side", 90, 0, 0.158), ("v_rear", 180, 0, 0.158), ("v_top", 0, 89.9, 0.135)]
for n, az, el, sc in V:
    look = "0,0,0.032" if n != "v_top" else "0,0,0"
    r = subprocess.run([BL, "-b", "-P", f"{O}/preview.py", "--", f"{O}/review/{n}.png", "1000", "800", str(az), str(el), str(sc), "1", look] + F, capture_output=True, text=True)
    print(n, "Saved" in r.stdout)
