# qb-natpmp

This helper keeps the TCP/UDP port mappings of Proton VPN alive. It also
synchronizes the listening port of qBittorrent. Run the helper in the same
network namespace as the VPN and qBittorrent. Make sure that the VPN kill
switch is active before you start the helper.

## Configuration

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `VPN_GATEWAY` | `10.2.0.1` | The IPv4 NAT-PMP gateway. |
| `QB_URL` | `http://127.0.0.1:9080` | The URL of the qBittorrent Web API. Set the actual WebUI port in this URL. |
| `QB_USER` | `admin` | The user name for the Web API. |
| `QB_PASS` | `admin` | The password for the Web API. |
| `QB_NATPMP_HEALTH_FILE` | `/tmp/qb-natpmp-health.json` | A writable, container-local file for the health marker. |

The VPN profile must enable NAT-PMP/port forwarding. qBittorrent must be
reachable at `QB_URL`. The helper accepts a successful sign-in with HTTP
200/`Ok.` or with HTTP 204. Failed credentials remain errors.

## Renewal and recovery

The helper requests 60-second TCP and UDP leases. It checks that both
protocols receive the same internal and external ports. It renews the leases
halfway through the shortest granted lease. Deadlines use monotonic time, and
the helper measures this time from the request. Thus, the duration of the API
calls does not extend a lease. This follows the renewal recommendation in
[RFC 6886 section 3.3](https://datatracker.ietf.org/doc/html/rfc6886#section-3.3).

The helper retransmits each NAT-PMP request within a three-second deadline.
Replies must come from the selected gateway on UDP 5351 and match the request.
Invalid or unrelated datagrams cannot extend that deadline. If a refresh fails,
the helper retries after five seconds.

Requests to qBittorrent use a two-second connection timeout and a three-second
read timeout. The helper disables automatic retries and redirects for these
requests. If the synchronization fails, the helper retries after five
seconds. This retry does not move the deadline for the next lease renewal.
After a qBittorrent restart, the helper authenticates the expired session
again. The helper sets the port in qBittorrent again on each successful
renewal.

## Health and monitoring

```sh
python3 /opt/app/health.py
```

Exit code 0 means that the helper synchronized TCP/UDP grants with the same
ports to qBittorrent. It also means that the earliest lease is still valid.
Exit code 1 means startup, absent/corrupt state, a failed mapping, or an
expired success marker. The JSON marker also records `last_success` as a Unix
timestamp for diagnostics. The helper writes the marker atomically. The marker
contains no credentials. The helper deletes the marker at process startup.
Keep this file on container-local storage, not on a persistent/shared volume.

The image contains a Docker `HEALTHCHECK`. Kubernetes does not run the Docker
health check. It needs an explicit probe. When you deploy a version that
contains `health.py`, add this probe to the **qb-natpmp container**:

```yaml
readinessProbe:
  exec:
    command: [python3, /opt/app/health.py]
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 2
```

A failed readiness probe marks the entire Pod unready. This removes the Pod
from normal Service traffic. The qBittorrent WebUI is also part of this
traffic. Choose this behavior intentionally. If the WebUI must remain
available during VPN outages, make your monitor run the health command
separately instead. An expired VPN credential needs a manual action. Thus,
this lease-health check is not a liveness restart policy.
[Kubernetes probe behavior](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

With kube-state-metrics and the readiness probe above, an alert rule can detect
persistent failures:

```yaml
- alert: QbNatpmpUnhealthy
  expr: kube_pod_container_status_ready{container="qb-natpmp"} == 0
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "qBittorrent port forwarding has not recovered"
    description: "Inspect qb-natpmp logs, VPN connectivity/credential expiry, and qBittorrent API access."
```

The probe configuration and the alert configuration belong to the deployment
repository. A rebuild of this helper alone does not add them to a Kubernetes
workload that already exists. The health command checks the lease/API
synchronization. It does not check an external inbound connection. It also
does not check the validity period of the VPN account credential.

## Tests

```sh
python3 -m pip install --require-hashes -r requirements.lock
python3 -m unittest discover -s tests -v
```

The tests cover these areas:

- API compatibility and stalled HTTP connections.
- Lost/malformed NAT-PMP replies.
- Renewal deadlines during API failures.
- TCP/UDP consistency.
- Health-marker expiry.

The tests do not need a VPN or a live qBittorrent.
