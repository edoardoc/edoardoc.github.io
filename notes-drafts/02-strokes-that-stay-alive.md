# Strokes that stay alive

Most drawing apps flatten your line into pixels the moment you lift your
finger. Doodle Tag keeps every stroke as a live vector object, which is the
only reason Eraser, Wind, and replay can exist.

- The model: what a stroke is in memory (points? curves?), and what it costs
  to keep thousands of them live on a giant pannable canvas. TODO: numbers.
- A true Eraser: cutting a vector line in two instead of painting white over
  it. TODO: the geometry edge cases that hurt.
- Wind: bending lines after the fact. TODO: how the deformation works.
- Replay and MP4: recording is a stroke log, export is encoded on the device.
  TODO: why on-device encoding, and what it took on each platform.
