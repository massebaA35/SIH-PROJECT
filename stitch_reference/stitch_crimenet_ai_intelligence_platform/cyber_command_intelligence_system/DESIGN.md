---
name: Cyber Command Intelligence System
colors:
  surface: '#0e1321'
  surface-dim: '#0e1321'
  surface-bright: '#343948'
  surface-container-lowest: '#090e1c'
  surface-container-low: '#161b2a'
  surface-container: '#1a1f2e'
  surface-container-high: '#252a39'
  surface-container-highest: '#303444'
  on-surface: '#dee2f6'
  on-surface-variant: '#b9cacb'
  inverse-surface: '#dee2f6'
  inverse-on-surface: '#2b303f'
  outline: '#849495'
  outline-variant: '#3b494b'
  surface-tint: '#00dbe9'
  primary: '#dbfcff'
  on-primary: '#00363a'
  primary-container: '#00f0ff'
  on-primary-container: '#006970'
  inverse-primary: '#006970'
  secondary: '#b4c5ff'
  on-secondary: '#002a78'
  secondary-container: '#0053db'
  on-secondary-container: '#cdd7ff'
  tertiary: '#d8ffe7'
  on-tertiary: '#003824'
  tertiary-container: '#65f2b5'
  on-tertiary-container: '#006d4a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#7df4ff'
  primary-fixed-dim: '#00dbe9'
  on-primary-fixed: '#002022'
  on-primary-fixed-variant: '#004f54'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0e1321'
  on-background: '#dee2f6'
  surface-variant: '#303444'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0.02em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  code-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.08em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  space-2xs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
  space-2xl: 2rem
  space-3xl: 3rem
  gutter-mobile: 0.75rem
  gutter-desktop: 1.25rem
  margin-screen: 1.5rem
---

## Brand & Style

This design system delivers an operational, mission-critical intelligence interface engineered for law enforcement, cyber analysts, and defense units. It merges precision tactical data visualization with an austere, cyber-command center aesthetic. 

### Design Philosophy
- **Tactical Authority:** Every line, value, and container conveys operational readiness, strict verification, and evidentiary weight. There are no ornamental flourishes or game-like tropes.
- **Glassmorphic Precision:** Glass layers do not simulate decorative frost; they serve as tactical heads-up display (HUD) projections—thin, razor-edged, translucent dark-navy strata that isolate complex data matrices without obscuring global telemetry.
- **Cognitive Clarity Under Stress:** Information density is high, but spatial hierarchy is disciplined. System status, investigative priority, and AI confidence scores are parseable within milliseconds via structured contrast and deterministic color coding.
- **Auditable Integrity:** Data integrity indicators, chain-of-custody tags, and cryptographic provenance markers are treated as primary visual anchors rather than afterthoughts.

## Colors

The system is built natively and exclusively for high-contrast dark mode command terminals. The palette simulates luminous telemetry projected over deep subterranean control surfaces.

### Core Hierarchy
- **Base Canvas (`#0a0f1d`):** Deep abyssal navy serving as the foundational background layer.
- **Surface Elevation 1 (`#0d1527`):** Base structural container for persistent panes, sidebars, and structural framing.
- **Surface Elevation 2 (`#131f37`):** Analytical cards, floating data panels, and focused module surfaces.
- **Surface Elevation 3 (`#1b2a4a`):** Active inspector panels, interactive hovering elements, and modal scrim overlays.

### Accents & Signal Indicators
- **Electric Cyan (`#00f0ff`, Secondary: `#06b6d4`):** Primary interactive focal point, telemetry paths, active network nodes, and high-frequency data streams.
- **Cobalt Blue (`#2563eb`, Secondary: `#3b82f6`):** Structural highlights, systematic links, contextual metadata, and secondary operational workflows.
- **Emerald Green (`#10b981`):** Verified chain of custody, system integrity nominal, authenticated identities, and cryptographically signed data.
- **Amber Warning (`#f59e0b`):** Investigative escalation, cross-node anomalies, moderate threat thresholds, and pending evidentiary reviews.
- **Crimson Alert (`#ef4444`):** Critical intrusion, imminent threat, priority red-flag anomalies, and chain-of-custody breaches.

