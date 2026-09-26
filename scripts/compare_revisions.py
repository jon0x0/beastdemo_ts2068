"""Create a labeled visual comparison from the captured emulator frames."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1]
current=json.loads((root/'build/manifest.json').read_text());revision=current['revision']
previous_root=root/f'revisions/rev{revision-1:02d}'
previous=json.loads((previous_root/'build/manifest.json').read_text())
def preview(folder,manifest):
    tag=manifest.get('tag',f"aqueduct_tides_rev{manifest['revision']:02d}")
    return folder/'build'/(tag+('_frame0.png' if manifest['revision']>=6 else '.png'))
out=Image.new('RGB',(1040,430),(15,18,27));d=ImageDraw.Draw(out)
font=ImageFont.load_default(size=15)
for x,source,title in [
    (0,preview(previous_root,previous),f"REV {revision-1:02d} / {previous['name']}"),
    (528,preview(root,current),f"REV {revision:02d} / {current['name']}")]:
    d.text((x+5,8),title,font=font,fill=(228,235,247))
    out.paste(Image.open(source).resize((512,384),Image.Resampling.NEAREST),(x,38))
out.save(root/f'build/comparison_rev{revision-1:02d}_rev{revision:02d}.png')
