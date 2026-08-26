---
name: design-deck
description: "Builds a slide deck in the house style — Times New Roman on white, melange in dark mode, one slide per screen, horizontal swipe. Use whenever the user wants slides, a deck, a presentation, a talk, a pitch or a lightning talk, and whenever they mention the house style, the slides template or design/. Prefer this over reaching for reveal.js, Marp or a Google Slides export."
---

# House-style deck

A deck is the page style laid out one screen at a time. Same typeface, same six colours,
same restraint — the only additions are the horizontal swipe and a staggered entry for
each slide's contents. The template already has all of it. Your job is to replace its
words, not to redesign it.

For a prose page, use `design-page` instead.

## Build it

Below, `<skill>` is this skill's own directory and `<out>` is where the document is
going.

1. **Copy the template into the output directory.** Everything the deck needs travels with
   it, so it can be zipped, moved or served from anywhere.

   ```sh
   mkdir -p <out>
   cp -R <skill>/assets/. <out>/
   ```

   That gives `<out>/slides.html`, `style.css`, `slides.css`, `theme.js` and
   `assets/{orb,band}.png`. `slides.css` loads after `style.css` — keep that order.

2. **Replace the lorem ipsum, one `<section class="slide">` at a time.** Duplicate or
   delete whole sections to get the count you need. Each slide's contents live inside its
   `.slide-inner`; that wrapper is what the stagger animation walks, so do not remove it.

3. **Serve it over HTTP and click through it, in both themes.** The ornaments are CSS masks
   and browsers refuse to load a mask from a `file://` origin, so opening the file directly
   shows an invisible ornament and hides real breakage.

   ```sh
   python3 -m http.server -d <out> 8000   # then http://localhost:8000/slides.html
   ```

   Walk the deck with the arrow keys, then toggle the theme and walk it again.

## The parts

| Part | What it is |
| --- | --- |
| `.slide` | One screen. Contents sit at the top, reading down. |
| `.slide--title` | Same slide, contents centred. For the opener, the closer, and section breaks. |
| `.slide-inner` | The wrapper inside every slide. Its direct children are what stagger in. |
| `.muted` | The quiet line — a date under the title, an attribution under a quotation. |
| `.tip` | `<span class="tip" data-tip="…" tabindex="0">term</span>`. Works on slides, but a deck rarely needs one — you are there to say the aside out loud. |
| `.deck-nav` | The two arrows and the `n / total` counter. |
| `.deck-progress` | The bar along the bottom. |
| `.theme-toggle` | Delete it and the deck follows the system only. |

The script at the bottom of the body counts the slides, binds the keys, drives the swipe
and writes the slide number into the URL. It reads the deck out of the DOM, so adding and
removing sections needs no change to it. Leave it alone.

## Navigation

Arrow keys, space, PageUp/PageDown, Home/End, the two arrow buttons, and a finger drag on
touch screens. Mouse dragging is deliberately unbound so text stays selectable.

The URL carries the slide number — `slides.html#4` opens on slide 4. Useful for pointing
someone at one slide, and for going straight back to the slide you are working on.

## Rules

- **One idea per slide.** A slide that needs a scrollbar is two slides. If the prose does
  not fit, it is speaker notes, not a slide.
- **One typeface.** Times New Roman, from `--serif`. No second font, no Google Fonts link.
- **Six colours.** `--paper`, `--ink`, `--muted`, `--rule`, `--link`, `--visited`, defined
  for both themes in `style.css`. Any colour you write by hand will be wrong in one theme
  or the other.
- **Do not edit `style.css` or `slides.css`.** If a slide needs something they have no
  class for, the slide usually needs less on it. When something really is missing, add a
  rule at the bottom of the copied `slides.css` built from the existing tokens, and say so.
- **Movement is already spent.** The swipe is 480ms and the incoming slide's children
  stagger 70ms apart — that is the deck's entire animation budget. Do not add a transition,
  a build or a click-to-reveal. All of it is off under `prefers-reduced-motion`.
- **No `.reveal` on slides.** It is a scrolling effect; a deck does not scroll. The stagger
  does that job.

## Ornaments

The two in `assets/` are samples — a sphere and a band. To make one from a photo:

```sh
uv run <skill>/scripts/dither.py photo.jpg -o <out>/assets/orb.png -w 110
```

The default output is an alpha mask, black ink on transparency, so one file takes the text
colour and works in both themes. Drop it into a slide with its own aspect ratio:

```html
<div class="dither dither--wide"
     style="--dither-src: url('assets/band.png'); --dither-ratio: 40 / 1"
     role="img" aria-label="Dithered band"></div>
```

`--dither-ratio` is the image's real aspect ratio, written as `1` or `40 / 1`. On a slide
the plain `.dither` sits above a title; `dither--wide` makes a band across a section break.

Dithering only reads as dithering when the dots are visible, so generate small — `-w 110`
for something displayed at 8rem — and let CSS scale it up. Keep the source's shading
running in one direction; a photo that fades both across and down dithers into a smudge.

Other flags: `-n 3` for a middle tone, `--theme light|dark|both` to bake the palette in
instead of emitting a mask, `-w 0` to keep the original width.

## When NOT to apply this

- **The deck has to match something else.** A conference template, a company deck, an
  existing series. Say the house style does not apply and follow theirs.
- **It has to be a .pptx or Google Slides.** This is HTML. Build what they asked for.
- **The content is not talk-shaped** — a document someone will read alone is a page, so use
  `design-page`.
- **The user asked for something the style forbids** — a build animation, a second
  typeface, a colour, full-bleed images. Their request wins. Build it, and say which rule
  you set aside.
