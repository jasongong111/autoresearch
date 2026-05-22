---
name: Langfuse Dashboard
description: Dense, table-first observability UI for LLM engineering workflows
colors:
  background: "#ffffff"
  foreground: "#020817"
  muted: "#f1f5f9"
  muted-foreground: "#64748b"
  border: "#e2e8f0"
  header: "#f8fafc"
  primary: "#0f172a"
  primary-foreground: "#f8fafc"
  primary-accent: "#4e46e5"
  primary-accent-hover: "#6366f1"
  secondary: "#f1f5f9"
  destructive: "#ef4444"
  success-bg: "#dcfce7"
  success-fg: "#134e4a"
  error-bg: "#fce7f2"
  error-fg: "#dc2626"
  warning-bg: "#fefce8"
  warning-fg: "#c89004"
  info-bg: "#dbeafe"
  info-fg: "#3b83f6"
  sidebar-background: "#ffffff"
  sidebar-border: "#e2e8f0"
  dark-background: "#020817"
  dark-foreground: "#c2d4e5"
  dark-muted: "#1e293b"
  dark-border: "#2f415d"
  dark-primary-accent: "#9188dd"
typography:
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, system-ui, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, system-ui, sans-serif"
    fontSize: "1.1rem"
    fontWeight: 600
    lineHeight: 1.75
    letterSpacing: "normal"
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, system-ui, sans-serif"
    fontSize: "0.825rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "normal"
  table-body:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, system-ui, sans-serif"
    fontSize: "0.7rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    fontSize: "0.7rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
rounded:
  sm: "4px"
  md: "8px"
  lg: "8px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  sidebar-expanded: "184px"
  sidebar-icon: "48px"
  control-height: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.md}"
    height: "{spacing.control-height}"
    padding: "4px 12px"
  button-primary-hover:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.md}"
    height: "{spacing.control-height}"
    padding: "4px 12px"
  button-secondary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    height: "{spacing.control-height}"
    padding: "4px 12px"
  button-outline:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    height: "{spacing.control-height}"
    padding: "4px 12px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    height: "{spacing.control-height}"
    padding: "4px 12px"
  input-default:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    height: "{spacing.control-height}"
    padding: "4px 8px"
  badge-success:
    backgroundColor: "{colors.success-bg}"
    textColor: "{colors.success-fg}"
    rounded: "{rounded.md}"
    padding: "2px 10px"
  badge-error:
    backgroundColor: "{colors.error-bg}"
    textColor: "{colors.error-fg}"
    rounded: "{rounded.md}"
    padding: "2px 10px"
  card-default:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.lg}"
    padding: "16px"
  tab-active:
    backgroundColor: "transparent"
    textColor: "{colors.foreground}"
    rounded: "0px"
    padding: "2px 8px"
---

# Design System: Langfuse Dashboard

> **Source of truth:** `web/src/styles/globals.css` (CSS variables), `web/src/components/ui/*` (components), `web/components.json` (shadcn config).

## Overview

**Creative North Star: "The Instrument Panel"**

Langfuse is a product UI for ML engineers who spend hours inside traces, scores, prompts, and datasets. The interface should feel like a well-calibrated instrument: familiar enough to trust immediately, dense enough to scan quickly, and quiet enough to stay out of the way during debugging sessions.

The dashboard follows a **Restrained** color strategy: cool slate neutrals carry most surfaces, and a single indigo accent marks selection, navigation state, and domain entities. Layout is table-first with collapsible sidebar navigation, sticky two-row page headers, and inline peek panels instead of modal-heavy flows.

**Key characteristics:**

- Light-first with system-aware dark mode (`next-themes`, class-based)
- Compact type scale (body at 0.9rem, table body at 0.7rem)
- shadcn/ui on Radix primitives, Tailwind CSS v4, `class-variance-authority` variants
- Border-forward separation; minimal shadow (`shadow-xs` only)
- Consistent 32px control height (`h-8`) across buttons and inputs
- Lucide outline icons at 12–16px
- Skeleton loading over in-content spinners

