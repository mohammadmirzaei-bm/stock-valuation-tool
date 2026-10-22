# Achievements

A record of notable problems solved in this project, with the diagnosis and the
fix that was applied.

---

## RTL sidebar no longer strands itself mid-page after collapsing

**Component:** `stock_valuation/ui/theme.py` (`RTL_STYLES`)
**Streamlit version:** 1.66.1
**Status:** Fixed and verified in the browser

### Problem

The dashboard uses a Persian, right-to-left interface. After clicking the
sidebar collapse button, the collapsible panel did not disappear cleanly. Instead
a narrow, vertically wrapped copy of the sidebar content plus its resize handle
stayed parked inside the viewport, well away from the right edge — it looked as
if the panel control had drifted to the middle of the page.

Measured on a 971 x 545 viewport, right after collapsing:

| Element | Measurement |
|---|---|
| `[data-testid="stSidebar"]` | `x = 783.8`, `width = 0`, `data-collapsed="true"` |
| sidebar `transform` | `translateX(-187.5px)` |
| leftover content | heading and radio label re-wrapped into a ~15 px wide vertical glyph column at `x ≈ 768` |
| `[data-testid="stSidebarResizeHandle"]` | 8 x 545 px strip at `x ≈ 782`, `z-index: 999995`, `pointer-events: auto`, `cursor: col-resize` |

The panel was technically collapsed (`width: 0`) but still painted and still
accepted pointer events, so the leftover strip hovered over the main content.

### Root cause

The RTL layout is applied by setting `direction: rtl` on
`[data-testid="stAppViewContainer"]` (and the sidebar and header). That flips
the flex row, so the sidebar is rendered on the **right** side instead of the
default left side.

Streamlit's collapse animation, however, is hardcoded for LTR layouts: it hides
the panel with `transform: translateX(-sidebarWidth)`. With the sidebar on the
right, that negative translation only pulls it **inward**, so the element never
leaves the viewport. The panel collapses to zero width but its children keep
`overflow: visible`, which is why squashed text and the resize handle remained
visible at the old sidebar boundary.

Two secondary findings from the DOM investigation:

- The re-open control in Streamlit 1.66.1 is
  `button[data-testid="stExpandSidebarButton"]` inside the toolbar — **not**
  `stSidebarCollapsedControl`, which does not exist in this build. The expand
  button itself was correctly anchored to the edge; the artifact came from the
  collapsed sidebar element.
- The collapse/expand chevrons are hardcoded (`keyboard_double_arrow_left` and
  `keyboard_double_arrow_right`), so in an RTL layout they pointed the wrong way.

### Solution

The collapsed state is exposed by Streamlit as `data-collapsed="true"` on the
sidebar element, which allows a pure CSS fix scoped to that state:

```css
/* نوار کناری جمع‌شده در چیدمان راست‌به‌چپ
   Streamlit نوار کناری را با translateX برای چیدمان چپ‌به‌راست بیرون می‌برد؛
   وقتی نوار در سمت راست است، این جابه‌جایی آن را داخل کادر دید رها می‌کند و
   نوار باریک متن به‌هم‌ریخته و دستگیره تغییر اندازه وسط صفحه می‌مانند.
   به‌جای visibility از opacity استفاده می‌شود، چون برخی ویجت‌های داخلی
   Streamlit دوباره visibility: visible می‌گیرند. */
[data-testid="stSidebar"][data-collapsed="true"] {
    opacity: 0;
    pointer-events: none;
}

/* فلش‌های باز و بستن نوار کناری در چیدمان راست‌به‌چپ آینه شوند */
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {
    transform: scaleX(-1);
}
```

Why these properties:

- **`opacity: 0` instead of `visibility: hidden`** — inner Streamlit widgets
  (for example `stWidgetLabel p` and metric spans) explicitly set
  `visibility: visible`, which defeats a `visibility` rule on the ancestor.
  Opacity applies to the whole subtree and cannot be overridden from below.
- **`pointer-events: none`** — removes the invisible resize handle
  (`z-index: 999995`) from hit-testing, so it no longer intercepts drags and
  clicks over the main content.
- **`scaleX(-1)` on the chevrons** — mirrors the hardcoded Material icons so
  they point outward when collapsing and inward when expanding a right-side
  panel.

The RTL `direction` itself is intentionally kept on the layout containers,
because placing the sidebar on the right is the expected convention for the
Persian UI. Only the collapsed state is overridden.

### Verification

Verified in a live browser session against the running app:

- Collapsed state: sidebar `width = 0`, `opacity = 0`,
  `pointer-events = none`; `document.elementsFromPoint(785, 270)` returns main
  content (`p` -> `div[data-testid="stMarkdownContainer"]` -> `span`) instead of
  the sidebar or its resize handle.
- No sidebar glyphs are painted in the `x = 700-971` band after collapsing.
- Re-expanding restores the sidebar to `187.5 px` flush with the right edge,
  `opacity = 1`, and the heading «پنل کنترل» renders at its full content width
  (147.5 px) with normal height.
- Two collapse/expand cycles completed with zero console errors.
- `python3 -m unittest discover -s tests -t .` -> 57 tests, OK.

### Notes

- Streamlit persists sidebar visibility in `localStorage` under
  `sidebarNavState`, so a browser that was left collapsed may open the app
  collapsed even with `initial_sidebar_state="expanded"`. This is existing
  Streamlit behavior and unrelated to the CSS fix.
- The fix is CSS-only, lives entirely in `RTL_STYLES`, and does not require any
  JavaScript, component wrapping, or changes to the domain layer.

---

