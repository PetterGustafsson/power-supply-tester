from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import json

ROOT = Path(__file__).resolve().parents[1] / 'sources'
URLS = {
    'ADG4612.pdf': 'https://www.analog.com/media/en/technical-documentation/data-sheets/adg4612_4613.pdf',
    'ADS1115.pdf': 'https://www.ti.com/lit/ds/symlink/ads1115.pdf',
    'ISO1640.pdf': 'https://www.ti.com/lit/ds/symlink/iso1640.pdf',
    'R05C05TE05S.pdf': 'https://recom-power.com/pdf/Econoline/RxxC05TExxS.pdf',
    'TLV755P.pdf': 'https://www.ti.com/lit/ds/symlink/tlv755p.pdf',
    'TLV803E.pdf': 'https://www.ti.com/lit/ds/symlink/tlv803e.pdf',
    'BZT52H.pdf': 'https://assets.nexperia.com/documents/data-sheet/BZT52H_SER.pdf',
    'OPA320.pdf': 'https://www.ti.com/lit/ds/symlink/opa320.pdf',
    'PMEG2010ER.pdf': 'https://assets.nexperia.com/documents/data-sheet/PMEG2010ER.pdf',
    'waveshare-dimensions.webp': 'https://docs.waveshare.com/assets/images/Esp32-s3-lcd-1.28-003-25ce15c59f8b0362f62e7581d6ca464b.webp',
    'waveshare-pinout.webp': 'https://docs.waveshare.com/assets/images/Esp32-s3-lcd-1.28-002-1060238584bb3acf3d75d12f192b72e3.webp',
    'waveshare-schematic.pdf': 'https://files.waveshare.com/wiki/ESP32-S3-LCD-1.28/Esp32-s3-lcd-.128-sch.pdf',
}

def fetch(item):
    name, url = item
    if (ROOT/name).exists():return name,'cached'
    try:
        data = urlopen(url, timeout=30).read()
        if name.endswith('.pdf') and not data.startswith(b'%PDF'):
            raise ValueError('Response is not a PDF')
        (ROOT / name).write_bytes(data)
        return name, len(data)
    except Exception as exc:
        return name, str(exc)

if __name__ == '__main__':
    ROOT.mkdir(exist_ok=True)
    (ROOT / 'urls.json').write_text(json.dumps(URLS, indent=2) + '\n')
    for result in ThreadPoolExecutor(6).map(fetch, URLS.items()):
        print(result)
