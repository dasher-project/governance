---
rfc: 0014
title: Image labels for alphabet symbols
status: proposed
platforms: [apple, windows, gtk, android, web, core]
created: 2026-07-31
updated: 2026-07-31
---

# Image labels for alphabet symbols

## Summary

Allow alphabet XML to associate an image path with each symbol. Expose it
through a single C API function. Frontends query the mapping at startup (or
when the alphabet changes), cache it, and substitute images for text labels
during rendering. Works identically for Strand 1 (command buffer) and Strand 2
(custom rendering). No new opcodes, no Label class changes, no node_info
changes.

## Motivation

Dasher's alphabet XML defines each symbol with a text `label` (what appears
in the Dasher box) and `text` (what gets output when selected). For
orthographic alphabets this is sufficient — the label is a letter.

For **phoneme-based AAC** (see `feature/phoneme-alphabet-xsampa` branch),
the label might be an IPA glyph (æ, ʃ) or X-SAMPA code ({, S). These are
meaningless to pre-literate users — the population that most needs phoneme-
based AAC. Trinh et al. (2012, 2014) used Jolly Phonics images (42
pictorial phoneme cards) precisely because their target users were
non-literate.

The need extends beyond phonemes: any symbol-based AAC alphabet (PCS, Bliss,
Minspeak) benefits from image labels. Dasher currently has no mechanism to
render images in boxes — only text.

## Detailed design

### Alphabet XML: optional `image` attribute

```xml
<node label="ae" image="phonemes/jolly_ae.png">
    <textCharAction />
</node>
```

The `image` attribute is:
- **Optional.** Nodes without it use the text label (current behaviour).
- **A relative path** resolved against the alphabet's data directory.
- **Frontend-resolved.** The engine stores the string; the frontend loads
  the image file.

### DasherCore changes

#### 1. AlphInfo: store image path

Add an `Image` field to the `character` struct (`AlphInfo.h:150`):

```cpp
struct character {
    std::string Display;    // existing
    std::string Text;       // existing
    std::string Image;      // new: optional image path (empty = no image)
    // ... existing fields unchanged
};
```

#### 2. AlphIO: parse image attribute

One line in `ReadCharAttributes` (`AlphIO.cpp`, after the existing `Display`
and `Text` parsing):

```cpp
alphabet_character.Image = xml_node.attribute("image").as_string();
```

#### 3. CAlphInfo: expose getter

```cpp
const std::string& GetImage(symbol i) const;
```

Returns the image path for symbol `i`, or empty string if none.

#### 4. C API: one new function

```c
// Returns the image path for symbol `index`, or empty string if no image.
// The path is relative to the alphabet's data directory.
// Returns 0 on success, -1 on error.
DASHER_API int dasher_get_alphabet_symbol_image(
    dasher_ctx* ctx, int index, char* out_path, int max_len
);
```

That's the entire API surface. One function.

### Frontend usage pattern

Both Strand 1 and Strand 2 frontends use the same pattern — query once, cache,
substitute at render time:

```swift
// At startup or when alphabet changes
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

// During rendering — same for Strand 1 and Strand 2
if let img = imageMap[label] {
    draw(img, in: rect)
} else {
    draw(text: label, in: rect)
}
```

The lookup table is small (typically 30–50 symbols for a phoneme alphabet),
built once, and only rebuilt when the user switches alphabet. This is the
same pattern frontends already use for palette colours.

### Image format and sizing

- **Format**: PNG with alpha (transparency). JPEG acceptable for photographic
  symbols. SVG is a future option but not required for v1.
- **Sizing**: images are scaled to fit the Dasher box at render time, same
  as text labels are sized to fit.
- **Compositing**: the palette's `fill_argb` fills the box background; the
  image is drawn on top.

### User-supplied image sets

Users create custom alphabets with their own images:

```xml
<node label="cat" image="user_symbols/cat.png">
    <textCharAction />
</node>
```

Image files are placed alongside the alphabet XML in the user data directory.
This enables teachers, clinicians, or users to import PCS/Bliss symbol sets,
create custom phoneme image sets, or mix text and image labels in the same
alphabet.

## Relationship to RFC 0013 (custom rendering)

No tension. RFC 0013 introduced two rendering strands:
- **Strand 1** (command buffer): frontend decodes `int[]` opcodes and renders
- **Strand 2** (custom rendering): frontend queries node tree via
  `dasher_get_visible_nodes` and renders from scratch

This RFC adds **one C API function** that works identically for both strands.
The frontend queries image paths independently of the rendering path it
chooses. There is:
- No `image_index` field added to `dasher_node_info` (Strand 2 doesn't need
  it — the frontend already has the mapping)
- No `ImageLabel` class in DasherCore (Strand 1 doesn't need it — the
  frontend substitutes before calling `DrawString`)
- No new command buffer opcodes

The engine carries the metadata (image path in the alphabet definition); the
frontend decides how to render it. This is the same separation as colours:
the engine carries palette values, the frontend paints pixels.

## Drawbacks

- **Per-frontend substitution code.** Each frontend implements the lookup
  table and image rendering (~10–20 lines). This is trivial and follows the
  existing pattern for palette colour caching.
- **Bundle size.** Image sets add to app bundle size. A 42-phoneme set at
  128×128 PNG is ~500 KB. Negligible.
- **Licensing.** Jolly Phonics images are copyrighted. Users provide their
  own image sets. The alphabet XML references paths; the engine does not
  bundle images.

## Alternatives considered

### A. Two mechanisms (Label class for Strand 1, image_index for Strand 2)

Proposed in an earlier draft of this RFC. Rejected because:
- Creates two code paths for the same feature
- The Label class approach only works for in-process frontends (GTK), not C
  API frontends (Apple, Windows, Web) — the command buffer carries text, not
  image paths
- Forces frontend devs to understand which strand they're on before
  implementing image labels
- More DasherCore internal changes for no benefit

### B. New command buffer opcode for images

Add opcode 8 carrying image data. Rejected because:
- The command buffer is already at 7 opcodes
- Image paths or data through an `int[]` buffer is awkward
- Adds decoding complexity to every Strand 1 frontend

### C. Frontend-only config file (no DasherCore changes)

Each frontend ships a JSON/plist mapping labels to image paths. Rejected
because:
- The mapping is disconnected from the alphabet definition
- Creating a new alphabet requires also creating per-frontend config files
- Not portable — a phoneme alphabet with images should work on all platforms

### D. Strand 2 only

Require Strand 2 for image support. Rejected because:
- Most frontends use Strand 1
- Forcing Strand 2 adoption just for image labels is disproportionate

### E. Unicode emoji as image substitutes

Use emoji characters as labels. Rejected because:
- No phonetically systematic emoji set
- Coverage incomplete (no emoji for schwa, affricates)
- Rendering varies by platform/font

## Prior art

- **Trinh et al. (2012, 2014)**: iSCAN used Jolly Phonics images (42
  pictorial phoneme cards) with phoneme prediction. Images were essential
  for pre-literate users.
- **Tobii Communicator, Proloquo2Go, Snap Core First**: commercial AAC apps
  with image-based symbol sets (PCS, Bliss). All support custom image sets.
- **CSS `content: url()`**: web analogy — text content replaced by an image
  at render time. Semantic content unchanged; visual representation changes.

## Testing

Per [RFC 0011](./0011-testing.md):

- **DasherCore unit tests** (`tests/`):
  - Verify `AlphIO` parses `image` attribute from a test alphabet XML.
  - Verify `GetImage(iSymbol)` returns correct path.
  - Verify `dasher_get_alphabet_symbol_image` returns correct path and
    handles errors (invalid index, null buffer).
  - Verify backward compatibility: alphabets without `image` attributes
    return empty string for all symbols.

- **Frontend (manual)**:
  - Create a test alphabet with a few image-labelled symbols.
  - Verify images render in Dasher boxes at various sizes.
  - Verify text fallback when image file is missing.
  - Verify mixed text/image alphabets render correctly.

## Unresolved questions

1. **SVG support.** Should v1 accept SVG for crisp rendering at all sizes?
   Adds parsing complexity per platform. PNG at 128×128 is simpler.

2. **Runtime image-set switching.** Should users swap image sets at runtime
   (e.g., Jolly Phonics ↔ PCS) without changing the alphabet XML? Could be a
   frontend settings option that overrides the image directory prefix.

3. **Image aspect ratio handling.** Dasher boxes vary in aspect ratio.
   Images could be stretched, letterboxed, or cropped. Text labels use a
   single font size; images may need different sizing logic.

## Resolution

_(Filled in once a decision is reached.)_

- Status: _pending_
- Decided by: _pending_
- Date: _pending_
- Decision: _pending_

## History

- 2026-07-31 — initial proposal. Motivated by phoneme-based AAC work and
  Trinh et al. papers on phoneme prediction for non-literate users.
- 2026-07-31 — simplified from two-mechanism design (Label class + node_info
  field) to single C API function after identifying that Strand 1/Strand 2
  tension was unnecessary. The frontend query-and-cache pattern works
  identically for both strands with no engine rendering changes.
