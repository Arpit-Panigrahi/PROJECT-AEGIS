<USER_REQUEST>
i want to # Design language

## How to use this design language

**Goal:** Learn this template's design language — then design **anything** (different page type, product UI, campaign, dashboard) with the same rigor.

**This is not a build spec.** You are not required to reproduce this template's section list, copy, layout order, or source stack.

**Design language stack** (read top-down, build bottom-up):

| Layer | Section | Use when building |
| --- | --- | --- |
| 0 | Anti-slop | Universal guardrails — always |
| 1 | Design principles | Taste and system character — internalize first |
| 2 | Design tokens | All colour, type, spacing values |
| — | Motion system | Transferable animation vocabulary |
| — | Imagery direction | Which image media + art styles fit |
| 3 | Primitive components | Atoms for any screen |
| 4 | Reference components | Study source compositions — adapt or omit |
| — | Composition guide | Apply language to the user's brief |

| Do | Don't |
| --- | --- |
| Internalize principles and token *relationships* | Copy every reference component for unrelated briefs |
| Reuse **primitives** in new combinations | Treat **reference components** as mandatory blocks |
| Match spacing, type, and colour *relationships* | Paste hash asset paths or brand names as defaults |
| Pick image **medium** and **style** from Imagery direction | Drop lifestyle stock or whimsical illustration into this technical dark SaaS language |
| Add npm/CDN libraries when they improve UI/UX — map to tokens and motion | Add colours, fonts, or motion outside **Design tokens** and this language |
| Implement in the **user's** stack when known (React, Vue, Tailwind, etc.) | Force vanilla HTML because the source template used it |
| Port snippets to components, utilities, or design tokens in their stack | Treat **Dependencies (from source)** as a closed allowlist — it is reference only |
| **Implement responsive** — mobile through desktop; preserve token relationships across breakpoints | Ship desktop-only because the source template was cloned desktop-first |

**Responsive (build rule):** Source templates are often extracted **desktop-first** — responsive `@media` rules may be absent or incomplete in reference snippets. That is expected. When you **build** from this design language, you **must** implement responsive layout and type (stack columns, scale display type, touch-friendly targets, readable line lengths). Infer breakpoints from token tiers and layout habits in **Design principles**; do not require per-reference-component responsive specs in this file.

When the user asks for something unlike the source (e.g. SaaS dashboard from a portfolio template), keep principles + tokens + motion + imagery vocabulary; invent new layouts using primitives.

---

### Anti-slop (builder) — hard rules

**Anti-slop:** follow **### Anti-slop (builder) — hard rules** below only — do not add colours, fonts, casing, layout, or motion outside **Design tokens**, **Primitive components**, **Reference components**, **Motion system**, and this section.

**Language contract:** everything you may use is in **this DESIGN.md** — read **How to use this design language** first. This file teaches craft; **Reference components** are reference studies, not mandatory blocks. Stay inside **Design tokens**, **Primitive components**, **Motion system**, **Imagery direction**, and this section when building. **Dependencies (from source)** is informational — see **Libraries & dependencies**.

Map legacy terms when reading rules below: **FIXED SPEC → Design tokens + Reference components**; **### Tokens → Design tokens**; **Section patterns / Section recipes → Reference components**; **CONTENT SLOTS / MEDIA SLOTS → copy and assets in reference components and snippets**.

Design tokens and documented section exceptions win when composing new pages from this design language. **Every rule below is mandatory.**

#### Casing & uppercase

**Default: sentence case everywhere** unless **Design tokens** or **Reference components** document `text-transform` on that exact element.

- This template may use `text-transform: capitalize` — preserve only where **Typography scale** or primitive/section docs name the selector.
- Do not invent all-caps nav, CTAs, labels, or eyebrows.
- No tag-left / header-right section heads (`01 · TITLE` left column + title right) unless **Reference components** document that layout. Stack eyebrow **above** heading in one column.

