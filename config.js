// ─── Site Configuration ───────────────────────────────────────
// tileUrl:     Orthoimage tiles (raw TIF tiled directly, no polygon overlay)
// boundaryUrl: KML file with site area polygons (rendered client-side)
//
// To update the orthoimage: just re-tile the new TIF and upload to S3.
// To update boundaries: upload a new KML to the boundaryUrl path.
// These are completely independent — no need to re-overlay polygons on imagery.
//
// To add a new site: copy an existing entry and update the values.
// The key (e.g. 'binduli-north') is used in the URL: ?site=binduli-north
// ──────────────────────────────────────────────────────────────

const SITES = {
    'binduli-north': {
        name: 'Binduli North',
        company: 'Norton',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/binduli-north/{z}/{x}/{y}.png',
        boundaryUrl: 'https://d3mamsvnskv4vj.cloudfront.net/binduli-north/binduli_north_boundaries.kml',
        center: [121.37, -30.78],
        defaultZoom: 15
    },
    'gudai-darri': {
        name: 'Gudai Darri',
        company: 'Rio Tinto',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/gudai-darri/{z}/{x}/{y}.png',
        boundaryUrl: 'https://d3mamsvnskv4vj.cloudfront.net/gudai-darri/gdi_boundaries.kml',
        center: [119.03, -22.53],
        defaultZoom: 15
    },
    'gruyere': {
        name: 'Gruyere',
        company: 'Goldfields',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/gruyere/{z}/{x}/{y}.png',
        boundaryUrl: 'https://d3mamsvnskv4vj.cloudfront.net/gruyere/gruyere_boundaries.kml',
        center: [123.8552, -27.9897],
        defaultZoom: 15
    },
    'saraji': {
        name: 'Saraji',
        company: 'BMA',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/saraji/{z}/{x}/{y}.png',
        boundaryUrl: 'https://d3mamsvnskv4vj.cloudfront.net/saraji/saraji_boundaries.kml',
        center: [148.30, -22.42],
        defaultZoom: 15
    },
    'peak-downs': {
        name: 'Peak Downs',
        company: 'BMA',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/peak-downs/{z}/{x}/{y}.png',
        boundaryUrl: 'https://d3mamsvnskv4vj.cloudfront.net/peak-downs/peak_downs_boundaries.kml',
        center: [148.19, -22.26],
        defaultZoom: 15
    },
    'goonyella': {
        name: 'Goonyella',
        company: 'BMA',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/goonyella/{z}/{x}/{y}.png',
        boundaryUrl: 'https://d3mamsvnskv4vj.cloudfront.net/goonyella/goonyella_boundaries.kml',
        center: [147.97, -21.77],
        defaultZoom: 15
    },
    'koth': {
        name: 'KOTH',
        company: 'Vault Minerals',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/koth/{z}/{x}/{y}.png',
        boundaryUrl: 'https://d3mamsvnskv4vj.cloudfront.net/koth/koth_boundaries.kml',
        center: [121.16, -28.67],
        defaultZoom: 15
    },
    'caval-ridge': {
        name: 'Caval Ridge',
        company: 'BMA',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/caval-ridge/{z}/{x}/{y}.png',
        boundaryUrl: 'https://d3mamsvnskv4vj.cloudfront.net/caval-ridge/caval_ridge_boundaries.kml',
        center: [148.06, -22.12],
        defaultZoom: 15
    }
};
