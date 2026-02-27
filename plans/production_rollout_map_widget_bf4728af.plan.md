---
name: Production rollout map widget
overview: Roll out the current dev implementation to production using a secure, supportable AWS path (default ECS Fargate, fallback EC2 Docker), with clear ownership split between you and head of development.
todos:
  - id: security-baseline
    content: Rotate secrets and establish Secrets Manager/SSM usage
    status: pending
  - id: aws-provisioning
    content: Provision IAM, S3, CloudFront, compute runtime, HTTPS
    status: pending
  - id: app-hardening
    content: Add health checks, persistent job state, logging, and improved ETA
    status: pending
  - id: staging-verification
    content: Run end-to-end staging smoke tests and fix gaps
    status: pending
  - id: production-cutover
    content: Deploy production and monitor post-release
    status: pending
isProject: false
---

# Production Rollout Plan

## Goal

Move the current dev state to production safely for TIFF/hillshade uploads, tile generation, KML overlays, and stable map serving.

## Recommended Path

- **Default:** ECS Fargate service for `server/` (containerized API + GDAL processing).
- **Fallback:** Single EC2 Docker host if you need fastest initial go-live.

## Phase 0: Immediate Safety (do first)

- Rotate exposed credentials and secrets immediately.
- Stop using long-lived AWS keys in local `.env` for production.
- Keep secrets only in AWS Secrets Manager / SSM Parameter Store.
- Confirm `.env` is never committed going forward.

## Phase 1: Decide and Lock Architecture

- Keep frontend static hosting on GitHub Pages (or CloudFront/S3 if your org prefers).
- Run upload/tiling backend from `server/app.py` behind HTTPS.
- Keep storage in S3 and serve tiles/KML through CloudFront.
- Use one canonical data layout:
  - Tiles: `tiles/{site}/{z}/{x}/{y}.png`
  - KML: `tiles/{site}/{layerType}.kml`

## Phase 2: AWS Resources Head of Dev Must Provision

- **Identity/Security**
  - IAM role for runtime service with least privilege to specific S3 prefixes.
  - IAM role for CI/CD deploys (if using pipeline).
  - Secrets Manager entries for upload secret and config values.
- **Storage/CDN**
  - S3 bucket(s) with versioning enabled.
  - CloudFront distribution with correct origin path and cache rules.
  - CORS rules allowing widget origin(s) for KML/tiles reads; upload API origin for requests.
- **Compute/Networking**
  - ECS cluster/service (or EC2 host) for container runtime.
  - ALB or API Gateway in front of service, HTTPS certificate via ACM.
  - CloudWatch log group and retention policy.

## Phase 3: Harden App Before Production Cutover

- In [server/app.py](server/app.py):
  - Add health endpoint (`/health`) and readiness semantics.
  - Replace in-memory `jobs` store with persistent/shared store (Redis/DynamoDB) so status survives restarts and scales beyond 1 worker.
  - Add structured logging for upload/tiling lifecycle and errors.
  - Improve ETA logic (phase-based + measured throughput; avoid `ETA 0s` until complete).
  - Add stronger upload validation (MIME/header checks, max size guards per file).
  - Restrict CORS origins instead of permissive defaults.
- In [server/Dockerfile](server/Dockerfile):
  - Keep single-worker mode until shared job store is implemented.
  - Add container healthcheck command.

## Phase 4: Deploy and Validate in Staging

- Deploy backend container to staging target.
- Configure frontend in [config.js](config.js) to staging API URL/asset URLs.
- Run smoke tests:
  - upload ortho only,
  - upload ortho + hillshade with custom opacity,
  - verify old site tiles are removed and replaced,
  - verify KML upload + map load,
  - verify status polling survives refresh/redeploy.
- Validate CORS from browser (no KML fetch errors).

## Phase 5: Production Release

- Freeze config and announce maintenance window.
- Deploy backend, then update frontend config and cache invalidation.
- Execute production checklist with one test site first, then full rollout.
- Monitor CloudWatch logs, 4xx/5xx rates, and tiling job durations for first 48 hours.

## What You Should Ask Your Head of Development

- Approve **runtime choice**: ECS Fargate (recommended) vs EC2 fallback.
- Confirm who owns:
  - IAM roles/policies,
  - S3/CloudFront CORS,
  - TLS certificate and DNS,
  - Secrets Manager setup,
  - staging and production accounts.
- Confirm production non-functional requirements:
  - expected upload concurrency,
  - max TIFF size,
  - acceptable processing time SLA,
  - retention and rollback policy.

## Ownership Split

- **You:** app behavior, frontend upload UX, functional testing, site onboarding, smoke tests.
- **Head of Development:** AWS provisioning, IAM/security, network/TLS, deployment approvals.

## Fallback Strategy (if blocked on platform work)

- Launch on single EC2 Docker host with HTTPS reverse proxy and locked IAM policy.
- Keep same S3/CloudFront layout and API contract.
- Migrate to ECS later without changing frontend behavior.

## Acceptance Criteria for Production Readiness

- Users can upload ortho (+ optional hillshade opacity) and KML from widget.
- New uploads fully replace prior tiles for the site.
- No browser CORS failures for KML/tiles.
- Status endpoint is reliable across restarts/scaling.
- Secrets are managed centrally; no hardcoded credentials.

