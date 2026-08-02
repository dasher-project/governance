---
rfc: 0014
title: Image labels for alphabet symbols
status: implemented
platforms: [apple, windows, gtk, android, web, core]
created: 2026-07-31
updated: 2026-08-01
---

# Image labels for alphabet symbols

## Summary

Allow the alphabet XML to associate an image path with each symbol. Expose the
path through one C API function. A frontend queries the mapping at startup (or
when the alphabet changes), caches it, and draws an image instead of the text
label. The path works the same way for command-buffer rendering and for
node-tree rendering (see [RFC 0013](./0013-custom-rendering.md)). There are no
new opcodes, no `Label` class changes, and no `node_info` changes.

## Implementation status

Audited August 2026. The engine API is implemented and tested. Uptake is
macOS-only and the result is not great.

- **DasherCore: implemented and tested.** The `image=` attribute is parsed in
  `AlphIO.cpp`; `AlphInfo.h` exposes `GetImage()`; the C API function
  `dasher_get_alphabet_symbol_image` is in `dasher.h` and `CAPI.cpp`; the test
  is `tests/test_image_labels.cpp`.
- **Dasher-Apple (macOS): implemented.** `DasherBridge` builds a label-to-image
  map, substitutes the image inside the opcode-5 (text) quad, and rebuilds the
  map when the alphabet changes.
- **Dasher-Apple (iOS, visionOS, keyboard): not implemented.** These bridges do
  not call the API.
- **No bundled alphabet uses it.** No shipped alphabet XML defines an `image=`
  attribute. The feature is API-ready but unused by the bundled data.

### Honest assessment

Two problems make this less useful than it first looks:

1. **Dynamic image sizing is hard.** Dasher boxes change size every frame as the
   user zooms. A text label scales cleanly because it is vector geometry. A
   raster image does not: it scales poorly, it is slow to resize each frame, and
   the aspect ratio rarely matches the box. The command-buffer path carries no
   layout hint for images, so the frontend sizes them on its own. On macOS the
   result works but is not great.
2. **The driving use case is experimental.** The reason to want image labels is
   phoneme-based AAC: a pre-literate user needs a picture for each phoneme, not
   an IPA glyph or an X-SAMPA code. That phoneme work (see
   `Dasher-Apple/docs/PHONEME_ALPHABET.md` and the `phonemeSymbols/` design
   assets) is experimental. Until a real phoneme alphabet with real images
   ships, image labels are infrastructure without a tested consumer.

### Scope

There is no plan to bring image-label rendering to every platform. It landed in
the engine because the cost is one C API function. The frontend work stays with
the platforms that have a concrete need (today, macOS).

## Motivation

Dasher's alphabet XML defines each symbol with a text `label` (what appears in
the Dasher box) and `text` (what is output when the symbol is selected). For an
orthographic alphabet this is enough — the label is a letter.