**Stack:** Tailwind v4 · shadcn/ui (baseColor: slate) · Radix UI · TanStack Table · Sonner toasts · lucide-react

## Colors

Slate neutrals with a single indigo accent. Semantic states use tinted background + saturated foreground pairs, never raw saturated fills on large surfaces.

### Primary

- **Deep Slate** (`#0f172a` / `hsl(222.2 47.4% 11.2%)`): Primary button fill, high-contrast actions. Paired with `#f8fafc` foreground text.
- **Signal Indigo** (`#4e46e5` / `hsl(243 75.4% 58.6%)`): Brand accent. Active tabs, entity highlights, selected navigation indicators. Hover: `#6366f1`.

### Secondary

- **Cool Mist** (`#f1f5f9` / `hsl(210 40% 96.1%)`): Secondary buttons, muted fills, table row hover (`muted/50`), sidebar accent hover.

### Tertiary

- **Header Wash** (`#f8fafc` / `hsl(210 40% 98%)`): Page header band (`bg-header`), visually separating title/actions from content without heavy elevation.

### Neutral

- **Paper White** (`#ffffff`): Page background, cards, popovers, sidebar (light mode).
- **Ink Slate** (`#020817`): Primary text (`foreground`).
- **Quiet Slate** (`#64748b`): Secondary text (`muted-foreground`), table headers, labels.
- **Hairline** (`#e2e8f0`): Borders on inputs, cards, table rows, sidebar dividers.

### Semantic

- **Success:** background `#dcfce7`, foreground `#134e4a` (badge variant `success`)
- **Error:** background `#fce7f2`, foreground `#dc2626` (badge variant `error`, destructive actions `#ef4444`)
- **Warning:** background `#fefce8`, foreground `#c89004` (badge variant `warning`)
- **Info:** background `#dbeafe`, foreground `#3b83f6` (callouts, informational alerts)

### Domain entity accents

Observation and resource types use distinct icon colors (see `ItemBadge.tsx`):

| Entity | Token | Usage |
|--------|-------|-------|
| Trace | `dark-green` | Tree/list icon |
| Generation | `muted-magenta` | Fan icon |
| Span | `muted-blue` | Horizontal move icon |
| Session, Dataset, Prompt, etc. | `primary-accent` | Shared indigo |

### Dark mode

Same token names, inverted values. Background `#020817`, foreground `#c2d4e5`, muted surface `#1e293b`, border `#2f415d`, accent softens to `#9188dd`. Components reference CSS variables; never hardcode light-only hex in JSX.

### Named Rules

**The One Accent Rule.** `primary-accent` appears on active tabs, current selection, entity badges, and key links only. It should occupy ≤10% of any screen. Its rarity signals interactivity.

**The Pair Rule.** Success, error, and warning always use a tinted background with a darker foreground. Never place saturated red/green/yellow as large surface fills.

## Typography

**Body Font:** System UI stack (`-apple-system, BlinkMacSystemFont, Segoe UI, system-ui, sans-serif`)  
**Mono Font:** `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`

No custom webfont is loaded. The interface inherits native platform rendering for speed and familiarity.

**Character:** Compact, utilitarian, and scan-friendly. Hierarchy comes from weight and size steps, not display type.

### Hierarchy

Fixed rem scale defined in `@theme inline` (`globals.css`):

| Role | Size | Weight | Usage |
|------|------|--------|-------|
| Page title | 1.1rem (`text-lg`) | 600 | Sticky page header (`h2`) |
| Section label | 0.825rem (`text-sm`) | 500 | Form labels, panel headings |
| Body | 0.9rem (`text-base`) | 400 | General UI copy |
| Table header | 0.825rem (`text-sm`) | 500 | Column headers, `text-muted-foreground` |
| Table body | 0.7rem (`text-xs`) | 400 | Dense data rows |
| Badge | 0.7rem (`text-xs`) | 600 | Status and entity badges |
| Code/JSON | 0.7rem mono | 400 | Trace payloads, JSON viewers |

