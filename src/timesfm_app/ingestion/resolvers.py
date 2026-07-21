from __future__ import annotations

import hashlib
import ipaddress
import os
import socket
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from timesfm_app.contracts import SUPPORTED_SUFFIXES, ResolvedAsset

DEFAULT_MAX_BYTES = 200 * 1024 * 1024
HostResolver = Callable[[str], Iterable[str]]


class SourceResolutionError(ValueError):
    """Raised when an external source is invalid or unsafe."""


def cache_uploaded_file(
    filename: str,
    content: bytes,
    cache_root: Path,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> ResolvedAsset:
    safe_name = Path(filename).name
    _validate_filename(safe_name)
    if len(content) > max_bytes:
        raise SourceResolutionError(f"Upload exceeds {max_bytes:,}-byte size limit.")
    _validate_signature(Path(safe_name).suffix.lower(), content[:4])
    digest = hashlib.sha256(content).hexdigest()
    destination = _destination(cache_root, digest, safe_name)
    if not destination.exists():
        destination.write_bytes(content)
    return ResolvedAsset(destination, "upload", safe_name, digest, len(content))


def validate_public_url(
    url: str,
    *,
    host_resolver: HostResolver | None = None,
) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise SourceResolutionError("Only HTTP and HTTPS dataset URLs are allowed.")
    if parsed.username or parsed.password:
        raise SourceResolutionError("URLs containing embedded credentials are not allowed.")
    if not parsed.hostname:
        raise SourceResolutionError("URL must include a hostname.")

    resolver = host_resolver or _resolve_host
    try:
        addresses = list(resolver(parsed.hostname))
    except OSError as error:
        raise SourceResolutionError(f"Could not resolve URL host {parsed.hostname!r}.") from error
    if not addresses:
        raise SourceResolutionError(f"Could not resolve URL host {parsed.hostname!r}.")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise SourceResolutionError("URL resolves to a private or otherwise unsafe address.")


def download_public_url(
    url: str,
    cache_root: Path,
    *,
    client: httpx.Client | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    host_resolver: HostResolver | None = None,
) -> ResolvedAsset:
    own_client = client is None
    active_client = client or httpx.Client(timeout=httpx.Timeout(30.0), follow_redirects=False)
    current_url = url
    temporary_path: Path | None = None
    try:
        for _ in range(4):
            validate_public_url(current_url, host_resolver=host_resolver)
            with active_client.stream("GET", current_url) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise SourceResolutionError("Remote source returned an invalid redirect.")
                    current_url = urljoin(current_url, location)
                    continue
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > max_bytes:
                    raise SourceResolutionError(f"Download exceeds {max_bytes:,}-byte size limit.")

                filename = Path(urlsplit(current_url).path).name
                _validate_filename(filename)
                cache_root.mkdir(parents=True, exist_ok=True)
                hasher = hashlib.sha256()
                size = 0
                with tempfile.NamedTemporaryFile(delete=False, dir=cache_root) as temporary:
                    temporary_path = Path(temporary.name)
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > max_bytes:
                            raise SourceResolutionError(
                                f"Download exceeds {max_bytes:,}-byte size limit."
                            )
                        hasher.update(chunk)
                        temporary.write(chunk)

                digest = hasher.hexdigest()
                destination = _destination(cache_root, digest, filename)
                with temporary_path.open("rb") as downloaded:
                    _validate_signature(destination.suffix.lower(), downloaded.read(4))
                if destination.exists():
                    temporary_path.unlink()
                else:
                    os.replace(temporary_path, destination)
                temporary_path = None
                return ResolvedAsset(destination, "url", _safe_locator(url), digest, size)
        raise SourceResolutionError("Remote source exceeded redirect limit.")
    except httpx.HTTPError as error:
        raise SourceResolutionError(f"Remote dataset download failed: {error}") from error
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
        if own_client:
            active_client.close()


def _destination(cache_root: Path, digest: str, filename: str) -> Path:
    directory = cache_root / digest
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


def _validate_filename(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if not filename or suffix not in SUPPORTED_SUFFIXES:
        formats = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise SourceResolutionError(f"Unsupported dataset file. Expected one of: {formats}.")


def _validate_signature(suffix: str, prefix: bytes) -> None:
    if suffix == ".parquet" and prefix != b"PAR1":
        raise SourceResolutionError("File content is not valid Parquet data.")
    if suffix == ".xlsx" and prefix[:2] != b"PK":
        raise SourceResolutionError("File content is not valid XLSX data.")


def _resolve_host(hostname: str) -> Iterable[str]:
    return {entry[4][0] for entry in socket.getaddrinfo(hostname, None)}


def _safe_locator(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
