"""RGB565 study of a connector approaching and seating in a port.

This is an optical presentation study, not a change to the contact geometry or
insertion sensing. The chrome and gold source SVGs have identical geometry.
"""

from pathlib import Path
import copy
import json
import math
import random
import subprocess
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
SIZE = 240
SUPER = 2
FPS = 50
DURATION = 10
SOURCE_SIZE = 2048
RING_RADIUS = 110.25
# The outermost pin seat ends near radius 49.4. Keep an undistorted central
# field beyond every seat, then ease the magnification down through the shell.
PLATEAU_RADIUS = 52.5
PINS = json.loads((OUT / 'geometry.json').read_text())['pin_centres_mm']
FONT_PATH = ROOT / 'assets/fonts/inter/Inter-opsz-wght.ttf'
ALLIED_PAIR = frozenset((1, 2))  # Temporary recognition pair for this study.
FLASH_STYLE = 'liquid'  # Study setting; one style is selected for the final art.
BAND_STYLE = 'reflected'  # Tapered enamel pockets over exposed machined metal.


def prepare_allied_mark():
    """Extract the red emblem without the supplied wordmark."""
    source = ET.parse(OUT / 'allied-vision-logo.svg').getroot()
    outlines = source.find(".//*[@id='Outlines_Col_Neg']")
    if outlines is None or not len(outlines) or not len(outlines[0]):
        raise ValueError('Allied Vision emblem was not found in the supplied SVG')
    outlines[0].remove(outlines[0][0])  # The first group is the wordmark.
    source.set('viewBox', '0 0 356 218')
    source.set('width', '356')
    source.set('height', '218')
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    mark_svg = OUT / 'allied-vision-mark.svg'
    mark_png = OUT / 'allied-vision-mark.png'
    mark_svg.write_bytes(ET.tostring(source, encoding='utf-8', xml_declaration=True))
    subprocess.run(('rsvg-convert', '-w', '712', '-h', '436',
                    '-o', str(mark_png), str(mark_svg)), check=True)
    return Image.open(mark_png).convert('RGBA')


ALLIED_MARK = prepare_allied_mark()


def source_pixels(name):
    rgba = np.asarray(Image.open(OUT / name).convert('RGBA'), dtype=np.float32) / 255
    rgba[:, :, :3] *= rgba[:, :, 3:4]
    return rgba


def prepare_orientation_sheen():
    """Rasterize just the five metal polarization keys for idle lighting."""
    source = copy.deepcopy(ET.parse(OUT / 'hr10a-10p-12p.svg').getroot())
    namespace = '{http://www.w3.org/2000/svg}'
    shell = source.find(".//*[@id='shell']")
    keys = source.find(".//*[@id='polarization-keys']")
    if shell is None or keys is None or len(keys) != 15:
        raise ValueError('Five polarization keys were not found in the connector SVG')
    for child in list(source):
        if child is not shell and child.tag != namespace + 'defs':
            source.remove(child)
    for child in list(shell):
        if child is not keys:
            shell.remove(child)
    gradient = ET.SubElement(source.find(namespace + 'defs'),
                             namespace + 'linearGradient',
                             {'id': 'orientation-orange', 'x1': '0', 'y1': '0',
                              'x2': '1', 'y2': '1'})
    for offset, color in (('0', '#ffe0a0'), ('.20', '#ff9a32'),
                          ('.46', '#a73c0a'), ('.71', '#ffb04b'),
                          ('1', '#69260b')):
        ET.SubElement(gradient, namespace + 'stop',
                      {'offset': offset, 'stop-color': color})
    for index, path in reversed(list(enumerate(keys))):
        if index % 3 == 0:
            # This foot is behind the inner collar in the original render.
            keys.remove(path)
        elif index % 3 == 1:
            path.set('fill', 'url(#orientation-orange)')
            path.set('opacity', '.97')
        else:
            path.set('fill', '#ffe3a1')
            path.set('opacity', '.98')
    result = OUT / 'connector-orientation-sheen-source.png'
    subprocess.run(('rsvg-convert', '-w', str(SOURCE_SIZE), '-h', str(SOURCE_SIZE),
                    '-o', str(result)),
                   input=ET.tostring(source, encoding='utf-8'), check=True)
    return result


prepare_orientation_sheen()
chrome = source_pixels('hr10a-10p-12p.png')
gold = source_pixels('hr10a-10p-12p-gold.png')
orientation_sheen = source_pixels('connector-orientation-sheen-source.png')
axis = (np.arange(SIZE * SUPER, dtype=np.float32) + .5) / SUPER - SIZE / 2
xx, yy = np.meshgrid(axis, axis)
rr = np.hypot(xx, yy)
aa = np.arctan2(yy, xx)


def annotation_layer():
    """Watch-dial-like numbers on the dark face, clear of every contact seat."""
    layer = Image.new('RGBA', (SIZE * SUPER, SIZE * SUPER))
    pen = ImageDraw.Draw(layer)
    face = ImageFont.truetype(str(FONT_PATH), 11 * SUPER)
    face.set_variation_by_axes([14, 640])

    def numeral(number, x, y):
        xy = (round(x * SUPER), round(y * SUPER))
        # An offset engraving shadow carries the numerals over shifting metal.
        pen.text((xy[0] + 1, xy[1] + 1), str(number), font=face,
                 anchor='mm', fill=(0, 0, 0, 170))
        pen.text(xy, str(number), font=face, anchor='mm',
                 fill=(235, 231, 215, 240))

    for number in range(1, 10):
        x_mm, y_mm = PINS[str(number)]
        angle = math.atan2(y_mm, x_mm)
        numeral(number, 120 + 80 * math.cos(angle),
                120 + 80 * math.sin(angle))
    # The three inner contacts need their own clear pockets between seats.
    for number, x, y in ((10, 120, 65), (11, 80, 145), (12, 160, 145)):
        numeral(number, x, y)
    return np.asarray(layer, dtype=np.float32) / 255


ANNOTATIONS = annotation_layer()
STATIC_WARPS = {}
QUIET_FRAMES = {}
ORIENTATION_GLOWS = {}

# The accepted 1/2 pair is shown in the primary preview. A second still below
# demonstrates an arbitrary other powered pair. Live pins belong to telemetry.
NEGATIVE_PIN = 1
POSITIVE_PIN = 2
DEMO_VOLTAGE = '12.03 V'
CONNECTED_PINS = {
    int(number): (120 + 15 * .94 * point[0], 120 + 15 * .94 * point[1])
    for number, point in PINS.items()
}


def bolt_points(start, end, rng, roughness=1., arch=0.):
    x0, y0 = start
    x1, y1 = end
    length = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / length, (x1 - x0) / length
    steps = max(8, round(length / 5))
    points = []
    for i in range(steps + 1):
        t = i / steps
        offset = 0 if i in (0, steps) else (
            arch + rng.uniform(-4.5, 4.5) * roughness) * math.sin(math.pi * t)
        points.append((x0 + (x1 - x0) * t + nx * offset,
                       y0 + (y1 - y0) * t + ny * offset))
    return points


