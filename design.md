# Stock Screener — Design System

This document defines the visual design system for the IOWN Stock Screener. **All UI changes must follow these specifications exactly** to maintain consistency with the parent IOWN Dashboard.

## Theme

The screener uses a **light theme** that matches the Dashboard's light palette. Do NOT use a dark theme.

## Color Palette (CSS Variables)

```css
:root {
    --bg: #F5F5F0;
    --surface: #FFFFFF;
    --card: #FFFFFF;
    --card-hover: #F0F2EC;
    --border: rgba(80,100,60,0.12);
    --border-hover: rgba(80,100,60,0.22);
    --border-active: rgba(80,100,60,0.40);
    --t1: #1A2010;          /* primary text */
    --t2: #3A4A28;          /* secondary text */
    --t3: #6E8450;          /* tertiary text */
    --t4: #9DAF88;          /* quaternary text */
    --accent: #4A6B25;      /* sage green accent */
    --accent-soft: rgba(74,107,37,0.08);
    --accent-glow: rgba(74,107,37,0.20);
    --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
}
```

### State Colors

| State        | Color     | Usage                      |
|-------------|-----------|----------------------------|
| Positive/Up | `#16A34A` | BUY badges, green bars     |
| Negative/Dn | `#DC2626` | SELL badges, red bars      |
| Hold/Gold   | `#D97706` | HOLD badges                |
| Watch/Blue  | `#2563EB` | WATCH badges               |
| Gold accent | `#B8860B` | Section headers, Inspire   |

### Recommendation Badge Styling

Badges use 10% opacity backgrounds with solid text color:

```css
.buy  { background: rgba(22,163,74,0.10);  color: #16A34A; }
.hold { background: rgba(217,119,6,0.10);  color: #D97706; }
.sell { background: rgba(220,38,38,0.10);  color: #DC2626; }
.watch { background: rgba(37,99,235,0.10); color: #2563EB; }
```

## Typography

- **Font**: `'DM Sans'` from Google Fonts (variable, weights 400–800)
- **Fallback**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- **Font features**: OpenType `'cv01' on, 'cv02' on`
- **Rendering**: `-webkit-font-smoothing: antialiased`

### Type Scale

| Element            | Size  | Weight | Color      |
|-------------------|-------|--------|------------|
| Stock ticker       | 17px  | 800    | `--accent` |
| Stock name         | 12px  | 400    | `--t3`     |
| Search input       | 15px  | 600    | `--t1`     |
| Score (large)      | 26px  | 800    | `--t1`     |
| Score denominator  | 12px  | 400    | `--t4`     |
| Tags (sleeve/rec)  | 10px  | 700–800| varies     |
| Section headers    | 11px  | 800    | `--t3`     |
| Body/analysis      | 12–13px | 400  | `--t2`     |
| Footer             | 10–11px | 400  | `--t4`     |

## Spacing & Layout

- **Max width**: 1000px (index), 800px (reports)
- **Container padding**: `24px` (index), `40px 48px` (reports)
- **Card gap**: `6px`
- **Card padding**: `14px 18px`
- **Border radius**: `14px` (cards, inputs), `8px` (badges), `10px` (back link)

## Component Patterns

### Cards (Stock List Items)

```css
.stock-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 18px;
    box-shadow: var(--shadow);
    transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
}
.stock-card:hover {
    border-color: var(--border-active);
    background: var(--card-hover);
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
```

### Search Input

```css
.search-input {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    box-shadow: var(--shadow);
}
.search-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
}
```

### Score Bars

- Track: `var(--bar-track)` — `rgba(80,100,60,0.10)`
- Height: `8px`, border-radius: `4px`
- Fill colors: green (`#16A34A`), gold (`#B8860B`), red (`#DC2626`)
- Transition: `width 0.5s ease`
- Score thresholds: 7+ = green, 4–6 = gold, <4 = red

### Section Headers

```css
.section-header {
    font-size: 11px;
    font-weight: 800;
    color: var(--t3);
    letter-spacing: 2px;
    text-transform: uppercase;
    border-bottom: 2px solid var(--accent-gold);
}
```

Border colors: default = gold (`#B8860B`), `.green` = `#16A34A`, `.red` = `#DC2626`

### Back Link

Pill-shaped with hover background:

```css
.back-link {
    font-size: 13px;
    font-weight: 700;
    color: var(--accent);
    padding: 8px 14px;
    border-radius: 10px;
}
.back-link:hover { background: var(--accent-soft); }
```

## Scrollbar

```css
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: rgba(74,107,37,0.15); border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: rgba(74,107,37,0.30); }
```

## Selection

```css
::selection { background: rgba(74,107,37,0.25); color: var(--t1); }
```

## Logo

Use the IOWN logo image, NOT text. Reference from Dashboard's GitHub Pages:

```html
<!-- Light theme (default) -->
<img src="https://richacarson.github.io/Dashboard/iown-logo.png" alt="IOWN">
```

Height: `48px` (index header), `40px` (report headers). Do NOT render "IOWN" as styled text.

## Embedded Mode

When loaded inside the Dashboard iframe (`?embed=1` query param), the screener applies these overrides:

- Background becomes transparent
- Header (logo + stats) is hidden
- Footer is hidden
- Container padding reduced to `12px 16px` (index) or `16px` (reports)
- Logo headers on report pages are hidden
- Stock card links and back links propagate `?embed=1`

Detection logic:

```javascript
var params = new URLSearchParams(window.location.search);
if (params.get('embed') === '1' || window.self !== window.top) {
    document.body.classList.add('embedded');
}
```

## Animation

```css
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeIn 0.3s ease; }
```

## Responsive Breakpoint

Mobile: `max-width: 640px`

- Reduced padding, smaller font sizes
- Stacked layouts where needed (e.g., header-row becomes column)

## Important Rules

1. **Always use light theme** — the Dashboard handles the screener inside a full-page overlay
2. **Never add "IOWN" as plain text** — always use the logo image
3. **Maintain the sage green accent** (`#4A6B25`) — this is the brand color
4. **Keep embedded mode working** — the `?embed=1` detection must remain functional
5. **Use DM Sans font** — do not switch to another font family
6. **Border radius 14px** for cards and inputs — matches Dashboard card styling
7. **Transitions at 0.15s** for interactive elements — consistent with Dashboard