For **phoneme-based AAC**, the label might be an IPA glyph (æ, ʃ) or an X-SAMPA
code ({, S). These are meaningless to a pre-literate user — the population that
most needs phoneme-based AAC. Trinh et al. (2012, 2014) used Jolly Phonics images
(42 pictorial phoneme cards) precisely because their users were non-literate.

The need extends beyond phonemes. Any symbol-based AAC alphabet (PCS, Bliss,
Minspeak) benefits from image labels. Dasher has no way to draw images in boxes
today — only text.

## Detailed design

### Alphabet XML: optional `image` attribute

```xml
<node label="ae" image="phonemes/jolly_ae.png">
    <textCharAction />
</node>
```

The `image` attribute is:

- **Optional.** A node without it uses the text label (the current behaviour).
- **A relative path**, resolved against the alphabet's data directory.
- **Frontend-resolved.** The engine stores the string; the frontend loads the
  image file.

### DasherCore changes

#### 1. AlphInfo: store the image path

Add an `Image` field to the `character` struct (`AlphInfo.h`):

```cpp
struct character {
    std::string Display;    // existing
    std::string Text;       // existing
    std::string Image;      // new: optional image path (empty = no image)
    // ... existing fields unchanged
};
```

#### 2. AlphIO: parse the image attribute

One line in `ReadCharAttributes` (`AlphIO.cpp`, after the existing `Display` and
`Text` parsing):

```cpp
alphabet_character.Image = xml_node.attribute("image").as_string();
```

#### 3. CAlphInfo: expose the getter

```cpp
const std::string& GetImage(symbol i) const;
```

Returns the image path for symbol `i`, or an empty string if there is none.

#### 4. C API: one new function

```c
// Returns the image path for symbol `index`, or an empty string if no image.
// The path is relative to the alphabet's data directory.
// Returns 0 on success, -1 on error.
DASHER_API int dasher_get_alphabet_symbol_image(
    dasher_ctx* ctx, int index, char* out_path, int max_len
);
```

That is the entire API surface: one function.

### Frontend usage pattern

Command-buffer frontends and node-tree frontends use the same pattern: query
once, cache, and substitute at draw time.

```swift
// At startup or when the alphabet changes
var imageMap: [String: NSImage] = [:]
let count = dasher_get_alphabet_symbol_count(ctx)
for i in 0..<count {
    var buf = [CChar](repeating: 0, count: 256)
    dasher_get_alphabet_symbol_image(ctx, i, &buf, 256)
    let path = String(cString: buf)
    if !path.isEmpty {
        imageMap[displayText[i]] = loadImage(path)
    }
}

// During rendering — the same for command-buffer and node-tree rendering
if let img = imageMap[label] {
    draw(img, in: rect)
} else {
    draw(text: label, in: rect)
}
```

The lookup table is small (typically 30–50 symbols for a phoneme alphabet). It
is built once and rebuilt only when the user switches alphabet. This is the same
pattern frontends already use for palette colours.

### Image format and sizing

- **Format:** PNG with alpha (transparency). JPEG is acceptable for photographic
  symbols. SVG is a future option, not required for v1.
- **Sizing:** the frontend scales the image to fit the Dasher box at draw time.
  See the honest assessment above: this is the hard part.
- **Compositing:** the palette `fill_argb` fills the box background; the image
  is drawn on top.

### User-supplied image sets

A user can create a custom alphabet with their own images:

```xml
<node label="cat" image="user_symbols/cat.png">
    <textCharAction />
</node>
```

The image files sit alongside the alphabet XML in the user data directory. This
lets a teacher, a clinician, or a user import PCS or Bliss symbol sets, build a
custom phoneme image set, or mix text and image labels in one alphabet.

## Relationship to RFC 0013 (node-tree rendering)

No tension. RFC 0013 defines two rendering paths:

- **Command-buffer rendering** — the frontend decodes the `int[]` opcodes and
  draws them.
- **Node-tree rendering** — the frontend queries the node tree through
  `dasher_get_visible_nodes` and draws from scratch.

This RFC adds **one C API function** that works the same way for both paths. The
frontend queries the image paths independently of the rendering path it chooses.
There is:

- No `image_index` field added to `dasher_node_info` (a node-tree frontend does
  not need it — it already has the mapping).
- No `ImageLabel` class in DasherCore (a command-buffer frontend does not need
  it — it substitutes the image before it calls `DrawString`).
- No new command-buffer opcode.

The engine carries the metadata (the image path in the alphabet definition); the
frontend decides how to draw it. This is the same split as colours: the engine
carries the palette values; the frontend paints the pixels.

## Drawbacks

- **Per-frontend substitution code.** Each frontend implements the lookup table
  and the image drawing (about 10–20 lines). This is trivial and follows the
  existing pattern for palette-colour caching.
- **Bundle size.** An image set adds to the app bundle size. A 42-phoneme set at
  128×128 PNG is about 500 KB. Negligible.
- **Licensing.** Jolly Phonics images are copyrighted. Users provide their own
  image sets. The alphabet XML references paths; the engine does not bundle
  images.
- **Dynamic sizing is hard** (see the honest assessment above). This is the real
  drawback, and it is why uptake is macOS-only for now.

## Alternatives considered

### A. Two mechanisms (a `Label` class for command-buffer rendering, an `image_index` for node-tree rendering)

This was an earlier draft of the RFC. Rejected because:

- It creates two code paths for one feature.
- The `Label` class only works for in-process frontends (GTK), not for C-API
  frontends (Apple, Windows, web). The command buffer carries text, not image
  paths.
- It forces a frontend dev to work out which path they are on before they
  implement image labels.
- It needs more DasherCore changes for no benefit.

### B. A new command-buffer opcode for images

Add opcode 8 to carry image data. Rejected because:

- The command buffer is already at seven opcodes.
- Image paths or data through an `int[]` buffer is awkward.
- It adds decoding work to every command-buffer frontend.

### C. A frontend-only config file (no DasherCore changes)

Each frontend ships a JSON or plist map from labels to image paths. Rejected
because:

- The map is disconnected from the alphabet definition.
- A new alphabet would also need per-frontend config files.
- It is not portable: a phoneme alphabet with images should work on every
  platform.

### D. Node-tree rendering only

Require node-tree rendering for image support. Rejected because:

- Most frontends use the command buffer.
- Forcing node-tree adoption just for image labels is disproportionate.

### E. Unicode emoji as image substitutes

Use emoji characters as labels. Rejected because:

- There is no phonetically systematic emoji set.
- Coverage is incomplete (no emoji for schwa or affricates).
- Rendering varies by platform and font.

## Prior art

- **Trinh et al. (2012, 2014):** iSCAN used Jolly Phonics images (42 pictorial
  phoneme cards) with phoneme prediction. The images were essential for
  pre-literate users.
- **Tobii Communicator, Proloquo2Go, Snap Core First:** commercial AAC apps with
  image-based symbol sets (PCS, Bliss). All support custom image sets.
- **CSS `content: url()`:** a web analogy — text content replaced by an image at
  draw time. The semantic content is unchanged; only the visual representation
  changes.

## Testing

Per [RFC 0011](./0011-testing.md):

- **DasherCore unit tests** (`tests/`):
  - Verify that `AlphIO` parses the `image` attribute from a test alphabet XML.
  - Verify that `GetImage(iSymbol)` returns the correct path.
  - Verify that `dasher_get_alphabet_symbol_image` returns the correct path and
    handles errors (an invalid index, a null buffer).
  - Verify backward compatibility: an alphabet without `image` attributes
    returns an empty string for every symbol.
- **Frontend (manual):**
  - Build a test alphabet with a few image-labelled symbols.
  - Verify that images render in Dasher boxes at several sizes.
  - Verify the text fallback when an image file is missing.
  - Verify that a mixed text-and-image alphabet renders correctly.

## Unresolved questions

1. **SVG support.** **Open.** PNG at 128×128 for v1; SVG is a future option.
2. **Runtime image-set switching.** **Open.** Could be a frontend setting that
   overrides the image-directory prefix.
3. **Image aspect-ratio handling.** **Open.** The hard problem — see the honest
   assessment. Dasher boxes vary in aspect ratio; images could be stretched,
   letterboxed, or cropped.

## Resolution

- State: implemented (engine API; macOS frontend; uptake is experimental and not
  planned for every platform)
- Decided by: maintainers
- Date: 2026-08-01
- Decision: The one-function C API lands. It is cheap in the engine. Frontend
  uptake stays with the platforms that have a concrete need. The dynamic
  sizing problem and the experimental phoneme work are recorded honestly so a
  reader does not over-estimate the feature.
- Open sub-questions: Q1, Q2, Q3.

## History

- 2026-07-31 — initial proposal. Motivated by the phoneme-based AAC work and the
  Trinh et al. papers on phoneme prediction for non-literate users.
- 2026-07-31 — simplified from a two-mechanism design (a `Label` class plus a
  `node_info` field) to one C API function, after it became clear that the
  command-buffer / node-tree tension was unnecessary. The frontend
  query-and-cache pattern works the same way for both paths, with no engine
  drawing changes.
- 2026-08-01 — renamed the rendering paths from "Strand 1 / Strand 2" to
  **command-buffer rendering** and **node-tree rendering** (per RFC 0013). Added
  the honest implementation status: engine and macOS-only frontend landed;
  dynamic image sizing is hard; the phoneme-symbol use case is experimental;
  not planned for every platform.
