---
name: design-page
description: "Builds a web page in the house style — Times New Roman on white, melange in dark mode, one centred column, nothing that has not earned its place. Use whenever the user wants a page, essay, note, write-up, report, README-as-a-page or any standalone HTML document, and whenever they mention the house style, the page template or design/. Prefer this over hand-rolling HTML and CSS from scratch."
---

# House-style page

The look comes from [bactra.org/notebooks](https://bactra.org/notebooks/): a single
centred column of left-aligned serif text, blue underlined links, and no other decoration.
The template already has that. Your job is to replace its words, not to redesign it.

For a slide deck, use `design-deck` instead.

## Build it

Below, `<skill>` is this skill's own directory and `<out>` is where the document is
going.

1. **Copy the template into the output directory.** Everything the page needs travels
   with it, so it can be zipped, moved or served from anywhere.

   ```sh
   mkdir -p <out>
   cp -R <skill>/assets/. <out>/
   ```

   That gives `<out>/page.html`, `style.css`, `theme.js` and `assets/{orb,band}.png`.
   Rename `page.html` to whatever the document is about.

2. **Replace the lorem ipsum.** Work through the template top to bottom: `<title>`, the
   `<h1>`, the `.meta` dates, then `<main>`. Delete any element the document has no use
   for — the epigraph, the blockquote, the ornaments — rather than leaving it filled with
   placeholder text.

3. **Serve it over HTTP and look at it, in both themes.** The ornaments are CSS masks and
   browsers refuse to load a mask from a `file://` origin, so opening the file directly
   shows an invisible ornament and hides real breakage.

   ```sh
   python3 -m http.server -d <out> 8000   # then http://localhost:8000/page.html
   ```

   Click the toggle in the top-right and check the page again in the other theme.

## The parts

Everything below already exists in `page.html`. Keep what the document needs, delete the
rest, add nothing new.

| Part | What it is |
| --- | --- |
| `.breadcrumb` | Commented out at the top. Uncomment it only when the page sits under a real index — it points at `./`. |
| `.theme-toggle` | The light/dark button. Delete it and the page follows the system only; `theme.js` does nothing when it is absent. |
| `header` | An ornament, the `<h1>`, and a `.meta` block of dates. |
| `.epigraph` | One line under the rule, before the prose. Optional and usually skipped. |
| `blockquote` | A quotation. `.muted` on the following paragraph makes an attribution line. |
| `h2` / `h3` | Section headings. These are what carry `class="reveal"`. |
| `.tip` | `<span class="tip" data-tip="…" tabindex="0">term</span>` — a dotted underline with a bubble on hover or keyboard focus. |
| `footer` | A wide ornament and one line of links. |

The reveal is driven by the `IntersectionObserver` at the bottom of the body. Leave that
script in place; without it `.reveal` elements are simply visible, which is the correct
fallback.

## Rules

- **One typeface.** Times New Roman, from `--serif`. Do not add a font, a font stack or a
  Google Fonts link.
- **Six colours.** `--paper`, `--ink`, `--muted`, `--rule`, `--link`, `--visited`, defined
  for both themes in `style.css`. Any colour you write by hand will be wrong in one theme
  or the other. If something needs to be quiet, that is `--muted`.
- **Do not edit `style.css`.** If the document needs something the stylesheet has no class
  for, that is usually a sign the document should say it in prose instead. When it really
  is missing, add a rule at the bottom of the copied `style.css` built from the existing
  tokens, and say so.
- **Links stay blue and underlined.** The underline thickening on hover is the whole hover
  treatment.
- **The column is `--measure`, 31rem.** Wide things — a table, a diagram — go in a
  container that scrolls, not in a wider column.
- **Movement is capped at three.** Reveal, tooltip, and nothing else on a page. Put
  `reveal` on section headings and the block that follows them, never on every paragraph;
  the effect is a page settling as you read, and it disappears when applied to everything.
  Use a `.tip` for an aside the reader can skip, never for something they need. Both are
  already off under `prefers-reduced-motion`.

## Ornaments

The two in `assets/` are samples — a sphere and a band. To make one from a photo:

```sh
uv run <skill>/scripts/dither.py photo.jpg -o <out>/assets/orb.png -w 110
```

The default output is an alpha mask, black ink on transparency, so one file takes the text
colour and works in both themes. Drop it in with its own aspect ratio:

```html
<div class="dither dither--header"
     style="--dither-src: url('assets/orb.png'); --dither-ratio: 1"
     role="img" aria-label="Dithered sphere"></div>
```

`dither--header`, `dither--footer` and `dither--wide` set the size. `--dither-ratio` is the
image's real aspect ratio, written as `1` or `40 / 1`.

Dithering only reads as dithering when the dots are visible, so generate small — `-w 110`
for something displayed at 8rem — and let CSS scale it up. Keep the source's shading
running in one direction; a photo that fades both across and down dithers into a smudge.

Other flags: `-n 3` for a middle tone, `--theme light|dark|both` to bake the palette in
instead of emitting a mask, `-w 0` to keep the original width.

## When NOT to apply this

- **The page has to match something else.** A site with its own stylesheet, a company
  template, a doc system. Say the house style does not apply and follow theirs.
- **It is not a document.** An app, a dashboard, a form, anything with state. This style is
  for prose.
- **The user asked for something the style forbids** — a second typeface, a colour, an
  image-heavy layout. Their request wins. Build it, and say which rule you set aside.
