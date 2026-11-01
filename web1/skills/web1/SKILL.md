---
name: web1
description: "Makes anything look like a plain late-90s homepage, the style of the neuron-chat site: Times New Roman on white, default blue and purple links, black rules, the browser's own buttons and inputs, no monospace, no decoration. Covers web pages, apps and tools, dashboards, slide decks, .pptx files, documents, charts and diagrams. Use whenever the user asks for any of these without naming another style, or mentions web1, Web 1.0, the neuron-chat look or this design."
---

# Web 1.0 style

A page in this style looks like a programmer's homepage from 1998: Times on white, blue
underlined links, a rule under the title, tables for layout, and the browser's own
buttons and boxes. It came from the neuron-chat site. The same rules carry over to slides,
documents and charts.

## The look

- **One typeface: Times New Roman**, `font: 17px/1.4 "Times New Roman", Times, serif`.
  Headings are the same face in bold: `h1` 28px, `h2` 21px, `h3` 17px. No web fonts.
- **No monospace anywhere.** Not for code, numbers, transcripts or text boxes. Browsers
  give `<textarea>` a monospace font by default, so every page sets
  `textarea { font: inherit; }`. Buttons, inputs and selects keep the browser's own font.
- **Nine colours and nothing else.** No dark mode: it is a white page.

  | Use | Colour |
  | --- | --- |
  | Text, rules, column dividers | `#000` |
  | Page | `#fff` |
  | Links | `#0000ee`, underlined |
  | Visited links | `#551a8b` |
  | Secondary text, set in italic (excerpts, attributions) | `#444` |
  | Status notes | `#555` |
  | Errors | `#c00` |
  | Borders of boxes and data tables | `#808080` |
  | The current row or item | `#ffffcc` background |

- **Structure.** A bold title, one `.meta` line at 14px under it, then an `<hr>`. Sections
  start with a heading or another `<hr>`. Columns are table cells divided by a 1px black
  line. Anything that scrolls sits in a box with a `1px inset #808080` border. Controls are
  grouped in a `<fieldset>` with a bold `<legend>`.
- **Controls are the browser's own.** Unstyled `<input type="submit">`, `<select>`,
  checkboxes and number fields. Small actions can be bracketed text links: `[shuffle]`.
- **Width.** 760px for reading, 1100px for apps. Below 760px wide, table columns stack.
- **None of these:** rounded corners, shadows, gradients, coloured or image backgrounds,
  cards, hero banners, sticky headers, icons, emoji, spinners, hover effects beyond the
  browser's, animation or transitions, CSS frameworks.

## Words

- No copy explaining how it is built: the model, the stack, the hosting. The user calls
  that AI slop. No explanatory footers.
- Status at body size: "Showing **First result** (one detail)", never a large banner.
- Short labels: "Search:", "Go", "Send", "New chat". Sentence case.
- An error is one red sentence saying what happened and what to do.
- Nothing happens until the user asks: no auto-sent messages, autoplay or pop-ups.
- Numbers over adjectives.

## Build it

Copy the closest template from `<skill>/assets/` (`<skill>` is this skill's directory),
replace its placeholder words, and delete the parts the job does not need. Each template is
one self-contained HTML file with its CSS inline, so the result can be opened, emailed or
published anywhere as a single file. Write any new CSS from the colours and rules above.

| Template | For |
| --- | --- |
| `page.html` | Reading: reports, write-ups, notes, documentation. Title, meta line, sections, a data table, a figure, a quotation. |
| `app.html` | Anything interactive: tools, dashboards, search, chat, forms. A two-column table with a list on the left and the work on the right. |
| `deck.html` | Slides. |

**Pages.** Use `table.data` for numbers, with `.num` cells right-aligned. Figures get a 1px
black border and an italic caption underneath. Wide tables go in `.scroll` so the page
itself never scrolls sideways.

**Apps.** Results are a numbered list in an inset box: a link, the kind in brackets, and an
italic one-line excerpt cut off with an ellipsis. Mark the current item with
`aria-current="true"`, which turns it yellow. Transcripts are IRC-style:
`<b>name&gt;</b> text`. A dashboard is tables of numbers and plain charts, not cards. When
script builds the UI, it builds these same elements.

**Decks.** One `<section class="slide">` per slide, with the content inside `.frame`. Use
`class="slide title"` for the opening, closing and section slides. A slide has a title, a
rule, and at most five short bullets or one table or figure; if it overflows, it is two
slides. Arrow keys, space and Home/End move between slides, and `#n` in the URL opens slide
n. **Print → Save as PDF** produces one slide per page at 1280×720. No builds or transitions.

## Other formats

| Format | How |
| --- | --- |
| .pptx or Google Slides | 16:9, white, blank layout rather than a designed theme. Theme fonts set to Times New Roman. Title 40pt bold top-left with a 0.75pt black line under it; body 24–28pt black; slide number 12pt bottom-right. Links `#0000EE` underlined. Tables with 0.75pt `#808080` borders and no fills. No transitions or animations. |
| Word, Google Docs, PDF | Times New Roman 12pt black. Title 18pt bold with a horizontal line under it, headings 14pt bold. Links `#0000EE` underlined. Tables with a 0.5pt `#808080` grid and no shading. No cover page. |
| Charts (matplotlib, SVG, Vega) | White background, 1px black axes, Times labels at body size, no gridlines unless values must be read off (then 1px `#c0c0c0`). Series in order: `#0000ee`, `#c00`, `#008000`, `#551a8b`, `#000`. Label lines at their ends instead of using a legend box. The title is a heading above the chart, not inside it. Export at 2x for crispness. |
| Diagrams (SVG, Mermaid, whiteboards) | White boxes with 1px black borders and square corners, Times labels, 1px black arrows. Blue only for things that are links. |
| Markdown | It cannot carry the style; write it plainly and render it into `page.html` when it needs to look like this. |

For matplotlib:

```python
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "font.size": 13,
                     "axes.edgecolor": "#000", "axes.linewidth": 1, "axes.grid": False,
                     "axes.prop_cycle": plt.cycler(color=["#0000ee", "#c00", "#008000", "#551a8b", "#000"])})
```

## Check it

For any HTML output, run the checker and then look at its screenshots:

```sh
uv run <skill>/scripts/check.py out.html /tmp/web1-check
```

It writes `desktop.png` and `phone.png`, or one `slide-N.png` per slide for a deck. It lists
anything set in monospace or a font other than Times, rounded corners, shadows, gradients,
animation, colours outside the palette, sideways scrolling on a phone, and slides that
overflow. Fix everything it lists. Then read the screenshots yourself, because the checker
cannot judge spacing or words.

## When not to use it

- **The work lives somewhere with its own design**, such as a product's codebase or a
  company template. Follow theirs.
- **The user asks for something this style forbids**, such as a colour, a second font or an
  animation. Their request wins: build it and say which rule you set aside.
