# Platform versions

| Component | Version |
|---|---|
| kind | v0.33.0 |
| Kubernetes | v1.37.0 |
| Envoy Gateway | v1.10.0 |

## Install Envoy Gateway

Download, inspect, then apply (server-side, because some CRDs exceed the client-side annotation limit):

    curl -fsSL -o /tmp/eg-install.yaml https://github.com/envoyproxy/gateway/releases/download/v1.10.0/install.yaml
    kubectl apply --server-side -f /tmp/eg-install.yaml
