# Jotform Map Widget

A browser-based map drawing widget built with [OpenLayers](https://openlayers.org/). Designed to be embedded in JotForm forms as a custom widget, allowing users to draw shapes on orthoimage base maps and export them as KML files compatible with DJI FlightHub 2.

## Features

- **Drawing Tools** -- Polygon, Rectangle, Circle, Line, and Point tools for creating map features
- **Named Features** -- Each drawn shape can be given a custom name, which is preserved in the exported KML
- **KML Export** -- Download drawn features as KML files, or automatically submit them via a JotForm field
- **Orthoimage Tiles** -- Per-site orthoimage base layers served from CloudFront, with OSM Street and Esri Satellite fallbacks
- **Site Boundaries** -- KML-based boundary overlays rendered client-side as white outlines with labels
- **Fullscreen Mode** -- Expand the map to fill the browser window
- **Undo / Clear** -- Step back through drawn features or clear the canvas entirely

## Hosting on GitHub Pages

1. Push this repository to GitHub
2. Go to **Settings > Pages** and set the source to `main` branch (root `/`)
3. The widget will be available at `https://<username>.github.io/<repo-name>/?site=<site-key>`

## URL Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `site`    | Yes      | Site key from `config.js` (e.g. `binduli-north`, `gudai-darri`) |
| `qid`     | No       | JotForm question ID -- enables JotForm iframe integration mode |

**Example:** `https://<your-domain>/?site=binduli-north`

## Site Configuration

All site definitions live in [`config.js`](config.js) for easy management. Each site entry has the following properties:

```javascript
'site-key': {
    name: 'Display Name',          // Shown in the header
    company: 'Company Name',       // Shown below the site name
    tileUrl: 'https://.../{z}/{x}/{y}.png',  // XYZ orthoimage tile URL
    boundaryUrl: 'https://.../boundaries.kml', // KML with site boundary polygons
    center: [longitude, latitude], // Initial map centre (WGS84)
    defaultZoom: 15                // Initial zoom level
}
```

### Adding a New Site

1. Open `config.js`
2. Copy an existing site entry
3. Update the key and all property values
4. Commit and push -- the new site is immediately available via `?site=your-new-key`

### Updating Orthoimages or Boundaries

- **Orthoimages:** Re-tile the new TIF and upload to the same S3/CloudFront path. No code changes needed.
- **Boundaries:** Upload a replacement KML to the `boundaryUrl` path. No code changes needed.

These are completely independent -- you can update one without touching the other.

## JotForm Integration

When embedded as a JotForm widget inside an iframe with a `qid` parameter, the widget automatically:

1. Sends a `frameReady` message to the parent form on load
2. Posts the current KML data to the parent form whenever features are added, removed, or cleared
3. Responds to `submit` messages from the parent form with the final KML data

## Tech Stack

- [OpenLayers 8.2](https://openlayers.org/) -- Map rendering, vector layers, and drawing interactions
- [DM Sans](https://fonts.google.com/specimen/DM+Sans) -- UI typography
- Vanilla HTML/CSS/JS -- No build step or dependencies beyond the CDN-loaded libraries
