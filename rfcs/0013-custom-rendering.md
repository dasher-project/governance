---
rfc: 0013
title: Node-tree rendering API (custom rendering)
status: active
platforms: [apple, windows, gtk, android, web, core]
created: 2026-07-25
updated: 2026-08-01
---

# Node-tree rendering API (custom rendering)

## Summary

Give a frontend a second way to render Dasher. Today every frontend renders from
the flat draw-command buffer. This RFC adds a second path: the frontend queries
the live node tree and draws it with its own graphics API. The two paths
coexist. A frontend can use the command buffer for most of its drawing and drop
into node-tree rendering for a specific feature, or it can render everything from
scratch.

> **Naming note (August 2026).** This RFC used to call the two paths "Strand 1"
> and "Strand 2". Those names said nothing about what each path does. They are
> renamed here:
>
> - **command-buffer rendering** — the existing path (`dasher_frame` returns an
>   `int[]` of draw commands; the frontend replays them).
> - **node-tree rendering** — the path this RFC adds (`dasher_get_visible_nodes`
>   returns the node tree; the frontend draws it itself).

## Implementation status

Audited August 2026. The engine API is implemented and tested. No production
frontend uses it.

- **DasherCore: implemented and tested.** `dasher_get_visible_nodes`,
  `dasher_set_visible_nodes_enabled`, `dasher_get_viewport`, and the
  `dasher_node_info` / `dasher_viewport` structs all exist in `dasher.h` and
  `CAPI.cpp`, with tests in `tests/test_strand2_nodes.cpp` and
  `tests/test_node_tree.cpp`.
- **Frontends: none use it in production.** Every Apple target, plus Windows,
  GTK, Android, and web, renders through the command buffer
  (`dasher_frame` → `int[]`). None calls `dasher_get_visible_nodes`.
- **DasherMac (experimental).** A branch of the macOS app uses node-tree
  rendering to draw the cube (3D) shape mode. The work is experimental and
  buggy. It is not merged and does not ship.
- **Scope.** There is no plan to bring node-tree rendering to every platform.
  It exists for the frontends that need full visual control (3D, VR, custom
  accessibility views). The command buffer stays the default.

### Where this might still matter

The most promising future use is a spatial, eye-tracked port — for example a
Meta Quest build that renders the node tree in 3D and drives it with foveated
eye tracking. That is future work, not a near-term plan. The API is in place so
that such a port can read the node tree through the same C boundary as every
other frontend.

## Motivation

The flat `int[]` command buffer (`dasher_frame`) is a 2D painter's algorithm. It
has no depth buffer, no perspective, and no compositing. It works well for flat
rectangles, circles, text, and lines. It **cannot** represent:

- **3D extruded cubes** (`LP_SHAPE_TYPE = CUBE`). The depth data
  (`CubeDepthLevel`) exists inside DasherCore, but the flat buffer discards it
  when it serialises the commands. A two-pass frontend overlay (buffer the
  opcode-7 cubes, then draw the shaded faces on top) was prototyped. The effect
  is barely visible, because the painter's algorithm buries the parent shading
  under the child rectangles.
- **Spatial or VR rendering** (visionOS). Placing Dasher nodes in 3D space, with
  depth based on the zoom level, is impossible through the flat buffer.
- **Alternative visualisations** — radial trees, force-directed layouts,
  particle effects, animated transitions.
- **Custom accessibility rendering** — high-contrast simplified views,
  audio-only spatial rendering, screen-reader-friendly text descriptions.

### What already exists

DasherCore already has test and diagnostic hooks (`dasher.h`, §Test, marked "not
intended for production frontends") that expose raw node-tree data:

```c
int dasher_get_probabilities(ctx, lbnds, hbnds, max);  // children of crosshair node
int dasher_get_root_child_count(ctx);
int dasher_get_root_child_bounds(ctx, index, &lbnd, &hbnd);
int dasher_dasher_to_screen(ctx, dx, dy, &sx, &sy);
int dasher_screen_to_dasher(ctx, sx, sy, &dx, &dy);
int dasher_get_alphabet_symbol_text(ctx, index, buf, len);
```

These prove the concept: a frontend can query node positions and text. They are
not complete enough for full rendering (no recursive tree walk, no node colours,
no labels for group or control nodes).

## Detailed design

### Two paths, coexisting

```
Command-buffer rendering (existing, default):
  dasher_frame() -> int[] draw commands -> the frontend renders

Node-tree rendering (new, opt-in):
  dasher_get_visible_nodes() -> node tree data -> the frontend renders from scratch
```

A frontend uses whichever path it wants. Most frontends use the command buffer,
because it is simpler and needs less code. A frontend that needs 3D, VR, or
custom visuals uses node-tree rendering for some or all of its drawing.

### The node-tree API

Both structs begin with a `struct_size` field. The caller sets this to
`sizeof(dasher_node_info)` or `sizeof(dasher_viewport)` before the call. The
engine then detects the ABI version and ignores fields it does not know. This
lets the structs evolve without new symbols and without breaking existing
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
    // Screen-space bounds (the engine pre-computes these, so the frontend does
    // not call dasher_dasher_to_screen for every node).
    int screen_x1, screen_y1, screen_x2, screen_y2;
    // Colours (from the active palette).
    int fill_argb;
    int outline_argb;
    // Text label (index into the strings array returned by the query, or -1).
    int label_index;
} dasher_node_info;

