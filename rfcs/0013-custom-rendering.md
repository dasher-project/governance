---
rfc: 0013
title: Custom rendering API (two-strand)
status: proposed
platforms: [apple, windows, gtk, android, web, core]
created: 2026-07-25
updated: 2026-07-25
---

# Custom rendering API (two-strand)

## Summary

Give frontends a choice: render Dasher from the existing flat draw-command
buffer (the current path), **or** query the live node tree and render it
themselves with their own graphics API. The two strands coexist — a frontend
can use the command buffer for most things and drop into custom rendering for
specific features (3D cubes, VR spatial layouts, custom visualisations), or
render everything from scratch.

## Motivation

The flat `int[]` command buffer (`dasher_frame`) is 2D painter's algorithm —
no depth buffer, no perspective, no compositing. It works well for flat
rectangles, circles, text, and lines. It **cannot** represent:

- **3D extruded cubes** (LP_SHAPE_TYPE = CUBE). The depth data
  (`CubeDepthLevel`) exists inside DasherCore but is discarded when serialised
  to the flat buffer. A two-pass frontend overlay (buffering opcode-7 cubes,
  rendering shaded faces on top) was prototyped but produces a barely-visible
  effect because the flat buffer's painter's algorithm buries parent shading
  under child rectangles.
- **Spatial / VR rendering** (visionOS). Placing Dasher nodes in 3D space,
  with depth based on zoom level, is impossible through the flat buffer.
- **Alternative visualisations** — radial trees, force-directed layouts,
  particle effects, animated transitions.
- **Custom accessibility rendering** — high-contrast simplified views,
  audio-only spatial rendering, screen-reader-friendly text descriptions.

### What already exists

DasherCore already has "test/diagnostic hooks" (`dasher.h` §Test, marked "NOT
intended for production frontends") that expose raw node-tree data:

```c
int dasher_get_probabilities(ctx, lbnds, hbnds, max);  // children of crosshair node
int dasher_get_root_child_count(ctx);
int dasher_get_root_child_bounds(ctx, index, &lbnd, &hbnd);
int dasher_dasher_to_screen(ctx, dx, dy, &sx, &sy);
int dasher_screen_to_dasher(ctx, sx, sy, &dx, &dy);
int dasher_get_alphabet_symbol_text(ctx, index, buf, len);
```

These prove the concept — a frontend can query node positions and text. They
just aren't complete enough for full rendering (no recursive tree walking, no
node colours, no labels for group/control nodes).

## Detailed design

### Two strands, coexisting

```
Strand 1 (existing, default):
  dasher_frame() → int[] draw commands → frontend renders

Strand 2 (new, opt-in):
  dasher_get_visible_nodes() → node tree data → frontend renders from scratch
```

A frontend uses whichever strand it wants. Most frontends use Strand 1 (simpler,
less code). A frontend that needs 3D, VR, or custom visuals uses Strand 2 for
some or all of its rendering.

### Strand 2 API: node tree exposure

Both structs begin with a `struct_size` field (set by the caller to
`sizeof(dasher_node_info)` / `sizeof(dasher_viewport)` before the call) so the
engine can detect the ABI version and gracefully ignore fields it doesn't know
about. This lets the structs evolve without new symbols or breaking existing
frontends.