## Principles: Persian RTL text without breaking the layout

These rules are distilled from the sidebar fix above. They keep the Persian
interface right-to-left while leaving Streamlit's layout engine and the
project's module boundaries untouched. Apply them whenever UI is added or
restyled.

### 1. Direction belongs to the presentation layer

- Streamlit 1.66 has no native RTL switch, so direction is necessarily CSS, but
  it lives in exactly one place: `RTL_STYLES` in
  `stock_valuation/ui/theme.py`, injected once by `apply_rtl_layout()`.
- View functions in `stock_valuation/ui/views.py` never set direction, margins,
  or alignment; they only create widgets and render results.
- The domain layer never imports Streamlit, and `TestLayering` in
  `tests/test_valuation_models.py` keeps it that way.

### 2. Pick the RTL boundary deliberately

- `direction` inherits, so set it on the narrowest container that owns Persian
  content. Applying it to `html`, `body`, or every element makes framework
  internals inherit assumptions they were never written for.
- This project flips `[data-testid="stAppViewContainer"]` on purpose: a
  right-side sidebar is the Persian convention, and reversing the flex row is
  the only way to get it. The documented cost is that Streamlit's collapse
  transform and toolbar order remain LTR and must be handled explicitly.
- If a left-side sidebar were acceptable, the safer boundary would be
  `direction: rtl` on `[data-testid="stSidebarContent"]` and
  `[data-testid="stMainBlockContainer"]` only, leaving the layout chrome in its
  native LTR behavior.

### 3. Never rebuild the layout in CSS

- No `float`, no absolute positioning of Streamlit elements, no negative
  margins to compensate for mirroring. Structure comes from `st.columns`,
  `st.container`, and `st.sidebar`.
- When a framework state misbehaves, override the state, not the engine. The
  sidebar fix hides the panel while `data-collapsed="true"`; its sizing and
  transform are still owned by Streamlit.

### 4. Target stable hooks only

- Prefer `data-testid` attributes and documented state attributes such as
  `data-collapsed`.
- Never target generated `st-emotion-cache-*` classes, `nth-child` positions, or
  long descendant chains. They change between Streamlit releases and fail
  silently.
- Reserve `!important` for framework overrides that cannot win otherwise, and
  state the reason in the comment.

### 5. Keep LTR islands for non-text content

| Content | Direction | Handled by |
|---|---|---|
| Persian prose, headings, captions | rtl | inherited from `stAppViewContainer` |
| Formulas (KaTeX), symbols | ltr | `.katex` rule |
| Tables, numeric grids | ltr | `[data-testid="stDataFrame"]` rule |
| Sliders and their ticks | ltr | `[data-testid="stSlider"]` rule |
| Numbers inside a Persian sentence | isolated | `unicode-bidi: isolate` or an inline `<span dir="ltr">` |

Forcing read-only numeric content to RTL reorders signs, decimals, and
percentages. Isolate such values instead of flipping them.

### 6. Align with logical, not physical, properties

- New styles should prefer `text-align: start/end`, `margin-inline-*`,
  `padding-inline-*`, and `inset-inline-*`. Physical `left`/`right` belongs only
  inside LTR islands.
- Streamlit ships some explicit physical alignment of its own, which is why the
  stylesheet still sets `text-align: right` for markdown containers, widget
  labels, captions, and metric text.

### 7. Mirror directional icons, not containers

- Chevrons, arrows, and progress indicators are horizontal glyphs with a
  meaning that flips in RTL. Apply `transform: scaleX(-1)` to the icon node
  (`[data-testid="stIconMaterial"]`), never to the button, panel, or page.
- Never mirror logos, checkmarks, media controls, charts, or any element whose
  shape is not directional.
- Framework icons are often hardcoded for LTR (the sidebar chevrons are), so
  audit every directional icon when a new component is introduced.

### 8. Typography and text hygiene

- Persian typography comes from `.streamlit/config.toml` (`font`,
  `headingFont`, sizes, colors), not from CSS `@font-face` blocks.
- Use the zero-width non-joiner (U+200C) for نیم‌فاصله words such as «می‌شود»,
  and the Persian comma «،» in UI strings.
- Never put Persian punctuation or Persian digits inside code, identifiers, CSS
  selectors, or file paths.
- Keep Latin acronyms and model names (`PEG`, `CAPM`, `NPVGO`) as-is inside
  Persian sentences; they are already direction-neutral.

### 9. Respect widget-specific behavior

- Radio and checkbox rows align to the start edge (the stylesheet uses
  `align-items: flex-start`), and their labels receive `direction: rtl` so the
  marker follows the text.
- Number and text inputs get `direction: rtl` with `text-align: right`; their
  editable values may still be Latin digits.
- Expander summaries, alerts, and buttons get `direction: rtl` so icons and
  text order match the rest of the page.
- Column order is mirrored visually. Re-check KPI and comparison grids after any
  RTL change; if the reading order matters, order the calls accordingly.

### 10. Verify states, not just the first render

- Sidebar expanded and collapsed, including hover-revealed controls.
- At least one rerun after an interaction, since Streamlit re-injects the
  stylesheet on every run.
- Expanders, tabs, radio groups, dataframes, chart tooltips, and a narrow
  viewport.
- No painted or hit-testable leftover where a panel used to be; confirm with
  `document.elementsFromPoint(...)` in the browser console.
- No console errors, `streamlit.testing.v1.AppTest` renders without exceptions,
  and `python3 -m unittest discover -s tests -t .` stays green.

**Rule of thumb:** Persian text may flip direction; the layout engine, the
module boundaries, and non-text content must not.