def storm_events():
    rng = random.Random(20261022)
    events = []
    start = 4.025
    while start < 5.91:
        duration = rng.uniform(.16, .26)
        arch = rng.uniform(-12, 14)
        main = bolt_points(CONNECTED_PINS[NEGATIVE_PIN],
                           CONNECTED_PINS[POSITIVE_PIN], rng, arch=arch)
        forks = []
        if rng.random() < .84:
            first = rng.randrange(2, len(main) // 2)
            last = rng.randrange(len(main) // 2 + 1, len(main) - 2)
            forks.append(bolt_points(main[first], main[last], rng, .85,
                                     rng.choice((-7, 7))))
        if rng.random() < .35:
            forks.append(bolt_points(CONNECTED_PINS[NEGATIVE_PIN],
                                     CONNECTED_PINS[POSITIVE_PIN], rng, .7,
                                     -arch * .6))
        events.append((start, duration, main, forks))
        start += rng.uniform(.055, .085)
    return events


STORM_EVENTS = storm_events()


def polarity_layer():
    layer = Image.new('RGBA', (SIZE * SUPER, SIZE * SUPER))
    pen = ImageDraw.Draw(layer)
    face = ImageFont.truetype(str(FONT_PATH), 9 * SUPER)
    face.set_variation_by_axes([14, 750])
    for pin, sign in ((NEGATIVE_PIN, '−'), (POSITIVE_PIN, '+')):
        x, y = CONNECTED_PINS[pin]
        pen.text((round(x * SUPER), round(y * SUPER)), sign, font=face,
                 anchor='mm', fill=(13, 26, 34, 250))
    return np.asarray(layer, dtype=np.float32) / 255


POLARITY = polarity_layer()


def logo_layer():
    accepted = frozenset((NEGATIVE_PIN, POSITIVE_PIN)) == ALLIED_PAIR
    mark = ALLIED_MARK.resize((34 * SUPER, 21 * SUPER),
                             Image.Resampling.LANCZOS)
    if not accepted:
        # Keep a trace of the original red under the disabled silver finish.
        gray = Image.new('RGBA', mark.size, (160, 138, 137, 0))
        gray.putalpha(mark.getchannel('A').point(lambda value: round(value * .58)))
        cross = Image.new('RGBA', mark.size)
        pen = ImageDraw.Draw(cross)
        margin = 3 * SUPER
        w, h = mark.size
        pen.line(((margin, margin), (w - margin, h - margin)),
                 fill=(202, 174, 172, 150), width=SUPER)
        pen.line(((margin, h - margin), (w - margin, margin)),
                 fill=(202, 174, 172, 150), width=SUPER)
        mark = Image.alpha_composite(gray, cross)
    canvas = Image.new('RGBA', (SIZE * SUPER, SIZE * SUPER))
    cx = 120 * SUPER
    cy = 203 * SUPER  # Six o'clock on the black enamel band.
    canvas.alpha_composite(mark, (round(cx - mark.width / 2),
                                  round(cy - mark.height / 2)))
    rgba = np.asarray(canvas, dtype=np.float32) / 255
    glow = np.asarray(canvas.getchannel('A').filter(
        ImageFilter.GaussianBlur(3.2 * SUPER)), dtype=np.float32) / 255
    if not accepted:
        glow *= .14
    return rgba, glow


LOGO, LOGO_GLOW = logo_layer()


def voltage_masks():
    """Oversized seven-segment characters tracking the outer black bezel."""
    mask = Image.new('L', (SIZE * SUPER, SIZE * SUPER))
    pen = ImageDraw.Draw(mask)
    segments = {
        'a': ((-2.0, -3.8), (2.0, -3.8)),
        'b': ((2.4, -3.3), (2.4, -.5)),
        'c': ((2.4, .5), (2.4, 3.3)),
        'd': ((-2.0, 3.8), (2.0, 3.8)),
        'e': ((-2.4, .5), (-2.4, 3.3)),
        'f': ((-2.4, -3.3), (-2.4, -.5)),
        'g': ((-2.0, 0), (2.0, 0)),
    }
    numerals = {
        '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd',
        '4': 'fgbc', '5': 'afgcd', '6': 'afgcde', '7': 'abc',
        '8': 'abcdefg', '9': 'abcdfg',
    }
    widths = {'.': 2.7, ' ': 3.4, 'V': 6.6}
    size = 3.0
    tracking = .85 * size
    advance = [widths.get(character, 6.7) * size
               for character in DEMO_VOLTAGE]
    total = sum(advance) + tracking * (len(advance) - 1)
    along = -total / 2
    radius = 83.0

    for character, width in zip(DEMO_VOLTAGE, advance):
        offset = along + width / 2
        angle = -math.pi / 2 + offset / radius
        cx = 120 + radius * math.cos(angle)
        cy = 120 + radius * math.sin(angle)
        tangent = (-math.sin(angle), math.cos(angle))
        inward = (-math.cos(angle), -math.sin(angle))

        def point(x, y):
            return (round((cx + size * (x * tangent[0] + y * inward[0])) * SUPER),
                    round((cy + size * (x * tangent[1] + y * inward[1])) * SUPER))

        if character in numerals:
            for segment in numerals[character]:
                a, b = segments[segment]
                pen.line((point(*a), point(*b)), fill=255, width=6)
        elif character == '.':
            x, y = point(0, 3.4)
            pen.ellipse((x - 3, y - 3, x + 3, y + 3), fill=255)
        elif character == 'V':
            pen.line((point(-2.3, -3.6), point(0, 3.7),
                      point(2.3, -3.6)), fill=255, width=6,
                     joint='curve')
        along += width + tracking

    core = np.asarray(mask, dtype=np.float32) / 255
    edge = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.0 * SUPER)),
                      dtype=np.float32) / 255
    glow = np.asarray(mask.filter(ImageFilter.GaussianBlur(3.2 * SUPER)),
                      dtype=np.float32) / 255
    return core, edge, glow


VOLTAGE_CORE, VOLTAGE_EDGE, VOLTAGE_GLOW = voltage_masks()


def voltage_readout(image, opacity, storm):
    # A restrained emerald phosphor sits in the black insert, with a small
    # crystalline lift on flashes. The actual reading must come from telemetry.
    shimmer = 1 + min(.25, storm * .07)
    image += VOLTAGE_GLOW[:, :, None] * np.array((.10, .40, .17)) * opacity * shimmer * 1.6
    image += VOLTAGE_EDGE[:, :, None] * np.array((.26, .74, .40)) * opacity * shimmer * .8
    image += VOLTAGE_CORE[:, :, None] * np.array((.73, 1., .73)) * opacity * shimmer * .8
    return image


