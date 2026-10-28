---
name: drawio-flowchart
description: Use this skill whenever the user asks to create, rewrite, edit, refactor, fix, or extend a draw.io / diagrams.net flowchart that is shipped as a `.drawio` XML file (mxGraphModel). Trigger on phrases like "drawio diagram", "mxGraphModel", "flowchart xml", "fix the arrows in this diagram", "make this flowchart readable", "redraw the FSM as drawio", or whenever the user attaches a `.drawio` file and asks to change its layout, connections, or readability — even if they do not mention any specific tool name. Use it BEFORE editing any `.drawio` XML so the file stays readable when rendered. Skip only when the user is just reading data out of a `.drawio` without changing it.
---

# draw.io mxGraphModel flowchart authoring

This skill describes the patterns that keep a draw.io FSM/flowchart XML readable when it is rendered. The patterns were extracted from a concrete session where a Sensor/MQTT/App-thread FSM was edited three times; the third pass (the user's hand-edits) was the readable one, the first two were not. What follows is the rule set inferred from the diff.

## Capability guard (MUST read before anything else)

This skill relies on **reading the reference screenshots** under `references/` to compare a candidate edit against good and bad examples. The agent MUST load every PNG in `references/` (decision-example.png, good-overlap-example.png, bad-overlap-example.png) before deciding whether a layout is "good" or "spaghetti".

- **If the agent has vision capability**: load all three PNGs, look at them, and use them as the visual benchmark for the diagram being edited.
- **If the agent does NOT have vision capability**: this skill cannot be applied safely — its whole assessment is visual. The agent MUST stop and address the user with a clear, short message that says "I cannot apply this skill without vision — please run this on a vision-capable model" rather than producing a diagram blind. Do not silently fall back to text-only style rules.

If unsure whether the runtime supports image reads, attempt to load `references/decision-example.png` first. A successful image read means vision is available; a failure means it is not.

## Bundled visual references

The model is expected to open and look at each of these BEFORE deciding layout:

- `references/decision-example.png` — staircase cascade of five diamonds with side boxes aligned at source-Y; the canonical "decision" pattern.
- `references/good-overlap-example.png` — two-column FSM with happy path on the left, error funnel on the right, parallel cross-column edges (this is the "aligned overlap" that is desired, not spaghetti).
- `references/bad-overlap-example.png` — anti-pattern: spaghetti with multi-waypoint orthogonal edges and multi-paragraph node labels. Use this as the visual baseline of "do not produce this".

The model is also expected to READ (not blindly copy) the two XML snippets in this folder, which encode the same patterns in runnable form:

- `references/cascade-decision-pattern.xml` — minimal staircase-decision FSM.
- `references/two-column-fsm-pattern.xml` — minimal happy-left / error-right FSM with a dashed left-channel loop-back.

## When this skill applies

- Single-page `mxGraphModel` flowcharts with vertex shapes (ellipse/rounded/rhombus) connected by orthogonal edges.
- Output is the `.drawio` XML file.

## Hard constraints (cannot be relaxed without explicit user override)

### 1. Page size: must fit A4

The page must fit within **A4 margin 210 × 297 mm (8.27 × 11.69 inches), or 2480 × 3508 pixels at 300 DPI**. Treat the inner usable area as `pageWidth ≤ 2330` and `pageHeight ≤ 3300` (≈8 mm margin each side).

In `mxGraphModel` this means:

- `pageWidth` ≤ 2330
- `pageHeight` ≤ 3300

If a single-page design does not fit, prefer splitting into a second diagram (`<diagram id="...">` next sibling inside the same `<mxfile>`) over scaling or overflowing the page. **Never** decrease the rendering scale to "fit" — readers print diagrams at 1:1 and an underscaled diagram is unreadable.

### 2. Style: white background, black blocks

The user has set the project style preference:

- Page background: **white** (`#FFFFFF`).
- Block (node) fill: **black** (`#000000`) — or near-black (`#1A1A1A`) if total black reads too heavy.
- Block stroke: same as the fill (no contrasting border that visually enlarges each box).
- Text inside blocks: **white** (`#FFFFFF`).
- Edges and arrows: **black** (`#000000`).
- Decision rhombus fill: same as rounded boxes (black); no contrasting fill.
- Start ellipse fill: same as boxes (black).

Apply this style to NEW diagrams and to diagrams the user asks you to update. For diagrams that already exist with a different palette and were not explicitly asked to change style, leave the existing palette alone — but state the deviation in your final message.

When in doubt, the canonical recipe is:

```
fillColor=#000000;strokeColor=#000000;fontColor=#FFFFFF;labelBackgroundColor=none
```

for every shape, and `strokeColor=#000000;labelBackgroundColor=none` for every edge.

### 3. No `shape=note` annotations unless the user asks

Notes added in earlier passes crowded the diagram and overlapped the main flow. Do not add them. Domain context belongs in node labels, the SSD, or the source code — never in the figure.

## Core principles (read these first)

1. **Readable overlap is fine; spaghetti is not.** Arrows may overlap, but only when they share a channel — i.e. they run parallel along the same x or y line, in the same direction, between adjacent nodes. If two edges cross at an angle or wrap around three nodes, that is spaghetti; redraw the geometry so they share a channel or diverge earlier.
2. **One node = one tight label, not a paragraph.** Each shape holds a single short verb-phrase action or a single short question on the rhombus. No notes, no multi-line essays, no enumerated caveats.
3. **Decisions cascade as a staircase.** When events flow into a chain of related decisions, stack the diamonds in one slightly-offset column (each diamond a few units right/down of the previous one). Vertical edges between diamonds are straight — no orthogonal L-shape, no `mxPoint` detour. Side branches exit on a single consistent side and enter a side box at the same Y.
4. **Side boxes align with their source decision.** Place a branch-action box so its `Y` overlaps the `Y` of its source decision. That makes the connecting edge a short horizontal stub, the easiest kind to read.
5. **Loop-back edges run in ONE channel.** All "back to the start" dashed edges use a single vertical channel on the same side of the diagram (e.g. always at `x=10` or `x=40`). Pick one channel and stick to it. Varying channels force the reader to track the eye across the page.
6. **Two columns beat one wide column for FSMs with an error axis.** Happy path on the left, error/recovery on the right. Edges that cross the columns are short and run in a small number of parallel channels — that overlap is desirable, that's "reading-aligned overlap".

## Geometry rules

### Cascade of decisions

```
[A] --yes--> [B rhombus] --yes--> [C rhombus] --yes--> [action]
              |                        |
              no                       no
              v                        v
           [branchA]                [branchB]
```

- Each rhombus: `exitX=0.5;exitY=1` to the next rhombus (or next action) below.
- Each side branch: `exitX=0;exitY=0.5` to a box placed slightly left and at the same Y.
- Number of rhombi in a cascade: keep under ~5 before splitting the diagram.
- See `references/cascade-decision-pattern.xml` for a runnable example.

### Error-and-recovery side column

```
[happy action] --fail--> [enter error] --always--> [step 1 of cleanup]
                                                      |
                                                      v
                                                  [step 2 of cleanup]
                                                      |
                                                      v
                                                  [step N of cleanup]
                                                      |
                                                      v
                                                  [branch by verdict]
                                                  /         \
                                            recover        fault
                                                |             |
                                                v             v
                                       back to happy    halt node
```

- The right column is a stack of rounded boxes, ordered top-to-bottom in clean-up order.
- All happy-path failure edges enter the right column at the TOP. The right column itself never zigzags.
- Verdict branches at the bottom: keep them as ONE decision and two SHORT stub edges.
- See `references/two-column-fsm-pattern.xml` for a runnable example.

### Loops and "back to start"

- Edge style: `dashed=1`. Solid = forward flow. Dashed = control flow / loop-back / re-entry.
- Use `<Array as="points">` with exactly TWO `mxPoint` entries: one at the channel-X and the source-Y, one at the channel-X and the target-Y. Avoid three or more detour points.
- All loopbacks use ONE channel X for the whole diagram.

### Initial entry pattern

- A single `ellipse` start node connects straight down to the first action with one short solid edge.
- Initial state description goes INTO the first action's label, or directly under it — never as a separate `shape=note`.

## What to avoid

- **Decorative `shape=note` annotations** — drop them unless the user explicitly says "add a note". This is also a hard constraint above.
- **Multi-paragraph labels** — split into multiple nodes or trim aggressively. If a labeled node exceeds ~80 characters, it is too long.
- **Long orthogonal paths with 3+ waypoints** — that means the layout is wrong; reposition the boxes so the edge becomes a 0 or 2-waypoint straight segment.
- **Edges that cross at angles** — re-route along x or y channels.
- **Two different side channels for loopbacks** — pick one.
- **State-name identifiers from the source code** in the diagram labels (e.g. `WS_ERROR`, `MQTT_INIT`, `prv_wifi_init`). The diagram MUST be a high-level view; concrete code identifiers belong in the SSD or the source itself.
- **Re-stating what the SSD or the source already says** — keep the figure to flow, not commentary.
- **Page overflow** — if your design exceeds 2330 × 3300, split into a second `<diagram>` inside the same `<mxfile>` rather than scale down.

## XML hygiene reminders

- Escape `&` as `&amp;`, `<` as `&lt;`, `>` as `&gt;` inside `value=` attributes.
- Use `&#xa;` for explicit line breaks inside node labels. Some editors auto-insert `<br>`; pick ONE per file and stay consistent. Prefer `&#xa;`.
- Every `mxCell` needs a unique `id`.
- Every edge references existing `source`/`target` ids.
- Preserve `mxfile host`, `diagram id`, and `shadow` setting across edits to an existing file.
- Style values come from the hard constraint; existing-project deviations are allowed only if the user has not asked you to update style.

## Validation pass before declaring done

Run all of these — failing any of them means the diagram is not finished.

1. `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" <file>` exits 0.
2. `python3 - <<'PY'
   import xml.etree.ElementTree as ET, sys
   t = ET.parse(sys.argv[1])
   ids = {c.get("id") for c in t.iter("mxCell")}
   bad = [(c.get("id"), a, c.get(a)) for c in t.iter("mxCell")
          for a in ("source","target","parent") if c.get(a) and c.get(a) not in ids]
   sys.exit(1 if bad else 0)
   PY <file` exits 0.
3. `grep -c "shape=note" <file>` returns 0 unless the user explicitly asked for notes.
4. `grep -cE "WS_|MQTT_NONE|MQTT_INIT|MQTT_OPERATIONAL|MQTT_ERROR|SENSOR_IDLE|SENSOR_OPERATIONAL|osMutex|osEventFlags|prv_" <file>` returns 0 — no source-code identifiers snuck into labels.
5. **A4 page-size check** — extract `pageWidth` and `pageHeight` from `<mxGraphModel ... pageWidth="..." pageHeight="..."` and assert both ≤ 2330 and ≤ 3300 respectively. If a diagram exceeds this, split it.

## Editing procedure when a diagram has spaghetti

1. Open the XML, list every rhombus and every edge that has 3+ `mxPoint` waypoints. Those are the spaghetti markers.
2. Compare the rendered diagram against `references/good-overlap-example.png` and `references/bad-overlap-example.png` to confirm which side your current edit is on.
3. Re-anchor the boxes: identify which boxes should be in the left "happy" column and which in the right "error/branch" column. Decide the side channel X for loopbacks (pick one).
4. Reposition boxes so cascade-rhombi share an X column within ~20 units of each other.
5. Re-author the edges: for each cascade pair, one straight solid edge with no `<Array>`. For each loop-back, exactly 2 `mxPoint`s. For each verdict decision, two short stubs.
6. Apply the hard style constraint (white background, black blocks) unless the user asked you not to.
7. Run the five-step validation pass.
8. Compare again to the PNG references — arrows should form lines/columns, not diagonals.