### Contrast & Boundaries
- **Border Rim Subtle:** `rgba(6, 182, 212, 0.15)` for standard component edges.
- **Border Rim Active:** `rgba(0, 240, 255, 0.40)` with a `0 0 10px rgba(0, 240, 255, 0.2)` soft optical fringe for focused or escalated states.

## Typography

The type system implements a strict functional divide between narrative comprehension, tactical headlines, and forensic data streams.

### Typographic Disciplines
- **Space Grotesk (Display & Section Headers):** Delivers clean, geometric tension with a technical edge. Headlines command visual order across heavy analytics dashboards without overwhelming the underlying data.
- **Inter (Body Text & Operational Logs):** Highly neutral and legible for investigative briefs, long-form dossier notes, and contextual reports. It prevents eye fatigue in sustained low-light monitoring environments.
- **JetBrains Mono (System Telemetry, Metrics, Code & Provenance Tags):** The tactical spine of the system. Used for IP addresses, hash strings, confidence matrices, timestamps, and metadata keys. Numbers are tabular to guarantee strict vertical alignment across dense analytical columns.

### Application Rules
- All labels, evidence status indicators, and operational priority tags must render in `label-caps` or `code-sm` with upper casing.
- Hash digests, MAC addresses, and coordinates must strictly leverage `code-md` or `code-sm` with non-proportional tabular figures.

## Layout & Spacing

The layout is architected as an adaptive intelligence command console utilizing a modular 12-column fluid grid system paired with strict 4px/8px micro-spacing rhythms.

### Grid & Viewport Model
- **Command Workspace:** Spans the entire screen (zero arbitrary page gutters in workstation views), using fixed analytical toolbars and responsive fluid panels.
- **Desktop (>=1440px):** 12-column matrix with 20px (`1.25rem`) gutters. Side rail navigation remains compact (64px collapsed, 240px expanded). Split-pane investigative consoles maintain minimum widths of 380px for dossiers and 640px for graph topologies.
- **Tablet (768px - 1439px):** 8-column layout. Analytical graph and dossier panels collapse from side-by-side into a tabbed layout.
- **Mobile (<768px):** 4-column layout with 12px (`0.75rem`) gutters. Interactive network visualizations convert into ranked tabular cards or prioritized alert feeds.

### Spacing Principles
- Density is dialed high to maximize visible screen real estate.
- Component padding relies on tight 8px (`space-sm`) and 12px (`space-md`) increments to keep forensic records and related telemetry visually grouped.
- Related telemetry clusters use `space-xs` (4px) to signal atomic cohesion.

## Elevation & Depth

Visual hierarchy is built via structural translucency, low-light illumination, and subtle laser-etched border rims rather than traditional drop shadows.

### Depth Stratification
- **Ground Floor (Z-0):** Unlit `#0a0f1d` with an optional 32px radial grid matrix (`rgba(0, 240, 255, 0.03)` grid lines) providing spatial grounding for canvas operations.
- **Structural Trays (Z-10):** Background `#0d1527` at 85% opacity with `backdrop-filter: blur(12px)`. Enclosed by a 1px solid border of `rgba(255, 255, 255, 0.05)`.
- **Active Surveillance Glass (Z-20):** Background `#131f37` at 70% opacity with `backdrop-filter: blur(16px)`. Bordered by `1px solid rgba(6, 182, 212, 0.20)`. Visual edge glow is handled via `box-shadow: inset 0 1px 0 0 rgba(0, 240, 255, 0.15)`.
- **Target Overlay & Alert Focus (Z-30):** Elevated investigative modals and active node popovers. Background `#1b2a4a` at 90% opacity with `backdrop-filter: blur(24px)`. Bordered by `1px solid rgba(0, 240, 255, 0.45)` with an ambient emission of `box-shadow: 0 0 24px rgba(0, 240, 255, 0.12)`.

### Shadow & Illumination Rules
- Never use black or muddy multi-layer ambient drop shadows.
- Surface transitions and interactive focus states project faint directional neon emissions matching the semantic state of the element (e.g., cyan for selected nodes, crimson for critical alerts).

## Shapes

The design system employs a soft-industrial, engineered shape geometry. Sharp, utilitarian lines dominate, softened minimally at contact points to maintain high structural density without appearing brutalist or dated.