def polarity_halos(image, opacity):
    # Two restrained enamel-like halos identify the energized pair without
    # recoloring the brass contacts or the rest of the connector.
    for pin, color in ((NEGATIVE_PIN, (.16, .55, 1.)),
                       (POSITIVE_PIN, (1., .24, .20))):
        x, y = CONNECTED_PINS[pin]
        distance = np.hypot(xx - (x - 120), yy - (y - 120))
        haze = np.exp(-.5 * ((distance - 9.) / 4.2) ** 2)
        fine = np.exp(-.5 * ((distance - 8.5) / 1.05) ** 2)
        strength = np.clip(opacity * (.12 * haze + .50 * fine), 0, .62)
        image = image * (1 - strength[:, :, None]) + \
            np.array(color, dtype=np.float32) * strength[:, :, None]
    return image


def storm_level(seconds):
    return sum(math.sin(math.pi * (seconds - start) / duration) ** .45
               for start, duration, _, _ in STORM_EVENTS
               if start < seconds < start + duration)


def lightning(image, seconds):
    level = storm_level(seconds)
    if not level:
        return image
    # A fleeting blue room flash gives the branching bolts an atmospheric lift.
    room = min(1., level / 3.) * np.exp(-.5 * (rr / 57) ** 4)
    image += room[:, :, None] * np.array((.065, .16, .28), dtype=np.float32)
    shape = (SIZE * SUPER, SIZE * SUPER)
    bolt = Image.new('L', shape)
    forks = Image.new('L', shape)
    pen = ImageDraw.Draw(bolt)
    branch_pen = ImageDraw.Draw(forks)
    for start, duration, path, branches in STORM_EVENTS:
        phase = (seconds - start) / duration
        if not 0 < phase < 1:
            continue
        power = math.sin(math.pi * phase) ** .45
        coords = [(round(x * SUPER), round(y * SUPER)) for x, y in path]
        pen.line(coords, fill=round(255 * power), width=2 * SUPER, joint='curve')
        for point in (coords[0], coords[-1]):
            radius = round(3 * SUPER)
            pen.ellipse((point[0] - radius, point[1] - radius,
                         point[0] + radius, point[1] + radius),
                        fill=round(255 * power))
        for branch in branches:
            branch_pen.line([(round(x * SUPER), round(y * SUPER))
                             for x, y in branch],
                            fill=round(175 * power), width=SUPER, joint='curve')
    united = np.maximum(np.asarray(bolt, dtype=np.float32),
                        np.asarray(forks, dtype=np.float32)) / 255
    mask = Image.fromarray((united * 255).astype(np.uint8), 'L')
    halo = np.asarray(mask.filter(ImageFilter.GaussianBlur(5 * SUPER)),
                      dtype=np.float32) / 255
    electric = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.15 * SUPER)),
                          dtype=np.float32) / 255
    # Blue atmospheric glow, then a saturated cyan sheath and near-white core.
    image += halo[:, :, None] * np.array((.12, .39, .96), dtype=np.float32) * 1.7
    image += electric[:, :, None] * np.array((.40, .78, 1.), dtype=np.float32) * 1.2
    image += united[:, :, None] * np.array((.94, .99, 1.), dtype=np.float32) * 1.3
    return np.clip(image, 0, 1)


