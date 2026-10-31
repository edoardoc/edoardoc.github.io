---
name: 500nits
description: A quiet correspondence sheet for Eddy's independent software label.
colors:
  ink: "#1f2d4d"
  paper: "#fff"
  muted: "#526078"
  rule: "#d2d5db"
  inverse-muted: "#e0e3e8"
  inverse-rule: "#8991a1"
typography:
  display:
    fontFamily: 'Karla, "Helvetica Neue", Arial, sans-serif'
    fontSize: "clamp(40px, 4.8vw, 66px)"
    fontWeight: 600
    lineHeight: 1.04
    letterSpacing: "-0.04em"
  headline:
    fontFamily: 'Karla, "Helvetica Neue", Arial, sans-serif'
    fontSize: "32px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  title:
    fontFamily: 'Karla, "Helvetica Neue", Arial, sans-serif'
    fontSize: "27px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  body:
    fontFamily: 'Karla, "Helvetica Neue", Arial, sans-serif'
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  reading-lead:
    fontFamily: 'Karla, "Helvetica Neue", Arial, sans-serif'
    fontSize: "22px"
    fontWeight: 400
    lineHeight: 1.5
  reading-body:
    fontFamily: 'Karla, "Helvetica Neue", Arial, sans-serif'
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1.65
  history-title:
    fontFamily: 'Karla, "Helvetica Neue", Arial, sans-serif'
    fontSize: "23px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  history-date:
    fontFamily: 'Karla, "Helvetica Neue", Arial, sans-serif'
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: 'Karla, "Helvetica Neue", Arial, sans-serif'
    fontSize: "14px"
    fontWeight: 500
    lineHeight: 1.55
rounded:
  square: "0"
spacing:
  inline: "8px"
  compact: "12px"
  text: "16px"
  group: "24px"
  panel: "36px"
  column: "48px"
  section: "72px"
components:
  button-subscribe:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.square}"
    padding: "11px 14px"
  button-subscribe-hover:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
  input-email:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
    padding: "11px 13px"
  newsletter:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.square}"
    padding: "34px 36px"
---

# Design System: 500nits

## Overview

**Creative North Star: "The independent-maker correspondence sheet"**

The hub feels like a simple printed sheet: white paper, navy lettering, generous margins, and direct first-person copy. The existing mark and Karla carry its identity. This records the hub's implemented system; product sites retain their own visual identities.

Lo-fi means restrained and readable. Ordinary links, horizontal rules, and one inverted newsletter region establish hierarchy without decorative motion or illustration.

**Key Characteristics:**
- Navy on white, with navy-derived supporting shades.
- One locally hosted type family and clear weight changes.
- Flat product rows, square controls, and visible keyboard focus.
- Static content with minimal progressive JavaScript.

## Colors

### Primary

**Ink** carries headings, body copy, links, the mark, and the inverted newsletter background.

### Neutral

**Paper** is the page ground and newsletter foreground. **Muted** supports metadata and secondary links. **Rule** separates ordinary rows. **Inverse muted** supports newsletter explanatory text; **inverse rule** separates its revealed status message.

**The Two-Color Identity Rule.** Keep navy and white as the identity; supporting shades provide readable hierarchy rather than introducing another accent.

## Typography

Karla is locally hosted with Helvetica Neue, Arial, and sans-serif fallbacks. The frontmatter records desktop roles; the system uses a compact, unembellished hierarchy rather than a separate display face.

The main heading is tightly tracked and fluid. Section headings use the headline role; product names use the title role. Newsletter headings are slightly smaller (29px desktop, 26px below 1000px, 27px below 650px). Intro and product descriptions use larger body copy (18px desktop, 17px mobile), with product descriptions limited to 65ch. Metadata is 14px; signup notes and the footer are 13px with signup notes at 1.5 line-height. Navigation and action links are 16px; prominent actions use weight 600. The wordmark uses weight 700.

Reading-page leads use the reading-lead role with a 58ch maximum width; their size reduces to 20px below 650px. Reading copy uses the reading-body role with a 70ch maximum width, reducing to 17px below 650px while retaining its line-height. Reading section headings inherit the headline role and reduce to 28px on mobile. Chronology headings use the history-title role; dates use the muted history-date role with tabular numerals, and chronology descriptions are 17px. In-page contents links are 15px.