```css
/* enforce unless Design tokens or Reference components name an exception */
nav a,
.btn,
button,
label,
h1,
h2,
h3,
h4,
p {
  text-transform: none;
}
```

Use `--text-transform-default` from **Design tokens** when present.

#### Typography & font-mono

**Default: `font-family` tokens from Design tokens only.** No decorative monospace.

- No `font-mono`, `font-family: monospace`, JetBrains Mono, or IBM Plex Mono on nav, eyebrows, section indices, CTAs, labels, stats, quotes, or body unless **Design tokens** or **Primitive components** document mono on **that element**.
- Monospace only for `<code>`, `<pre>`, inline code, terminal/CLI UI, file paths — when documented in this design language.
- Section numbers use the **same face as section titles** — not mono — unless this design language says otherwise.
- No `--font-mono` in tokens unless Design tokens includes it. Use `font-variant-numeric: tabular-nums` on the **existing** face for stats — not a mono swap.

#### Colours

**Closed palette.** Use **only** colours in **Design tokens** (`:root` `--color-*` and any other colour tokens). **If a colour is not in Design tokens, do not use it.**

- Every `color`, `background`, `background-color`, `border-color`, `fill`, `stroke`, `box-shadow`, and gradient stop → `var(--*)` from Design tokens. **No inline hex, `rgb()`, `hsl()`, `oklch()`, or Tailwind arbitrary colours** outside `:root`.
- No invented hover/focus/active colours — only tokens in Design tokens or per-element values in **Primitive components** / **Reference components**.
- No new `--color-*` at build time. No default greys, lighter borders, or purple/blue accents.

```css
/* BAD — not in Design tokens */
.card {
  border-color: #333;
  background: rgba(255, 255, 255, 0.05);
}

/* GOOD */
.card {
  border-color: var(--color-border);
  background: var(--color-surface);
}
```

#### Layout

No purple/blue/pink gradient heroes; aurora blobs; equal 3-col icon grids; card-in-card; glassmorphism on gradients; fake browser/phone/IDE chrome; `width: 100vw`; identical section padding when this design language varies section by section.

**Exceptions only when documented in this design language:** gradient text (`background-clip: text`), glass frames, footer wordmarks — must appear in **Design tokens** and **Reference components** for that element.

Gradients only with stops from Design tokens.

#### Type, icons & motion

- Fonts from Design tokens only — no Inter/Roboto default when this design language names other faces; roman headings unless this design language uses italic.
- One icon library per page; no emoji feature icons like ✨, 🚀, 🎯, ⚡, 🔥, 💡
- Lottie, Three.js, or similar are allowed when they improve UI/UX — map timing and feel to **Motion system** and tokens, not generic bounce/elastic defaults.
- Motion from this design language only — no bounce/elastic, `transition-all`, universal `hover:scale-105`, scroll fade-up on every section unless documented; `:focus-visible` rings instant when added.

#### Libraries & dependencies

- **Dependencies (from source)** records fonts, scripts, and CDNs the template used — **reference only**, not a closed allowlist.
- Agents may add **any npm package or CDN** when it improves UI/UX (animation, icons, scroll, charts, accessibility, etc.) — map behaviour back to this design language's **Design tokens**, **Motion system**, and anti-slop guardrails.
- Prefer the user's stack when known. Libraries must not override closed palette, typography, casing, or documented motion signatures.

#### Content & media

- No invented stats, testimonials, or placeholder brands ("Acme", "Jane Doe") unless user brief overrides.
- **Extraction vs build:** Primitive and reference HTML snippets in this file use **role-based placeholders** (`Brand name`, `Section heading`, …) — not origin template copy and not fake brand names. When **building** a page, replace placeholders with the user's real brief content.
- Hero video: `autoplay muted loop playsinline`; LCP `fetchpriority="high"`, not `loading="lazy"`.
- Copy polish: curly quotes `"…"`; em-dash `—`; nav/CTAs `white-space: nowrap`; z-index from Design tokens — not `9999`.

