# design

House style for web pages and slide decks, after the plainness of
[bactra.org/notebooks](https://bactra.org/notebooks/). Times New Roman, a single centred
column of left-aligned text, blue underlined links, and nothing else unless it earns its
place.

| File | What it is |
| --- | --- |
| `style.css` | The whole style: colour tokens, typography, tooltips, reveal-on-scroll, dithered ornaments. |
| `theme.js` | Runs the light/dark toggle. Load it synchronously in `<head>`. |
| `page.html` | Page template, filled with lorem ipsum. Copy it and replace the words. |
| `slides.css` | Slide-deck layer. Load after `style.css`. |
| `slides.html` | Deck template — same styling, one slide per screen, horizontal swipe. |
| `dither.py` | Turns a photo into a 2- or 3-colour dithered ornament. |
| `assets/` | Two sample ornaments, and the greyscale sources they came from. |

Open the templates over HTTP, not `file://` — the ornaments are CSS masks and browsers
refuse to load a mask from a `file://` origin, so they come out invisible:

```sh
python3 -m http.server -d design 8000   # then http://localhost:8000/page.html
```

## Colour

Light mode is white paper and black ink. Dark mode is
[melange](https://github.com/savq/melange-nvim).

|  | Light | Dark |
| --- | --- | --- |
| `--paper` | `#ffffff` | `#292522` |
| `--ink` | `#000000` | `#ece1d7` |
| `--muted` | `#55504b` | `#a98a78` |
| `--rule` | `#c9c4be` | `#403a36` |
| `--link` | `#0000ee` | `#a3a9ce` |
| `--visited` | `#551a8b` | `#cf9bc2` |

Links stay blue and underlined in both. The underline thickens on hover; that is the
whole hover treatment.

It follows `prefers-color-scheme` until someone touches the toggle in the top-right
corner, which sets `data-theme` on `<html>` and remembers the choice in `localStorage`.
The button is labelled with the theme it will switch *to*. Clearing the stored value
hands control back to the system:

```js
delete localStorage.theme;
```

Drop the `<button class="theme-toggle">` and the pages go back to following the system
only — `theme.js` does nothing when the button is absent.

The templates have no breadcrumb, since there is no index to point at. `page.html` keeps
the markup for one commented out at the top, and `.breadcrumb` is still styled: it sits at
the top-left of the viewport, outside the column, and takes over the top spacing when
present.

## Movement

Restraint is the point. There are three animations and no more:

- **Reveal.** Anything with `class="reveal"` fades and rises 8px as it scrolls into view,
  once. Use it on section headings, not on every paragraph.
- **Tooltip.** `<span class="tip" data-tip="…" tabindex="0">term</span>` — dotted
  underline, bubble on hover or keyboard focus. For an aside a reader can skip, not for
  anything they need.
- **Swipe.** Slides move horizontally over 480ms; the incoming slide's contents stagger in
  at 70ms apart.

All of it is off under `prefers-reduced-motion`, and the reveal is skipped entirely when
JavaScript does not run.

## Slides

Arrow keys, space, PageUp/PageDown, Home/End, the two arrow buttons, and a finger drag on
touch screens. Mouse dragging is deliberately not bound so text stays selectable. The URL
carries the slide number, so `slides.html#4` opens on slide 4.

Give a slide `class="slide slide--title"` to centre its contents.

## Dithered ornaments

```sh
uv run dither.py photo.jpg -o assets/orb.png -w 110
```

The default output is an **alpha mask** — black ink on transparency. Dropped into a page
as a mask, it takes whatever colour the text is, so one file works in both light and dark
mode:

```html
<div class="dither" style="--dither-src: url('assets/orb.png'); --dither-ratio: 1"></div>
```

Add `dither--header`, `dither--footer`, or `dither--wide` to size it. `--dither-ratio` is
the image's own aspect ratio.

Dithering only reads as dithering when the dots are visible, so generate small — `-w 110`
for something shown at 8rem — and let CSS scale it up. `.dither` sets
`image-rendering: pixelated`, which keeps the dots square instead of blurring them.

Other options:

| Flag | Effect |
| --- | --- |
| `-n 3` | Three tones instead of two. As a mask, the middle tone is a half-opaque ink. |
| `--theme light` / `dark` | Bake the palette in rather than emitting a mask. |
| `--theme both` | Write `-light.png` and `-dark.png`, for a `<picture>` with `prefers-color-scheme`. |
| `-w 0` | Keep the original width. |

The samples in `assets/` came from the greyscale gradients in `assets/src/`: a ball that
dissolves at the rim, and a rule of even thickness whose ink thins out towards both ends.
Keep any ornament's shading in one direction — a source that fades both across and down
dithers into a smudge rather than a shape.
