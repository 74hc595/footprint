#!/usr/bin/env python
# Matt Sarnoff - October 14, 2014 - msarnoff.org
"""
Example footprint definitions using the `footprint` library.
(http://github.com/74hc595/footprint)
"""

from footprint import *

# Through-hole USB micro-B connector
# http://www.newark.com/global-connector-technology/usb3130-30-a/micro-usb-2-0-b-connector-5pos/dp/73T7896
with Footprint("USB3130") as f:
  pins = f.add_pins(5, x=0, y=0, dx=0.65*mm, dy=(1*mm, -1*mm), hole=0.4*mm, diameter=0.8*mm)
  p3 = pins[2]
  p2 = pins[1]
  s1 = f.add_pin(x=p3.x-3.575*mm, y=p2.y-0.78*mm, hole=1.35*mm, diameter=1.95*mm, number="")
  s2 = f.add_pin(base=s1, x=p3.x+3.575*mm)
  f.mark(p3)



# Surface-mount USB micro-B connector
# http://www.newark.com/global-connector-technology/usb3140-30-0170-1-c/connector-usb-2-0-micro-b-rcpt/dp/72W0922
with Footprint("USB3140") as f:
  pads = f.add_pads(5, x=0, y=0, dx=0.65*mm, width=0.4*mm, height=1.5*mm)
  p3 = pads[2]
  p1 = pads[0]
  s1 = f.add_pin(x=p3.x-(7.15*mm)*0.5, y=p1.top+1.64*mm, hole=1.15*mm, diameter=1.55*mm, number="")
  s2 = f.add_pin(base=s1, x=p3.x+(7.15*mm)*0.5)
  f.mark(p3)



# Surface-mount 12mm coin cell battery holder
# http://www.mouser.com/ProductDetail/Linx-Technologies/BAT-HLD-012-SMT/?qs=sGAEpiMZZMtT9MhkajLHrtLdadThLjMVSNg%2f9RTE5Tg%3d
with Footprint("BAT-HLD-012-SMT") as f:
  pl = f.add_pad(width=100, height=200, x=0, y=0, name="+", number=1)
  pr = f.add_pad(width=pl.width, height=pl.height, x=pl.left+700, y=pl.y, name="+", number=1)
  m = f.add_pad(width=350, height=350, x=between(pl.x, pr.x), y=pl.y, name="-", number=2, round=True)
  s = f.add_arc(m.x, m.y, diameter=400)
  f.mark(m)
