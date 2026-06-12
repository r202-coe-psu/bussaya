# Fomantic-UI → daisyUI 5 conversion guide (Bussaya)

You are converting Jinja2 templates in `/home/tl/projects/r202/bussaya/bussaya/web/templates/` from Fomantic-UI 2.8 to daisyUI 5 + Tailwind CSS 4. The base layout already loads daisyUI, a custom `liberation` theme, Font Awesome 6 (free), the Tailwind browser runtime, and jQuery. Fomantic CSS/JS is GONE — any leftover `ui ...` class renders unstyled, and any leftover Fomantic jQuery call (`.dropdown()`, `.modal()`, `.calendar()`, `.accordion()`, `.popup()`, `.transition()`, `.sidebar()`, `.form()`, `.tab()`, `.checkbox()`) throws a JS error. You must remove them all from your assigned files.

## Theme intent
The app uses a freedom-inspired "liberation" palette: sky-blue `primary`, sunrise-gold `secondary`, dawn-orange `accent`. **Status colors keep their meaning**: approved/submitted → `success`, rejected/not-submitted/expired → `error`, late/pending → `warning`, open/informational → `info`. Express every Fomantic color through these semantic daisyUI colors.

## Already-converted shared files (do NOT touch; use as style reference)
- `base/base-layout.html`, `base/default-page.html`, `base/default-dashboard.html` (daisyUI drawer; provides `breadcrumbs` wrapper `<ul>` around `{% block breadcrumbs %}`)
- `base/html-renderer.html` — macros keep the same names/signatures (`render_field`, `render_checkbox`, `render_fileinput`, `render_select*`, `render_calendar`, `render_timepicker`). They now emit daisyUI inputs. Calls like `renderer.render_field(form.x)` stay as-is, BUT remove any Fomantic class arguments: `render_field(form.x, class_='ui fluid dropdown ...')` → `render_field(form.x)`.
- `base/error-handler.html`, `base/toolbar.html`, `base/toolbar-dashboard.html`, `base/banner.html`, `base/footer.html`, `base/project-material-renderer.html`, `base/solution-style.html`, `navbar/class-navbar.html`

## Class mapping