// Query the visible node tree. Returns the number of nodes written (up to
// max_nodes). The result is clipped to the visible region — the same set of
// nodes the command buffer would render for the same frame — so the two paths
// see the same nodes and the parity invariant holds.
//
// Nodes come back in depth-first tree-traversal order (parent before children).
// This is convenient for a painter's-algorithm frontend (draw in the returned
// order). A 3D frontend will usually re-sort back-to-front or use a z-buffer,
// so treat the order as tree-traversal order, not a required draw order.
//
// out_strings holds the label text for nodes that have one; label_index in
// dasher_node_info indexes into it. Both out_nodes and out_strings point into
// engine-owned buffers that stay valid until the next call to dasher_frame or
// dasher_get_visible_nodes on this context. Copy the data if you need it beyond
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

### How a frontend uses node-tree rendering

1. Call `dasher_mouse_move` / `dasher_frame` as normal so the engine advances.
2. Call `dasher_get_visible_nodes` to get the array of `dasher_node_info` and
   the strings.
3. For each node (in the returned order, or re-sorted for 3D):
   - Draw it however you want (flat rect, 3D cube, sphere, text card).
   - Use `fill_argb` / `outline_argb` for the colours.
   - Use `label_index` → `out_strings` for the text.
   - Use `screen_x1..y2` for the position.
   - Use `has_children` and `depth` for tree-aware drawing (for example, 3D
     extrusion scaled by depth).
4. Optionally call `dasher_frame` too (for the crosshair, game decorations, and
   so on) and draw those commands on top. Or draw the crosshair yourself from
   the viewport data.

### What the engine provides vs what the frontend decides

| Concern | Engine (node-tree) | Frontend |
| --- | --- | --- |
| Node positions (Dasher and screen) | Yes, via `dasher_node_info` | — |
| Node colours | Yes, from the active palette | May override |
| Node text labels | Yes, via the strings array | May restyle |
| Node tree structure | Yes (depth-first order, depth, has_children) | — |
| Shape (rect / circle / cube / triangle) | Not the engine's call | The frontend decides |
| Depth / 3D extrusion | Not provided | The frontend decides (for example, from `depth`) |
| Animation / transitions | Not provided | The frontend decides |
| Input handling | Yes (`mouse_move` / `key_event`) | — |
| Language model / probabilities | Yes | — |

The key shift: **shape and depth become frontend concerns, not engine concerns.**
`LP_SHAPE_TYPE` becomes a hint, not a mandate. The frontend can draw cubes, flat
rectangles, or something new. A frontend that wants 3D cube extrusion derives it
from `dasher_node_info.depth`; the viewport does not need a separate extrusion
level.

### Relationship to command-buffer rendering

The two paths are not mutually exclusive:

- **Default:** command buffer only. `dasher_frame()` → `int[]` → render. Simplest.
- **Hybrid:** command buffer for most drawing, plus node-tree rendering for a
  specific feature. For example, call `dasher_frame()` for everything, but when
  `LP_SHAPE_TYPE` is `CUBE`, switch to `dasher_get_visible_nodes()` and draw 3D
  cubes from the node tree.
- **Full custom:** node-tree only. The frontend renders everything from the node
  data. Most flexible; most work.

### What about the opcode-7 cube experiment?