Avoid generic filler vibes like:

- unleash
- elevate
- revolutionize
- next-gen
- seamless
- transformative platform

Avoid fake brand slop:

- Acme
- Nexus
- Flowbit
- Quantumly
- NovaCore

Avoid fake complexity slop:

- pseudo-enterprise control labels
- decorative system markers
- filler status microcopy
- fake operator / runtime / orchestration jargon unless truly central to the brand

---

## Design principles

### Style

A near-black charcoal canvas carries warm cream typography with restrained coral accent pulses — the mood is technical, confident, and product-forward without neon chaos. Inter drives both display and UI at medium weight with negative letter-spacing on large headlines; secondary copy sits in cool gray one step quieter than body. Geometry is pill-first: full-round buttons, tab capsules, and soft card radii on product chrome. Surfaces stay flat and editorial — depth comes from layered UI screenshots, drop-shadow glows on product mockups, and full-bleed imagery rather than heavy card stacks. A persistent center-axis guide line (dashed or solid) runs through the page like a drafting column, anchoring asymmetric headline grids. Motion is subtle: scroll-triggered fade-up reveals, pulsing accent underscores, and crossfading demo videos — never bouncy or playful. The overall energy is premium dev-tool SaaS: dark, precise, and demo-rich.

### Design system overview

**Visual identity & metaphor:** Product truth shown through real interface captures — the page is a sequence of live UI demonstrations framed by concise copy bands, not abstract metaphors.

**Color philosophy:** Charcoal field (`--color-bg`) with cream foreground (`--color-fg`) and cool gray muted text (`--color-muted`). One warm coral accent (`--color-accent`) marks emphasis words and pulses; feature CTAs use a separate hot-pink outline channel (`--feature-cta-primary`) distinct from the brand accent. Borders are low-alpha cream hairlines. Status and trust use a teal green outside the primary accent family.

**Typography:** Single sans family (Inter) for display and UI. Display headlines scale with `clamp()` and tight negative tracking; section titles split across two lines — first line cream, second line muted. Body stays 16px / 1.5; button labels are slightly smaller at 13px / medium weight.

**Shape & surface:** Pill radius on all primary actions and nav signup; 8px on nav link hover targets; 24px on product cards inside screenshots. Surfaces avoid nested card stacks — sections breathe on the flat dark field with 1px dividers.

**Layout & spacing:** Max content width ~1280px with 48px horizontal padding. Vertical rhythm alternates compact copy bands (~14–28rem) with tall viewport-bound demo modules (~50rem). Desktop uses 2-column headline grids (title left, meta right) inside feature bands. Center guide line is a recurring alignment device.

**Motion & interaction:** Intersection Observer fade-up on `[data-reveal]` elements; accent underscore pulse; tab panel switching without page navigation; autoplay muted video loops with opacity crossfade. Reduced-motion disables transforms.

**Accent & proof:** Logo strip at low opacity with gradient mask fade; testimonial portraits at full bleed; enterprise shields as minimal 3D glass icons; footer status dot with pulse animation.

**What this system rejects:** Purple gradient heroes, symmetric three-icon feature grids, glassmorphism cards floating on aurora backgrounds, decorative monospace labels, all-caps marketing eyebrows, stock handshakes, and whimsical illustration.

### Key characteristics