def polarity_ooze(image, seconds, opacity, style=None):
    """A cool-to-gold current flowing from the negative to positive contact."""
    style = style or FLASH_STYLE
    settings = {
        # wobble, body width, side droplets, envelope radius
        'ribbon': (1.0, 2.7, 6, 4.6),
        'liquid': (3.0, 5.8, 20, 7.2),
        'filament': (3.4, 1.8, 20, 3.5),
    }
    wobble, breadth, sparkle_count, halo_radius = settings[style]
    x0, y0 = CONNECTED_PINS[NEGATIVE_PIN]
    x1, y1 = CONNECTED_PINS[POSITIVE_PIN]
    length = max(1., math.hypot(x1 - x0, y1 - y0))
    dx, dy = (x1 - x0) / length, (y1 - y0) / length
    nx, ny = -dy, dx
    cycle = seconds % 1
    outward = 1 if nx * ((x0 + x1) / 2 - 120) + ny * ((y0 + y1) / 2 - 120) >= 0 else -1
    arch = outward * min(13., length * .17)

    def point(u, side=0):
        envelope = max(0., math.sin(math.pi * u))
        ripple = envelope * (arch +
            wobble * math.sin(2 * math.pi * (u * 1.4 - cycle)) +
            .22 * wobble * math.sin(2 * math.pi * (u * 3.8 + cycle * 2)))
        return ((x0 + dx * length * u + nx * (ripple + side)) * SUPER,
                (y0 + dy * length * u + ny * (ripple + side)) * SUPER)

    def metal_mix(u, warmth=0):
        # The travelling front heats from ice blue to polished yellow gold.
        warm = smoothstep((u - .13 + warmth * .12) / .64)
        cold = np.array((.18, .70, 1.), dtype=np.float32)
        gold = np.array((1., .50 + .20 * warmth, .08 + .08 * warmth),
                        dtype=np.float32)
        return tuple(round(v * 255) for v in cold * (1-warm) + gold * warm)

    def scale_color(color, value):
        return tuple(round(channel * value) for channel in color)

    shape = (SIZE * SUPER, SIZE * SUPER)
    luminous = Image.new('RGB', shape)
    sharp = Image.new('RGB', shape)
    gleam = Image.new('RGB', shape)
    pool = ImageDraw.Draw(luminous)
    pen = ImageDraw.Draw(sharp)
    star_pen = ImageDraw.Draw(gleam)

    # Fine enamel channel remains after each stroke. It bends around the pins
    # that sit between a widely separated powered pair.
    for i in range(48):
        u, v = i / 48, (i + 1) / 48
        color = metal_mix((u + v) / 2)
        pool.line((point(u), point(v)), fill=scale_color(color, .48),
                  width=round(3.2 * SUPER))
        pen.line((point(u), point(v)), fill=scale_color(color, .64),
                 width=round(1.4 * SUPER))

    head = smoothstep(cycle)
    fade = smoothstep(cycle / .07) * (1-smoothstep((cycle-.88)/.10))
    tail = max(0., head - (.46 if style == 'filament' else .80))
    head_warmth = smoothstep((head-.20)/.58)
    if style == 'liquid':
        # Two uneven, narrower tongues peel off the main stream and rejoin at
        # its leading edge. They give the flash a molten, oozing silhouette.
        for sign, delay in ((1, .05), (-1, .12)):
            branch_head = max(0., head-delay)
            branch_tail = max(0., branch_head-.55)
            for i in range(40):
                u = branch_tail+(branch_head-branch_tail)*i/40
                v = branch_tail+(branch_head-branch_tail)*(i+1)/40
                if v <= u:
                    continue
                strength = fade * (.28+.72*(i+1)/40)
                spread = sign * (3.5+2.3*math.sin(2*math.pi*(u*1.3-cycle))) * math.sin(math.pi*u)
                p0 = point(u, spread)
                p1 = point(v, spread)
                color = metal_mix((u+v)/2, head_warmth)
                pool.line((p0,p1), fill=scale_color(color, strength*.75),
                          width=round(5.0*SUPER))
                pen.line((p0,p1), fill=scale_color(color, strength*.94),
                         width=round(2.2*SUPER))
    for i in range(64):
        u = tail + (head-tail) * i / 64
        v = tail + (head-tail) * (i + 1) / 64
        if v <= u:
            continue
        fraction = (i + .5) / 64
        taper = (.25 + .75 * smoothstep(fraction)) * fade
        color = metal_mix((u + v) / 2, head_warmth)
        diameter = max(1, round(breadth * (.55 + .65 * fraction) * SUPER))
        segment = (point(u), point(v))
        pool.line(segment, fill=scale_color(color, taper * .83),
                  width=diameter + 4 * SUPER)
        pen.line(segment, fill=scale_color(color, taper * 1.22), width=diameter)
        # A hairline specular streak makes the current look liquid and metallic.
        if fraction > .57:
            star_pen.line(segment, fill=scale_color(
                (255, 245, 174) if u > .35 else (185, 235, 255),
                taper * .55), width=SUPER)
    hx, hy = point(head)
    flare_color = (255, 206, 76) if head > .38 else (140, 216, 255)
    flare_size = (16.5 if style == 'liquid' else 5.7) * (0.7 + .3 * fade) * SUPER
    flare_cross = flare_size * (.68 if style == 'liquid' else .43)
    # Long, fine specular flares travel with the molten front. A perpendicular
    # gold streak catches the eye without turning the pin into a white disc.
    star_pen.line((hx-nx*flare_size, hy-ny*flare_size,
                   hx+nx*flare_size*.71, hy+ny*flare_size*.71),
                  fill=scale_color(flare_color, fade), width=SUPER)
    star_pen.line((hx-dx*flare_cross, hy-dy*flare_cross,
                   hx+dx*flare_cross*.66, hy+dy*flare_cross*.66),
                  fill=scale_color(flare_color, fade*.78), width=SUPER)
    pool.ellipse((hx-5*SUPER, hy-5*SUPER, hx+5*SUPER, hy+5*SUPER),
                 fill=scale_color(flare_color, fade*.48))
    r = (1.6 + 1.0 * fade) * SUPER
    star_pen.ellipse((hx-r, hy-r, hx+r, hy+r),
                     fill=metal_mix(head, 1.))
    r = .75 * SUPER
    star_pen.ellipse((hx-r, hy-r, hx+r, hy+r),
                     fill=(255, 240, 177) if head > .35 else (218, 244, 255))

    # The charge breaks into a directional gold fan when it reaches +. The
    # longest streak points away from the contact, never around its edge.
    arrival = smoothstep((head-.67)/.29) * fade
    if arrival > .001 and style == 'liquid':
        px, py = point(1.)
        burst = (255, 193, 56)
        for forward, sideways, gain, width in (
                (32., 0., 1., 1.9), (24., 15., .92, 1.4),
                (25., -14., .83, 1.3), (11., 21., .73, 1.1),
                (12., -20., .68, 1.1)):
            ex = px + (dx*forward+nx*sideways)*SUPER
            ey = py + (dy*forward+ny*sideways)*SUPER
            star_pen.line((px+dx*2*SUPER, py+dy*2*SUPER, ex, ey),
                          fill=scale_color(burst, arrival*gain),
                          width=max(1,round(width*SUPER)))
        pool.ellipse((px-10*SUPER,py-10*SUPER,px+10*SUPER,py+10*SUPER),
                     fill=scale_color(burst,arrival*.75))
        r=2.7*SUPER
        star_pen.ellipse((px-r,py-r,px+r,py+r),
                         fill=scale_color((255,240,161),arrival))
        # Tiny fragments advance beyond the receiving pin like gold filings.
        for index in range(12):
            advance = 5 + index*2.35 + 2.0*math.sin(cycle*7+index*2.2)
            side = math.sin(index*4.17)*(.35*advance+3.0)
            sx = px+(dx*advance+nx*side)*SUPER
            sy = py+(dy*advance+ny*side)*SUPER
            glint = arrival * (.45+.55*max(0.,math.sin(cycle*13+index*1.9))**3)
            radius = (.7+(index%4==0)*.8)*SUPER
            star_pen.ellipse((sx-radius,sy-radius,sx+radius,sy+radius),
                             fill=scale_color((255,218,93),glint))

    # Individual gold fragments trail outward; their tiny asymmetric strokes
    # make the direction legible even when the two pins are close together.
    for i in range(sparkle_count):
        u = head - .035 - i * (.39 / sparkle_count)
        if u <= 0:
            continue
        side = (-1 if i % 2 else 1) * (8.5 + (i % 5) * 3.0)
        sx, sy = point(u, side)
        twinkle = (.28 + .72 * max(0., math.sin(2*math.pi*(cycle*3.7+i*.273)))**4) * fade
        if twinkle < .06:
            continue
        color = metal_mix(u, .95)
        radius = (2.0 + 5.0 * twinkle + (1.8 if style == 'liquid' else 0)) * SUPER
        star_pen.line((sx-radius, sy, sx+radius*.54, sy),
                      fill=scale_color(color, twinkle), width=SUPER)
        star_pen.line((sx, sy-radius*.65, sx, sy+radius),
                      fill=scale_color(color, twinkle*.85), width=SUPER)
        r = .65 * SUPER
        star_pen.ellipse((sx-r, sy-r, sx+r, sy+r),
                         fill=scale_color((255, 244, 186), twinkle))

    # A small colour catch on each contact signals the ends without drawing
    # rings around them or washing out the brass faces.
    for u, gain in ((0, .25), (1, .40)):
        px, py = point(u)
        contact_color = metal_mix(u, head_warmth)
        r = 2.2 * SUPER
        pool.ellipse((px-r, py-r, px+r, py+r),
                     fill=scale_color(contact_color, gain * fade))

    luminous = luminous.filter(ImageFilter.GaussianBlur(halo_radius * SUPER))
    sharp_halo = sharp.filter(ImageFilter.GaussianBlur(.95 * SUPER))
    # A moving reflection brushes the neighbouring enamel and makes the cold
    # to warm travel visible at 240 pixels.
    head_x, head_y = hx / SUPER - 120, hy / SUPER - 120
    atmosphere_radius = 17 if style == 'liquid' else 11
    atmospheric = np.exp(-.5 * (((xx-head_x)/atmosphere_radius)**2 +
                                   ((yy-head_y)/atmosphere_radius)**2))
    image += atmospheric[:, :, None] * np.array(metal_mix(head, 1.),
             dtype=np.float32)[None, None, :] / 255 * opacity * fade * .28
    image += np.asarray(luminous, dtype=np.float32) / 255 * opacity * .74
    image += np.asarray(sharp_halo, dtype=np.float32) / 255 * opacity * .55
    image += np.asarray(sharp, dtype=np.float32) / 255 * opacity * 1.05
    image += np.asarray(gleam, dtype=np.float32) / 255 * opacity * 1.05
    if style == 'liquid' and arrival > .001:
        # The arriving flash briefly gilds the machined collars, as though a
        # warm light has filled the room. This makes the tiny contact event
        # register across the whole watch-like object without a screen wash.
        incident_angle = math.atan2(y1-120, x1-120)
        angle_delta = np.arctan2(np.sin(aa-incident_angle),
                                 np.cos(aa-incident_angle))
        beam = np.exp(-.5*(angle_delta/.43)**2)
        collars = (np.exp(-.5*((rr-62.5)/8.5)**2) +
                   .75*np.exp(-.5*((rr-100.5)/6.0)**2))
        image += (beam*collars*arrival*opacity)[:, :, None] * \
                 np.array((.60, .29, .055), dtype=np.float32)
    return np.clip(image, 0, 1)


