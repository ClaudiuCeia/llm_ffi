from typing import Any

from llm_ffi import llm_impl


@llm_impl
def parse_apache_log(line: str) -> dict[str, str]:
    """Parse Apache Common Log Format:
    127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326

    Return dict with: ip, user, timestamp, method, path, protocol, status, size
    """
    raise NotImplementedError  # llm-ffi:d4b2ce0a513894bd:bf0ea41a5bccb635


@llm_impl
def parse_syslog(line: str) -> dict[str, str]:
    """Parse RFC 3164 syslog format:
    <34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8

    Return dict with: priority, timestamp, hostname, application, message
    """
    raise NotImplementedError  # llm-ffi:0f87cb26b885a69b:578faec3112520a6


@llm_impl
def parse_gcp_log(line: str) -> dict[str, Any]:
    """Parse GCP JSON log format:
    {"severity":"INFO","timestamp":"2024-01-01T12:00:00Z","labels":{"pod":"api-xyz"},"textPayload":"Request processed"}

    Return dict with at least: severity, timestamp, message (from textPayload or jsonPayload)
    Include labels if present.
    """
    raise NotImplementedError  # llm-ffi:8d0cfd79fc175a0c:86d6811ad41cce5a


if __name__ == "__main__":
    print("=== Apache Common Log Format ===")
    apache = '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326'
    result = parse_apache_log(apache)
    print(f"IP: {result['ip']}, Method: {result['method']}, Status: {result['status']}")

    print("\n=== Syslog Format ===")
    syslog = (
        "<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8"
    )
    result = parse_syslog(syslog)
    print(
        f"Host: {result['hostname']}, App: {result['application']}, Message: {result['message']}"
    )

    print("\n=== GCP Cloud Logging ===")
    gcp = '{"severity":"ERROR","timestamp":"2024-01-01T12:00:00Z","labels":{"pod":"api-xyz"},"textPayload":"Database timeout"}'
    result = parse_gcp_log(gcp)
    print(
        f"Severity: {result['severity']}, Message: {result['message']}, Labels: {result.get('labels')}"
    )
