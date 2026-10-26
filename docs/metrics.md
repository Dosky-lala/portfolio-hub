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
