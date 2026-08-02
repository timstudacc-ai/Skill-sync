# Designer Agent Guidelines: Explanational HTML Documentation

This document contains a strict set of technical, visual, and explanatory rules for generating HTML documentation. It is synthesized from the standard `uart_driver_explanation.html` template. 

When asked to create an explanatory HTML document for a user, you **MUST** adhere to the following ruleset.

---

## 1. Visual Style & Design Tokens

Your HTML must be built using a clean, modern, and sleek design system. 

### Color Palette (Birchline/Web Style)
- **Primary Text & Borders (Slate):** `#141413`
- **Background (Off-white):** `#F9F8F6`
- **Surface/Container (White):** `#ffffff`
- **Primary Accent (Clay):** `#D97757` (Used for highlights, errors, and important borders)
- **Secondary Accent (Olive):** `#788C5D` (Used for hardware/success states)
- **Tertiary Accent (Sky):** `#6A8CAF` (Used for software/logic states)
- **Neutral/Borders (Oat):** `#E3DACC`
- **Muted Text (Gray):** `#8c8c8c`

### Typography
- **Display & Headings (`h1`, `h2`, `h3`):** Serif font (`Georgia, serif`). Display size 32px, headings 20px.
- **Body Text (`p`, `li`):** Sans-serif (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`). Size 15px.
- **Code & Tokens (`code`, `.code-box`):** Monospace (`ui-monospace, SFMono-Regular, Consolas, monospace`). Size 13px.

### Layout & Containers
- **Main Container:** Max-width 900px, centered, white background, 12px border radius, subtle shadow (`box-shadow: 0 4px 12px rgba(0,0,0,0.03)`), and an Oat border.
- **Layout Grid (`.layout-grid`):** Use a 2-column CSS Grid (`grid-template-columns: 1fr 1fr; gap: 30px;`) to place code snippets on the left and explanatory prose on the right. Stack into 1 column on mobile devices.

---

## 2. Explanatory Style & Narrative Structure

The core philosophy of this documentation style is **Contrastive Explanation**. Do not just explain *how* the code works; explain *why* alternative approaches would fail.

### Focus on the "Why Not"
- Use headings like *"Why not use X?"* or *"What if we only used Y?"*
- Explicitly demonstrate the failure mode of the naive approach (e.g., "If we used a single buffer, the DMA would overwrite the data while the CPU is reading it, causing Data Corruption").
- Justify the complexity of the current architecture by proving the necessity of solving those failure modes.

### The "Gotchas" Section
- Every document must end with a `.gotchas` section.
- Use `.gotcha-item` boxes (white background, Oat borders, thick Clay left border).
- Document non-obvious hardware quirks, alternate function behaviors, or edge cases that cause silent failures.

### Metaphors and Analogies
- Translate complex technical timing or architecture into relatable mechanical or physical analogies (e.g., "The Starter Motor vs. The Chain Reaction").

---

## 3. Code Presentation & UI Components

Do not dump large, unformatted code blocks. Code must be presented as a visual learning aid.

### Annotated Code Snippets (`.code-box`)
- Code boxes must have a dark Slate background with White text.
- **Highlights (`.code-highlight`):** Use a 2px solid Clay bottom border to underline the specific lines of code being discussed in the adjacent prose.
- **Annotations (`.code-annotation`):** Add small, Oat-colored tags beneath logical blocks of code to summarize the block in 2-3 words (e.g., `[Hardware RTS De-assertion]`).
- **Comments:** Color code comments with the muted gray (`#8c8c8c`) or Clay (`#D97757`) for emphasis on failure states.

### Workflow Diagrams (`.workflow-box`)
- Use Mermaid.js flowcharts to visualize architecture.
- Wrap diagrams in a `.workflow-box` (Off-white background, Oat border).
- Include a `.diagram-title` (Uppercase, 11px, spaced letters, gray text) above the diagram.
- **Mermaid Styling:** Override default Mermaid styles to match the design system. Nodes should be Oat with Slate borders, rounded corners (`rx: 6px, ry: 6px`). Match node fill colors to the logical domains (e.g., Hardware = Olive, Software = Sky).

### Inline Tokens (`.token`)
- When referring to variables, registers, or specific byte sizes in paragraphs, wrap them in a `.token` class (Monospace, 12px, Oat background with an Oat border, slight padding) rather than standard markdown backticks.
