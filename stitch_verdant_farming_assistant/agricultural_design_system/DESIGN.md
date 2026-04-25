---
name: Agricultural Design System
colors:
  surface: '#f7fbf1'
  surface-dim: '#d8dbd2'
  surface-bright: '#f7fbf1'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f5ec'
  surface-container: '#ecefe6'
  surface-container-high: '#e6e9e0'
  surface-container-highest: '#e0e4db'
  on-surface: '#191d17'
  on-surface-variant: '#41493e'
  inverse-surface: '#2d322c'
  inverse-on-surface: '#eff2e9'
  outline: '#717a6d'
  outline-variant: '#c0c9bb'
  surface-tint: '#2a6b2c'
  primary: '#00450d'
  on-primary: '#ffffff'
  primary-container: '#1b5e20'
  on-primary-container: '#90d689'
  inverse-primary: '#91d78a'
  secondary: '#556158'
  on-secondary: '#ffffff'
  secondary-container: '#d9e6da'
  on-secondary-container: '#5b675e'
  tertiary: '#6b1d3d'
  on-tertiary: '#ffffff'
  tertiary-container: '#883454'
  on-tertiary-container: '#ffaec6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#acf4a4'
  primary-fixed-dim: '#91d78a'
  on-primary-fixed: '#002203'
  on-primary-fixed-variant: '#0c5216'
  secondary-fixed: '#d9e6da'
  secondary-fixed-dim: '#bdcabe'
  on-secondary-fixed: '#131e17'
  on-secondary-fixed-variant: '#3e4a41'
  tertiary-fixed: '#ffd9e2'
  tertiary-fixed-dim: '#ffb1c8'
  on-tertiary-fixed: '#3e001d'
  on-tertiary-fixed-variant: '#7a2949'
  background: '#f7fbf1'
  on-background: '#191d17'
  surface-variant: '#e0e4db'
typography:
  h1:
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  h2:
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  h3:
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-caps:
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  margin-mobile: 16px
  margin-desktop: 32px
  gutter: 16px
---

## Brand & Style

The brand personality for this design system is **Precision Agriculture**. It targets modern farm owners, agronomists, and enterprise stakeholders who view farming through the lens of data-driven stewardship. The UI evokes a sense of calm authority, reliability, and growth.

The design style is **Minimalist with Subtle Glassmorphism**. This combination maintains high legibility and professional efficiency while introducing sophisticated, translucent layers that represent the "high-tech" layer of data superimposed over the "grounded" reality of the physical field. Surfaces are clean, whitespace is generous to prevent cognitive load in outdoor environments, and the overall aesthetic feels like a premium digital cockpit for agricultural management.

## Colors

The palette is a monochromatic study in verdant greens, designed to feel intrinsic to the agricultural sector while maintaining high-end professional contrast.

- **Primary (Emerald/Forest):** Used for primary actions, active states, and brand-critical iconography. It represents the health of a mature crop.
- **Secondary/Background (Mint/Sage):** This is the foundation of the interface. It replaces stark whites with a soft, natural tint that reduces glare during field use.
- **Accents/Headers (Teal/Deep Sea):** Reserved for high-level navigation, headers, and weightier structural elements to provide visual grounding and authority.
- **Gradients:** The transition from Forest to Lime is used exclusively for data visualizations (growth charts), primary call-to-action buttons, and featured "hero" cards to signify vitality and progress.

## Typography

**Manrope** is the sole typeface for this design system. It was selected for its modern, geometric construction and its exceptional readability in both data-heavy tables and large editorial headlines.

The typographic scale emphasizes clarity. Headlines utilize tighter letter-spacing and heavier weights to feel impactful and grounded. Body text maintains a generous line height to ensure legibility when the user is on the move. Labels and captions utilize uppercase styling with increased tracking to differentiate "Metadata" from "Content."

## Layout & Spacing

This design system utilizes a **Fixed Grid** philosophy to maintain a sense of structured order. For handheld devices, a 4-column grid is used; for tablet and desktop dashboards, a 12-column grid is employed.

The spacing rhythm is built on an **8px base unit**. Component internal padding is strictly enforced at 16px (md) or 24px (lg) to ensure touch targets are accessible for users who may be wearing gloves or working in outdoor conditions. Content blocks should be separated by 40px (xl) to maintain the minimalist, high-end feel of the brand.

## Elevation & Depth

Hierarchy in this design system is achieved through **Tonal Layering and Tinted Shadows**. 

Instead of traditional grey shadows, elevation is conveyed via low-opacity shadows tinted with the Teal accent color (`#004D40`). This keeps the interface feeling "organic" rather than "synthetic." 

1.  **Level 0 (Base):** The Mint/Sage background (`#E8F5E9`).
2.  **Level 1 (Cards/Surface):** Pure white or ultra-light mint surfaces with a soft, 4px blur tinted shadow.
3.  **Level 2 (Modals/Overlays):** Utilizes glassmorphism—a backdrop blur of 20px with a 60% opacity white fill—to maintain context of the underlying crop data while focusing the user's attention.

## Shapes

The shape language is **Rounded**, reflecting the organic curves found in nature. 

Standard components (inputs, buttons) utilize a **0.5rem (8px)** corner radius. Larger containers, such as dashboard cards and modular sections, use **1rem (16px)** to create a soft, approachable container for complex data. This avoids the "aggressive" feel of sharp corners, reinforcing the grounded and professional aesthetic.

## Components

### Buttons
- **Primary:** Gradient fill (Forest to Lime) with white text. High-contrast shadow.
- **Secondary:** Forest Green outline with a subtle Mint tint on hover.
- **Tertiary:** Text only in Teal with an underline on hover.

### Cards
Cards are the primary container for data. They feature a white background, 16px corner radius, and a 1px border in a slightly darker shade of Mint to provide definition without the heaviness of grey.

### Input Fields
Inputs use a soft Sage background instead of white to reduce eye strain. The active state is signaled by a 2px Forest Green bottom border and a subtle glow.

### Chips & Badges
Used for crop status (e.g., "Healthy," "Harvest-Ready"). These utilize pill-shaped geometry. "Healthy" statuses use the primary Forest Green, while neutral statuses use the Teal accent.

### Data Visualization
Charts should utilize the primary gradient for "Growth" metrics. Grid lines in charts should be kept at 0.5px thickness in a muted Sage to ensure the data remains the focal point.

### Lists
List items are separated by subtle horizontal rules in `#C8E6C9`. Leading icons are always contained within a circular Forest Green background to ensure high visibility.