| Fomantic | daisyUI 5 / Tailwind |
|---|---|
| `ui button` | `btn` |
| `ui primary button` | `btn btn-primary` |
| `ui negative/red button` | `btn btn-error` |
| `ui positive/green button` | `btn btn-success` |
| `ui yellow/orange button` | `btn btn-warning` |
| `ui blue button` | `btn btn-info` |
| `ui teal button` | `btn btn-accent` |
| `ui black/grey button` | `btn btn-neutral` |
| `ui basic button` | `btn btn-outline` |
| `ui mini/tiny button` | add `btn-xs` |
| `ui small button` | add `btn-sm` |
| `ui large/big/huge button` | add `btn-lg` |
| `ui icon button` (icon only) | `btn btn-square` (or `btn` if it has text too) |
| `ui labeled icon button` | `btn` (icon + text are fine inside) |
| `ui fluid button` | add `btn-block` |
| `ui circular button` | add `btn-circle` |
| `ui container` | `container mx-auto px-4` |
| `ui grid` + `N column row` / `N column grid` | `grid grid-cols-1 md:grid-cols-N gap-4` |
| `column` (child) | plain `div` |
| `ui segment` | `card bg-base-100 shadow my-4` with inner `card-body` (use `p-4` body for dense content) |
| `ui inverted segment` | `bg-neutral text-neutral-content rounded-box p-4` |
| `ui (celled/striped/single line/definition/structured) table` | `<div class="overflow-x-auto"><table class="table table-zebra">…</table></div>`; for definition tables make the first column `<th class="font-medium">` |
| `ui form` | plain `<form>` (keep method/action/enctype); add `class="space-y-1"` if helpful |
| `field` / `fields` wrappers | plain `div` (macros already handle labels/inputs) |
| raw `<input>`/`<select>`/`<textarea>` not from macros | `input w-full` / `select w-full` / `textarea w-full` |
| `ui checkbox` | `<label class="label cursor-pointer justify-start gap-2"><input type="checkbox" class="checkbox">…</label>` |
| `ui message` | `alert` |
| `ui info message` | `alert alert-info` |
| `ui negative/error/red message` | `alert alert-error` |
| `ui positive/success/green message` | `alert alert-success` |
| `ui warning/yellow message` | `alert alert-warning` |
| `ui label` | `badge` (colors: `badge-success`, `badge-error`, `badge-warning`, `badge-info`, `badge-primary`, `badge-accent`, `badge-neutral`; sizes: `badge-xs/sm/lg`) |
| `ui circular label` | `badge` (already rounded) |
| `ui header` (h1–h6 or div) | keep the heading tag, use Tailwind: `text-3xl font-bold` (h1), `text-2xl font-bold` (h2), `text-xl font-semibold` (h3), `text-lg font-semibold` (h4/h5); `ui sub header` → `text-sm opacity-70` |
| `ui divider` | `<div class="divider"></div>`; `ui horizontal divider` with text → `<div class="divider">text</div>` |
| `ui list` / `item` | `<ul class="space-y-1">` / `<li>`; `divided` → `divide-y divide-base-300` |
| `ui card(s)` | `card bg-base-100 shadow` + `card-body`, `card-title`, `card-actions` |
| `ui breadcrumb` | the dashboard layout already wraps `{% block breadcrumbs %}` in `<div class="breadcrumbs"><ul>…</ul></div>`. Inside the block, emit ONLY `<li>` items: `<a class="section" href=…>X</a>` → `<li><a href=…>X</a></li>`, `<div class="active section">Y</div>` → `<li>Y</li>`. DELETE `<i class="right angle icon divider"></i>` / `<div class="divider">/</div>` separators (breadcrumbs adds them via CSS). If a breadcrumb appears OUTSIDE that block, wrap it yourself in `<div class="breadcrumbs text-sm"><ul>…</ul></div>`. |
| `ui steps` / `step` | `<ul class="steps">` / `<li class="step">` (`active`/`completed` → `step-primary`) |
| `ui statistic(s)` | `stats shadow` / `stat` with `stat-title`, `stat-value`, `stat-desc` |
| `ui menu` (page-level nav/tabs) | `<ul class="menu menu-horizontal bg-base-100 rounded-box shadow gap-1">` with `<li><a>` items; `active item` → class `menu-active` on the `<a>` |
| `ui tabular menu` + `ui tab segment` (JS tabs) | radio-input tabs: `<div class="tabs tabs-lift">` with `<input type="radio" name="t" class="tab" aria-label="…" checked>` + `<div class="tab-content bg-base-100 border-base-300 p-4">…</div>` pairs; delete `.tab()` init |
| `ui modal` + `$('.x').modal('show')` | `<dialog id="…" class="modal">` containing `modal-box` (+ `modal-action` for buttons, `<form method="dialog"><button class="btn">Cancel</button></form>` for dismiss, and `<form method="dialog" class="modal-backdrop"><button>close</button></form>` after the box). Open with `document.getElementById('…').showModal()`. If the page opened modals per-row with jQuery selectors, give each dialog a unique id derived from the loop variable. |
| `ui dropdown` (nav/action menus) | `<details class="dropdown"><summary class="btn">…</summary><ul class="menu dropdown-content bg-base-100 text-base-content rounded-box z-10 w-52 p-2 shadow">…</ul></details>`; delete `.dropdown()` init |
| `ui dropdown` (form select) | native `<select class="select w-full">` (macros already do this) |
| `ui accordion` + `.accordion()` | `<div class="collapse collapse-arrow bg-base-100 shadow"><input type="checkbox"><div class="collapse-title font-semibold">title</div><div class="collapse-content">content</div></div>`; delete init |
| `data-content="…"` popup / `.popup()` | `class="tooltip" data-tip="…"` on the wrapper; delete init |
| `ui calendar` wrappers + calendar.js | native input via existing `render_calendar` macro (it now renders `datetime-local`). DELETE: `<script src="…fomantic-ui-css/components/calendar.js">`, all `$('#…').calendar({…})` init blocks, and `formatter:` helpers. Date-range constraints (startCalendar/endCalendar) → set `min`/`max` attributes via small vanilla JS if trivial, otherwise just drop the constraint. |
| `.transition('…')` | element show/hide via `classList.toggle('hidden')`, or delete if purely decorative |
| `ui progress` | `<progress class="progress progress-primary" value="X" max="100">` |
| `ui avatar image` | `avatar` + `<div class="w-8 rounded-full"><img …></div>` |
| `ui input` wrappers | remove wrapper, class the `<input>` itself: `input w-full` |
| `ui action input` | `<div class="join">` with `join-item` input + button |
| `loading` class on buttons | `<span class="loading loading-spinner"></span>` inside the btn |
| `disabled` class | keep `disabled` attribute on buttons/inputs; for links use `btn-disabled` or `opacity-30 pointer-events-none` |
| text colors `ui red/green/blue text`, `class="… colored text"` | `text-error` / `text-success` / `text-info` etc. |
| colored table rows/cells (`positive`, `negative`, `error`, `warning` on `<tr>/<td>`) | `bg-success/20`, `bg-error/20`, `bg-warning/20` |
| `right floated` / `left floated` | `float-right` / `float-left` (prefer flexbox `ml-auto` in flex rows) |
| `center aligned` / `right aligned` | `text-center` / `text-right` |
| `inverted` | `bg-neutral text-neutral-content` |