Scale ratio between steps is ~1.125–1.2 (tighter than marketing sites). Prose blocks cap at 65–75ch; tables may run wider.

OpenType features enabled on body: `"rlig" 1, "calt" 1`.

### Named Rules

**The Density Rule.** Default to `text-sm` or smaller for interactive UI. Reserve `text-lg` and above for page titles only.

**The Mono Rule.** Any machine-readable content (IDs, JSON keys, token counts, timestamps in tables) uses monospace at `text-xs`.

## Elevation

Langfuse is **flat-by-default with border separation**. Depth is conveyed through tonal layering (`background` → `header` → `muted` hover states), not shadow stacks.

### Shadow Vocabulary

- **Resting card/panel:** `shadow-xs` (barely perceptible; defined by Tailwind v4 theme)
- **Sticky page header:** `shadow-xs` + `border-b` (structural, not decorative)
- **Popovers, dropdowns, sheets:** border + background contrast; no heavy drop shadow

No glassmorphism, no gradient overlays, no floating card stacks.

### Depth via surfaces

| Layer | Token | Role |
|-------|-------|------|
| Base | `background` | Page canvas |
| Raised band | `header` | Page header second row |
| Interactive hover | `muted/50` | Table rows, ghost buttons |
| Overlay | `popover` | Dropdowns, tooltips, command menu |

### Named Rules

**The Flat-By-Default Rule.** Surfaces at rest have no shadow. Elevation appears only on sticky headers and subtle card containers.

**The Border Rule.** Prefer `border-b` and `border` over shadow to separate regions. Nested cards are avoided; use panels and tables instead.

## Components

Built on shadcn/ui defaults with Langfuse-specific extensions. All interactive components implement default, hover, focus-visible, active, disabled, and loading states where applicable.

### Buttons

- **Shape:** `rounded-md` (8px), default height 32px (`h-8`)
- **Primary:** `bg-primary text-primary-foreground`, hover `bg-primary/90`
- **Secondary:** `bg-secondary text-secondary-foreground`
- **Tertiary:** compact variant, `text-xs font-medium`
- **Outline:** `border border-input bg-background`, hover `bg-accent`
- **Ghost:** no fill, hover `bg-accent` (icon buttons in tables)
- **Destructive:** `bg-destructive` for irreversible actions
- **Focus:** `ring-2 ring-ring ring-offset-2` on focus-visible
- **Loading:** inline spinner, button disabled during load

Sizes: `default h-8`, `sm h-6`, `lg h-9`, `icon h-8 w-8`, `icon-xs h-6 w-6`.

### Inputs

- Height 32px, `border-input rounded-md px-2 text-sm`
- Placeholder: `text-muted-foreground`
- Disabled: `bg-muted/50 opacity-50 cursor-not-allowed`
- Focus: ring removed on input (`focus:ring-0`); rely on border contrast

### Badges

- `rounded-md border font-semibold text-xs px-2.5 py-0.5`
- Semantic variants: `success`, `error`, `warning` use paired tint colors
- Entity badges: `outline` variant + Lucide icon + optional truncated label

### Cards

- `rounded-lg border shadow-xs bg-card p-4`
- Used for isolated content blocks; not the default layout primitive
- Nested cards are avoided

### Tables

Primary UI surface. TanStack Table with Langfuse column definitions.

- `table-fixed border-separate border-spacing-0 text-sm`
- Header cells: `bg-background text-muted-foreground font-medium h-10 border-b px-2`
- Body cells: `text-xs`, compact density (`py-0 px-2`) or comfortable (`p-2`)
- Row hover: `hover:bg-muted/50 transition-colors`
- Selected row: `data-[state=selected]:bg-muted`
- Loading: skeleton cells, not centered spinners

### Tabs

Underline style, not pills:

- Inactive: `border-b-4 border-transparent text-sm font-medium`
- Active: `border-b-4 border-primary-accent` (4px indigo bottom border)
- Hover: `hover:bg-muted/50`

Used in page headers (`PageHeader`) and `TabsBar` component.

### Sidebar

- Expanded width: 184px (`11.5rem`); icon mode: 48px (`3rem`)
- Collapsible via `Cmd/Ctrl+B`, state persisted in localStorage
- Mobile: sheet overlay
- Logo, grouped nav, notifications, user menu in footer

### Page header

Two-row sticky header (`top-banner-offset z-30 border-b shadow-xs`):

1. **Top row:** sidebar trigger, environment label, breadcrumbs
2. **Bottom row:** entity badge, page title (`text-lg font-semibold`), action buttons, optional tabs

Content max-width on container pages: `max-w-screen-xl` / `2xl:max-w-[1400px]`.

### Loading and feedback

- **Skeleton:** `bg-muted animate-pulse rounded-md`
- **Toasts:** Sonner, non-blocking mutation feedback
- **Tooltips:** Radix tooltip, `max-w-xs` for long titles

### Icons

- Library: Lucide React (outline style)
- Sizes: `h-3 w-3` (inline actions), `h-3.5 w-3.5` (filters), `h-4 w-4` (nav, badges)

### Layout shell

```
SidebarProvider → AppSidebar + SidebarInset
  → Page (sticky PageHeader + main content)
    → DataTable / forms / peek panels
```

Peek panels and resizable split views (`ResizableDesktopLayout`) show detail inline without full navigation.

### Motion

| Pattern | Value |
|---------|-------|
| Color transitions | `transition-colors` (~150ms) |
| Accordion | `0.2s ease-out` |
| Appear fade | `0.2s ease-out` |
| Theme switch | `disableTransitionOnChange` (no flash) |

No page-load animation sequences. Motion conveys state change only.

## Do's and Don'ts

### Do

- Use CSS variable tokens (`bg-background`, `text-muted-foreground`, `border-primary-accent`) so light/dark mode works automatically
- Keep controls at `h-8` (32px) baseline height for visual rhythm
- Prefer data tables with inline peek/detail panels over modal-first flows
- Use `primary-accent` sparingly for active/selected states
- Apply skeleton loaders for table and panel loading states
- Use `cn()` (`clsx` + `tailwind-merge`) for conditional classes
- Define component variants with `cva` + `VariantProps`
- Support `top-banner-offset` / `min-h-screen-with-banner` when sticky elements anchor to viewport
- Write compact copy; labels should be scannable in dense layouts

### Don't

- Load display or marketing fonts into the product UI
- Use gradient text, glassmorphism, or side-stripe colored borders on alerts
- Build identical icon + heading + text card grids for every feature
- Default to modals when inline expansion or drawers would preserve context
- Use saturated accent colors on large inactive surfaces
- Hardcode hex colors in components (always reference tokens)
- Use spinners inside table body cells
- Nest cards inside cards
- Invent custom form controls when shadcn/Radix patterns exist
- Enlarge the type scale for "visual hierarchy" (use weight and muted color instead)

---

## Migration quick reference

Copy in this order when porting to another project:

1. CSS variables from `web/src/styles/globals.css` (`:root` + `.dark`)
2. Tailwind v4 `@theme inline` block (color, radius, text scale mappings)
3. shadcn/ui init with `baseColor: slate`, `cssVariables: true`
4. Langfuse overrides: `Button`, `Badge`, `Table`, `TabsBar`, `sidebar`
5. Layout: `SidebarProvider` → `PageHeader` → `Page`
6. Utilities: `cn()` in `web/src/utils/tailwind.ts`

**Key files:**

| File | Purpose |
|------|---------|
| `web/src/styles/globals.css` | All design tokens |
| `web/components.json` | shadcn configuration |
| `web/src/components/ui/*` | Component library |
| `web/src/components/layouts/*` | App shell and page structure |
| `web/src/components/table/*` | Data table patterns |