- Dark charcoal canvas with cream type — never pure black on pure white
- Split headlines: primary line in foreground, secondary line in muted gray
- Coral accent reserved for emphasis tokens (underscore pulse, keyword highlights) — not every CTA
- Hot-pink outline pill CTAs with arrow for feature deep-links — distinct from cream-filled primary buttons
- Center vertical guide line (dashed in copy bands, solid gradient in demo modules) as layout spine
- Full-bleed UI screenshot bands bleeding past container padding with left border anchor
- Fixed translucent nav with backdrop blur and three-column grid (logo | links | actions)
- Pill tab bars with inline SVG icons for demo switching
- Intersection Observer scroll reveals — opacity + translateY, one-shot unobserve
- Product mockup layering: workspace backdrop + centered recorder frame + autoplay webcam video
- Testimonial spotlight: quote column + portrait column + bottom logo tab strip
- Enterprise block uses 2×2 grid with hatch-pattern spacer and glass shield artwork
- Logo strip uses horizontal mask fade — opacity 0.7 default, full on hover
- Footer status link in teal with pulsing dot — separate from brand accent
- Section dividers as 1px `--color-border` rules at band bottoms
- Responsive: stack 2-column headline grids on mobile; hide decorative side videos on small screens

---

## Design tokens

```css
:root {
  /* Core palette */
  --color-bg: #100e0e;              /* page canvas — near-black charcoal */
  --color-fg: #fdfff0;                /* primary text — warm cream */
  --color-muted: #969692;             /* secondary text — cool gray */
  --color-accent: #e8453c;            /* brand emphasis — coral red */
  --color-border: rgba(253, 255, 240, 0.12); /* hairline dividers */
  --color-header-bg: rgba(16, 14, 14, 0.9);  /* fixed nav scrim */

  /* Feature CTA channel (outline pills in feature bands) */
  --feature-cta-primary: #ff0055;     /* hot pink outline + hover wash */

  /* Status / trust (footer operational dot) */
  --color-status: #00b093;            /* teal green — outside accent family */

  /* Typography families */
  --font-display: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-body: "Inter", ui-sans-serif, system-ui, sans-serif;

  /* Layout */
  --header-height: 64px;
  --layout-max: 1280px;
  --layout-padding: 48px;

  /* Radii */
  --radius-pill: 999px;
  --radius-card: 24px;
  --radius-nav-item: 8px;

  /* Type scale */
  --text-h1: clamp(2.5rem, 4vw, 3.75rem);
  --text-h1-lh: 1.1;
  --text-h1-ls: -0.018em;
  --text-h2: 1.125rem;
  --text-h2-lh: 1.44;
  --text-h3: 2.5rem;
  --text-h3-lh: 1.15;
  --text-body: 1rem;
  --text-body-lh: 1.5;
  --text-btn: 0.8125rem;

  /* Z-index */
  --z-header: 50;

  /* Motion */
  --motion-reveal-duration: 0.6s;
  --motion-reveal-distance: 1.5rem;
  --motion-hover-duration: 0.15s;
}
```

---

## Dependencies (from source)

| Asset | Type | Notes |
| --- | --- | --- |
| Google Fonts — Inter 400/500/600 | Font CDN | `fonts.googleapis.com` |
| Inline SVG icons | Icon | Lucide-style stroke icons embedded in HTML |
| Vanilla JS | Script | IntersectionObserver, tab switching, video carousel |
| `<picture>` element | Responsive images | Desktop JPG sources at 1024px+ breakpoint |

---

## Suggestions

- **Suggestion:** Add `:focus-visible` outline tokens for keyboard nav on tabs and CTAs — source relies on hover only.
- **Suggestion:** Consolidate `--feature-cta-primary` into semantic `--color-cta-feature` if expanding beyond feature bands.
- **Suggestion:** Add `--color-surface-raised` token if card-based dashboard adaptations need elevated panels.

---

## Motion system

| Technique | Timing / trigger | Used in source |
| --- | --- | --- |
| Scroll reveal fade-up | 0.6s ease, IO threshold 0.15 | Feature bands, hero copy, enterprise grid |
| Accent underscore pulse | 2s ease-in-out infinite | Emphasis token before keyword |
| Video crossfade carousel | 0.3s opacity, 6s interval | Product demo webcam layer |
| Product demo reveal | 1s ease translateY(2rem) | Workspace + recorder entrance |
| Tab panel switch | Instant display toggle | Use-case demos, testimonials |
| Status dot pulse | 2s ease-in-out infinite | Footer operational indicator |
| Nav/backdrop | 0.15s background on hover | Header links and login |

