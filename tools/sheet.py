"""Proof sheet: same lines at three weights, with guides."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proof import render_lines, stack
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lines = sys.argv[1].split('|')
size = float(sys.argv[2]) if len(sys.argv) > 2 else 96
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, 'proof', 'sheet.png')
masters = sys.argv[4].split(',') if len(sys.argv) > 4 else ['Thin', 'Regular', 'ExtraBold']
imgs = [render_lines(os.path.join(ROOT, 'build', 'test', f'test-{m}.ttf'), lines, size=size, guides=True) for m in masters]
stack(imgs, 4).save(out)
