# Hirose HR10A-10P-12P(73) — UI artwork

Original, orthographic SVG illustration of the **male cable plug viewed from its mating face**. Main polarization key is at 12 o'clock. Transparent background. No external images, fonts, JavaScript or raster textures in the SVG.

## Files

- `hr10a-10p-12p.svg`: clean artwork, 1024 × 1024 viewBox, scalable.
- `hr10a-10p-12p-numbered.svg`: same artwork with pin numbers.
- Corresponding `.png` files: 2048 × 2048 transparent raster exports.
- `geometry.json`: all twelve pin centers and coordinate convention.
- `preview-dark.png`: preview on a dark UI background.

## Geometry and materials

Sources inspected on 2026-09-15:

1. [Hirose product and technical downloads](https://www.hirose.com/product/p/CL0110-0401-7-73).
2. [Hirose mechanical drawing EDC-010386-73-73, revision 4 dated 2025-04-25](https://www.hirose.com/en/product/document?clcode=CL0110-0401-7-73&documentid=0000959181&documenttype=2DDrawing&lang=en&productname=HR10A-10P-12P%2873%29&series=HR10).
3. [Hirose HR10 catalog](https://docs.rs-online.com/0992/0900766b8136356c.pdf), printed page 193 for the contact center dimensions. The catalog's wiring-side plug view is mirrored horizontally to match the mating-side view in the part-specific drawing.
4. Manufacturer's simplified STEP model, document 0001221236S, used to inspect concentric shell proportions and the asymmetric key layout. It omits individual contacts.

Nominal maximum shell diameter: **14.7 mm** (drawing tolerance ±0.5 mm). SVG scale: 64 units/mm; center at (512,512). Shell radii referenced from simplified CAD: 7.35, 6.9, 6.3, 5.5, 5.15, 4.75, 4.55 and 3.85 mm. Five keys, with the wider key at top and the lower key offset toward the right. CAD axes projected as x and negative z.

Materials from the exact part drawing: matte nickel-plated zinc-alloy/brass shell, black polyamide insulator, and silver-plated brass contacts. The visible contact color is intentionally silver, not gold. The drawing specifies a minimum 2 μm silver plating for the relevant contact parts.

## Accuracy limits

This is a UI illustration, not a certified CAD projection, metrology result or manufacturing drawing. The pin centers and mating-side numbering follow Hirose's documents. Pin-tip shape/diameter, molded contact seats, knurl count, minute bevels and optical texture are artistic approximations. The 0.6 mm displayed pin diameter is an illustration parameter, not a verified solder-contact mating diameter. Fine surface reflections are independent vector artwork. Lighting cannot represent a physical material across all environments.

The STEP archive has manufacturer restrictions on commercial use, redistribution and modification. It is retained as a local reference, not included as a deliverable asset. If this illustration will be distributed commercially as a CAD-derived product representation, check the manufacturer's applicable permissions. No blanket license for Hirose source material is implied.

## UI integration

Use either SVG directly as an image for a static connector. To address individual pins, inline the SVG into the DOM. Each contact has a stable ID and a `data-pin` attribute:

```js
const connector = document.querySelector('svg');
connector.querySelector('#pin-3').setAttribute('data-active', 'true');
connector.style.setProperty('--pin-highlight', '#6bd5ee');
```

Each pin includes a `<title>` for identification. Add application-appropriate keyboard handlers and button semantics if contacts become controls. All IDs, including gradient IDs, should be prefixed when inserting multiple inline copies in the same document. PNG exports preserve transparency.

Rebuild with `python3 scripts/build_connector.py` from the project root. `scripts/render.cjs` renders PNG previews using the installed Sharp package.