### Scroll reveal (`[data-reveal]`)

**Learn:** One-shot fade-up on enter — unobserve after reveal to avoid re-triggering. Use on copy and imagery in bands, not on every child element (group at band level).

**Implementation notes:** `opacity: 0; transform: translateY(var(--motion-reveal-distance))` → `.is-revealed` resets. `prefers-reduced-motion` disables transform.

### Video crossfade carousel

**Learn:** Layer muted autoplay videos with opacity crossfade — no hard cuts. Pair with poster frames for LCP.

**Implementation notes:** Active video gets `.is-active { opacity: 1 }`; swap on interval and `ended` event.

### Accent underscore pulse

**Learn:** Single-character accent pulse draws eye to a keyword without underline animation on full words.

**Implementation notes:** `animation: pulse 2s ease-in-out infinite` on accent span; disable in `prefers-reduced-motion`.

---

## Imagery direction

### Medium

| ID | Role in this language | Treatment |
| --- | --- | --- |
| ui-screenshot | Primary proof — product demos, feature bands | Full-bleed on dark canvas; left border anchor; desktop `<picture>` sources |
| photography | Social proof portraits | Full-bleed right column; warm presenter; dark gradient overlay at edge |
| 3d-render | Enterprise trust icons | Minimal glass shields on charcoal; subtle edge highlights |
| vector | Logo strips, tab labels, inline icons | Monochrome cream SVGs at reduced opacity |

### Style

| ID | Why it fits |
| --- | --- |
| technical | UI captures show real product chrome — precise, dark, tooling-native |
| minimal | Shield icons and logo strips are reduced, not ornate |
| realistic | Presenter portraits are documentary headshots — not stylized |
| cinematic | Feature screenshots embed presenter video in dramatic dark UI frames |

### Avoid

| ID | Why it clashes |
| --- | --- |
| anime | Breaks premium dev-tool positioning |
| watercolor | Too soft for charcoal technical canvas |
| whimsical-illustration | Undermines product-demo credibility |
| cartoon | Conflicts with real UI screenshot proof model |
| warm-editorial-portrait | Portraits here sit inside dark product UI — not warm lifestyle editorial |

**Learn:** Imagery lives in a **dark product UI world** separate from the page canvas warmth. Screenshots show real app chrome with embedded presenter video; portraits are documentary but framed inside dark gradients, not sunlit lifestyle stock. Pick images with low saturation backgrounds and high UI legibility. When generating assets, favor screen captures and minimal 3D icons — not illustration-forward hero art.

**Visual verification (Step 1b):** Inspected `home_share.jpg` (UI screenshot with presenter + chapters sidebar), `home_capture-mobile.jpg` (recorder overlay on cinematic lens background), `home_polish.jpg` (transcript editing UI with toolbar), `home_enterprise.jpg` (glass 3D shields), and testimonial portrait slot (documentary headshot per ideal frame).

---

## Primitive components

### Typography — display

**Purpose:** Primary marketing headline at largest scale.
**When to use:** Page hero, final CTA band.
**Avoid:** More than one display block per viewport.

**Learn:** Tight negative tracking and medium weight keep Inter feeling editorial, not default bootstrap bold.

```html
<h1 class="heading-display">
  <span>Display title line one</span>
  <span>Display title line two</span>
</h1>
```

```css
.heading-display {
  font-family: var(--font-display);
  font-size: var(--text-h1);
  font-weight: 500;
  line-height: var(--text-h1-lh);
  letter-spacing: var(--text-h1-ls);
  color: var(--color-fg);
}
```

### Typography — section heading

**Purpose:** Feature band titles with split emphasis.
**When to use:** Feature sections, enterprise block.

**Learn:** Second line in `--color-muted` creates rhythm without shrinking font size.

