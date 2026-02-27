// ─── Site Configuration ───────────────────────────────────────
// tileUrl:  Orthoimage tiles served from CloudFront
// layers:   KML overlay URLs hosted on CloudFront (all optional)
//
// To update the orthoimage: use the Upload panel in the widget or
// re-tile the TIF and upload to S3 manually.
//
// To add a new site: copy an existing entry and update the values.
// The key (e.g. 'binduli-north') is used in the URL: ?site=binduli-north
// ──────────────────────────────────────────────────────────────

const SERVER_URL = 'http://localhost:5000';  // e.g. 'https://your-ec2-domain.com'

const CF_BASE = 'https://d3mamsvnskv4vj.cloudfront.net';

const SITES = {
    'binduli-north': {
        name: 'Binduli North',
        company: 'Norton',
        tileUrl: `${CF_BASE}/binduli-north/{z}/{x}/{y}.png`,
        layers: {
            boundaries:     `${CF_BASE}/binduli-north/boundaries.kml`,
            infrastructure: null,
            nfzPermanent:   null,
            nfzDaily:       null
        },
        center: [121.37, -30.78],
        defaultZoom: 15
    },
    'gudai-darri': {
        name: 'Gudai Darri',
        company: 'Rio Tinto',
        tileUrl: `${CF_BASE}/gudai-darri/{z}/{x}/{y}.png`,
        layers: {
            boundaries:     null,
            infrastructure: null,
            nfzPermanent:   null,
            nfzDaily:       null
        },
        center: [119.03, -22.53],
        defaultZoom: 15
    },
    'gruyere': {
        name: 'Gruyere',
        company: 'Goldfields',
        tileUrl: `${CF_BASE}/gruyere/{z}/{x}/{y}.png`,
        layers: {
            boundaries:     `${CF_BASE}/gruyere/boundaries.kml`,
            infrastructure: null,
            nfzPermanent:   null,
            nfzDaily:       null
        },
        center: [123.8552, -27.9897],
        defaultZoom: 15
    },
    'saraji': {
        name: 'Saraji',
        company: 'BMA',
        tileUrl: `${CF_BASE}/saraji/{z}/{x}/{y}.png`,
        layers: {
            boundaries:     `${CF_BASE}/saraji/boundaries.kml`,
            infrastructure: null,
            nfzPermanent:   null,
            nfzDaily:       null
        },
        center: [148.30, -22.42],
        defaultZoom: 15
    },
    'peak-downs': {
        name: 'Peak Downs',
        company: 'BMA',
        tileUrl: `${CF_BASE}/peak-downs/{z}/{x}/{y}.png`,
        layers: {
            boundaries:     `${CF_BASE}/peak-downs/boundaries.kml`,
            infrastructure: null,
            nfzPermanent:   null,
            nfzDaily:       null
        },
        center: [148.19, -22.26],
        defaultZoom: 15
    },
    'goonyella': {
        name: 'Goonyella',
        company: 'BMA',
        tileUrl: `${CF_BASE}/goonyella/{z}/{x}/{y}.png`,
        layers: {
            boundaries:     `${CF_BASE}/goonyella/boundaries.kml`,
            infrastructure: null,
            nfzPermanent:   null,
            nfzDaily:       null
        },
        center: [147.97, -21.77],
        defaultZoom: 15
    },
    'koth': {
        name: 'KOTH',
        company: 'Vault Minerals',
        tileUrl: `${CF_BASE}/koth/{z}/{x}/{y}.png`,
        layers: {
            boundaries:     `${CF_BASE}/koth/boundaries.kml`,
            infrastructure: null,
            nfzPermanent:   null,
            nfzDaily:       null
        },
        center: [121.16, -28.67],
        defaultZoom: 15
    },
    'caval-ridge': {
        name: 'Caval Ridge',
        company: 'BMA',
        tileUrl: `${CF_BASE}/caval-ridge/{z}/{x}/{y}.png`,
        layers: {
            boundaries:     `${CF_BASE}/caval-ridge/boundaries.kml`,
            infrastructure: null,
            nfzPermanent:   null,
            nfzDaily:       null
        },
        center: [148.06, -22.12],
        defaultZoom: 15
    },
    'blackwater': {
        name: 'Blackwater',
        company: 'Whitehaven',
        tileUrl: `${CF_BASE}/blackwater/{z}/{x}/{y}.png`,
        layers: {
            boundaries:     `${CF_BASE}/blackwater/boundaries.kml`,
            infrastructure: null,
            nfzPermanent:   null,
            nfzDaily:       null
        },
        center: [148.82, -23.73],
        defaultZoom: 15
    }
};
