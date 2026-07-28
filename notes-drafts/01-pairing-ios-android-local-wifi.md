# Pairing an iPhone with an Android over local Wi-Fi

The one-sentence promise: two phones from rival ecosystems find each other on
the same network and share a canvas, with no account and no server.

- Why local: what the no-cloud constraint buys (privacy, zero infra) and what
  it costs (no relay fallback, the network is whatever the room gives you).
- TODO: discovery: how the devices actually find each other (mDNS/NSD?
  something custom?), and the first thing that broke on real routers.
- TODO: transport: the protocol carrying strokes between platforms, and how
  message order/latency is handled while both people draw at once.
- TODO: one war story: the ugliest incompatibility between iOS and Android
  networking stacks, and the fix that shipped.
- What "Glue" means in the app, in one paragraph, for non-engineers.