def double_helix(image, seconds, opacity):
    """White-hot electrical ribbons with rotating spectral discharge."""
    if frozenset((NEGATIVE_PIN, POSITIVE_PIN)) != ALLIED_PAIR:
        return image
    x0, y0 = CONNECTED_PINS[NEGATIVE_PIN]
    x1, y1 = CONNECTED_PINS[POSITIVE_PIN]
    length = math.hypot(x1 - x0, y1 - y0)
    direction = ((x1 - x0) / length, (y1 - y0) / length)
    normal = (-direction[1], direction[0])
    strands = ([], [])
    depths = ([], [])
    samples = 72
    for index in range(samples + 1):
        u = -.16 + 1.32 * index / samples
        taper = max(0, math.sin(math.pi * index / samples)) ** .65
        phase = 2 * math.pi * (1.28 * index / samples + seconds)
        for strand, sign in enumerate((1, -1)):
            depth = sign * math.sin(phase)
            displacement = 7.5 * sign * math.cos(phase) * taper * (1 + .17 * depth)
            parallax = 1.7 * depth * taper
            x = (x0 + (x1 - x0) * u +
                 normal[0] * displacement + direction[0] * parallax)
            y = (y0 + (y1 - y0) * u +
                 normal[1] * displacement + direction[1] * parallax)
            strands[strand].append((round(x * SUPER), round(y * SUPER)))
            depths[strand].append(depth)

    cycle = seconds % 1
    warmth = math.sin(math.pi * cycle) ** 2
    layer = Image.new('RGBA', (SIZE * SUPER, SIZE * SUPER))
    pen = ImageDraw.Draw(layer)
    back = ((30, 73, 153, 210), (95, 42, 149, 215))
    turn = cycle * 360
    for pin, color, offset in ((NEGATIVE_PIN, (169, 238, 255), 0),
                               (POSITIVE_PIN, (255, 155, 128), 180)):
        px, py = CONNECTED_PINS[pin]
        radius = 9.1 * SUPER
        bounds = ((px * SUPER - radius, py * SUPER - radius),
                  (px * SUPER + radius, py * SUPER + radius))
        start = turn + offset
        pen.arc(bounds, start, start + 90, fill=color + (245,), width=4)
        tip = math.radians(start + 72)
        tx = round((px + 9.1 * math.cos(tip)) * SUPER)
        ty = round((py + 9.1 * math.sin(tip)) * SUPER)
        pen.ellipse((tx - 3, ty - 3, tx + 3, ty + 3),
                    fill=(255, 255, 255, 245))
    for strand in range(2):
        for index in range(samples):
            depth = (depths[strand][index] + depths[strand][index + 1]) / 2
            if depth < 0:
                pen.line((strands[strand][index], strands[strand][index + 1]),
                         fill=back[strand], width=5)
    for index in range(9, samples-3, 9):
        rung_flash = .5 + .5 * math.sin(2*math.pi*(cycle*4 + index/27))
        color = (180, 244, 236) if index % 2 else (194, 157, 255)
        pen.line((strands[0][index], strands[1][index]),
                 fill=color + (round(125 + 100*rung_flash),),
                 width=2*SUPER if rung_flash > .67 else SUPER)
    for strand in range(2):
        for index in range(samples):
            depth = (depths[strand][index] + depths[strand][index + 1]) / 2
            if depth >= 0:
                segment = (strands[strand][index], strands[strand][index + 1])
                spectrum = 2*math.pi*(cycle*3 + index/23 + strand*.37)
                violet = .5 + .5*math.sin(spectrum)
                green = .5 + .5*math.sin(spectrum + 2*math.pi/3)
                blue = .5 + .5*math.sin(spectrum + 4*math.pi/3)
                sheath = (round(75 + 100*violet + 70*blue),
                          round(95 + 125*green + 40*blue),
                          round(170 + 75*violet + 10*blue))
                pen.line(segment, fill=sheath + (245,), width=10)
                flash = max(0, math.sin(2*math.pi*(cycle*7 + index/17 + strand*.29))) ** 7
                core = (255,
                        round(235 + 20*flash + 9*warmth*flash),
                        round(240 + 15*flash - 15*warmth*flash))
                pen.line(segment, fill=core + (round(218 + 37*depth),), width=5)
    nearest = 0 if depths[0][samples // 2] >= depths[1][samples // 2] else 1
    gx, gy = strands[nearest][samples // 2]
    pen.ellipse((gx - 4, gy - 4, gx + 4, gy + 4),
                fill=(255, 255, 255, 255))

    # Green, violet and briefly warm white fragments drift off the helix.
    for i, index in enumerate((11, 19, 29, 39, 51, 61)):
        pulse = max(0, math.sin(2*math.pi*(cycle*5 + i*.37))) ** 5
        if pulse < .04:
            continue
        strand = i % 2
        sx, sy = strands[strand][index]
        reach = (4 + 7*pulse) * SUPER
        side = -1 if i % 3 else 1
        ex = round(sx + normal[0]*reach*side + direction[0]*3*SUPER)
        ey = round(sy + normal[1]*reach*side + direction[1]*3*SUPER)
        fragment = ((179, 255, 190), (197, 145, 255), (221, 247, 255))[i % 3]
        if i == 5:
            fragment = (255, round(220 + 22*(1-warmth)), round(211 + 35*(1-warmth)))
        pen.line(((sx, sy), (ex, ey)), fill=fragment + (round(230*pulse),), width=3)
        radius = round((1.5 + 1.5*pulse)*SUPER)
        pen.ellipse((ex-radius, ey-radius, ex+radius, ey+radius),
                    fill=fragment + (round(255*pulse),))

    rgba = np.asarray(layer, dtype=np.float32) / 255
    halo = np.asarray(layer.getchannel('A').filter(
        ImageFilter.GaussianBlur(3.4 * SUPER)), dtype=np.float32) / 255
    image += halo[:, :, None] * np.array((.075, .12, .21)) * opacity * 2.1
    alpha = rgba[:, :, 3:4] * opacity
    return image * (1 - alpha) + rgba[:, :, :3] * alpha


def source_warp(name, source, seated, scale, magnification):
    if seated not in (0., 1.):
        return warp(source, scale, magnification)
    key = (name, seated)
    if key not in STATIC_WARPS:
        STATIC_WARPS[key] = warp(source, scale, magnification)
    return STATIC_WARPS[key]


def bilinear(image, u, v):
    u = np.clip(u, 0, SOURCE_SIZE - 1.001)
    v = np.clip(v, 0, SOURCE_SIZE - 1.001)
    x0 = u.astype(np.int32)
    y0 = v.astype(np.int32)
    fx = (u - x0)[:, :, None]
    fy = (v - y0)[:, :, None]
    top = image[y0, x0] * (1 - fx) + image[y0, x0 + 1] * fx
    bottom = image[y0 + 1, x0] * (1 - fx) + image[y0 + 1, x0 + 1] * fx
    return top * (1 - fy) + bottom * fy


def warp(image, scale, magnification):
    # A flat-magnification disc keeps every pin and seat the same relative size.
    # The smooth shoulder outside that disc compresses only the surrounding
    # shell; the rim follows the full-part scale as it moves into the port.
    radii = np.linspace(0, 256, 4097, dtype=np.float32)
    shoulder = np.clip((radii - PLATEAU_RADIUS) /
                       (RING_RADIUS - PLATEAU_RADIUS), 0, 1)
    shoulder = 1 - shoulder * shoulder * (3 - 2 * shoulder)
    projected = scale * radii * (1 + (magnification - 1) * shoulder)
    assert np.all(np.diff(projected) > 0), 'Optical shoulder folded over'
    src_radius = np.interp(rr, projected, radii).astype(np.float32)
    stretch = src_radius / np.maximum(rr, .001) * (SOURCE_SIZE / SIZE)
    u = SOURCE_SIZE / 2 + xx * stretch
    v = SOURCE_SIZE / 2 + yy * stretch
    return bilinear(image, u, v)


def smoothstep(value):
    value = max(0., min(1., value))
    return value * value * (3 - 2 * value)


def idle_orientation_sheen(image, seconds, seated, scale, magnification):
    """Warm crown-coloured light catches the five rotation-locating keys."""
    visibility = 1 - smoothstep(seated / .78)
    if visibility <= 0:
        return image
    keys = source_warp('orientation', orientation_sheen,
                       seated, scale, magnification)
    phase = 2 * math.pi * (seconds / 2.8)
    beam_angle = -math.pi / 2 + phase
    delta = np.arctan2(np.sin(aa - beam_angle), np.cos(aa - beam_angle))
    beam = np.exp(-.5 * (delta / .30) ** 2)
    brightness = (.86 + .31 * beam) * visibility
    opacity = np.clip(keys[:, :, 3] * brightness, 0, 1)
    image = image * (1 - opacity[:, :, None]) + keys[:, :, :3] * brightness[:, :, None]

    glow_key = round(seated, 6)
    if glow_key not in ORIENTATION_GLOWS:
        mask = Image.fromarray(np.uint8(np.clip(keys[:, :, 3], 0, 1) * 255), 'L')
        ORIENTATION_GLOWS[glow_key] = np.asarray(mask.filter(
            ImageFilter.GaussianBlur(2.2 * SUPER)), dtype=np.float32) / 255
    halo = ORIENTATION_GLOWS[glow_key]
    image += halo[:, :, None] * (0.60 + .40*beam[:, :, None]) * \
             np.array((.17, .043, .008)) * visibility
    return image


def seat_progress(seconds):
    if seconds < 3:
        return 0.
    if seconds < 4:
        return smoothstep(seconds - 3)
    if seconds < 6:
        return 1.
    if seconds < 7:
        return 1 - smoothstep(seconds - 6)
    return 0.


def warm_light(seconds):
    # Two uneven passes: a gold-lit room is briefly reflected by the chrome.
    value = 0.
    for start, length, direction in ((.6, 2.0, 1), (7.45, 2.0, -1)):
        p = (seconds - start) / length
        if 0 < p < 1:
            envelope = math.sin(math.pi * p) ** 1.2
            centre = (-1.4 + 2.8 * p) if direction == 1 else (2.6 - 2.4 * p)
            delta = np.arctan2(np.sin(aa - centre), np.cos(aa - centre))
            beam = np.exp(-.5 * (delta / .62) ** 2)
            value = np.maximum(value, envelope * (.32 + .57 * beam))
    return value


def port_background(progress):
    # A fixed recessed port becomes visible as the connector recedes into it.
    base = np.zeros((*rr.shape, 3), dtype=np.float32)
    recess = np.exp(-.5 * ((rr - 105.5) / 10.5) ** 2)
    rim = np.exp(-.5 * ((rr - 106.6) / 1.75) ** 2)
    fine = np.exp(-.5 * ((rr - 111.4) / .72) ** 2)
    angular = .58 + .42 * np.cos(aa + .85) ** 2
    base += recess[:, :, None] * np.array((.085, .094, .10))
    base += rim[:, :, None] * angular[:, :, None] * np.array((.27, .30, .31))
    base += fine[:, :, None] * np.array((.24, .26, .27))
    # The port exists throughout the shot; the near connector hides it.
    return base


def port_lip(image, progress):
    if progress <= 0:
        return image
    # At full seating the forward edge hides the last millimetres of knurl,
    # reading as a metal lip in front of the connector instead of a flat zoom.
    shadow = np.exp(-.5 * ((rr - 99.7) / 2.15) ** 2) * progress
    lip = np.exp(-.5 * ((rr - 104.9) / 2.0) ** 2) * progress
    glint = np.exp(-.5 * ((rr - 104.7) / .64) ** 2) * progress
    shade = np.array((.025, .031, .034), dtype=np.float32)
    metal = np.array((.24, .27, .28), dtype=np.float32)
    sparkle = (.65 + .35 * np.cos(aa + .78) ** 2)[:, :, None]
    image = image * (1 - shadow[:, :, None] * .65) + shade * shadow[:, :, None] * .65
    image = image * (1 - lip[:, :, None] * .8) + metal * sparkle * lip[:, :, None] * .8
    image += glint[:, :, None] * sparkle * .23
    return image


def display_band(image, opacity, seconds):
    # The readouts live on dark enamel pockets while exposed sides show the
    # machined annulus beneath. The edge rails keep the pieces visually joined.
    inner = np.clip((rr - 69.7) / 2.0, 0, 1)
    outer = np.clip((96.2 - rr) / 2.0, 0, 1)
    coverage = inner * outer * opacity
    enamel = np.array((.020, .030, .031), dtype=np.float32)
    if BAND_STYLE == 'solid':
        veil = .94
        pocket = None
    else:
        def lobe(center, core, taper):
            distance = np.abs(np.arctan2(np.sin(aa-center), np.cos(aa-center)))
            t = np.clip((distance-core)/taper, 0, 1)
            return 1-t*t*(3-2*t)

        voltage_pocket = lobe(-math.pi/2, .81, .45)
        logo_pocket = lobe(math.pi/2, .30, .56)
        pocket = np.maximum(voltage_pocket, logo_pocket)
        base = .39 if BAND_STYLE == 'smoked' else .11
        veil = base + (.95-base)*pocket
    alpha = coverage * veil
    image = image * (1-alpha[:, :, None]) + enamel * alpha[:, :, None]
    if BAND_STYLE == 'reflected':
        # A narrow moving room reflection rolls over the exposed metal. It is
        # suppressed under the black readout pockets to keep both marks clear.
        sweep = -.24 + .16*math.sin(seconds*2*math.pi)
        right = np.exp(-.5*(np.arctan2(np.sin(aa-sweep),
                                       np.cos(aa-sweep))/.26)**2)
        left = np.exp(-.5*(np.arctan2(np.sin(aa-math.pi+.30),
                                      np.cos(aa-math.pi+.30))/.32)**2)
        glint = (right+.55*left)*(1-pocket)*coverage
        middle = np.exp(-.5*((rr-83.2)/5.6)**2)
        image += (glint*middle)[:, :, None] * np.array((.22,.26,.27))
    edge = (np.exp(-.5 * ((rr - 69.9) / .62) ** 2) +
            np.exp(-.5 * ((rr - 96.0) / .68) ** 2)) * opacity
    image += edge[:, :, None] * np.array((.23, .25, .25))
    return image


def powered_roughness_masks():
    """Small physical scuffs on the machined rings, absent in the idle pose."""
    size = (SIZE * SUPER, SIZE * SUPER)
    bright = Image.new('L', size)
    shadow = Image.new('L', size)
    glint_pen = ImageDraw.Draw(bright)
    cut_pen = ImageDraw.Draw(shadow)
    rng = random.Random(1731)
    for index in range(48):
        radius = rng.choice((60.8, 63.5, 66.2, 98.9, 101.5, 104.2))
        angle = rng.uniform(-math.pi, math.pi)
        span = rng.uniform(.025, .075) * rng.choice((-1, 1))
        tilt = rng.uniform(-.6, .6)
        points = []
        shade_points = []
        for step in range(5):
            fraction = step / 4
            a = angle + span * fraction
            r = radius + tilt * (fraction - .5)
            points.append((round((120 + r * math.cos(a)) * SUPER),
                           round((120 + r * math.sin(a)) * SUPER)))
            shade_points.append((round((120 + (r + .7) * math.cos(a)) * SUPER),
                                 round((120 + (r + .7) * math.sin(a)) * SUPER)))
        cut_pen.line(shade_points, fill=rng.randrange(75, 135), width=SUPER)
        glint_pen.line(points, fill=rng.randrange(65, 125), width=SUPER)
    return (np.asarray(bright, dtype=np.float32) / 255,
            np.asarray(shadow, dtype=np.float32) / 255)


ROUGH_GLINT, ROUGH_CUT = powered_roughness_masks()


def powered_material(image, seconds, opacity):
    # Polished idle metal becomes harder and more tactile under grazing blue
    # and garnet light. The marks stay fixed on the metal as the light shifts.
    first = CONNECTED_PINS[NEGATIVE_PIN]
    second = CONNECTED_PINS[POSITIVE_PIN]
    angle = math.atan2((first[1] + second[1]) / 2 - 120,
                       (first[0] + second[0]) / 2 - 120)
    delta = np.arctan2(np.sin(aa - angle), np.cos(aa - angle))
    ice = np.exp(-.5 * (delta / .48) ** 2)
    garnet = np.exp(-.5 * (np.arctan2(np.sin(aa - angle - 1.05),
                                     np.cos(aa - angle - 1.05)) / .55) ** 2)
    metal = (np.exp(-.5 * ((rr - 63.) / 4.8) ** 2) +
             np.exp(-.5 * ((rr - 101.) / 5.1) ** 2))
    flicker = .86 + .14 * math.sin(seconds * 6 * math.pi) ** 2
    image += opacity * flicker * metal[:, :, None] * (
        ice[:, :, None] * np.array((.055, .16, .24)) +
        garnet[:, :, None] * np.array((.17, .047, .039)))
    image *= 1 - ROUGH_CUT[:, :, None] * opacity * .35
    image += ROUGH_GLINT[:, :, None] * opacity * np.array((.13, .16, .16))

    # Two very brief exposure jolts punctuate seating. The held powered image
    # remains crisp so the pin positions, helix and readout can be inspected.
    impact = (math.exp(-.5 * ((seconds - 3.96) / .023) ** 2) +
              .48 * math.exp(-.5 * ((seconds - 4.08) / .026) ** 2))
    if impact > .001:
        centre = np.exp(-.5 * (rr / 65.) ** 4)
        image += centre[:, :, None] * np.array((.48, .67, .75)) * impact * opacity
    return image


def rgb565(image):
    pixels = np.clip(image * 255, 0, 255).astype(np.uint16)
    red = pixels[:, :, 0] >> 3
    green = pixels[:, :, 1] >> 2
    blue = pixels[:, :, 2] >> 3
    return np.stack((red * 255 // 31, green * 255 // 63,
                     blue * 255 // 31), axis=2).astype(np.uint8)


def frame_at(seconds):
    seated = seat_progress(seconds)
    warmth = warm_light(seconds)
    matched_pair = frozenset((NEGATIVE_PIN, POSITIVE_PIN)) == ALLIED_PAIR
    storm = 0
    # Seat and release traverse the same optical path in opposite directions.
    # Reuse identical unlit frames; idle and connected holds reuse their warp.
    frame_key = round(seated, 6)
    flash_active = seated > .78
    idle_sheen_active = seated < .78
    if (not np.any(warmth) and not storm and not flash_active and
            not idle_sheen_active and frame_key in QUIET_FRAMES):
        return QUIET_FRAMES[frame_key]
    scale = 1.065 - .125 * seated
    magnification = 1.40 - .40 * seated
    cool = source_warp('chrome', chrome, seated, scale, magnification)
    if np.any(warmth):
        warm = source_warp('gold', gold, seated, scale, magnification)
        # The gold source differs only on the machined shell. Pins stay brass.
        cool = cool * (1 - warmth[:, :, None]) + warm * warmth[:, :, None]
    image = cool[:, :, :3] + port_background(seated) * (1 - cool[:, :, 3:4])
    image = port_lip(image, seated)
    image = idle_orientation_sheen(image, seconds, seated, scale, magnification)
    polarity_alpha = smoothstep((seated - .78) / .22)
    if polarity_alpha > 0:
        image = display_band(image, polarity_alpha, seconds)
        image = powered_material(image, seconds, polarity_alpha)
    # Labels belong only to the close-up resting state. They disappear early
    # in the seating travel, before the powered effects would take the stage.
    label_alpha = 1 - smoothstep(seated / .55)
    if label_alpha > 0:
        alpha = ANNOTATIONS[:, :, 3:4] * label_alpha
        image = image * (1 - alpha) + ANNOTATIONS[:, :, :3] * alpha
    if polarity_alpha > 0:
        image = polarity_ooze(image, seconds, polarity_alpha)
        alpha = POLARITY[:, :, 3:4] * polarity_alpha
        image = image * (1 - alpha) + POLARITY[:, :, :3] * alpha
        image = voltage_readout(image, polarity_alpha, storm)
        glow_color = ((.36, .042, .025) if matched_pair else
                      (.32, .045, .025))
        image += LOGO_GLOW[:, :, None] * np.array(glow_color) * polarity_alpha
        logo_alpha = LOGO[:, :, 3:4] * polarity_alpha
        image = image * (1 - logo_alpha) + LOGO[:, :, :3] * logo_alpha
    image = np.clip(image, 0, 1)
    small = Image.fromarray((image * 255).astype(np.uint8), 'RGB').resize(
        (SIZE, SIZE), Image.Resampling.LANCZOS)
    frame = Image.fromarray(rgb565(np.asarray(small, dtype=np.float32) / 255), 'RGB')
    if not np.any(warmth) and not storm and not flash_active and not idle_sheen_active:
        QUIET_FRAMES[frame_key] = frame
    return frame


def select_preview_pair(negative, positive):
    """Switch the illustrated measurement without moving any physical pins."""
    global NEGATIVE_PIN, POSITIVE_PIN, STORM_EVENTS, POLARITY, LOGO, LOGO_GLOW
    NEGATIVE_PIN, POSITIVE_PIN = negative, positive
    STORM_EVENTS = storm_events()
    POLARITY = polarity_layer()
    LOGO, LOGO_GLOW = logo_layer()
    QUIET_FRAMES.clear()


def build_previews():
    frames = []
    for index in range(FPS * DURATION):
        frames.append(frame_at(index / FPS))
        if index % 24 == 0:
            print(f'frame {index}/{FPS * DURATION}', flush=True)

    frames[0].save(OUT / 'connector-wide-idle-240.png', optimize=True)
    frames[80].save(OUT / 'connector-warm-reflection-240.png', optimize=True)
    frames[200].save(OUT / 'connector-connected-240.png', optimize=True)
    frames[175].save(OUT / 'connector-seating-240.png', optimize=True)
    frames[200].save(OUT / 'connector-allied-pair-240.png', optimize=True)
    frames[275].save(OUT / 'connector-allied-helix-240.png', optimize=True)
    frames[0].save(OUT / 'connector-optics-240.webp', save_all=True,
                   append_images=frames[1:], duration=1000 // FPS,
                   loop=0, lossless=True, method=1)
    frames[250].save(OUT / 'connector-allied-helix-240.webp', save_all=True,
                     append_images=frames[251:300], duration=1000 // FPS,
                     loop=0, lossless=True, method=1)

    # Shared GIF palette avoids static metal colour changes caused by per-frame
    # palette selection. WebP remains the colour-accurate animation master.
    sheet = Image.new('RGB', (SIZE * 5, SIZE * 3))
    for i, frame_index in enumerate((0, 80, 175, 200, 205, 210, 215, 220,
                                     225, 230, 235, 245, 260, 280, 420)):
        sheet.paste(frames[frame_index], ((i % 5) * SIZE, (i // 5) * SIZE))
    palette = sheet.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE)
               for frame in frames]
    indexed[0].save(OUT / 'connector-optics-240.gif', save_all=True,
                    append_images=indexed[1:], duration=1000 // FPS,
                    loop=0, optimize=True, disposal=2)
    frames[0].save(OUT / 'connector-orange-datums-idle-240.webp', save_all=True,
                   append_images=frames[1:140], duration=1000 // FPS,
                   loop=0, lossless=True, method=1)
    indexed[0].save(OUT / 'connector-orange-datums-idle-240.gif', save_all=True,
                    append_images=indexed[1:140], duration=1000 // FPS,
                    loop=0, optimize=True, disposal=2)
    indexed[250].save(OUT / 'connector-allied-helix-240.gif', save_all=True,
                      append_images=indexed[251:300], duration=1000 // FPS,
                      loop=0, optimize=True, disposal=2)
    detail = [frame.crop((72, 65, 128, 121)).resize((336, 336),
              Image.Resampling.NEAREST) for frame in indexed[250:300]]
    detail[0].save(OUT / 'connector-allied-helix-detail.gif', save_all=True,
                   append_images=detail[1:], duration=1000 // FPS,
                   loop=0, optimize=True, disposal=2)
    logo_detail = [frame.crop((96, 183, 144, 222)).resize((384, 312),
                   Image.Resampling.NEAREST) for frame in indexed[250:300]]
    logo_detail[0].save(OUT / 'connector-allied-logo-detail.gif', save_all=True,
                        append_images=logo_detail[1:], duration=1000 // FPS,
                        loop=0, optimize=True, disposal=2)

    # A different powered pair demonstrates the muted, crossed logo and retains
    # the full between-pin thunderstorm from the earlier visual study.
    select_preview_pair(3, 7)
    other_frames = [frame_at(index / FPS) for index in range(200, 300)]
    other_frames[0].save(OUT / 'connector-allied-other-pair-240.png', optimize=True)
    storm_peak = max(range(100), key=lambda i: storm_level((200 + i) / FPS))
    other_frames[storm_peak].save(OUT / 'connector-thunderstorm-240.png', optimize=True)
    other_frames[storm_peak].save(OUT / 'connector-allied-other-pair-storm-240.png',
                                  optimize=True)
    other_frames[0].save(OUT / 'connector-thunderstorm-240.webp', save_all=True,
                         append_images=other_frames[1:], duration=1000 // FPS,
                         loop=0, lossless=True, method=1)
    storm_sheet = Image.new('RGB', (SIZE * 3, SIZE * 2))
    for i, frame_index in enumerate((0, 12, 25, 38, storm_peak, 75)):
        storm_sheet.paste(other_frames[frame_index],
                          ((i % 3) * SIZE, (i // 3) * SIZE))
    storm_palette = storm_sheet.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    storm_indexed = [frame.quantize(palette=storm_palette,
                                    dither=Image.Dither.NONE)
                     for frame in other_frames]
    storm_indexed[0].save(OUT / 'connector-thunderstorm-240.gif', save_all=True,
                          append_images=storm_indexed[1:], duration=1000 // FPS,
                          loop=0, optimize=True, disposal=2)
    comparison = Image.new('RGB', (SIZE * 3 + 24, SIZE), (0, 0, 0))
    comparison.paste(frames[0], (0, 0))
    comparison.paste(frames[275], (SIZE + 12, 0))
    comparison.paste(other_frames[storm_peak], (SIZE * 2 + 24, 0))
    comparison.save(OUT / 'connector-idle-powered-study.png', optimize=True)
    print('Wrote 240 x 240 RGB565 optical seating study and keyframes')


if __name__ == "__main__":
    build_previews()
