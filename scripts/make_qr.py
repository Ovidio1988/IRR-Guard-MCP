#!/usr/bin/env python3
import argparse
from pathlib import Path
import qrcode

p=argparse.ArgumentParser(description='Generate the public IRR Guard QR once the GitHub/Pages URL exists.')
p.add_argument('url')
p.add_argument('-o','--output',default='IRR_Guard_QR.png')
a=p.parse_args()
img=qrcode.make(a.url)
out=Path(a.output)
img.save(out)
print(out.resolve())
