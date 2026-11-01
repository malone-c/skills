# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright"]
# ///
"""Screenshots a web1 page, app or deck and lists what breaks the style: monospace anywhere, a font other than Times
(the browser's own buttons, inputs and selects excepted), rounded corners, shadows, gradients, animation, colours
outside the palette, sideways scrolling on a phone, and slides whose contents overflow.

Usage: uv run check.py PAGE_OR_URL [OUT_DIR]. Writes desktop.png and phone.png, or slide-N.png for a deck, to OUT_DIR
(default ./web1-check) and exits 1 when it finds a problem. If Chromium is missing:
uv run --with playwright python -m playwright install chromium
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

target = sys.argv[1]
out = Path(sys.argv[2] if len(sys.argv) > 2 else "web1-check")
out.mkdir(parents=True, exist_ok=True)
url = target if "://" in target else Path(target).resolve().as_uri()

audit = """() => {
  const browserStyled = new Set(["INPUT", "BUTTON", "SELECT", "OPTION", "TEXTAREA", "FIELDSET", "LEGEND"]);
  const ownFont = new Set(["INPUT", "BUTTON", "SELECT", "OPTION"]);
  const palette = new Set(["rgb(0, 0, 0)", "rgb(255, 255, 255)", "rgb(0, 0, 238)", "rgb(85, 26, 139)", "rgb(68, 68, 68)",
    "rgb(85, 85, 85)", "rgb(204, 0, 0)", "rgb(128, 128, 128)", "rgb(255, 255, 204)", "rgba(0, 0, 0, 0)"]);
  const found = new Set();
  for (const element of document.body.querySelectorAll("*")) {
    if (["SCRIPT", "STYLE", "BR"].includes(element.tagName)) continue;
    const style = getComputedStyle(element), tag = `<${element.tagName.toLowerCase()}>`;
    if (/mono|courier|menlo|consolas|monaco/i.test(style.fontFamily)) found.add(`${tag} is monospace`);
    else if (!ownFont.has(element.tagName) && !style.fontFamily.startsWith('"Times New Roman"'))
      found.add(`${tag} is set in ${style.fontFamily}`);
    if (browserStyled.has(element.tagName)) continue;
    if (style.borderRadius !== "0px") found.add(`${tag} has rounded corners`);
    if (style.boxShadow !== "none" || style.textShadow !== "none") found.add(`${tag} has a shadow`);
    if (style.backgroundImage.includes("gradient")) found.add(`${tag} has a gradient`);
    if (style.animationName !== "none" || style.transitionDuration.split(",").some(d => parseFloat(d) > 0))
      found.add(`${tag} moves`);
    for (const colour of [style.color, style.backgroundColor, style.borderTopColor])
      if (!palette.has(colour)) found.add(`${tag} uses ${colour}`);
  }
  if (document.documentElement.scrollWidth > innerWidth) found.add("the page scrolls sideways");
  return [...found];
}"""

problems = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto(url)
    page.wait_for_timeout(300)
    num_slides = page.locator(".slide").count()
    if num_slides:
        problems += page.evaluate(audit)
        page.keyboard.press("Home")
        for number in range(1, num_slides + 1):
            page.screenshot(path=out / f"slide-{number}.png")
            if page.evaluate("() => { const f = document.querySelector('.slide.current .frame'); "
                             "return f.scrollHeight > f.clientHeight + 1 }"):
                problems.append(f"slide {number} overflows: split it or cut words")
            page.keyboard.press("ArrowRight")
    else:
        for name, width, height in [("desktop", 1280, 800), ("phone", 390, 844)]:
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_timeout(200)
            page.screenshot(path=out / f"{name}.png", full_page=True)
            problems += [f"{name}: {problem}" for problem in page.evaluate(audit)]
    browser.close()

print(f"Screenshots in {out.resolve()}")
for problem in dict.fromkeys(problems):
    print(f"- {problem}")
if problems:
    sys.exit(1)
print("No problems found.")