The opcode-7 approach (DasherCore PR #50) carries cube depth data through the
flat buffer for a frontend two-pass overlay. It works — the cubes are buffered
and drawn on top — but the effect is weak, because the painter's algorithm
limits the visual result.

With node-tree rendering, opcode 7 is unnecessary: the frontend has the full
node tree and can draw real 3D cubes directly. The recommendation is:

- **Withdraw opcode 7** from the command buffer (it added complexity for a weak
  result).
- **Keep `LP_SHAPE_TYPE`** as a hint (the frontend can read it through
  `dasher_get_long_parameter` and use it to choose its drawing style).
- **Frontends that want cubes** use node-tree rendering plus their own 3D code.

## Drawbacks

- **API surface growth.** `dasher_get_visible_nodes`, `dasher_viewport`, and
  `dasher_node_info` are a significant new API. The `struct_size`
  ABI-versioning field mitigates the forward-compatibility risk, but the API
  still needs docs and tests.
- **Duplicate drawing logic.** Each frontend that uses node-tree rendering
  reimplements the coordinate transforms, the colour lookups, and the text
  positioning that `DasherViewSquare` already does. This is by design
  (flexibility), but it is more code per frontend.
- **Performance.** Copying the node tree into a struct array every frame has a
  cost. For typical Dasher use (50–200 visible nodes) the cost is negligible;
  for extreme cases it may matter.
- **Risk of inconsistency.** A custom-rendering frontend might position nodes
  slightly differently from the command-buffer path, which would mismatch the
  input coordinates. The pre-computed `screen_x1..y2` fields mitigate this,
  because the engine does the coordinate transform.

## Alternatives considered

- **Opcode 7 (cube data in the flat buffer).** Prototyped in DasherCore PR #50.
  It works, but it produces a weak 3D effect, because the painter's algorithm
  cannot composite depth. Withdraw it in favour of node-tree rendering.
- **A new opcode for every 3D shape.** Rejected: the flat buffer would grow
  without end (cube, sphere, cylinder, perspective-rect, and more), and each
  frontend would still have to implement the new opcodes. Node-tree rendering
  solves this once.
- **Frontend-specific rendering paths (bypass the C API).** For example,
  Dasher-Apple queries DasherCore internals directly for node positions.
  Rejected: it breaks the C-API boundary (CONTRIBUTING Rule 4), it is not
  portable, and each frontend reinvents the same queries.

## Prior art

- **Browser DOM rendering.** The browser exposes a DOM tree; CSS and JavaScript
  decide how to render it. Node-tree rendering is analogous: DasherCore exposes
  the node tree; the frontend decides how to draw it.
- **Accessibility APIs** (UIAutomation, AXAPI). They expose semantic structure
  (a tree, roles, labels); the consumer (a screen reader or automation tool)
  renders or interprets it however it wants.
- **Unity / Unreal entity-component systems.** The engine provides data; the
  renderer (which you can swap) decides the visual representation.

## Testing

Per [RFC 0011](./0011-testing.md):

- **DasherCore unit tests** (`tests/`): verify that `dasher_get_visible_nodes`
  returns the correct count, tree-traversal order (depth-first), positions
  (they match `dasher_dasher_to_screen`), and colours for a known node tree.
  Property invariant: the screen bounds in `dasher_node_info` match the
  opcode-4 rectangles from `dasher_frame` for the same frame (parity between the
  two paths). Verify that the node set is clipped to the visible region, the
  same as the command buffer.
- **Frontend (manual):** draw the same node tree in command-buffer mode and in
  node-tree mode; verify visual parity. Then switch to cube mode under
  node-tree rendering and verify that 3D cubes are visible.

## Unresolved questions

1. **Should the engine still emit opcode 7 (cube data)** for frontends that want
   the two-pass approach, or withdraw it entirely in favour of node-tree
   rendering? (Recommendation: withdraw.)
2. **Colour palette access.** Should the API expose the palette directly
   (`dasher_get_palette_colors`), or only the per-node colours in
   `dasher_node_info`?

## Resolution

- Status: _accepted (engine API implemented; no production frontend yet)_
- Decided by: _maintainers_
- Date: _2026-08-01_
- Decision: _The C API lands as the second rendering path. It is opt-in and
  coexists with the command buffer. There is no plan to bring it to every
  platform; it exists for frontends that need full visual control._

## History

- 2026-07-25 — initial proposal, framed as a "two-strand" API. Motivated by the
  cube-mode limit (DasherCore issue #49, PR #50) and the broader goal of VR and
  custom rendering through the C API.
- 2026-07-25 — review feedback folded in: clip to the visible region; document
  tree-traversal order as traversal, not draw order; add the `struct_size`
  ABI-versioning field; drop cube depth from the viewport (the frontend derives
  it from `node_info.depth`); document the string lifetime.
- 2026-08-01 — renamed "Strand 1" / "Strand 2" to **command-buffer rendering**
  and **node-tree rendering**. Added the honest implementation status: the
  engine API is implemented and tested, no production frontend uses it, and the
  DasherMac cube experiment is unmerged and buggy. Recorded that a spatial
  eye-tracked port (for example Meta Quest) is the most promising future use.
