# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""Floyd-Steinberg dither an image down to 2 or 3 colours.

The default output is an alpha mask: black ink on transparency, so CSS can paint it with
currentColor and one file serves both light and dark mode. Use --theme to bake the
colours in instead.
"""

import argparse
from pathlib import Path

from PIL import Image

# Ink, mid, paper.
THEMES = {
    "light": ("#000000", "#8a8a8a", "#ffffff"),
    "dark": ("#ece1d7", "#a98a78", "#292522"),
}
MASK_ALPHA = (255, 140, 0)


def paint(dithered, levels, colours):
    """Map each grey level in the dithered image onto an RGBA colour, darkest first."""
    nearest = [
        min(zip(levels, colours), key=lambda pair: abs(pair[0] - value))[1]
        for value in range(256)
    ]
    return Image.merge(
        "RGBA",
        [dithered.point([colour[channel] for colour in nearest]) for channel in range(4)],
    )


parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument("input", type=Path)
parser.add_argument("-o", "--output", type=Path, help="defaults to <input>-dither.png")
parser.add_argument("-n", "--colors", type=int, default=2, choices=(2, 3))
parser.add_argument("-w", "--width", type=int, default=900, help="0 keeps the original width")
parser.add_argument(
    "--theme",
    default="mask",
    choices=("mask", "light", "dark", "both"),
    help="mask writes an alpha mask; both writes a -light and a -dark file",
)
args = parser.parse_args()

source = Image.open(args.input).convert("L")
if args.width and args.width != source.width:
    height = round(source.height * args.width / source.width)
    source = source.resize((args.width, height), Image.Resampling.LANCZOS)

# Quantise to evenly spaced greys, darkest first, diffusing the error into the neighbours.
levels = [round(255 * step / (args.colors - 1)) for step in range(args.colors)]
palette_image = Image.new("P", (1, 1))
palette_image.putpalette([channel for level in levels for channel in (level,) * 3])
dithered = (
    source.convert("RGB")
    .quantize(palette=palette_image, dither=Image.Dither.FLOYDSTEINBERG)
    .convert("L")
)

output = args.output or args.input.with_name(f"{args.input.stem}-dither.png")

if args.theme == "mask":
    alphas = MASK_ALPHA if args.colors == 3 else (MASK_ALPHA[0], MASK_ALPHA[-1])
    paint(dithered, levels, [(0, 0, 0, alpha) for alpha in alphas]).save(output)
    print(output)
else:
    for theme in ("light", "dark") if args.theme == "both" else (args.theme,):
        swatches = THEMES[theme] if args.colors == 3 else THEMES[theme][::2]
        colours = [(*bytes.fromhex(swatch[1:]), 255) for swatch in swatches]
        path = output
        if args.theme == "both":
            path = output.with_name(f"{output.stem}-{theme}{output.suffix}")
        paint(dithered, levels, colours).save(path)
        print(path)