```c
// Information about a single visible node in the Dasher tree.
typedef struct dasher_node_info {
    int struct_size;            // Caller sets to sizeof(dasher_node_info) before the call
    long long dasher_y1;        // Dasher Y range (lower bound, normalised 0..65536)
    long long dasher_y2;        // Dasher Y range (upper bound)
    int       symbol;           // Alphabet symbol index (-1 for group/control nodes)
    int       has_children;     // 1 if this node has visible children
    int       depth;            // Recursion depth from root (0 = root child)
    int       is_game_node;     // 1 if on the game-mode path
    // Screen-space bounds (pre-computed by the engine — saves the frontend
    // from calling dasher_dasher_to_screen for every node).
    int screen_x1, screen_y1, screen_x2, screen_y2;
    // Colours (from the active palette).
    int fill_argb;
    int outline_argb;
    // Text label (index into the strings array returned by the query, or -1).
    int label_index;
} dasher_node_info;

// Query the visible node tree. Returns the number of nodes written (up to
// max_nodes). The result is clipped to the visible region — exactly the same
// set of nodes the command buffer would render for the same frame — so Strand 1
// and Strand 2 see identical node sets and the parity invariant holds.
//
// Nodes are returned in depth-first tree-traversal order (parent before
// children). This is convenient for painter's-algorithm frontends (render in
// the returned order), but a 3D frontend will typically re-sort back-to-front
// or use a z-buffer, so the ordering should be treated as tree-traversal
// order, not a mandated render order.
//
// out_strings holds label text for nodes that have one; label_index in
// dasher_node_info indexes into it. Both out_nodes and out_strings point into
// engine-owned buffers valid until the next call to dasher_frame or
// dasher_get_visible_nodes on this context — copy if you need the data beyond
// the next frame.
DASHER_API int dasher_get_visible_nodes(
    dasher_ctx* ctx,
    dasher_node_info* out_nodes, int max_nodes,
    char*** out_strings, int* out_string_count
);

// Viewport state — tells the frontend where the engine's viewpoint is.
typedef struct dasher_viewport {
    int struct_size;            // Caller sets to sizeof(dasher_viewport) before the call
    long long crosshair_x;      // Current crosshair Dasher X
    long long crosshair_y;      // Current crosshair Dasher Y
    long long visible_min_y;    // Visible Dasher Y range
    long long visible_max_y;
    int screen_width;           // Canvas dimensions the engine was told about
    int screen_height;
} dasher_viewport;

DASHER_API int dasher_get_viewport(dasher_ctx* ctx, dasher_viewport* out);
```

### How a frontend uses Strand 2

```
1. dasher_mouse_move / dasher_frame as normal (engine advances)
2. dasher_get_visible_nodes → array of dasher_node_info + strings
3. For each node (in returned order, or re-sort for 3D):
   - Render it however you want (flat rect, 3D cube, sphere, text card)
   - Use fill_argb / outline_argb for colours
   - Use label_index → out_strings for text
   - Use screen_x1..y2 for position
   - Use has_children + depth for tree-aware rendering (e.g. 3D extrusion
     scaled by depth)
4. Optionally call dasher_frame too (for the crosshair, game decorations, etc.)
   and render those commands on top — or render the crosshair yourself from
   the viewport data.
```

### What the engine provides vs what the frontend decides

| Concern | Engine (Strand 2) | Frontend |
|---|---|---|
| Node positions (Dasher + screen) | ✅ via `dasher_node_info` | — |
| Node colours | ✅ from active palette | may override |
| Node text labels | ✅ via strings array | may restyle |
| Node tree structure | ✅ depth-first order, depth, has_children | — |
| Shape (rect / circle / cube / triangle) | ❌ not the engine's call | ✅ frontend decides |
| Depth / 3D extrusion | ❌ | ✅ frontend decides (e.g. from `depth`) |
| Animation / transitions | ❌ | ✅ frontend decides |
| Input handling | ✅ mouse_move / key_event | — |
| Language model / probabilities | ✅ | — |

The key shift: **shape and depth become frontend concerns, not engine
concerns.** LP_SHAPE_TYPE becomes a hint, not a mandate — the frontend can
render cubes, flat rects, or something entirely new. A frontend that wants 3D
cube extrusion derives it from `dasher_node_info.depth` — no separate
extrusion level is needed in the viewport.

### Relationship to Strand 1

The strands are not mutually exclusive:

- **Default:** Strand 1 only. `dasher_frame()` → `int[]` → render. Simplest.
- **Hybrid:** Strand 1 for most rendering + Strand 2 for specific features.
  Example: use `dasher_frame()` for everything, but when LP_SHAPE_TYPE is CUBE,
  switch to `dasher_get_visible_nodes()` and render 3D cubes from the node
  tree.
- **Full custom:** Strand 2 only. Frontend renders everything from node data.
  Most flexible; most work.

### What about the existing opcode-7 cube experiment?

