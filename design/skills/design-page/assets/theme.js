// Load this synchronously in <head>: it marks the document before first paint, so a
// stored theme does not flash the system one first.
document.documentElement.classList.add("js");

// localStorage throws in sandboxed frames, where the toggle still works for the session.
let store = null;
try {
  store = localStorage;
} catch {}

if (store?.theme) document.documentElement.dataset.theme = store.theme;

function currentTheme() {
  if (document.documentElement.dataset.theme) return document.documentElement.dataset.theme;
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector(".theme-toggle");
  if (!toggle) return;

  // The button names the theme it will switch to.
  const relabel = () => (toggle.textContent = currentTheme() === "dark" ? "light" : "dark");
  relabel();

  toggle.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    if (store) store.theme = next;
    relabel();
  });

  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", relabel);
});
