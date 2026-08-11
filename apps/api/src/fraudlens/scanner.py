import asyncio
import socket
import struct
from dataclasses import dataclass


@dataclass(frozen=True)
class ScanResult:
    status: str
    signature: str | None = None


class VirusScanner:
    def __init__(self, enabled: bool, required: bool, host: str, port: int) -> None:
        self.enabled = enabled
        self.required = required
        self.host = host
        self.port = port

    async def scan(self, data: bytes) -> ScanResult:
        if not self.enabled:
            return ScanResult("SKIPPED")
        try:
            return await asyncio.to_thread(self._scan_sync, data)
        except OSError:
            if self.required:
                raise RuntimeError("Malware scanner is unavailable") from None
            return ScanResult("UNAVAILABLE")

    def _scan_sync(self, data: bytes) -> ScanResult:
        with socket.create_connection((self.host, self.port), timeout=15) as connection:
            connection.sendall(b"zINSTREAM\0")
            for start in range(0, len(data), 65_536):
                chunk = data[start : start + 65_536]
                connection.sendall(struct.pack("!I", len(chunk)))
                connection.sendall(chunk)
            connection.sendall(struct.pack("!I", 0))
            response = connection.recv(4096).decode("utf-8", errors="replace").strip("\0\n")
        if response.endswith("OK"):
            return ScanResult("CLEAN")
        if "FOUND" in response:
            signature = response.rsplit(":", 1)[-1].replace("FOUND", "").strip()
            return ScanResult("INFECTED", signature)
        raise RuntimeError(f"Unexpected malware scanner response: {response}")