```html
<h3 class="heading-section">
  <span>Section heading</span>
  <span class="heading-section__muted">muted continuation.</span>
</h3>
```

### Typography — subhead

**Purpose:** Supporting paragraph below display title.
**When to use:** Directly under hero headline.

**Learn:** Muted gray at 18px — never compete with display size.

### Button — primary pill

**Purpose:** Main conversion action.
**When to use:** One primary per view cluster.
**Avoid:** Multiple filled cream buttons side by side without hierarchy.

**Learn:** Inverted cream-on-charcoal pill — high contrast without glow.

```html
<a class="btn btn--primary" href="#">Primary action</a>
```

```css
.btn--primary {
  background: var(--color-fg);
  color: var(--color-bg);
  border-radius: var(--radius-pill);
  padding: 0.625rem 1.25rem;
  font-size: var(--text-btn);
  font-weight: 500;
}
.btn--primary:hover { opacity: 0.9; }
```

### Button — outline

**Purpose:** Secondary action on dark field.
**When to use:** Paired with primary pill.

**Learn:** Hairline border from `--color-border` — no fill until hover wash.

### Button — ghost

**Purpose:** Tertiary text action.
**When to use:** Final CTA band secondary option.

**Learn:** Opacity hover only — no border needed when primary is filled nearby.

### CTA — feature outline pill

**Purpose:** Deep-link to feature page from band header.
**When to use:** Feature band meta column.

**Learn:** Hot-pink outline channel separates feature navigation from global signup CTA.

```html
<a class="feature-cta" href="#">
  <span>Feature label</span>
  <svg aria-hidden="true"><!-- arrow icon --></svg>
</a>
```

```css
.feature-cta {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--feature-cta-primary);
  border-radius: var(--radius-pill);
  color: var(--color-fg);
  font-size: var(--text-btn);
  font-weight: 500;
}
```

### Nav — link item

**Purpose:** Single navigation link or dropdown trigger.
**When to use:** Header center cluster.

**Learn:** 8px radius hover wash — not underline nav.

### Nav — signup pill

**Purpose:** Header conversion shortcut.
**When to use:** Header actions column.

**Learn:** Same inverted pill as primary button but smaller padding.

### Tab — pill with icon

**Purpose:** Switch demo panels without navigation.
**When to use:** Tab lists with 3–5 options.

**Learn:** Inline 14px SVG icon + label; active state gets top hairline and subtle gradient fill.

```html
<button type="button" class="tab is-active" role="tab" aria-selected="true">
  <svg class="tab__icon" aria-hidden="true"></svg>
  <span>Tab label</span>
</button>
```

### Divider — section rule

**Purpose:** Band separator.
**When to use:** Bottom of feature/demo modules.

**Learn:** 1px `--color-border` — not margin-only separation.

### Guide line — center axis

**Purpose:** Vertical alignment spine.
**When to use:** Full-height modules.

**Learn:** Dashed in copy bands, gradient-faded in tall demo modules — same center position.

### Badge — status dot

**Purpose:** Operational status indicator.
**When to use:** Footer status link.

**Learn:** Teal dot with pulse — color outside brand accent to signal "live/system".

### Icon — stroke inline

**Purpose:** UI affordances in tabs, CTAs, footer.
**When to use:** 14–16px inline with text.

**Learn:** `stroke="currentColor"` SVGs — no filled emoji substitutes.

---

## Reference components

### Fixed navigation (`#site-header`)

**Reference only** — source template header chrome; adapt or omit for other briefs.

**Role in source:** Persistent top bar with logo, centered nav links, login + signup actions.
**Primitives used:** Nav link item, Nav signup pill, stroke inline icons
**Learn:** Three-column grid keeps nav centered while logo and actions pin to edges — works on wide desktop without hamburger.

**If adapting:** Keep translucent scrim + blur on scroll; swap link list for app-specific IA; preserve pill signup as primary header conversion.

### Hero (`#section-hero`)

**Reference only**

