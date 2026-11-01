# Loop-3: GTK ydotool correction + trivia (backward-only wording, test home, node count)
import re

P = r'C:\github\DasherProjects\governance\rfcs\0021-control-select-subtree.md'
s = open(P, encoding='utf-8').read()

# GTK table rows: XTest -> the frontend's existing injection path
s = s.replace(
    '| XTest `Shift+←/→` |',
    '| ydotool `Shift+←/→` |')
s = s.replace(
    '| `Ctrl+Shift+↑/↓` (GtkTextView-class targets) |',
    '| `Ctrl+Shift+↑/↓` (GtkTextView-class targets) |')

old_gtk = '''- **GTK**: XTest keystrokes work under X11; **Wayland has no XTest** (same
  open item as RFC 0015's clipboard notes) — Wayland GTK degrades to
  editor-mode-only until a portal path exists.'''
new_gtk = '''- **GTK**: reuses the frontend's existing **ydotool** injection path (RFC
  0015's status table) — available under X11 and Wayland alike where the
  daemon runs, so no new injection mechanism and no editor-mode-only
  degradation; Wayland inherits 0015's focus/keep-above caveats. XTest
  remains an X11-native fallback only.'''
assert old_gtk in s
s = s.replace(old_gtk, new_gtk)

# Rollout's GTK line follows the old conclusion
s = s.replace(
    'GTK may land\n   editor-mode-only pending Wayland)',
    'GTK lands on\n   the ydotool path with 0015\'s Wayland focus caveats)')

# trivia: direction-agnostic diagnosis
s = s.replace(
    'so a BACKWARD selection that crosses\n  a sentence boundary (which *Select paragraph backward* does by definition)',
    'so any selection\n  that moves the caret-anchored window across a sentence boundary (backward\n  paragraph selects by definition; forward selects past a delimiter too)')

# trivia: test home is Dasher-Windows, not engine-side
s = s.replace(
    'must add\n  engine-side or test-side confirmation that chained backward selects no\n  longer re-seed',
    'must add a\n  Dasher-Windows test (ContextSeedPolicy xUnit suite) confirming chained\n  selects in the settle window no longer re-seed')

# trivia: node count
s = s.replace(
    '- Another ten nodes deepen the control subtree',
    '- Another eleven node templates deepen the control subtree')

open(P, 'w', encoding='utf-8', newline='').write(s)
print('loop-3 fixes applied')
