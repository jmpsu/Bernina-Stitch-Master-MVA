#!/bin/bash

echo "=== StitchScale Level 3 ==="

read -p "Enter full path to SVG: " SVGFILE
[ ! -f "$SVGFILE" ] && echo "File not found." && exit 1

BASENAME=$(basename "$SVGFILE" .svg)

echo "Resize direction:"
echo "1) Bigger"
echo "2) Smaller"
read DIR

echo "Percentage (example 25 for 25%):"
read PCT

if [ "$DIR" == "1" ]; then
  FACTOR=$(echo "1 + $PCT/100" | bc -l)
else
  FACTOR=$(echo "1 - $PCT/100" | bc -l)
fi

NEWSVG="${BASENAME}_L3.svg"
TMPPES="/tmp/${BASENAME}_L3.pes"
FINALPES="${BASENAME}_L3.pes"

echo "Scaling geometry..."
inkscape "$SVGFILE" \
 --actions="select-all;transform-scale:$FACTOR,$FACTOR;export-filename:$NEWSVG;export-do" \
 >/dev/null 2>&1

echo "Rewriting Ink/Stitch spacing..."

python3 << END
import xml.etree.ElementTree as ET
import sys

svg="$NEWSVG"
factor=float("$FACTOR")

tree=ET.parse(svg)
root=tree.getroot()

for elem in root.iter():
    for attr in list(elem.attrib):
        if "row_spacing" in attr or "satin_spacing" in attr:
            val=float(elem.attrib[attr])
            if factor < 1:
                elem.attrib[attr]=str(round(val/factor,3))
            else:
                elem.attrib[attr]=str(round(val*factor,3))
        if "pull_compensation" in attr:
            val=float(elem.attrib[attr])
            elem.attrib[attr]=str(round(val*factor,3))

tree.write(svg)
print("XML spacing adjusted.")
END

echo "Generating stitches..."
inkscape "$NEWSVG" \
 --actions="inkstitch-output-pes;export-filename:$TMPPES;export-do" \
 >/dev/null 2>&1

echo "Pruning tiny stitches..."

python3 << END
from pyembroidery import EmbPattern
import math

pattern=EmbPattern()
pattern.read("$TMPPES")

min_len=1.2  # minimum stitch length in mm

new=[]
prev=None

for s in pattern.stitches:
    x,y,cmd=s
    if prev and cmd==0:
        dx=x-prev[0]
        dy=y-prev[1]
        dist=math.sqrt(dx*dx+dy*dy)/10
        if dist<min_len:
            continue
    new.append(s)
    prev=s

pattern.stitches=new
pattern.write("$FINALPES")
print("Micro stitches removed.")
END

echo "Done."
echo "Final file: $FINALPES"