**Role in source:** Opening copy band — display title, subhead with pulsing accent token, dual CTAs, trusted-by logo strip.
**Primitives used:** Typography display, Typography subhead, Button primary pill, Button outline, Guide line center axis
**Learn:** Copy band sits above product demo — headline grid uses 2-column meta at desktop with logos masked to fade at right edge.

```html
<section class="section--hero">
  <div class="hero">
    <div class="hero__guide" aria-hidden="true"></div>
    <div class="hero__copy">
      <div class="container">
        <h1 class="heading-display">Display title</h1>
        <h2 class="heading-sub">Subhead with <span class="accent-token">keyword</span></h2>
        <div class="hero__ctas">
          <a class="btn btn--primary" href="#">Primary action</a>
          <a class="btn btn--outline" href="#">Secondary action</a>
        </div>
        <div class="hero__logos"><!-- Logo strip --></div>
      </div>
    </div>
  </div>
</section>
```

**If adapting:** Keep bottom-weighted copy layout and logo mask; product mockup can move to separate band or be omitted for non-product briefs.

### Product demo (`#section-product-demo`)

**Reference only**

**Role in source:** Tall viewport module — workspace screenshot backdrop with centered recorder frame and crossfading webcam videos.
**Primitives used:** Guide line center axis, scroll reveal
**Learn:** Layered mockup with drop-shadow glow sells "real product" — video inside frame humanizes the demo.

**If adapting:** Replace workspace asset with your product shell; keep centered focal frame pattern and muted autoplay video.

### Use case demo (`#section-use-case`)

**Reference only**

**Role in source:** Centered split headline + pill tab bar + full-width embedded player iframe per tab.
**Primitives used:** Typography section heading, Tab pill with icon, Divider section rule
**Learn:** Tabs switch content panels in-place — headline stays stable while demo changes.

**If adapting:** Swap iframe for static screenshot or inline video; keep pill tablist centered above player.

### Feature band — capture (`#section-capture`)

**Reference only**

**Role in source:** Template for capture/share/polish/move bands — 2-col header grid + full-bleed screenshot.
**Primitives used:** Typography section heading, CTA feature outline pill, Guide line, scroll reveal
**Learn:** Header row (~14rem) then bleeding visual — title left, description + CTA right on desktop.

```html
<section class="section--feature">
  <div class="feature__header" data-reveal>
    <h3 class="heading-section">Section heading <span class="muted">continuation.</span></h3>
    <p class="feature__desc">Body text with <span class="accent">highlight phrase</span>.</p>
    <a class="feature-cta" href="#">Feature label</a>
  </div>
  <div class="feature__visual" data-reveal>
    <img src="[asset]" alt="Product screenshot" class="feature__image">
  </div>
</section>
```

**If adapting:** Reuse band structure for any feature count; swap screenshot and accent color per feature token.

### Benefits grid (`#section-benefits`)

**Reference only**

**Role in source:** Compact three-column value props with stroke icons and split titles.
**Primitives used:** Typography section heading, Icon stroke inline, Guide line
**Learn:** Short band (~20rem) between tall modules — icon glow uses accent color at low alpha.

**If adapting:** Adjust column count; keep icon + split headline + muted description pattern.

### Testimonials (`#section-testimonials`)

**Reference only**

**Role in source:** Large quote + attribution + CTA left; full-bleed portrait right; bottom logo tab bar switches customers.
**Primitives used:** Tab pill, Button ghost, scroll reveal
**Learn:** Portrait bleeds to container edge; tab bar is a 4-column grid with active top rule — social proof as spotlight not carousel dots.

**If adapting:** Keep asymmetric split; swap tab labels for your customer logos.

### Enterprise (`#section-enterprise`)

**Reference only**

**Role in source:** 2×2 grid — headline, compliance copy, shield artwork, dual CTAs; hatch spacer above.
**Primitives used:** Typography section heading, Button primary pill, Button outline
**Learn:** Hatch-pattern spacer signals "infrastructure band" without extra copy.