### Geometry Specifications
- **Base Components (Inputs, Buttons, Cards, Badges):** Fixed at `4px` (`0.25rem`, soft). This preserves an angular, machine-milled aesthetic.
- **Surface Panels & Modals:** Scaled to `6px` or `8px` (`rounded-lg`) maximum to frame complex intelligence workspaces cleanly.
- **Data Nodes & Graph Pins:** Perfectly circular (`50%`) to contrast against rigid rectangular container geometry.
- **Chamfer Accents:** Key investigative dossier panels and alert headers may feature single-corner 45-degree chamfered cuts (8px clip-path) to reinforce the tactical cyber HUD theme.

## Components

### Buttons & Tactical Triggers
- **Primary Cyber Trigger:** Background `rgba(0, 240, 255, 0.12)`, border `1px solid #00f0ff`, text `#00f0ff`. On hover, background shifts to `#00f0ff`, text snaps to `#0a0f1d`, with a subtle aura: `box-shadow: 0 0 16px rgba(0, 240, 255, 0.4)`. Text is uppercase `label-caps`.
- **Secondary Operation:** Background `rgba(255, 255, 255, 0.03)`, border `1px solid rgba(255, 255, 255, 0.12)`, text `#e2e8f0`. Hover transitions to `rgba(255, 255, 255, 0.08)` and border `rgba(255, 255, 255, 0.25)`.
- **Destructive / High Priority:** Background `rgba(239, 68, 68, 0.1)`, border `1px solid #ef4444`, text `#ef4444`. Hover causes background `#ef4444`, text `#0a0f1d`, with red halo illumination.

### Priority & Provenance Badges
- **Investigation Priority Indicators:** 
  - `P1 - CRITICAL`: Crimson background (`rgba(239, 68, 68, 0.15)`), border `1px solid #ef4444`, text `#fca5a5`, accompanied by a blinking 6px status beacon.
  - `P2 - ELEVATED`: Amber background (`rgba(245, 158, 11, 0.15)`), border `1px solid #f59e0b`, text `#fcd34d`.
  - `P3 - ROUTINE`: Cobalt background (`rgba(37, 99, 235, 0.15)`), border `1px solid #3b82f6`, text `#93c5fd`.
- **Evidence Provenance Tag:** Monospaced label (`code-sm`) featuring a lock or hash prefix, background `rgba(16, 185, 129, 0.08)`, border `1px solid rgba(16, 185, 129, 0.3)`, text `#34d399`. Conveys cryptographic verification (e.g., `SHA-256: 4f8a...e9b1`).

### AI Explainability & Confidence Metrics
- **Confidence Rating Unit:** Compact horizontal telemetry bar paired with tabular percentage readout (e.g., `94.8% MATCH`). Progress fill uses a dual-stop linear gradient (`#2563eb` to `#00f0ff`).
- **Explainability Drawer / Hover Matrix:** Micro-card listing contributing feature weights with fractional deviations (`+0.42 Network Proximity`, `-0.18 Geolocation Anomaly`) in `code-sm`.

### Input & Query Fields
- Deep navy background (`#0a0f1d`), inset border `1px solid rgba(6, 182, 212, 0.25)`, text `#f8fafc`, placeholder text `rgba(148, 163, 184, 0.5)`. Typography: `code-md`.
- Focus state triggers a vibrant cyan border (`#00f0ff`) and an inner glowing ring (`box-shadow: inset 0 0 4px rgba(0, 240, 255, 0.2)`).
- Prefix icons (search loupe, terminal caret `>`) render in muted cyan (`#06b6d4`).

### Network Graph Nodes & Entity Cards
- **Graph Nodes:** Crisp circular vector vertices with interactive concentric shock rings on active inspection. Rings pulse via cyan or crimson outlines according to alert level.
- **Glass Dossier Cards:** Background `#0d1527` at 75% opacity, `backdrop-filter: blur(12px)`, border `1px solid rgba(6, 182, 212, 0.2)`. Header contains monospaced record identifier, target entity title, and priority tag pinned to top-right.

### Data Tables & Forensic Feeds
- Header row uses uppercase `label-caps` in muted slate (`#64748b`) with a bottom boundary of `1px solid rgba(255, 255, 255, 0.08)`.
- Alternating zebra striping is rejected in favor of razor-thin divider lines (`rgba(255, 255, 255, 0.04)`). Hovering over a record applies a subtle cyan tint highlight across the entire row (`rgba(0, 240, 255, 0.04)`).