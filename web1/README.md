# web1

A skill for making things that look like a plain late-90s homepage: Times New Roman on
white, default blue and purple links, black rules, the browser's own buttons and inputs, no
monospace and no decoration. It came from the neuron-chat site and covers web pages, apps,
slide decks, .pptx files, documents, charts and diagrams.

```sh
npx skills add malone-c/skills --skill web1
```

| File | What it is |
| --- | --- |
| `skills/web1/SKILL.md` | The rules, how to build each kind of thing, and how to check it. |
| `skills/web1/assets/page.html` | Template for reading: reports, notes, documentation. |
| `skills/web1/assets/app.html` | Template for anything interactive: a two-column tool layout. |
| `skills/web1/assets/deck.html` | Slide template. Arrow keys move; printing to PDF gives one 1280×720 slide per page. |
| `skills/web1/scripts/check.py` | Screenshots an HTML file and lists what breaks the style. `uv run check.py page.html` |