**If adapting:** Replace shields with your compliance artwork; keep 2×2 grid and dual CTA pairing.

### Get started (`#section-get-started`)

**Reference only**

**Role in source:** Centered final CTA with decorative side portrait videos at low opacity.
**Primitives used:** Typography display, Button primary pill, Button ghost
**Learn:** Tall centered band (~50rem) — side videos are atmosphere only, hidden on mobile.

**If adapting:** Omit side videos for simpler close; keep centered stack and dual CTA.

### Footer (`#section-footer`)

**Reference only**

**Role in source:** Logo + status + vulnerability link; 4-column nav; legal row + compliance badge pills.
**Primitives used:** Badge status dot, Nav link item, Divider section rule
**Learn:** Desktop uses 50/50 split (brand+product | resources+company+connect); mobile stacks 2-col nav grid.

**If adapting:** Reduce nav columns for smaller products; keep status dot + compliance badges for trust-heavy sites.

---

## Composition guide

### Applying the design language to any brief

1. Start from **Design principles** — charcoal canvas, cream type, coral accent discipline.
2. Map all colors to **Design tokens** — add semantic tokens if the brief needs surfaces beyond flat field.
3. Build UI from **Primitive components** — pills, split headings, feature CTAs, tabs.
4. Study **Reference components** for rhythm inspiration — do not copy every band for a dashboard or settings page.
5. Pick imagery from **Imagery direction** — UI screenshots and minimal 3D, not stock lifestyle.
6. Apply **Motion system** sparingly — one reveal per band, not per element.
7. **Ship responsive** — stack 2-column grids, hide decorative videos, scale type with clamp().

For app UI (dashboard, settings, onboarding): use flat charcoal field, cream text, pill primary buttons, hairline borders, and compact spacing — omit full-bleed screenshot bands and viewport-tall demo modules.

### Source page rhythm

Reference order only: fixed nav → hero copy → product demo mockup → tabbed use-case player → four feature bands (capture/share/polish/move) → three-column benefits → testimonial spotlight → enterprise grid → final CTA → footer.

### Combining primitives

- One cream primary pill per CTA cluster; outline/ghost for secondary.
- Split headings always: line one `--color-fg`, line two `--color-muted`.
- Feature CTAs use hot-pink outline channel — not coral accent fill.
- Center guide line aligns headlines and demo modules — keep consistent `left: 50%` position.

### Animation stacking

- Max one scroll reveal group per band (header group + visual group, not every child).
- Tab switches are instant — no slide animation.
- Video crossfade only in product demo layer.
- Always provide `prefers-reduced-motion` fallbacks.

### New work checklist

- [ ] All colors from Design tokens?
- [ ] One motion signature per viewport (not reveal + bounce + parallax)?
- [ ] Primitives consistent (pill buttons, split headings)?
- [ ] Imagery matches technical/ui-screenshot direction?
- [ ] Responsive layout implemented mobile through desktop?
- [ ] No origin template copy in shipped content?

---

## Appendix: global scripts

### `initRevealAnimations()`

Powers: scroll reveal on all `[data-reveal]` elements across reference components.

Uses `IntersectionObserver` with `threshold: 0.15` and `rootMargin: '0px 0px -10% 0px'`. Adds `.is-revealed` class and unobserves.

### `initTabs()`

Powers: use-case demo tabs, testimonials customer tabs.

Click handler toggles `.is-active` on tabs and matching `[data-tab-panel]` panels; sets `aria-selected`.

### `initProductDemoCarousel()`

Powers: product demo webcam video crossfade.

Swaps `.is-active` between videos on 6s interval and `ended` event; opacity transition 0.3s.

Read the design spec and follow instructions. the whole plan for frountend designign is prvodied.use 3 aubagents to make it success in detialed manner
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-09-22T21:59:40+05:30.
</ADDITIONAL_METADATA>