## Icons (Fomantic icon → Font Awesome 6 free)
`<i class="NAME icon">` → `<i class="fa-solid fa-NAME"></i>` with these renames (FA6):
`edit`→`pen-to-square`, `trash`/`trash alternate`→`trash`, `sign in`→`right-to-bracket`, `sign out`→`right-from-bracket`, `sign-out`→`right-from-bracket`, `dashboard`→`gauge`, `setting(s)`→`gear`, `time`→`clock`, `calendar alternate`→`calendar-days`, `chalkboard teacher`→`chalkboard-user`, `student`/`graduation`→`graduation-cap`, `group`/`users`/`user friends`→`users`, `mail`→`envelope`, `attach`/`paperclip`→`paperclip`, `download`→`download`, `upload`→`upload`, `search`→`magnifying-glass`, `info circle`→`circle-info`, `exclamation triangle`→`triangle-exclamation`, `check circle`→`circle-check`, `close`/`times`→`xmark`, `angle right`→`angle-right`, `caret down`→`caret-down`, `file pdf`→`file-pdf`, `file alternate`→`file-lines`, `external alternate`→`up-right-from-square`, `vote yea`→`check-to-slot`, `address book`→`address-book`, `world`/`globe`→`globe`, `building`→`building`, `award`→`award`, `tag`→`tag`, `eye`→`eye`, `plus`→`plus`, `save`→`floppy-disk`, `print`→`print`, `copy`→`copy`, `archive`→`box-archive`, `git`→`fa-brands fa-git-alt` (brands prefix!), `github`→`fa-brands fa-github`, `google`→`fa-brands fa-google`, `facebook`→`fa-brands fa-facebook`, `line`→`fa-brands fa-line`.
Multi-word names hyphenate: `chevron down icon` → `fa-solid fa-chevron-down`. Sizes: `large icon`→`fa-lg`, `big icon`→`fa-xl`, `huge icon`→`fa-2x`, `small icon`→`fa-sm`. `disabled icon`→ add `opacity-30`. If unsure a name exists in FA6 free, pick the closest solid icon.

## Inline scripts
- DELETE every `<script src="...fomantic-ui-css/...">` include and every Fomantic widget init block. If a `$(document).ready` becomes empty, delete it entirely (and the surrounding `{% block additional_js %}` if now empty — but keep the block tags if the parent defines them, emptiness is fine).
- Keep non-Fomantic logic (fetch/AJAX, brython, custom functions) intact; jQuery itself is still loaded, so plain jQuery DOM code may stay.
- `votings/vote.html` contains brython (`<script type="text/python">`): convert MARKUP only; do not touch the brython code or its element ids/classes that the script queries (check before renaming any id/class used by scripts).
- Old fake file-input wiring (`.attach-file-*` click handlers) is obsolete — `render_fileinput` now renders a native `file-input`; delete those script blocks.
- A reference to `components/form.js` + `$('.ui.form').form({...})` validation → delete; add `required` attributes to the relevant inputs instead where the rules were `empty`.

## Hard rules
1. Never alter Jinja logic (conditions, loops, url_for, variables) except where a class string or macro class argument is involved. Keep all `{% block %}` structure and template inheritance exactly as-is.
2. `{% extends %}` targets and `{% import %}`/`{% include %}` paths stay unchanged.
3. Do not leave ANY `class="ui …"`, `… icon"` Fomantic icon classes, or Fomantic JS calls in your files.
4. Keep diffs reviewable: same content, same order, converted classes. Don't redesign layouts beyond the mapping (exception: replacing widget markup like modals/dropdowns/accordions per the mapping).
5. Inline `style="…"` attributes: replace with Tailwind utilities when trivial (padding/margin/width), otherwise keep.
6. After editing each file, re-grep it for `ui |icon"| icon |\.modal(|\.dropdown(|\.calendar(|\.accordion(|\.popup(|\.transition(|fomantic` to verify it's clean. ("icon" inside fa-* classes is fine.)
