// ─── Site Configuration ───────────────────────────────────────
// tileUrl:      Orthoimage tiles served from CloudFront
// boundaryUrl:  KML boundary files hosted in this repo's /boundaries folder
//
// To update the orthoimage: re-tile the new TIF and upload to S3.
// To update boundaries: replace the KML in the /boundaries folder and push.
// These are completely independent.
//
// To add a new site: copy an existing entry and update the values.
// The key (e.g. 'binduli-north') is used in the URL: ?site=binduli-north
// ──────────────────────────────────────────────────────────────

const BOUNDARY_BASE = 'https://ciarangracie.github.io/jotform-map-widget/boundaries';

const SITES = {
    'binduli-north': {
        name: 'Binduli North',
        company: 'Norton',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/binduli-north/{z}/{x}/{y}.png',
        boundaryUrl: `${BOUNDARY_BASE}/binduli-north_boundaries.kml`,
        center: [121.37, -30.78],
        defaultZoom: 15
    },
    'gudai-darri': {
        name: 'Gudai Darri',
        company: 'Rio Tinto',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/gudai-darri/{z}/{x}/{y}.png',
        boundaryUrl: `${BOUNDARY_BASE}/gdi_boundaries.kml`,
        center: [119.03, -22.53],
        defaultZoom: 15
    },
    'gruyere': {
        name: 'Gruyere',
        company: 'Goldfields',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/gruyere/{z}/{x}/{y}.png',
        boundaryUrl: `${BOUNDARY_BASE}/gruyere_boundaries.kml`,
        center: [123.8552, -27.9897],
        defaultZoom: 15
    },
    'saraji': {
        name: 'Saraji',
        company: 'BMA',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/saraji/{z}/{x}/{y}.png',
        boundaryUrl: `${BOUNDARY_BASE}/saraji_boundaries.kml`,
        center: [148.30, -22.42],
        defaultZoom: 15
    },
    'peak-downs': {
        name: 'Peak Downs',
        company: 'BMA',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/peak-downs/{z}/{x}/{y}.png',
        boundaryUrl: `${BOUNDARY_BASE}/peak-downs_boundaries.kml`,
        center: [148.19, -22.26],
        defaultZoom: 15
    },
    'goonyella': {
        name: 'Goonyella',
        company: 'BMA',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/goonyella/{z}/{x}/{y}.png',
        boundaryUrl: `${BOUNDARY_BASE}/goonyella_boundaries.kml`,
        center: [147.97, -21.77],
        defaultZoom: 15
    },
    'koth': {
        name: 'KOTH',
        company: 'Vault Minerals',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/koth/{z}/{x}/{y}.png',
        boundaryUrl: `${BOUNDARY_BASE}/koth_boundaries.kml`,
        center: [121.16, -28.67],
        defaultZoom: 15
    },
    'caval-ridge': {
        name: 'Caval Ridge',
        company: 'BMA',
        tileUrl: 'https://d3mamsvnskv4vj.cloudfront.net/caval_ridge/{z}/{x}/{y}.png',
        boundaryUrl: `${BOUNDARY_BASE}/caval-ridge_boundaries.kml`,
        center: [148.06, -22.12],
        defaultZoom: 15
    }
};
