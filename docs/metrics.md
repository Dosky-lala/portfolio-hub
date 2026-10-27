# Metrics: Chapter 1

## Backend image (naive vs optimized)
| Metric | Naive | Optimized | Change |
|---|---|---|---|
| Compressed size | 501 MB | 74.5 MB | -85% |
| Disk size | 1.95 GB | 320 MB | -84% |
| Runs as | root | appuser (10001) | least privilege |
| Cold build | n/a | 5m 13s | network-bound |
| Cached rebuild | n/a | 6.2 s | ~50x faster |

Environment: WSL2 Ubuntu 26.04, Docker 29.9, ~200 ms latency link.

## Frontend image (single-stage vs multi-stage, same Alpine base)
| Metric | Naive (node:24-alpine) | Multi-stage (nginx-unprivileged) | Change |
|---|---|---|---|
| Compressed size | 110 MB | 25.7 MB | -77% (4.3x) |
| Disk size | 434 MB | 90.5 MB | -79% (4.8x) |
| Runs as | root | nginx | least privilege |
| Ships | Node, npm, node_modules, source | static files + Nginx | build tools never ship |

Both images use an Alpine base, so this isolates the effect of the multi-stage build alone.
