"""Client identification for rate limiting."""

import ipaddress

from starlette.requests import Request

# https://www.cloudflare.com/ips/ (checked 2026-11-02)
_CLOUDFLARE_NETWORKS = tuple(ipaddress.ip_network(cidr) for cidr in (
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20",
    "197.234.240.0/22", "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
    "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22",
    "2400:cb00::/32", "2606:4700::/32", "2803:f800::/32", "2405:b500::/32",
    "2405:8100::/32", "2a06:98c0::/29", "2c0f:f248::/32",
))


def _parse_ip(value: str):
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError:
        return None


def _is_cloudflare(ip) -> bool:
    return any(ip in network for network in _CLOUDFLARE_NETWORKS if network.version == ip.version)


def client_ip(request: Request) -> str:
    """The caller's IP, usable as a rate-limit key.

    The reverse proxy overwrites X-Forwarded-For with the peer it saw, so only the last
    hop is trustworthy. CF-Connecting-IP counts only when that peer really is Cloudflare;
    otherwise anyone could pick their own rate-limit bucket by sending the header.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    peer = forwarded.rsplit(",", 1)[-1].strip() or (request.client.host if request.client else "unknown")
    peer_ip = _parse_ip(peer)
    if peer_ip is not None and _is_cloudflare(peer_ip):
        claimed = _parse_ip(request.headers.get("cf-connecting-ip", ""))
        if claimed is not None:
            return str(claimed)
    return peer