Below 650px, the main heading becomes `clamp(36px, 7.8vw, 49px)`, section headings 28px, product names 26px, and navigation 14px.

## Layout

The centered page is at most 1080px wide, with 48px gutters on larger screens and 20px gutters below 650px. The desktop introduction, newsletter, product rows, and maker section use asymmetric two-column grids. Generous vertical spacing separates sections; small repeated gaps bind labels, links, and controls.

At 1000px the introduction becomes one column, section headings stack, and form controls can wrap. At 650px the newsletter, product rows, and maker section stack in reading order; controls fill their row, and navigation moves below the wordmark. Newsletter padding reduces from the frontmatter value to 30px at the intermediate breakpoint and 25px 22px on mobile.

Reading pages place a ruled introduction above a two-column layout: a 180px contents column, a flexible reading column, and a 64px gap. The introduction has 72px top and 46px bottom padding; the reading layout has 42px top and 64px bottom padding. Below 800px, contents links wrap above the text with a lower rule and 22px bottom padding; the layout gap becomes 30px. Below 650px, introduction padding becomes 42px 0 30px, reading-layout padding becomes 26px 0 42px, and section spacing reduces from 46px to 36px. The lead's top margin reduces from 22px to 18px.

## Elevation & Depth

No shadows, gradients, or animated elevation. White space and thin rules organize the page; the solid navy newsletter panel supplies the strongest contrast.

**The Flat Sheet Rule.** Separate content with space and rules; preserve flat surfaces at rest and during interaction.

## Shapes

Controls and the newsletter panel have square corners. Dividers and control borders are thin (1px). Directional arrows are inline SVG strokes (20px square, 1.6 stroke width), with round caps and joins. The existing favicon supplies the brand mark.

## Components

### Buttons

The subscription button is a square, navy control with a white border and a minimum height of 50px. Its text is 15px, weight 600. Hover and active states immediately invert foreground and background. Disabled styling reduces opacity to 0.6 and uses a waiting cursor.

### Inputs / Fields

The email field is white with navy text, square corners, a white border, and a minimum height of 50px. Placeholder text uses muted ink. A visible label stays above the field. Native email validation is retained.

### Navigation and links

Navigation uses plain text, with underlines on hover. The current page has a persistent 2px underline. Reading-page contents use ordinary in-page links. Body and product action links are ordinarily underlined; hover increases underline thickness from 1px to 2px. Underlines sit 5px below text. Product-name links reveal their underline on hover. All interactive elements receive an immediate 2px focus outline offset by 5px; the newsletter input uses a white outline against navy.

### Product rows

Product entries are open editorial rows, each introduced by a thin top rule. The name and platform occupy the left column; description, detail, and wrapping links occupy the right. They collapse into one column on mobile. There are no card backgrounds, enclosing borders, or shadows.

### Reading pages and chronology

The reading column uses open text sections, with 18px between paragraphs and beneath section headings. Lists use ordinary bullets with 10px between items. Development histories use flat rows separated by thin rules, with 22px vertical padding. A 120px date column sits beside the entry with a 24px gap; below 650px the date stacks above the entry with an 8px gap. There are no enclosing cards or decorative timeline markers.

### Newsletter panel

The inverted panel pairs a short invitation with a labeled email field and an action. Supporting copy explicitly states that the visitor must send an email request. Submitting reveals a polite live status with a retry link; it does not claim subscription success. Updates links focus the email field. The ordinary mailto form remains available without JavaScript; no hosted newsletter endpoint is configured.

## Do's and Don'ts

### Do:

- **Do** retain the existing mark, lowercase 500nits, and first-person singular voice.
- **Do** use navy-derived secondary shades for readable metadata and rules.
- **Do** keep navigation and product destinations available as ordinary HTML links.
- **Do** preserve visible labels, native validation, and clear keyboard focus.
- **Do** describe the email request honestly until a verified provider is connected.

### Don't:

- **Don't** add decorative animation, flashes, gradients, or shadows.
- **Don't** turn product rows into ornamental cards or add rounded control styling.
- **Don't** introduce a competing accent palette or display font.
- **Don't** claim an email draft has subscribed its sender.