The opcode-7 approach (DasherCore PR #50) carries cube depth data through the
flat buffer for a frontend two-pass overlay. It works (cubes are buffered and
rendered on top) but the effect is underwhelming because the flat buffer's
painter's algorithm limits the visual result.

With Strand 2, opcode 7 becomes unnecessary — the frontend has the full node
tree and can render proper 3D cubes directly. The recommendation is:

- **Withdraw opcode 7** from the command buffer (it added complexity for a
  limited result).
- **Keep LP_SHAPE_TYPE** as a hint (the frontend can read it via
  `dasher_get_long_parameter` and use it to choose its rendering style).
- **Frontends that want cubes** use Strand 2 + their own 3D rendering.

## Drawbacks

- **API surface growth.** `dasher_get_visible_nodes` + `dasher_viewport` +
  `dasher_node_info` is a significant new API. The `struct_size` ABI-versioning
  field mitigates forward-compatibility concerns, but the API still needs docs
  and tests.
- **Duplication of rendering logic.** Each frontend that uses Strand 2
  reimplements coordinate transforms, colour lookups, text positioning, etc.
  that DasherViewSquare already does. This is by design (flexibility) but it's
  more code per frontend.
- **Performance.** Copying the node tree into a struct array every frame has a
  cost. For typical Dasher (50–200 visible nodes) this is negligible; for
  extreme cases it may matter.
- **Potential for inconsistency.** A custom-rendering frontend might position
  nodes slightly differently than the command-buffer path, leading to
  mismatched input coordinates. The pre-computed `screen_x1..y2` fields
  mitigate this (the engine does the coordinate transform).

## Alternatives considered

- **Opcode 7 (cube data in the flat buffer).** Prototyped in DasherCore PR
  #50. Works but produces an unconvincing 3D effect because the flat buffer's
  painter's algorithm can't composite depth correctly. Withdraw in favour of
  Strand 2.

- **New opcodes for every 3D shape.** Rejected: the flat buffer would grow
  indefinitely (cube, sphere, cylinder, perspective-rect...), and each
  frontend still has to implement the new opcodes. Strand 2 solves this once.

- **Frontend-specific rendering paths (bypass the C API entirely).** Example:
  DasherApple queries DasherCore internals directly for node positions.
  Rejected: violates the C API boundary (CONTRIBUTING Rule 4), not portable,
  and each frontend reinvents the same queries.

## Prior art

- **Browser DOM rendering.** The browser exposes a DOM tree; CSS / JavaScript
  decide how to render it. Strand 2 is analogous: DasherCore exposes the node
  tree; the frontend decides how to render it.
- **Accessibility APIs** (UIAutomation, AXAPI). Expose semantic structure
  (tree, roles, labels); the consumer (screen reader, automation tool) renders
  or interprets however it wants.
- **Unity / Unreal entity-component systems.** The engine provides data; the
  renderer (which may be swapped) decides visual representation.

## Testing

Per [RFC 0011](./0011-testing.md):

- **DasherCore unit tests** (`tests/`): verify `dasher_get_visible_nodes`
  returns the correct count, tree-traversal order (depth-first), positions
  (match `dasher_dasher_to_screen`), and colours for a known node tree.
  Property invariant: the screen bounds in `dasher_node_info` match the
  opcode-4 rectangles from `dasher_frame` for the same frame (Strand 1/2
  parity). Verify the node set is clipped to the visible region (same as the
  command buffer).
- **Frontend (manual):** render the same node tree in flat mode (Strand 1) and
  custom mode (Strand 2); verify visual parity. Then switch to cube mode under
  Strand 2 and verify 3D cubes are visible.

## Unresolved questions

1. **Should the engine still emit opcode 7 (cube data) for frontends that
   want the two-pass approach?** Or withdraw it entirely in favour of Strand 2?
   (Recommendation: withdraw.)
2. **Colour palette access.** Should the API expose the palette directly
   (`dasher_get_palette_colors`), or only per-node colours in
   `dasher_node_info`?

## Resolution

_(Filled in once a decision is reached.)_

- Status: _pending_
- Decided by: _pending_
- Date: _pending_
- Decision: _pending_

## History

- 2026-07-25 — initial proposal. Motivated by the cube-mode limitation
  (DasherCore issue #49, PR #50) and the broader vision of enabling VR/custom
  rendering through the C API.
- 2026-07-25 — review feedback incorporated: clipping to visible region
  (resolved Q2); tree-traversal order documented as traversal, not render
  order; `struct_size` ABI-versioning field added to both structs; cube depth
  removed from viewport (frontend derives from `node_info.depth`); string
  lifetime documented (valid until next `dasher_frame` /
  `dasher_get_visible_nodes`).
