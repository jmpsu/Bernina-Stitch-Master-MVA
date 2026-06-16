

===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/scripts/build_wheels.py =====

from __future__ import annotations

"""Build Python wheels for PyPI distribution from pre-built agentsview binaries.

Takes release archives (tar.gz/zip) and packages them into platform-specific
Python wheels that can be uploaded to PyPI.
"""

import argparse
import base64
import hashlib
import io
import os
import re
import stat
import sys
import tarfile
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Platform constants
# ---------------------------------------------------------------------------

PLATFORM_MAP: dict[str, dict[str, str]] = {
    "linux_amd64": {
        "wheel_tag": "manylinux_2_28_x86_64",
        "binary_name": "agentsview",
    },
    "linux_arm64": {
        "wheel_tag": "manylinux_2_28_aarch64",
        "binary_name": "agentsview",
    },
    "darwin_amd64": {
        "wheel_tag": "macosx_11_0_x86_64",
        "binary_name": "agentsview",
    },
    "darwin_arm64": {
        "wheel_tag": "macosx_11_0_arm64",
        "binary_name": "agentsview",
    },
    "windows_amd64": {
        "wheel_tag": "win_amd64",
        "binary_name": "agentsview.exe",
    },
    "windows_arm64": {
        "wheel_tag": "win_arm64",
        "binary_name": "agentsview.exe",
    },
}

_ARCHIVE_RE = re.compile(
    r"^agentsview_(?P<version>[^_]+)_(?P<platform>[^.]+)\.(?:tar\.gz|zip)$"
)

# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------


def parse_archive_filename(filename: str) -> tuple[str, str] | None:
    """Parse a release archive filename into (platform_key, version).

    Recognizes filenames of the form:
        agentsview_<version>_<platform>.(tar.gz|zip)

    Returns None for unrecognized filenames or unknown platforms.
    """
    m = _ARCHIVE_RE.match(filename)
    if m is None:
        return None
    platform_key = m.group("platform")
    if platform_key not in PLATFORM_MAP:
        return None
    return (platform_key, m.group("version"))


# ---------------------------------------------------------------------------
# Archive extraction
# ---------------------------------------------------------------------------


def extract_binary(archive_path: Path, binary_name: str) -> bytes:
    """Extract a named binary from a .tar.gz or .zip archive.

    Searches for an entry whose basename matches binary_name (handles
    nested paths inside the archive).

    Raises FileNotFoundError if the binary is not found.
    """
    suffix = archive_path.name
    if suffix.endswith(".tar.gz"):
        return _extract_from_targz(archive_path, binary_name)
    if suffix.endswith(".zip"):
        return _extract_from_zip(archive_path, binary_name)
    raise ValueError(f"Unsupported archive format: {archive_path}")


def _extract_from_targz(archive_path: Path, binary_name: str) -> bytes:
    with tarfile.open(archive_path, "r:gz") as tf:
        for member in tf.getmembers():
            if os.path.basename(member.name) == binary_name:
                f = tf.extractfile(member)
                if f is not None:
                    return f.read()
    raise FileNotFoundError(
        f"Binary '{binary_name}' not found in {archive_path}"
    )


def _extract_from_zip(archive_path: Path, binary_name: str) -> bytes:
    with zipfile.ZipFile(archive_path) as zf:
        for name in zf.namelist():
            if os.path.basename(name) == binary_name:
                return zf.read(name)
    raise FileNotFoundError(
        f"Binary '{binary_name}' not found in {archive_path}"
    )


# ---------------------------------------------------------------------------
# Wheel assembly
# ---------------------------------------------------------------------------

_INIT_PY_UNIX = """\
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path


def main() -> None:
    bin_path = str(Path(__file__).parent / "bin" / "agentsview")
    mode = os.stat(bin_path).st_mode
    if not (mode & stat.S_IXUSR):
        os.chmod(bin_path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    os.execvp(bin_path, [bin_path] + sys.argv[1:])
"""

_INIT_PY_WINDOWS = """\
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    bin_path = Path(__file__).parent / "bin" / "agentsview.exe"
    sys.exit(subprocess.call([str(bin_path)] + sys.argv[1:]))
"""

_MAIN_PY = """\
from agentsview import main

main()
"""


def _sha256_record_hash(data: bytes) -> str:
    """Return a url-safe base64 sha256 hash in RECORD format."""
    digest = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def build_wheel(
    binary_content: bytes,
    output_dir: Path,
    version: str,
    platform_key: str,
    readme: str | None = None,
) -> Path:
    """Build a Python wheel containing the agentsview binary.

    Args:
        binary_content: Raw bytes of the platform binary.
        output_dir: Directory where the wheel file will be written.
        version: Package version string (e.g. "0.15.0").


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/scripts/build_wheels_test.py =====

from __future__ import annotations

import io
import os
import stat
import tarfile
import zipfile
from pathlib import Path

import pytest

from build_wheels import (
    PLATFORM_MAP,
    build_all_wheels,
    build_wheel,
    extract_binary,
    parse_archive_filename,
)


# ---------------------------------------------------------------------------
# Platform mapping
# ---------------------------------------------------------------------------


class TestPlatformMap:
    def test_all_required_platforms_present(self) -> None:
        required = {
            "linux_amd64",
            "linux_arm64",
            "darwin_amd64",
            "darwin_arm64",
            "windows_amd64",
            "windows_arm64",
        }
        assert set(PLATFORM_MAP.keys()) == required

    def test_each_entry_has_wheel_tag(self) -> None:
        for key, entry in PLATFORM_MAP.items():
            assert "wheel_tag" in entry, f"{key} missing wheel_tag"
            assert isinstance(entry["wheel_tag"], str)
            assert entry["wheel_tag"]

    def test_each_entry_has_binary_name(self) -> None:
        for key, entry in PLATFORM_MAP.items():
            assert "binary_name" in entry, f"{key} missing binary_name"
            assert isinstance(entry["binary_name"], str)
            assert entry["binary_name"]

    def test_windows_binary_has_exe_extension(self) -> None:
        assert PLATFORM_MAP["windows_amd64"]["binary_name"] == "agentsview.exe"
        assert PLATFORM_MAP["windows_arm64"]["binary_name"] == "agentsview.exe"

    def test_unix_binaries_have_no_extension(self) -> None:
        for key in ("linux_amd64", "linux_arm64", "darwin_amd64", "darwin_arm64"):
            assert PLATFORM_MAP[key]["binary_name"] == "agentsview"

    def test_manylinux_wheel_tags(self) -> None:
        assert PLATFORM_MAP["linux_amd64"]["wheel_tag"] == "manylinux_2_28_x86_64"
        assert PLATFORM_MAP["linux_arm64"]["wheel_tag"] == "manylinux_2_28_aarch64"

    def test_macos_wheel_tags(self) -> None:
        assert PLATFORM_MAP["darwin_amd64"]["wheel_tag"] == "macosx_11_0_x86_64"
        assert PLATFORM_MAP["darwin_arm64"]["wheel_tag"] == "macosx_11_0_arm64"

    def test_windows_wheel_tag(self) -> None:
        assert PLATFORM_MAP["windows_amd64"]["wheel_tag"] == "win_amd64"
        assert PLATFORM_MAP["windows_arm64"]["wheel_tag"] == "win_arm64"


# ---------------------------------------------------------------------------
# Archive filename parsing
# ---------------------------------------------------------------------------


class TestParseArchiveFilename:
    def test_parse_linux_amd64_tar_gz(self) -> None:
        result = parse_archive_filename("agentsview_0.15.0_linux_amd64.tar.gz")
        assert result == ("linux_amd64", "0.15.0")

    def test_parse_darwin_arm64_tar_gz(self) -> None:
        result = parse_archive_filename("agentsview_1.2.3_darwin_arm64.tar.gz")
        assert result == ("darwin_arm64", "1.2.3")

    def test_parse_windows_amd64_zip(self) -> None:
        result = parse_archive_filename("agentsview_0.15.0_windows_amd64.zip")
        assert result == ("windows_amd64", "0.15.0")

    def test_parse_windows_arm64_zip(self) -> None:
        result = parse_archive_filename("agentsview_0.15.0_windows_arm64.zip")
        assert result == ("windows_arm64", "0.15.0")

    def test_parse_darwin_amd64_tar_gz(self) -> None:
        result = parse_archive_filename("agentsview_2.0.0_darwin_amd64.tar.gz")
        assert result == ("darwin_amd64", "2.0.0")

    def test_unrecognized_filename_returns_none(self) -> None:
        assert parse_archive_filename("somethingelse_0.1.0_linux_amd64.tar.gz") is None

    def test_unknown_platform_returns_none(self) -> None:
        assert parse_archive_filename("agentsview_0.1.0_freebsd_amd64.tar.gz") is None

    def test_no_extension_returns_none(self) -> None:
        assert parse_archive_filename("agentsview_0.1.0_linux_amd64") is None

    def test_sha256sums_returns_none(self) -> None:
        assert parse_archive_filename("agentsview_0.15.0_SHA256SUMS") is None

    def test_path_with_directory_uses_basename(self) -> None:
        result = parse_archive_filename(
            "releases/agentsview_0.15.0_linux_arm64.tar.gz"
        )
        # parse_archive_filename only accepts basenames, so paths return None
        assert result is None

        # The caller is responsible for passing just the filename
        result = parse_archive_filename("agentsview_0.15.0_linux_arm64.tar.gz")
        assert result == ("linux_arm64", "0.15.0")


# ---------------------------------------------------------------------------
# Archive extraction
# ---------------------------------------------------------------------------


def _make_targz(binary_name: str, content: bytes) -> bytes:
    """Create an in-memory .tar.gz with a single binary file."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo(name=binary_name)
        info.size = len(content)
        tf.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def _make_zip(binary_name: str, content: bytes) -> bytes:
    """Create an in-memory .zip with a single binary file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(binary_name, content)
    return buf.getvalue()


class TestExtractBinary:
    def test_extract_from_tar_gz(self, tmp_path: Path) -> None:
        content = b"fake-binary-content"
        archive = tmp_path / "agentsview_0.15.0_linux_amd64.tar.gz"
        archive.write_bytes(_make_targz("agentsview", content))
        result = extract_binary(archive, "agentsview")
        assert result == content

    def test_extract_from_zip(self, tmp_path: Path) -> None:
        content = b"fake-binary-exe"
        archive = tmp_path / "agentsview_0.15.0_windows_amd64.zip"
        archive.write_bytes(_make_zip("agentsview.exe", content))
        result = extract_binary(archive, "agentsview.exe")
        assert result == content

    def test_missing_binary_raises_file_not_found(self, tmp_path: Path) -> None:
        archive = tmp_path / "agentsview_0.15.0_linux_amd64.tar.gz"
        archive.write_bytes(_make_targz("wrong_name", b"data"))
        with pytest.raises(FileNotFoundError, match="agentsview"):
            extract_binary(archive, "agentsview")

    def test_missing_binary_in_zip_raises_file_not_found(self, tmp_path: Path) -> None:
        archive = tmp_path / "agentsview_0.15.0_windows_amd64.zip"
        archive.write_bytes(_make_zip("wrong.exe", b"data"))
        with pytest.raises(FileNotFoundError, match="agentsview.exe"):
            extract_binary(archive, "agentsview.exe")

    def test_nested_path_in_tar_gz(self, tmp_path: Path) -> None:
        """Binary may be inside a subdirectory in the archive."""
        content = b"nested-binary"
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            info = tarfile.TarInfo(name="agentsview_0.15.0_linux_amd64/agentsview")
            info.size = len(content)
            tf.addfile(info, io.BytesIO(content))
        archive = tmp_path / "agentsview_0.15.0_linux_amd64.tar.gz"
        archive.write_bytes(buf.getvalue())


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/cmd/agentsview/testdata/stats_golden.json =====

{
  "adoption": {
    "claude_only": true,
    "distinct_skills": 1,
    "plan_mode_rate": 0.1111111111111111,
    "subagents_per_session": 0.2222222222222222
  },
  "agent_portfolio": {
    "by_messages": {
      "claude": 322,
      "codex": 20,
      "cursor": 6
    },
    "by_messages_human": {
      "claude": 322,
      "codex": 20,
      "cursor": 6
    },
    "by_sessions": {
      "claude": 9,
      "codex": 1,
      "cursor": 1
    },
    "by_sessions_human": {
      "claude": 9,
      "codex": 1,
      "cursor": 1
    },
    "by_tokens": {
      "claude": 151420
    },
    "by_tokens_human": {
      "claude": 151420
    },
    "primary": "claude",
    "primary_human": "claude"
  },
  "archetypes": {
    "automation": 0,
    "deep": 2,
    "marathon": 1,
    "primary": "quick",
    "primary_human": "quick",
    "quick": 5,
    "standard": 3
  },
  "cache_economics": {
    "cache_hit_ratio": {
      "buckets": [
        {
          "count": 0,
          "edge": [
            0,
            0.25
          ]
        },
        {
          "count": 0,
          "edge": [
            0.25,
            0.5
          ]
        },
        {
          "count": 9,
          "edge": [
            0.5,
            0.75
          ]
        },
        {
          "count": 0,
          "edge": [
            0.75,
            0.95
          ]
        },
        {
          "count": 0,
          "edge": [
            0.95,
            1
          ]
        }
      ],
      "overall": 0.5793498147018812
    },
    "claude_only": true,
    "dollars_saved_vs_uncached": 2.373315,
    "dollars_spent": 6.751545
  },
  "distributions": {
    "duration_minutes": {
      "scope_all": {
        "buckets": [
          {
            "count": 0,
            "edge": [
              0,
              1
            ]
          },
          {
            "count": 1,
            "edge": [
              1,
              5
            ]
          },
          {
            "count": 3,
            "edge": [
              5,
              20
            ]
          },
          {
            "count": 4,
            "edge": [
              20,
              60
            ]
          },
          {
            "count": 0,
            "edge": [
              60,
              120
            ]
          },
          {
            "count": 3,
            "edge": [
              120,
              null
            ]
          }
        ],
        "mean": 60.36363636363637
      },
      "scope_human": {
        "buckets": [
          {
            "count": 0,
            "edge": [
              0,
              1
            ]
          },
          {
            "count": 1,
            "edge": [
              1,
              5
            ]
          },
          {
            "count": 3,
            "edge": [
              5,
              20
            ]
          },
          {
            "count": 4,
            "edge": [
              20,
              60
            ]
          },
          {
            "count": 0,
            "edge": [
              60,
              120
            ]
          },
          {
            "count": 3,
            "edge": [


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/desktop/package-lock.json =====

{
  "name": "agentsview-desktop",
  "version": "0.1.0",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "": {
      "name": "agentsview-desktop",
      "version": "0.1.0",
      "devDependencies": {
        "@tauri-apps/cli": "^2"
      }
    },
    "node_modules/@tauri-apps/cli": {
      "version": "2.11.2",
      "resolved": "https://registry.npmjs.org/@tauri-apps/cli/-/cli-2.11.2.tgz",
      "integrity": "sha512-bk3HemqvGRoy+5D/dVMUQHKMYLglD0jVnMm/0iGMH6ufZ+p8r14m6BpIixwij3PBvZdvORUp1YifTD8QxVZ1Nw==",
      "dev": true,
      "license": "Apache-2.0 OR MIT",
      "bin": {
        "tauri": "tauri.js"
      },
      "engines": {
        "node": ">= 10"
      },
      "funding": {
        "type": "opencollective",
        "url": "https://opencollective.com/tauri"
      },
      "optionalDependencies": {
        "@tauri-apps/cli-darwin-arm64": "2.11.2",
        "@tauri-apps/cli-darwin-x64": "2.11.2",
        "@tauri-apps/cli-linux-arm-gnueabihf": "2.11.2",
        "@tauri-apps/cli-linux-arm64-gnu": "2.11.2",
        "@tauri-apps/cli-linux-arm64-musl": "2.11.2",
        "@tauri-apps/cli-linux-riscv64-gnu": "2.11.2",
        "@tauri-apps/cli-linux-x64-gnu": "2.11.2",
        "@tauri-apps/cli-linux-x64-musl": "2.11.2",
        "@tauri-apps/cli-win32-arm64-msvc": "2.11.2",
        "@tauri-apps/cli-win32-ia32-msvc": "2.11.2",
        "@tauri-apps/cli-win32-x64-msvc": "2.11.2"
      }
    },
    "node_modules/@tauri-apps/cli-darwin-arm64": {
      "version": "2.11.2",
      "resolved": "https://registry.npmjs.org/@tauri-apps/cli-darwin-arm64/-/cli-darwin-arm64-2.11.2.tgz",
      "integrity": "sha512-+4UZzLt+eOAEQCwgd+TqKgyUJMrvx+BgdXLLaqJYmPqzP+nE6YZr/hY6CWLYGQb8jFn99jEkmC6uA3tNvamA1w==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "license": "Apache-2.0 OR MIT",
      "optional": true,
      "os": [
        "darwin"
      ],
      "engines": {
        "node": ">= 10"
      }
    },
    "node_modules/@tauri-apps/cli-darwin-x64": {
      "version": "2.11.2",
      "resolved": "https://registry.npmjs.org/@tauri-apps/cli-darwin-x64/-/cli-darwin-x64-2.11.2.tgz",
      "integrity": "sha512-VjYYtZUPqDMLutSfJEyxFE3Bz+DPi7c8wC3imckgvciLDZLq4qwKJxBicg0BXGhXjJsl8vKWgWRFNMPELQ+Xyg==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "license": "Apache-2.0 OR MIT",
      "optional": true,
      "os": [
        "darwin"
      ],
      "engines": {
        "node": ">= 10"
      }
    },
    "node_modules/@tauri-apps/cli-linux-arm-gnueabihf": {
      "version": "2.11.2",
      "resolved": "https://registry.npmjs.org/@tauri-apps/cli-linux-arm-gnueabihf/-/cli-linux-arm-gnueabihf-2.11.2.tgz",
      "integrity": "sha512-yMemD6f4i95AQriS8EazyOFzbE34yjnP16i3IOzpHGQvBoy2DjypFMFBq0NtPuITURv/cOGguRtHR5d79/9CSA==",
      "cpu": [
        "arm"
      ],
      "dev": true,
      "license": "Apache-2.0 OR MIT",
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">= 10"
      }
    },
    "node_modules/@tauri-apps/cli-linux-arm64-gnu": {
      "version": "2.11.2",
      "resolved": "https://registry.npmjs.org/@tauri-apps/cli-linux-arm64-gnu/-/cli-linux-arm64-gnu-2.11.2.tgz",
      "integrity": "sha512-cgI91D2wL8GSgoWwZXDqt+DwnuZCP2/bz03QAE4TrhgAKIsrB4hX26W/H1EONPUUNkqrsgeCD0wU6pcNjV/5kw==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "libc": [
        "glibc"
      ],
      "license": "Apache-2.0 OR MIT",
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">= 10"
      }
    },
    "node_modules/@tauri-apps/cli-linux-arm64-musl": {
      "version": "2.11.2",
      "resolved": "https://registry.npmjs.org/@tauri-apps/cli-linux-arm64-musl/-/cli-linux-arm64-musl-2.11.2.tgz",
      "integrity": "sha512-X1rm0BERqAAggtYTESSgXrS3sz4Sb/OiPiz54UqISlXW+GkR3vNIGnsy/lejNmoXGVqri3Q53BCfQiclOIyRPw==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "libc": [
        "musl"
      ],
      "license": "Apache-2.0 OR MIT",
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">= 10"
      }
    },
    "node_modules/@tauri-apps/cli-linux-riscv64-gnu": {
      "version": "2.11.2",
      "resolved": "https://registry.npmjs.org/@tauri-apps/cli-linux-riscv64-gnu/-/cli-linux-riscv64-gnu-2.11.2.tgz",
      "integrity": "sha512-usbMLJbT3KtkOrBMDVeGYNM35aTHXx38SJSzTMSqqjeUIOQ+iVPjb2yAGNAE+KqmBbAx4FOFIyMeKXx2M/JKGQ==",
      "cpu": [
        "riscv64"
      ],
      "dev": true,
      "libc": [
        "glibc"
      ],
      "license": "Apache-2.0 OR MIT",
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">= 10"
      }
    },
    "node_modules/@tauri-apps/cli-linux-x64-gnu": {
      "version": "2.11.2",
      "resolved": "https://registry.npmjs.org/@tauri-apps/cli-linux-x64-gnu/-/cli-linux-x64-gnu-2.11.2.tgz",
      "integrity": "sha512-Ru4gwJKPG0ctVGchRGpRup4Y4lW2SSfFnrbQcyHhCliKy4g8Qz97TrUgCur4CbWyAgKxvGh3SjrkA0LDYzDGiw==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "libc": [
        "glibc"
      ],
      "license": "Apache-2.0 OR MIT",
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">= 10"
      }
    },
    "node_modules/@tauri-apps/cli-linux-x64-musl": {
      "version": "2.11.2",
      "resolved": "https://registry.npmjs.org/@tauri-apps/cli-linux-x64-musl/-/cli-linux-x64-musl-2.11.2.tgz",
      "integrity": "sha512-eUm7T6clN1MMmNSRQ9gaWsQdyehQx2Gmn5hht/QUlqZQI/qcP2OJK5dnaxqwFzCr2HdsEo9ydxaqcS1oJzMvUw==",
      "cpu": [
        "x64"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/desktop/package.json =====

{
  "name": "agentsview-desktop",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "prepare-sidecar": "bash ./scripts/prepare-sidecar.sh",
    "tauri:dev": "npm run prepare-sidecar && bash ./scripts/run-tauri.sh dev",
    "tauri:build": "npm run prepare-sidecar && bash ./scripts/run-tauri.sh build",
    "tauri:build:macos-app": "npm run prepare-sidecar && bash ./scripts/run-tauri.sh build --bundles app",
    "tauri:build:macos-dmg": "npm run prepare-sidecar && bash ./scripts/run-tauri.sh build --bundles dmg",
    "tauri:build:windows": "npm run prepare-sidecar && bash ./scripts/run-tauri.sh build --bundles nsis",
    "tauri:build:linux": "npm run prepare-sidecar && bash ./scripts/run-tauri.sh build --bundles appimage",
    "tauri": "tauri"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^2"
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/desktop/src-tauri/capabilities/default.json =====

{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default"
  ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/desktop/src-tauri/tauri.conf.json =====

{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "AgentsView",
  "version": "0.12.1",
  "identifier": "io.agentsview.desktop",
  "build": {
    "frontendDist": "../ui"
  },
  "app": {
    "windows": [
      {
        "label": "main",
        "title": "AgentsView",
        "width": 1440,
        "height": 900,
        "minWidth": 1024,
        "minHeight": 700,
        "resizable": true,
        "fullscreen": false
      }
    ],
    "security": {
      "csp": "default-src 'self' http://127.0.0.1:* http://localhost:*; script-src 'self' http://127.0.0.1:* http://localhost:*; connect-src 'self' http: https: ws: wss:; img-src 'self' data: http://127.0.0.1:* http://localhost:*; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com http://127.0.0.1:* http://localhost:*; font-src 'self' data: https://fonts.gstatic.com http://127.0.0.1:* http://localhost:*; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "copyright": "Copyright 2026 Kenn Software LLC",
    "shortDescription": "Local viewer for AI agent sessions",
    "longDescription": "AgentsView is a local web viewer for AI agent coding sessions.",
    "createUpdaterArtifacts": "v1Compatible",
    "externalBin": [
      "binaries/agentsview"
    ],
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "macOS": {
      "entitlements": "./Entitlements.plist",
      "minimumSystemVersion": "11.0"
    }
  },
  "plugins": {
    "updater": {
      "pubkey": "NOT_SET",
      "endpoints": [
        "https://github.com/wesm/agentsview/releases/download/updater/latest.json"
      ]
    }
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/frontend/package-lock.json =====

{
  "name": "agentsview-frontend",
  "version": "0.1.0",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "": {
      "name": "agentsview-frontend",
      "version": "0.1.0",
      "dependencies": {
        "@lucide/svelte": "1.17.0",
        "@tanstack/virtual-core": "3.17.0",
        "dompurify": "3.4.8",
        "marked": "18.0.5",
        "shiki": "4.2.0"
      },
      "devDependencies": {
        "@playwright/test": "1.60.0",
        "@sveltejs/vite-plugin-svelte": "7.1.2",
        "@testing-library/svelte": "^5.3.1",
        "@tsconfig/svelte": "5.0.8",
        "jsdom": "29.1.1",
        "openapi-typescript-codegen": "^0.30.0",
        "svelte": "5.56.1",
        "svelte-check": "4.6.0",
        "typescript": "6.0.3",
        "vite": "npm:@voidzero-dev/vite-plus-core@0.1.24",
        "vite-plus": "0.1.24",
        "vitest": "npm:@voidzero-dev/vite-plus-test@0.1.24"
      },
      "engines": {
        "node": "^20.19 || ^22.12 || >=24"
      }
    },
    "node_modules/@apidevtools/json-schema-ref-parser": {
      "version": "14.2.1",
      "resolved": "https://registry.npmjs.org/@apidevtools/json-schema-ref-parser/-/json-schema-ref-parser-14.2.1.tgz",
      "integrity": "sha512-HmdFw9CDYqM6B25pqGBpNeLCKvGPlIx1EbLrVL0zPvj50CJQUHyBNBw45Muk0kEIkogo1VZvOKHajdMuAzSxRg==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "js-yaml": "^4.1.0"
      },
      "engines": {
        "node": ">= 20"
      },
      "funding": {
        "url": "https://github.com/sponsors/philsturgeon"
      },
      "peerDependencies": {
        "@types/json-schema": "^7.0.15"
      }
    },
    "node_modules/@asamuzakjp/css-color": {
      "version": "5.1.11",
      "resolved": "https://registry.npmjs.org/@asamuzakjp/css-color/-/css-color-5.1.11.tgz",
      "integrity": "sha512-KVw6qIiCTUQhByfTd78h2yD1/00waTmm9uy/R7Ck/ctUyAPj+AEDLkQIdJW0T8+qGgj3j5bpNKK7Q3G+LedJWg==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@asamuzakjp/generational-cache": "^1.0.1",
        "@csstools/css-calc": "^3.2.0",
        "@csstools/css-color-parser": "^4.1.0",
        "@csstools/css-parser-algorithms": "^4.0.0",
        "@csstools/css-tokenizer": "^4.0.0"
      },
      "engines": {
        "node": "^20.19.0 || ^22.12.0 || >=24.0.0"
      }
    },
    "node_modules/@asamuzakjp/dom-selector": {
      "version": "7.1.1",
      "resolved": "https://registry.npmjs.org/@asamuzakjp/dom-selector/-/dom-selector-7.1.1.tgz",
      "integrity": "sha512-67RZDnYRc8H/8MLDgQCDE//zoqVFwajkepHZgmXrbwybzXOEwOWGPYGmALYl9J2DOLfFPPs6kKCqmbzV895hTQ==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@asamuzakjp/generational-cache": "^1.0.1",
        "@asamuzakjp/nwsapi": "^2.3.9",
        "bidi-js": "^1.0.3",
        "css-tree": "^3.2.1",
        "is-potential-custom-element-name": "^1.0.1"
      },
      "engines": {
        "node": "^20.19.0 || ^22.12.0 || >=24.0.0"
      }
    },
    "node_modules/@asamuzakjp/generational-cache": {
      "version": "1.0.1",
      "resolved": "https://registry.npmjs.org/@asamuzakjp/generational-cache/-/generational-cache-1.0.1.tgz",
      "integrity": "sha512-wajfB8KqzMCN2KGNFdLkReeHncd0AslUSrvHVvvYWuU8ghncRJoA50kT3zP9MVL0+9g4/67H+cdvBskj9THPzg==",
      "dev": true,
      "license": "MIT",
      "engines": {
        "node": "^20.19.0 || ^22.12.0 || >=24.0.0"
      }
    },
    "node_modules/@asamuzakjp/nwsapi": {
      "version": "2.3.9",
      "resolved": "https://registry.npmjs.org/@asamuzakjp/nwsapi/-/nwsapi-2.3.9.tgz",
      "integrity": "sha512-n8GuYSrI9bF7FFZ/SjhwevlHc8xaVlb/7HmHelnc/PZXBD2ZR49NnN9sMMuDdEGPeeRQ5d0hqlSlEpgCX3Wl0Q==",
      "dev": true,
      "license": "MIT"
    },
    "node_modules/@babel/code-frame": {
      "version": "7.29.7",
      "resolved": "https://registry.npmjs.org/@babel/code-frame/-/code-frame-7.29.7.tgz",
      "integrity": "sha512-Aup7aUOfpbAUg2ROOJN6Iw5f9DMBlzu0mIkm/malLQFN/YQgO48wCj0Kxa3sEHJvPVFg7siR+qRInwXd2qhQKw==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "@babel/helper-validator-identifier": "^7.29.7",
        "js-tokens": "^4.0.0",
        "picocolors": "^1.1.1"
      },
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@babel/helper-validator-identifier": {
      "version": "7.29.7",
      "resolved": "https://registry.npmjs.org/@babel/helper-validator-identifier/-/helper-validator-identifier-7.29.7.tgz",
      "integrity": "sha512-qehxGkRj55h/ff8EMaJ+cYhyaKlHIxqYDn682wQD7RNp9UujOQsHog2uS0r2vzr4pW+sXf90NeeayjcNaX3fFg==",
      "dev": true,
      "license": "MIT",
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@babel/runtime": {
      "version": "7.29.7",
      "resolved": "https://registry.npmjs.org/@babel/runtime/-/runtime-7.29.7.tgz",
      "integrity": "sha512-Nq8OhGWiZIZGV6hLHoyAKLLcJihP/xFeBMGJoUrxTX2psI8dCifzLhZISFb+VWS3wFMRDmCGw5R+dOySCqPLhw==",
      "dev": true,
      "license": "MIT",
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@bramus/specificity": {
      "version": "2.4.2",
      "resolved": "https://registry.npmjs.org/@bramus/specificity/-/specificity-2.4.2.tgz",
      "integrity": "sha512-ctxtJ/eA+t+6q2++vj5j7FYX3nRu311q1wfYH3xjlLOsczhlhxAg2FWNUXhpGvAw3BWo1xBcvOV6/YLc2r5FJw==",
      "dev": true,
      "license": "MIT",
      "dependencies": {
        "css-tree": "^3.0.0"
      },
      "bin": {
        "specificity": "bin/cli.js"
      }
    },
    "node_modules/@csstools/color-helpers": {
      "version": "6.0.2",
      "resolved": "https://registry.npmjs.org/@csstools/color-helpers/-/color-helpers-6.0.2.tgz",
      "integrity": "sha512-LMGQLS9EuADloEFkcTBR3BwV/CGHV7zyDxVRtVDTwdI2Ca4it0CCVTT9wCkxSgokjE5Ho41hEPgb8OEUwoXr6Q==",
      "dev": true,
      "funding": [
        {
          "type": "github",
          "url": "https://github.com/sponsors/csstools"
        },
        {
          "type": "opencollective",
          "url": "https://opencollective.com/csstools"
        }
      ],
      "license": "MIT-0",
      "engines": {
        "node": ">=20.19.0"
      }
    },
    "node_modules/@csstools/css-calc": {
      "version": "3.2.0",
      "resolved": "https://registry.npmjs.org/@csstools/css-calc/-/css-calc-3.2.0.tgz",
      "integrity": "sha512-bR9e6o2BDB12jzN/gIbjHa5wLJ4UjD1CB9pM7ehlc0ddk6EBz+yYS1EV2MF55/HUxrHcB/hehAyt5vhsA3hx7w==",
      "dev": true,
      "funding": [
        {
          "type": "github",


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/frontend/package.json =====

{
  "name": "agentsview-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "engines": {
    "node": "^20.19 || ^22.12 || >=24"
  },
  "scripts": {
    "dev": "vp dev",
    "build": "vp build",
    "generate:api": "node scripts/generate-api-client.mjs",
    "preview": "vp preview",
    "check": "svelte-check --tsconfig ./tsconfig.json",
    "test": "vp test run",
    "e2e": "playwright test"
  },
  "dependencies": {
    "@lucide/svelte": "1.17.0",
    "@tanstack/virtual-core": "3.17.0",
    "dompurify": "3.4.8",
    "marked": "18.0.5",
    "shiki": "4.2.0"
  },
  "devDependencies": {
    "@playwright/test": "1.60.0",
    "@sveltejs/vite-plugin-svelte": "7.1.2",
    "@testing-library/svelte": "^5.3.1",
    "@tsconfig/svelte": "5.0.8",
    "jsdom": "29.1.1",
    "openapi-typescript-codegen": "^0.30.0",
    "svelte": "5.56.1",
    "svelte-check": "4.6.0",
    "typescript": "6.0.3",
    "vite": "npm:@voidzero-dev/vite-plus-core@0.1.24",
    "vitest": "npm:@voidzero-dev/vite-plus-test@0.1.24",
    "vite-plus": "0.1.24"
  },
  "overrides": {
    "vite": "npm:@voidzero-dev/vite-plus-core@0.1.24",
    "vitest": "npm:@voidzero-dev/vite-plus-test@0.1.24"
  }
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/frontend/tsconfig.json =====

{
  "extends": "@tsconfig/svelte/tsconfig.json",
  "compilerOptions": {
    "target": "ESNext",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "resolveJsonModule": true,
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true
  },
  "include": ["src/**/*.ts", "src/**/*.svelte"]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/internal/parser/testdata/gemini/standard_session.json =====

{
  "lastUpdated": "2024-01-01T10:05:05Z",
  "messages": [
    {
      "content": "Fix the login bug",
      "id": "u1",
      "timestamp": "2024-01-01T10:00:00Z",
      "type": "user"
    },
    {
      "content": "Looking at the auth module...",
      "id": "a1",
      "timestamp": "2024-01-01T10:00:05Z",
      "tokens": {
        "input": 1500,
        "output": 200,
        "cached": 100,
        "thoughts": 50,
        "tool": 0,
        "total": 1850
      },
      "type": "gemini"
    },
    {
      "content": "That looks right",
      "id": "u2",
      "timestamp": "2024-01-01T10:05:00Z",
      "type": "user"
    },
    {
      "content": "Applied the fix.",
      "id": "a2",
      "timestamp": "2024-01-01T10:05:05Z",
      "tokens": {
        "input": 2000,
        "output": 300,
        "cached": 50,
        "thoughts": 100,
        "tool": 0,
        "total": 2450
      },
      "type": "gemini"
    }
  ],
  "projectHash": "abc123def456",
  "sessionId": "sess-uuid-1",
  "startTime": "2024-01-01T10:00:00Z"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/internal/parser/testdata/gemini/system_messages.json =====

{
  "lastUpdated": "2024-01-01T10:00:05Z",
  "messages": [
    {
      "content": "Starting session",
      "id": "i1",
      "timestamp": "2024-01-01T10:00:00Z",
      "type": "info"
    },
    {
      "content": "Some error",
      "id": "e1",
      "timestamp": "2024-01-01T10:00:01Z",
      "type": "error"
    },
    {
      "content": "Some warning",
      "id": "w1",
      "timestamp": "2024-01-01T10:00:05Z",
      "type": "warning"
    }
  ],
  "projectHash": "abc123def456",
  "sessionId": "sess-uuid-3",
  "startTime": "2024-01-01T10:00:00Z"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/internal/parser/testdata/gemini/thinking_only.json =====

{
  "lastUpdated": "2024-01-01T10:00:05Z",
  "messages": [
    {
      "content": "Explain how this works",
      "id": "u1",
      "timestamp": "2024-01-01T10:00:00Z",
      "type": "user"
    },
    {
      "content": "Here is how it works: the system reads the config file on startup.",
      "id": "a1",
      "model": "gemini-2.5-pro",
      "thoughts": [
        {
          "description": "The user wants an explanation of the system.",
          "subject": "Understanding request",
          "timestamp": "2024-01-01T10:00:01Z"
        },
        {
          "description": "I should describe the config loading flow.",
          "subject": "Planning response",
          "timestamp": "2024-01-01T10:00:02Z"
        }
      ],
      "timestamp": "2024-01-01T10:00:05Z",
      "type": "gemini"
    }
  ],
  "projectHash": "abc123def456",
  "sessionId": "sess-uuid-thinking",
  "startTime": "2024-01-01T10:00:00Z"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/internal/parser/testdata/gemini/tool_calls.json =====

{
  "lastUpdated": "2024-01-01T10:00:05Z",
  "messages": [
    {
      "content": "Read this file",
      "id": "u1",
      "timestamp": "2024-01-01T10:00:00Z",
      "type": "user"
    },
    {
      "content": "Let me read it.",
      "id": "a1",
      "model": "gemini-2.5-pro",
      "thoughts": [
        {
          "description": "I need to read the file first.",
          "subject": "Planning",
          "timestamp": "2024-01-01T10:00:01Z"
        }
      ],
      "timestamp": "2024-01-01T10:00:05Z",
      "toolCalls": [
        {
          "args": {
            "file_path": "main.go"
          },
          "displayName": "ReadFile",
          "name": "read_file",
          "status": "success"
        }
      ],
      "type": "gemini"
    }
  ],
  "projectHash": "abc123def456",
  "sessionId": "sess-uuid-2",
  "startTime": "2024-01-01T10:00:00Z"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/internal/parser/testdata/gemini/tool_calls_with_results.json =====

{
  "lastUpdated": "2024-01-01T10:00:05Z",
  "messages": [
    {
      "content": "Read the planning doc",
      "id": "u1",
      "timestamp": "2024-01-01T10:00:00Z",
      "type": "user"
    },
    {
      "content": "Let me read that file.",
      "id": "a1",
      "model": "gemini-2.5-pro",
      "thoughts": [
        {
          "description": "I need to read the planning document.",
          "subject": "Planning",
          "timestamp": "2024-01-01T10:00:01Z"
        }
      ],
      "timestamp": "2024-01-01T10:00:05Z",
      "toolCalls": [
        {
          "id": "read_file_1772747340739_0",
          "name": "read_file",
          "displayName": "ReadFile",
          "args": {"file_path":".planning/ONE-PAGER.md"},
          "status": "success",
          "result": [
            {
              "functionResponse": {
                "id": "read_file_1772747340739_0",
                "name": "read_file",
                "response": {
                  "output": "# Agentstrove -- One-Pager\n\nDraft: 2026-03-04"
                }
              }
            }
          ]
        },
        {
          "id": "run_command_1772747340739_1",
          "name": "run_command",
          "displayName": "RunCommand",
          "args": {"command":"ls -la"},
          "status": "success",
          "result": [
            {
              "functionResponse": {
                "id": "run_command_1772747340739_1",
                "name": "run_command",
                "response": {
                  "output": "total 42\ndrwxr-xr-x  5 user user 160 Mar  4 10:00 ."
                }
              }
            }
          ]
        }
      ],
      "type": "gemini"
    }
  ],
  "projectHash": "abc123def456",
  "sessionId": "sess-uuid-tool-results",
  "startTime": "2024-01-01T10:00:00Z"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/internal/parser/testdata/kiro_sqlite/overlap_payload.json =====

{
  "conversation_id": "overlap-session",
  "history": [
    {
      "user": {
        "env_context": {
          "env_state": {
            "current_working_directory": "/home/user/code/current-kiro"
          }
        },
        "content": {
          "Prompt": {
            "prompt": "Current store should win"
          }
        },
        "timestamp": "2026-05-17T11:00:00Z"
      },
      "assistant": {
        "Response": {
          "message_id": "assistant-overlap",
          "content": "Using the SQLite version."
        }
      },
      "request_metadata": {
        "stream_end_timestamp_ms": 1779015610000
      }
    }
  ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/internal/parser/testdata/kiro_sqlite/standard_payload.json =====

{
  "conversation_id": "sqlite-session",
  "history": [
    {
      "user": {
        "env_context": {
          "env_state": {
            "current_working_directory": "/home/user/code/kiro-app"
          }
        },
        "content": {
          "Prompt": {
            "prompt": "Build the Kiro parser"
          }
        },
        "timestamp": "2026-05-17T10:00:00Z"
      },
      "assistant": {
        "Response": {
          "message_id": "assistant-1",
          "content": "I can do that."
        }
      },
      "request_metadata": {
        "stream_end_timestamp_ms": 1779012010000
      }
    },
    {
      "user": {
        "env_context": {
          "env_state": {
            "current_working_directory": "/home/user/code/kiro-app"
          }
        },
        "content": {
          "Prompt": {
            "prompt": "Read the source first"
          }
        },
        "timestamp": "2026-05-17T10:00:20Z"
      },
      "assistant": {
        "ToolUse": {
          "message_id": "assistant-2",
          "content": "",
          "tool_uses": [
            {
              "id": "tool-1",
              "name": "execute_bash",
              "args": {
                "command": "sed -n '1,120p' internal/parser/kiro.go"
              }
            }
          ]
        }
      },
      "request_metadata": {
        "stream_end_timestamp_ms": 1779012030000
      }
    }
  ],
  "transcript": [
    "> Build the Kiro parser",
    "I can do that."
  ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/renovate.json =====

{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "dependencyDashboard": true,
  "enabledManagers": ["github-actions", "gomod", "npm"],
  "osvVulnerabilityAlerts": true,
  "minimumReleaseAge": "7 days",
  "minimumReleaseAgeBehaviour": "timestamp-required",
  "prCreation": "not-pending",
  "internalChecksFilter": "strict",
  "vulnerabilityAlerts": {
    "minimumReleaseAge": null,
    "prCreation": "immediate"
  },
  "packageRules": [
    {
      "matchManagers": ["gomod"],
      "groupName": "Go dependencies",
      "groupSlug": "go-dependencies",
      "postUpdateOptions": ["gomodUpdateImportPaths", "gomodTidy"]
    },
    {
      "matchManagers": ["npm"],
      "groupName": "JavaScript dependencies",
      "groupSlug": "javascript-dependencies"
    }
  ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/.custom-gcl.yml =====

version: v2.11.4
plugins:
  - module: "go.uber.org/nilaway"
    import: "go.uber.org/nilaway/cmd/gclplugin"
    version: "v0.0.0-20260318203545-ad240b12fb4c"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/.github/workflows/ci.yml =====

name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - uses: actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c  # v6.4.0
        with:
          go-version-file: go.mod

      - name: Install lint tools
        run: |
          make lint-tools
          echo "$(go env GOPATH)/bin" >> "$GITHUB_PATH"

      - name: Run Go linters
        run: make lint-ci

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - uses: actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e  # v6.4.0
        with:
          node-version: "24"

      - name: Install frontend dependencies
        run: npm ci
        working-directory: frontend

      - name: Type-check (svelte-check)
        run: npm run check
        working-directory: frontend

      - name: Run frontend tests
        run: npm test
        working-directory: frontend

  frontend-node-25:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - uses: actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e  # v6.4.0
        with:
          node-version: "25"

      - name: Install frontend dependencies
        run: npm ci
        working-directory: frontend

      - name: Run frontend tests
        run: npm test
        working-directory: frontend

  test:
    name: Go Test (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - uses: actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c  # v6.4.0
        with:
          go-version-file: go.mod

      - name: Setup MinGW (Windows)
        if: runner.os == 'Windows'
        id: setup_mingw
        continue-on-error: true
        uses: msys2/setup-msys2@e9898307ac31d1a803454791be09ab9973336e1c  # v2
        with:
          msystem: MINGW64
          update: false
          install: mingw-w64-x86_64-gcc
          path-type: inherit

      - name: Setup MinGW (Windows, retry on transient failure)
        if: runner.os == 'Windows' && steps.setup_mingw.outcome == 'failure'
        uses: msys2/setup-msys2@e9898307ac31d1a803454791be09ab9973336e1c  # v2
        with:
          msystem: MINGW64
          update: false
          install: mingw-w64-x86_64-gcc
          path-type: inherit

      - name: Run Go tests
        run: go test -tags "fts5,kit_posthog_disabled" ./... -v -count=1
        env:
          CGO_ENABLED: "1"

      - name: Run Go tests (race detector)
        if: runner.os == 'Linux'
        run: |
          go test -tags "fts5,kit_posthog_disabled" ./internal/duckdb -count=1
          go test -tags "fts5,kit_posthog_disabled" -race $(go list ./... | grep -v '/internal/duckdb$') -count=1
        env:
          CGO_ENABLED: "1"

  desktop-windows-unit:
    name: Desktop Unit Tests (Windows)
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - name: Prepare placeholder sidecar resource
        shell: pwsh
        run: |
          $hostTriple = (rustc -vV | Select-String '^host: ').ToString() -replace '^host:\s+', ''
          if (-not $hostTriple) {
            throw "could not determine Rust host triple"
          }
          New-Item -ItemType Directory -Force desktop/src-tauri/binaries | Out-Null
          New-Item -ItemType File -Force "desktop/src-tauri/binaries/agentsview-$hostTriple.exe" | Out-Null

      - name: Run Windows desktop update tests
        run: cargo test --manifest-path desktop/src-tauri/Cargo.toml --lib install_downloaded_update

  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - uses: actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c  # v6.4.0
        with:
          go-version-file: go.mod

      - name: Test with coverage
        run: go test -tags "fts5,kit_posthog_disabled" -coverprofile=coverage.out ./...
        env:
          CGO_ENABLED: "1"

      - name: Upload coverage
        id: codecov
        uses: codecov/codecov-action@e79a6962e0d4c0c17b229090214935d2e33f8354  # v6.0.1
        with:
          files: coverage.out
        continue-on-error: true

      - name: Warn on coverage upload failure
        if: steps.codecov.outcome == 'failure'
        run: echo "::warning::Codecov upload failed"

  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:18-alpine
        env:
          POSTGRES_USER: agentsview_test
          POSTGRES_PASSWORD: agentsview_test_password
          POSTGRES_DB: agentsview_test


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/.github/workflows/desktop-artifacts.yml =====

name: Desktop Artifacts

on:
  workflow_dispatch:
  pull_request:
    paths:
      - 'desktop/**'
      - 'frontend/**'
      - 'go.mod'
      - 'go.sum'
      - '.github/workflows/desktop-*.yml'

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.ref }}
  cancel-in-progress: true

jobs:
  build:
    name: Desktop Build (${{ matrix.name }})
    runs-on: ${{ matrix.os }}
    env:
      AGENTSVIEW_TARGET_TRIPLE: ${{ matrix.target_triple }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - name: macOS (aarch64)
            os: macos-15
            bundle: app
            target_triple: aarch64-apple-darwin
            artifact_name: agentsview-desktop-macos-aarch64
            artifact_dir: desktop/src-tauri/target/aarch64-apple-darwin/release/bundle/macos/
          - name: macOS (x86_64)
            os: macos-15
            bundle: app
            target_triple: x86_64-apple-darwin
            artifact_name: agentsview-desktop-macos-x86_64
            artifact_dir: desktop/src-tauri/target/x86_64-apple-darwin/release/bundle/macos/
          - name: Windows
            os: windows-latest
            bundle: nsis
            target_triple: ""
            artifact_name: agentsview-desktop-windows
            artifact_dir: desktop/src-tauri/target/release/bundle/nsis/
          - name: Linux
            os: ubuntu-22.04
            bundle: appimage
            target_triple: ""
            artifact_name: agentsview-desktop-linux
            artifact_dir: desktop/src-tauri/target/release/bundle/appimage/
          - name: Linux (arm64)
            os: ubuntu-22.04-arm
            bundle: appimage
            target_triple: aarch64-unknown-linux-gnu
            artifact_name: agentsview-desktop-linux-arm64
            artifact_dir: desktop/src-tauri/target/aarch64-unknown-linux-gnu/release/bundle/appimage/

    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - uses: actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c  # v6.4.0
        with:
          go-version-file: go.mod

      - uses: actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e  # v6.4.0
        with:
          node-version: "24"

      - name: Setup MinGW (Windows)
        if: runner.os == 'Windows'
        uses: msys2/setup-msys2@e9898307ac31d1a803454791be09ab9973336e1c  # v2
        with:
          msystem: MINGW64
          update: false
          install: mingw-w64-x86_64-gcc
          path-type: inherit

      - name: Install Linux system dependencies
        if: runner.os == 'Linux'
        run: |
          sudo apt-get update -q
          sudo apt-get install -y \
            libwebkit2gtk-4.1-dev libgtk-3-dev \
            libappindicator3-dev librsvg2-dev \
            patchelf xdg-utils

      - name: Install Rust target
        if: env.AGENTSVIEW_TARGET_TRIPLE != ''
        run: rustup target add "$AGENTSVIEW_TARGET_TRIPLE"

      - name: Install desktop dependencies
        run: npm ci
        working-directory: desktop

      - name: Desktop smoke tests (shell scripts)
        shell: bash
        run: |
          bash desktop/scripts/test-prepare-sidecar.sh
          bash desktop/scripts/test-desktop-workflows.sh
          bash desktop/scripts/test-startup-ui.sh

      - name: Build desktop bundle
        shell: bash
        run: |
          cd desktop
          export TAURI_ENV_TARGET_TRIPLE="$AGENTSVIEW_TARGET_TRIPLE"
          npm run prepare-sidecar
          build_cmd=(npx tauri build --bundles "${{ matrix.bundle }}")
          if [ -n "$AGENTSVIEW_TARGET_TRIPLE" ]; then
            build_cmd+=(--target "$AGENTSVIEW_TARGET_TRIPLE")
          fi
          build_cmd+=(--config '{"bundle":{"createUpdaterArtifacts":false}}')
          "${build_cmd[@]}"

      - name: Desktop smoke tests (Rust unit tests)
        shell: bash
        run: |
          test_cmd=(cargo test --manifest-path desktop/src-tauri/Cargo.toml --lib)
          if [ -n "$AGENTSVIEW_TARGET_TRIPLE" ]; then
            export TAURI_ENV_TARGET_TRIPLE="$AGENTSVIEW_TARGET_TRIPLE"
            test_cmd+=(--target "$AGENTSVIEW_TARGET_TRIPLE")
          fi
          "${test_cmd[@]}"

      - name: Smoke check sidecar metadata
        shell: bash
        run: |
          target_triple="${AGENTSVIEW_TARGET_TRIPLE:-$(rustc -vV | awk '/^host: /{print $2}')}"
          if [ -z "$target_triple" ]; then
            echo "target triple is empty" >&2
            exit 1
          fi

          ext=""
          if [[ "$target_triple" == *"windows"* ]]; then
            ext=".exe"
          fi
          sidecar="desktop/src-tauri/binaries/agentsview-${target_triple}${ext}"
          if [ ! -f "$sidecar" ]; then
            echo "missing sidecar binary: $sidecar" >&2
            exit 1
          fi

          "$sidecar" version > sidecar-version.txt
          if grep -q "agentsview dev" sidecar-version.txt; then
            echo "sidecar version should not be dev: $(cat sidecar-version.txt)" >&2
            exit 1
          fi
          if grep -q "commit unknown" sidecar-version.txt; then
            echo "sidecar metadata missing commit: $(cat sidecar-version.txt)" >&2
            exit 1
          fi
          if grep -Eq "built[[:space:]]*\)$" sidecar-version.txt; then
            echo "sidecar metadata missing build date: $(cat sidecar-version.txt)" >&2
            exit 1
          fi

      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a  # v7.0.1
        with:
          name: ${{ matrix.artifact_name }}
          path: ${{ matrix.artifact_dir }}
          if-no-files-found: error


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/.github/workflows/desktop-release.yml =====

name: Desktop Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build-macos:
    name: Desktop Build (macOS ${{ matrix.arch }})
    runs-on: macos-15
    env:
      AGENTSVIEW_TARGET_TRIPLE: ${{ matrix.target_triple }}
      CARGO_BUILD_TARGET: ${{ matrix.target_triple }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - arch: aarch64
            target_triple: aarch64-apple-darwin
          - arch: x86_64
            target_triple: x86_64-apple-darwin
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false
          fetch-depth: 0

      - uses: actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c  # v6.4.0
        with:
          go-version-file: go.mod

      - uses: actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e  # v6.4.0
        with:
          node-version: "24"

      - name: Install Rust target
        run: rustup target add "$AGENTSVIEW_TARGET_TRIPLE"

      - name: Install desktop dependencies
        run: npm ci
        working-directory: desktop

      - name: Prepare sidecar
        env:
          AGENTSVIEW_VERSION: ${{ github.ref_name }}
        run: |
          export TAURI_ENV_TARGET_TRIPLE="$AGENTSVIEW_TARGET_TRIPLE"
          npm run prepare-sidecar
        working-directory: desktop

      - name: Patch updater config for current repository
        env:
          AGENTSVIEW_UPDATER_PUBKEY: ${{ secrets.AGENTSVIEW_UPDATER_PUBKEY }}
        run: |
          sed -i.bak \
            -e "s|wesm/agentsview|${GITHUB_REPOSITORY}|g" \
            -e "s|NOT_SET|${AGENTSVIEW_UPDATER_PUBKEY}|g" \
            desktop/src-tauri/tauri.conf.json
          rm -f desktop/src-tauri/tauri.conf.json.bak

      - name: Import signing certificate
        env:
          APPLE_CERTIFICATE: ${{ secrets.APPLE_CERTIFICATE }}
          APPLE_CERTIFICATE_PASSWORD: ${{ secrets.APPLE_CERTIFICATE_PASSWORD }}
        run: |
          KEYCHAIN_PATH="$RUNNER_TEMP/build.keychain"
          KEYCHAIN_PASS="$(openssl rand -base64 32)"

          security create-keychain -p "$KEYCHAIN_PASS" "$KEYCHAIN_PATH"
          security set-keychain-settings -lut 3600 "$KEYCHAIN_PATH"
          security unlock-keychain -p "$KEYCHAIN_PASS" "$KEYCHAIN_PATH"

          CERT_PATH="$RUNNER_TEMP/certificate.p12"
          echo "$APPLE_CERTIFICATE" | base64 -d > "$CERT_PATH"
          security import "$CERT_PATH" \
            -k "$KEYCHAIN_PATH" \
            -P "$APPLE_CERTIFICATE_PASSWORD" \
            -T /usr/bin/codesign \
            -T /usr/bin/security
          rm -f "$CERT_PATH"

          security set-key-partition-list \
            -S apple-tool:,apple: \
            -k "$KEYCHAIN_PASS" "$KEYCHAIN_PATH"
          security list-keychains -d user -s "$KEYCHAIN_PATH" login.keychain

      - name: Write API key
        env:
          APPLE_API_KEY_CONTENT: ${{ secrets.APPLE_API_KEY_CONTENT }}
          APPLE_API_KEY: ${{ secrets.APPLE_API_KEY }}
        run: |
          KEY_DIR="$RUNNER_TEMP/apple-keys"
          mkdir -p "$KEY_DIR"
          echo "$APPLE_API_KEY_CONTENT" | base64 -d \
            > "$KEY_DIR/AuthKey_${APPLE_API_KEY}.p8"
          echo "APPLE_API_KEY_PATH=$KEY_DIR/AuthKey_${APPLE_API_KEY}.p8" \
            >> "$GITHUB_ENV"

      - name: Build DMG and updater bundle
        env:
          APPLE_SIGNING_IDENTITY: ${{ secrets.APPLE_SIGNING_IDENTITY }}
          APPLE_API_ISSUER: ${{ secrets.APPLE_API_ISSUER }}
          APPLE_API_KEY: ${{ secrets.APPLE_API_KEY }}
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
          TAURI_SIGNING_PRIVATE_KEY_PASSWORD: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY_PASSWORD }}
          AGENTSVIEW_UPDATER_PUBKEY: ${{ secrets.AGENTSVIEW_UPDATER_PUBKEY }}
        run: npx tauri build --target "$AGENTSVIEW_TARGET_TRIPLE"
        working-directory: desktop

      - name: Collect build artifacts
        run: |
          bundle_dir="desktop/src-tauri/target/${AGENTSVIEW_TARGET_TRIPLE}/release/bundle"
          mkdir -p staging
          cp "$bundle_dir"/dmg/*.dmg staging/

          app_bundle="$(find "$bundle_dir"/macos -maxdepth 1 -name '*.app.tar.gz' -print -quit)"
          app_sig="$(find "$bundle_dir"/macos -maxdepth 1 -name '*.app.tar.gz.sig' -print -quit)"

          app_name="$(basename "$app_bundle")"
          app_sig_name="$(basename "$app_sig")"
          cp "$app_bundle" "staging/${app_name%.app.tar.gz}_${{ matrix.arch }}.app.tar.gz"
          cp "$app_sig" "staging/${app_sig_name%.app.tar.gz.sig}_${{ matrix.arch }}.app.tar.gz.sig"
          ls -la staging/

      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a  # v7.0.1
        with:
          name: agentsview-desktop-macos-${{ matrix.arch }}
          path: staging/*
          if-no-files-found: error

      - name: Cleanup signing secrets
        if: always()
        run: |
          KEYCHAIN_PATH="$RUNNER_TEMP/build.keychain"
          security delete-keychain "$KEYCHAIN_PATH" 2>/dev/null || true
          rm -rf "$RUNNER_TEMP/apple-keys" 2>/dev/null || true

  build-windows:
    name: Desktop Build (Windows)
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false
          fetch-depth: 0

      - uses: actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c  # v6.4.0
        with:
          go-version-file: go.mod

      - uses: actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e  # v6.4.0
        with:
          node-version: "24"

      - name: Setup MinGW
        id: setup_mingw
        continue-on-error: true
        uses: msys2/setup-msys2@e9898307ac31d1a803454791be09ab9973336e1c  # v2
        with:
          msystem: MINGW64
          update: false
          install: mingw-w64-x86_64-gcc
          path-type: inherit

      - name: Setup MinGW (retry on transient failure)
        if: steps.setup_mingw.outcome == 'failure'
        uses: msys2/setup-msys2@e9898307ac31d1a803454791be09ab9973336e1c  # v2
        with:
          msystem: MINGW64
          update: false
          install: mingw-w64-x86_64-gcc
          path-type: inherit


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/.github/workflows/docker.yml =====

name: Docker

on:
  push:
    branches: [main]
    tags:
      - 'v*'
  workflow_dispatch:

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - name: Compute image build metadata
        id: vars
        shell: bash
        run: |
          if [[ "${GITHUB_REF}" == refs/tags/v* ]]; then
            VERSION="${GITHUB_REF#refs/tags/}"
          else
            VERSION="dev"
          fi
          echo "version=${VERSION}" >> "$GITHUB_OUTPUT"
          echo "commit=${GITHUB_SHA::8}" >> "$GITHUB_OUTPUT"
          echo "build_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$GITHUB_OUTPUT"
          echo "image=${GITHUB_REPOSITORY,,}" >> "$GITHUB_OUTPUT"

      - uses: docker/setup-qemu-action@06116385d9baf250c9f4dcb4858b16962ea869c3  # v4.1.0

      - uses: docker/setup-buildx-action@d7f5e7f509e45cec5c76c4d5afdd7de93d0b3df5  # v4.1.0

      - uses: docker/login-action@650006c6eb7dba73a995cc03b0b2d7f5ca915bee  # v4.2.0
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/metadata-action@80c7e94dd9b9319bd5eb7a0e0fe9291e23a2a2e9  # v6.1.0
        id: meta
        with:
          images: ${{ env.REGISTRY }}/${{ steps.vars.outputs.image }}
          tags: |
            type=raw,value=latest,enable={{is_default_branch}}
            type=semver,pattern={{version}}
          labels: |
            org.opencontainers.image.title=agentsview
            org.opencontainers.image.description=Local web viewer for AI agent sessions

      - uses: docker/build-push-action@f9f3042f7e2789586610d6e8b85c8f03e5195baf  # v7.2.0
        with:
          context: .
          file: ./Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          build-args: |
            VERSION=${{ steps.vars.outputs.version }}
            COMMIT=${{ steps.vars.outputs.commit }}
            BUILD_DATE=${{ steps.vars.outputs.build_date }}
          cache-from: type=gha
          cache-to: type=gha,mode=max


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/.github/workflows/fuzz.yml =====

name: Fuzz

# Long-running fuzz exploration of the Antigravity wire-walk
# (GitHub #648). Every CI run already executes the committed seed
# corpus via plain `go test`; this workflow spends real fuzz time
# searching for new invariant violations on a schedule. A found
# failure is written to testdata/fuzz/ by the fuzz engine and
# uploaded as an artifact so it can be committed as a regression
# case.

on:
  schedule:
    - cron: "17 5 * * 1" # weekly, Monday 05:17 UTC
  workflow_dispatch:
    inputs:
      fuzztime:
        description: "Fuzz time per target (Go duration)"
        required: false
        default: "10m"

jobs:
  fuzz:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        target:
          - FuzzAgProtoParse
          - FuzzAgProtoLooksLikePrefix
          - FuzzDecodeAntigravityStep
          - FuzzExtractModelName
          - FuzzExtractTokenUsage
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - uses: actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c  # v6.4.0
        with:
          go-version-file: go.mod

      # The dispatch input goes through an env var, never directly
      # into the run script, so it cannot inject shell commands.
      - name: Fuzz ${{ matrix.target }}
        run: >
          go test -tags "fts5,kit_posthog_disabled"
          -fuzz "^${TARGET}$"
          -fuzztime "$FUZZTIME"
          ./internal/parser/
        env:
          CGO_ENABLED: "1"
          TARGET: ${{ matrix.target }}
          FUZZTIME: ${{ github.event.inputs.fuzztime || '10m' }}

      - name: Upload failing inputs
        if: failure()
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a  # v7.0.1
        with:
          name: fuzz-failures-${{ matrix.target }}
          path: internal/parser/testdata/fuzz/
          if-no-files-found: ignore


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/.github/workflows/msys2-update-check.yml =====

name: MSYS2 Update Check

# Periodically run Windows CI with MSYS2 updates enabled to catch
# toolchain drift, security fixes, and package metadata changes.
# If this workflow fails, update the pinned SHA and packages in ci.yml.

on:
  schedule:
    - cron: "0 9 * * 1"  # Every Monday at 09:00 UTC
  workflow_dispatch:

jobs:
  windows-update-check:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - uses: actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c  # v6.4.0
        with:
          go-version-file: go.mod

      - name: Setup MinGW (with updates)
        uses: msys2/setup-msys2@e9898307ac31d1a803454791be09ab9973336e1c  # v2
        with:
          msystem: MINGW64
          update: true
          install: mingw-w64-x86_64-gcc
          path-type: inherit

      - name: Stub frontend embed dir
        run: mkdir -p internal/web/dist && echo ok > internal/web/dist/stub.html

      - name: Run Go tests
        run: go test -tags "fts5,kit_posthog_disabled" ./... -v -count=1
        env:
          CGO_ENABLED: "1"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/.github/workflows/release.yml =====

name: Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: read

jobs:
  build-linux:
    strategy:
      fail-fast: false
      matrix:
        include:
          - goarch: amd64
            runner: ubuntu-latest
            container: quay.io/pypa/manylinux_2_28_x86_64@sha256:853663dc8253b62be437bb52a5caecffd020792af4442f55d927d22e0ea795ae
          - goarch: arm64
            runner: ubuntu-24.04-arm
            container: quay.io/pypa/manylinux_2_28_aarch64@sha256:ca1f9d96910e129d38f999644a1f211a6cdb4147da9f19157a49d72c5092453a

    runs-on: ${{ matrix.runner }}
    container: ${{ matrix.container }}
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - uses: actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c  # v6.4.0
        with:
          go-version-file: go.mod

      - uses: actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e  # v6.4.0
        with:
          node-version: "24"

      - name: Build frontend
        run: npm ci && npm run build
        working-directory: frontend

      - name: Embed frontend
        shell: bash
        run: |
          rm -rf internal/web/dist
          cp -r frontend/dist internal/web/dist

      - name: Build
        shell: bash
        env:
          GOOS: linux
          GOARCH: ${{ matrix.goarch }}
          CGO_ENABLED: "1"
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          COMMIT=${GITHUB_SHA::8}
          BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

          mkdir -p dist
          LDFLAGS="-s -w -X main.version=v${VERSION} -X main.commit=${COMMIT} -X main.buildDate=${BUILD_DATE}"
          go build -tags fts5 -buildvcs=false -ldflags="$LDFLAGS" -trimpath \
            -o dist/agentsview ./cmd/agentsview

          # Smoke test (native builds — no cross-compilation)
          ./dist/agentsview --version

          # Verify glibc compatibility
          MAX_GLIBC="GLIBC_2.28"
          HIGHEST=$(objdump -T dist/agentsview | grep -oP 'GLIBC_\d+\.\d+' | sort -t. -k1,1n -k2,2n | tail -1)
          echo "Highest glibc symbol: $HIGHEST (max allowed: $MAX_GLIBC)"
          if [ "$(printf '%s\n%s' "$MAX_GLIBC" "$HIGHEST" | sort -t. -k1,1n -k2,2n | tail -1)" != "$MAX_GLIBC" ]; then
            echo "ERROR: Binary requires $HIGHEST but wheel claims $MAX_GLIBC"
            exit 1
          fi

          cd dist
          ARCHIVE="agentsview_${VERSION}_linux_${{ matrix.goarch }}.tar.gz"
          tar czf "$ARCHIVE" agentsview
          rm agentsview

      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a  # v7.0.1
        with:
          name: agentsview-linux-${{ matrix.goarch }}
          path: dist/*.tar.gz

  build:
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: macos-15
            goos: darwin
            goarch: amd64
          - os: macos-15
            goos: darwin
            goarch: arm64
          - os: windows-latest
            goos: windows
            goarch: amd64
          - os: windows-11-arm
            goos: windows
            goarch: arm64

    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - uses: actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c  # v6.4.0
        with:
          go-version-file: go.mod

      - uses: actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e  # v6.4.0
        with:
          node-version: "24"

      - name: Build frontend
        run: npm ci && npm run build
        working-directory: frontend

      - name: Embed frontend
        shell: bash
        run: |
          rm -rf internal/web/dist
          cp -r frontend/dist internal/web/dist

      - name: Setup MinGW (Windows amd64)
        if: matrix.goos == 'windows' && matrix.goarch == 'amd64'
        uses: msys2/setup-msys2@e9898307ac31d1a803454791be09ab9973336e1c  # v2
        with:
          msystem: MINGW64
          update: false
          install: mingw-w64-x86_64-gcc
          path-type: inherit

      - name: Setup llvm-mingw (Windows arm64)
        if: matrix.goos == 'windows' && matrix.goarch == 'arm64'
        shell: pwsh
        env:
          # Self-contained aarch64 mingw clang toolchain (clang + runtime +
          # lld). cgo (mattn/go-sqlite3) needs a C compiler; no Visual
          # Studio / Windows SDK required. Pinned to a version + SHA256 for
          # reproducibility and supply-chain integrity.
          LLVM_MINGW_VERSION: "20260602"
          LLVM_MINGW_NAME: llvm-mingw-20260602-ucrt-aarch64
          LLVM_MINGW_SHA256: cb5c20fbe1808e31ada5cbe4efd9daa2fee19c91dac6ec5ca1ac46a9c7247e37
        run: |
          $ErrorActionPreference = 'Stop'
          $zip = Join-Path $env:RUNNER_TEMP 'llvm-mingw.zip'
          $url = "https://github.com/mstorsjo/llvm-mingw/releases/download/$env:LLVM_MINGW_VERSION/$env:LLVM_MINGW_NAME.zip"
          Write-Host "Downloading $url"
          Invoke-WebRequest -Uri $url -OutFile $zip
          # Verify the archive against the pinned SHA256 before extracting or
          # executing any of it, so a swapped or compromised upstream asset
          # fails the build instead of producing a trojaned binary.
          $actual = (Get-FileHash -Path $zip -Algorithm SHA256).Hash
          if ($actual -ne $env:LLVM_MINGW_SHA256) {
            throw "Checksum mismatch for $url`n  expected $env:LLVM_MINGW_SHA256`n  actual   $actual"
          }
          # 7-Zip is preinstalled on the runner image and extracts faster
          # than Expand-Archive for this many files.
          7z x $zip -o"$env:RUNNER_TEMP" | Out-Null
          $bin = Join-Path $env:RUNNER_TEMP "$env:LLVM_MINGW_NAME\bin"
          $cc = Join-Path $bin 'aarch64-w64-mingw32-clang.exe'
          if (-not (Test-Path $cc)) { throw "CC not found at $cc" }
          Add-Content -Path $env:GITHUB_PATH -Value $bin
          Add-Content -Path $env:GITHUB_ENV -Value "CC=$cc"

      - name: Build
        shell: bash
        env:
          GOOS: ${{ matrix.goos }}
          GOARCH: ${{ matrix.goarch }}
          CGO_ENABLED: "1"
          MACOSX_DEPLOYMENT_TARGET: ${{ matrix.goos == 'darwin' && '11.0' || '' }}
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          COMMIT=${GITHUB_SHA::8}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/.golangci.nilaway.yml =====

version: "2"
run:
  tests: false
linters:
  default: none
  enable:
    - nilaway
  settings:
    custom:
      nilaway:
        type: "module"
        description: Static analysis tool to detect potential nil panics in Go code.
        settings:
          include-pkgs: "go.kenn.io/agentsview"
  exclusions:
    rules:
      - path: "_test\\.go"
        linters:
          - nilaway


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/.golangci.yml =====

version: "2"
run:
  tests: true
  go: "1.26"
  build-tags:
    - fts5
linters:
  default: none
  enable:
    - errcheck
    - govet
    - ineffassign
    - modernize
    - staticcheck
    - unused
  settings:
    errcheck:
      check-type-assertions: false
      check-blank: false
  exclusions:
    generated: lax
    presets:
      - comments
      - common-false-positives
      - legacy
      - std-error-handling
    rules:
      - linters:
          - errcheck
        path: _test\.go
      - linters:
          - modernize
        text: "omitzero:"
    paths:
      - third_party$
      - builtin$
      - examples$
issues:
  max-issues-per-linter: 0
  max-same-issues: 0
formatters:
  exclusions:
    generated: lax
    paths:
      - third_party$
      - builtin$
      - examples$


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/docker-compose.test.yml =====

# Docker Compose file for integration testing
# Usage:
#   make postgres-up / make test-postgres / make postgres-down
#   make ssh-up / make test-ssh / make ssh-down

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: agentsview_test
      POSTGRES_PASSWORD: agentsview_test_password
      POSTGRES_DB: agentsview_test
    ports:
      - "5433:5432"  # Non-standard port to avoid conflict with local postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentsview_test -d agentsview_test"]
      interval: 2s
      timeout: 5s
      retries: 10
    tmpfs:
      - /var/lib/postgresql/data  # Use tmpfs for faster tests, no persistence needed

  sshd:
    build:
      context: .
      dockerfile: testdata/ssh/Dockerfile
    ports:
      - "2222:22"
    healthcheck:
      test: ["CMD-SHELL", "nc -z localhost 22"]
      interval: 2s
      timeout: 5s
      retries: 10
    tmpfs:
      - /tmp


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/docker-compose.prod.yaml =====

services:
  agentsview:
    image: ghcr.io/kenn-io/agentsview:latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      CLAUDE_PROJECTS_DIR: /agents/claude
      CODEX_SESSIONS_DIR: /agents/codex
      FORGE_DIR: /agents/forge
      OPENCODE_DIR: /agents/opencode
      # Set both of these to serve from PostgreSQL instead of the local archive.
      # PG_SERVE: "1"
      # AGENTSVIEW_PG_URL: postgres://user:password@postgres.example.com:5432/agentsview?sslmode=require
    volumes:
      - agentsview-data:/data
      - ${HOME}/.claude/projects:/agents/claude:ro
      - ${HOME}/.codex/sessions:/agents/codex:ro
      - ${HOME}/.forge:/agents/forge:ro
      - ${HOME}/.local/share/opencode:/agents/opencode:ro

volumes:
  agentsview-data:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/AGENTS.md =====

# AGENTS.md

Instructions for autonomous coding agents working in this repository.

## Scope

- Applies to all agent-driven work in this repo.
- If multiple instruction files exist, follow the most specific one for the
  files you are editing.

## Required Git Rules

1. Commit every turn.
1. Do not amend commits.
1. Do not change branches without explicit user permission.

## Commit Expectations

- Keep commits focused and related to the requested task.
- Use clear conventional commit messages.
- Do not push, pull, or rebase unless explicitly requested.
- Do not include generated-with lines, attribution blocks, validation footers,
  or command transcripts in commit messages.

## Validation

- Run relevant tests before committing when practical.
- If tests cannot be run, state that clearly in the handoff.
- After Go code changes, run `go fmt ./...` and `go vet ./...` before
  committing.

## Backend Parity

- Preserve behavior and query-shape parity between supported storage backends
  whenever practical. SQLite and PostgreSQL/Cockroach queries, indexes,
  aggregations, filtering, and ordering should match until there is a concrete,
  documented reason for them to differ.
- Do not implement a performance or correctness fix for only one backend and
  call the problem solved unless the user explicitly scopes the work to that
  backend, for example "this is only for PostgreSQL". If one backend needs a
  different implementation, explain why and keep the observable behavior the
  same.

## Test Style

- Go tests use `github.com/stretchr/testify` for assertions. Use `require.X`
  when a failed check should abort the test (setup, nil receivers, length checks
  before indexing) and `assert.X` for independent checks that should keep
  running. Don't write `if got != want { t.Fatalf(...) }` in new tests.
- Domain-specific helpers are fine, but they must use testify internally rather
  than stdlib comparisons.

## Safety

- Do not revert user-authored or unrelated local changes unless explicitly
  requested.
- Avoid destructive git commands unless explicitly requested.
- The SQLite database is a persistent archive. Never delete, drop, truncate, or
  recreate it to handle data version changes. Schema changes use non-destructive
  migrations such as `ALTER TABLE` and `UPDATE`; parser changes trigger a full
  resync that builds a fresh DB, syncs files, copies orphaned sessions from the
  old DB, and swaps atomically. Existing session data must be preserved even
  when source files no longer exist on disk.

## Project Overview

agentsview is a local web viewer for AI agent sessions. It syncs session data
from disk into SQLite with FTS5 full-text search, serves a Svelte 5 SPA via an
embedded Go HTTP server, and provides real-time updates via SSE. See
`internal/parser/types.go` for the full list of supported agents.

## Architecture

```text
CLI (agentsview) -> Config -> DB (SQLite/FTS5)
                  |           |
                  v           v
              File Watcher -> Sync Engine -> Parsers (per agent)
                  |           |
                  v           v
              HTTP Server -> REST API + SSE + Embedded SPA
                              |
                              v
                           PG Push Sync -> PostgreSQL (optional)
                              ^
                              |
              HTTP Server (pg serve) <- PostgreSQL
```

- Server: HTTP server with auto-port discovery, defaulting to 8080.
- Storage: SQLite with WAL mode, FTS5 for full-text search, and optional
  PostgreSQL for multi-machine shared access.
- Sync: file watcher plus periodic sync every 15 minutes for session
  directories.
- PG sync: on-demand push sync from SQLite to PostgreSQL via `pg push`.
- Frontend: Svelte 5 SPA embedded in the Go binary at build time.
- Config: `AGENTSVIEW_DATA_DIR` plus per-agent directory overrides and CLI
  flags. Per-agent env vars are listed on each entry in
  `internal/parser/types.go`.

## Project Structure

- `cmd/agentsview/` - Go server entrypoint.
- `cmd/testfixture/` - Test data generator for E2E tests.
- `internal/config/` - Config loading, JSON migration, and flag registration.
- `internal/db/` - SQLite sessions, messages, search, analytics, and schema.
- `internal/postgres/` - PostgreSQL push sync, read-only store, schema, and
  connection helpers.
- `internal/parser/` - Per-agent session file parsers and content extraction.
- `internal/server/` - HTTP handlers, SSE, middleware, search, and export.
- `internal/sync/` - Sync engine, file watcher, discovery, and hashing.
- `internal/timeutil/` - Time parsing utilities.
- `internal/web/` - Embedded frontend copied from `frontend/dist/` at build
  time.
- `frontend/` - Svelte 5 SPA with Vite and TypeScript.
- `scripts/` - Utility scripts for E2E server setup and changelog work.

## Key Files

| Path                             | Purpose                                       |
| -------------------------------- | --------------------------------------------- |
| `cmd/agentsview/main.go`         | CLI entry point, server startup, file watcher |
| `cmd/agentsview/pg.go`           | `pg` command group: push, status, serve       |
| `internal/server/server.go`      | HTTP router and handler setup                 |
| `internal/server/sessions.go`    | Session list/detail API handlers              |
| `internal/server/search.go`      | Full-text search API                          |
| `internal/server/events.go`      | SSE event streaming                           |
| `internal/db/db.go`              | Database open, migrations, schema             |
| `internal/db/sessions.go`        | Session CRUD queries                          |
| `internal/db/search.go`          | FTS5 search queries                           |
| `internal/sync/engine.go`        | Sync orchestration                            |
| `internal/parser/types.go`       | Agent registry with one `AgentDef` per agent  |
| `internal/parser/*.go`           | Per-agent session parsers                     |
| `internal/postgres/connect.go`   | Connection setup, SSL checks, DSN helpers     |
| `internal/postgres/schema.go`    | PG DDL and schema management                  |
| `internal/postgres/push.go`      | Push logic and fingerprinting                 |
| `internal/postgres/sync.go`      | Push sync lifecycle                           |
| `internal/postgres/store.go`     | PostgreSQL read-only store                    |
| `internal/postgres/sessions.go`  | PG session queries on the read side           |
| `internal/postgres/messages.go`  | PG message queries and ILIKE search           |
| `internal/postgres/analytics.go` | PG analytics queries                          |
| `internal/postgres/time.go`      | Timestamp conversion helpers                  |
| `internal/config/config.go`      | Config loading and flag registration          |

## Development

```bash
make build          # Build binary with embedded frontend
make dev            # Run Go server in dev mode
make frontend       # Build frontend SPA only
make frontend-dev   # Run Vite dev server, use alongside make dev
make install        # Build and install to ~/.local/bin or GOPATH
make install-hooks  # Install pre-commit git hooks
```

## Testing

All new features and bug fixes must include unit tests. Run tests before
committing:

```bash
make test       # Go tests with CGO_ENABLED=1 and -tags "fts5,kit_posthog_disabled"
make test-short # Fast tests only with -short
make e2e        # Playwright E2E tests
make lint       # golangci-lint plus NilAway
make vet        # go vet
```

## Test Style

- Prefer table-driven tests for Go code.
- Go tests use `github.com/stretchr/testify` for assertions.
- Use `require.X` when a failed check should abort the test, including setup
  errors, nil receivers, and length checks before indexing.
- Use `assert.X` for independent checks that should keep running.
- Do not write `if got != want { t.Fatalf(...) }` in new tests.
- Domain-specific helpers are fine, but they must use testify internally rather
  than stdlib comparisons.
- Use the existing `testDB(t)` helper for database tests.
- Frontend tests are colocated `*.test.ts` files, with Playwright specs in


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/CLAUDE.md =====

# AGENTS.md

Instructions for autonomous coding agents working in this repository.

## Scope

- Applies to all agent-driven work in this repo.
- If multiple instruction files exist, follow the most specific one for the
  files you are editing.

## Required Git Rules

1. Commit every turn.
1. Do not amend commits.
1. Do not change branches without explicit user permission.

## Commit Expectations

- Keep commits focused and related to the requested task.
- Use clear conventional commit messages.
- Do not push, pull, or rebase unless explicitly requested.
- Do not include generated-with lines, attribution blocks, validation footers,
  or command transcripts in commit messages.

## Validation

- Run relevant tests before committing when practical.
- If tests cannot be run, state that clearly in the handoff.
- After Go code changes, run `go fmt ./...` and `go vet ./...` before
  committing.

## Backend Parity

- Preserve behavior and query-shape parity between supported storage backends
  whenever practical. SQLite and PostgreSQL/Cockroach queries, indexes,
  aggregations, filtering, and ordering should match until there is a concrete,
  documented reason for them to differ.
- Do not implement a performance or correctness fix for only one backend and
  call the problem solved unless the user explicitly scopes the work to that
  backend, for example "this is only for PostgreSQL". If one backend needs a
  different implementation, explain why and keep the observable behavior the
  same.

## Test Style

- Go tests use `github.com/stretchr/testify` for assertions. Use `require.X`
  when a failed check should abort the test (setup, nil receivers, length checks
  before indexing) and `assert.X` for independent checks that should keep
  running. Don't write `if got != want { t.Fatalf(...) }` in new tests.
- Domain-specific helpers are fine, but they must use testify internally rather
  than stdlib comparisons.

## Safety

- Do not revert user-authored or unrelated local changes unless explicitly
  requested.
- Avoid destructive git commands unless explicitly requested.
- The SQLite database is a persistent archive. Never delete, drop, truncate, or
  recreate it to handle data version changes. Schema changes use non-destructive
  migrations such as `ALTER TABLE` and `UPDATE`; parser changes trigger a full
  resync that builds a fresh DB, syncs files, copies orphaned sessions from the
  old DB, and swaps atomically. Existing session data must be preserved even
  when source files no longer exist on disk.

## Project Overview

agentsview is a local web viewer for AI agent sessions. It syncs session data
from disk into SQLite with FTS5 full-text search, serves a Svelte 5 SPA via an
embedded Go HTTP server, and provides real-time updates via SSE. See
`internal/parser/types.go` for the full list of supported agents.

## Architecture

```text
CLI (agentsview) -> Config -> DB (SQLite/FTS5)
                  |           |
                  v           v
              File Watcher -> Sync Engine -> Parsers (per agent)
                  |           |
                  v           v
              HTTP Server -> REST API + SSE + Embedded SPA
                              |
                              v
                           PG Push Sync -> PostgreSQL (optional)
                              ^
                              |
              HTTP Server (pg serve) <- PostgreSQL
```

- Server: HTTP server with auto-port discovery, defaulting to 8080.
- Storage: SQLite with WAL mode, FTS5 for full-text search, and optional
  PostgreSQL for multi-machine shared access.
- Sync: file watcher plus periodic sync every 15 minutes for session
  directories.
- PG sync: on-demand push sync from SQLite to PostgreSQL via `pg push`.
- Frontend: Svelte 5 SPA embedded in the Go binary at build time.
- Config: `AGENTSVIEW_DATA_DIR` plus per-agent directory overrides and CLI
  flags. Per-agent env vars are listed on each entry in
  `internal/parser/types.go`.

## Project Structure

- `cmd/agentsview/` - Go server entrypoint.
- `cmd/testfixture/` - Test data generator for E2E tests.
- `internal/config/` - Config loading, JSON migration, and flag registration.
- `internal/db/` - SQLite sessions, messages, search, analytics, and schema.
- `internal/postgres/` - PostgreSQL push sync, read-only store, schema, and
  connection helpers.
- `internal/parser/` - Per-agent session file parsers and content extraction.
- `internal/server/` - HTTP handlers, SSE, middleware, search, and export.
- `internal/sync/` - Sync engine, file watcher, discovery, and hashing.
- `internal/timeutil/` - Time parsing utilities.
- `internal/web/` - Embedded frontend copied from `frontend/dist/` at build
  time.
- `frontend/` - Svelte 5 SPA with Vite and TypeScript.
- `scripts/` - Utility scripts for E2E server setup and changelog work.

## Key Files

| Path                             | Purpose                                       |
| -------------------------------- | --------------------------------------------- |
| `cmd/agentsview/main.go`         | CLI entry point, server startup, file watcher |
| `cmd/agentsview/pg.go`           | `pg` command group: push, status, serve       |
| `internal/server/server.go`      | HTTP router and handler setup                 |
| `internal/server/sessions.go`    | Session list/detail API handlers              |
| `internal/server/search.go`      | Full-text search API                          |
| `internal/server/events.go`      | SSE event streaming                           |
| `internal/db/db.go`              | Database open, migrations, schema             |
| `internal/db/sessions.go`        | Session CRUD queries                          |
| `internal/db/search.go`          | FTS5 search queries                           |
| `internal/sync/engine.go`        | Sync orchestration                            |
| `internal/parser/types.go`       | Agent registry with one `AgentDef` per agent  |
| `internal/parser/*.go`           | Per-agent session parsers                     |
| `internal/postgres/connect.go`   | Connection setup, SSL checks, DSN helpers     |
| `internal/postgres/schema.go`    | PG DDL and schema management                  |
| `internal/postgres/push.go`      | Push logic and fingerprinting                 |
| `internal/postgres/sync.go`      | Push sync lifecycle                           |
| `internal/postgres/store.go`     | PostgreSQL read-only store                    |
| `internal/postgres/sessions.go`  | PG session queries on the read side           |
| `internal/postgres/messages.go`  | PG message queries and ILIKE search           |
| `internal/postgres/analytics.go` | PG analytics queries                          |
| `internal/postgres/time.go`      | Timestamp conversion helpers                  |
| `internal/config/config.go`      | Config loading and flag registration          |

## Development

```bash
make build          # Build binary with embedded frontend
make dev            # Run Go server in dev mode
make frontend       # Build frontend SPA only
make frontend-dev   # Run Vite dev server, use alongside make dev
make install        # Build and install to ~/.local/bin or GOPATH
make install-hooks  # Install pre-commit git hooks
```

## Testing

All new features and bug fixes must include unit tests. Run tests before
committing:

```bash
make test       # Go tests with CGO_ENABLED=1 and -tags "fts5,kit_posthog_disabled"
make test-short # Fast tests only with -short
make e2e        # Playwright E2E tests
make lint       # golangci-lint plus NilAway
make vet        # go vet
```

## Test Style

- Prefer table-driven tests for Go code.
- Go tests use `github.com/stretchr/testify` for assertions.
- Use `require.X` when a failed check should abort the test, including setup
  errors, nil receivers, and length checks before indexing.
- Use `assert.X` for independent checks that should keep running.
- Do not write `if got != want { t.Fatalf(...) }` in new tests.
- Domain-specific helpers are fine, but they must use testify internally rather
  than stdlib comparisons.
- Use the existing `testDB(t)` helper for database tests.
- Frontend tests are colocated `*.test.ts` files, with Playwright specs in


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/README.md =====

# agentsview

Browse, search, and track costs across all your AI coding agents. One binary, no
accounts, everything local.

<p align="center">
  <img src="https://agentsview.io/screenshots/dashboard.png" alt="Analytics dashboard" width="720">
</p>

## Install

```bash
# macOS / Linux
curl -fsSL https://agentsview.io/install.sh | bash

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://agentsview.io/install.ps1 | iex"
```

Or download the **desktop app** (macOS / Windows) from
[GitHub Releases](https://github.com/kenn-io/agentsview/releases) or via
homebrew: `brew install --cask agentsview`

Or run the published Docker image:

```bash
docker run --rm -p 127.0.0.1:8080:8080 \
  -v agentsview-data:/data \
  -v "$HOME/.claude/projects:/agents/claude:ro" \
  -v "$HOME/.forge:/agents/forge:ro" \
  -e CLAUDE_PROJECTS_DIR=/agents/claude \
  -e FORGE_DIR=/agents/forge \
  ghcr.io/kenn-io/agentsview:latest
```

## Quick Start

```bash
agentsview serve           # start server, open web UI
agentsview usage daily     # print daily cost summary
```

On first run, agentsview discovers sessions from every supported agent on your
machine, syncs them into a local SQLite database, and opens a web UI at
`http://127.0.0.1:8080`.

## Remote / forwarded access

agentsview binds to loopback and validates the request `Host` header to guard
against DNS-rebinding attacks. When you reach it through SSH port-forwarding, a
reverse proxy, or a remote dev environment (exe.dev, Codespaces, Coder, WSL2),
the browser sends a `Host` that the server does not recognize, so API requests
such as `/api/v1/settings` are rejected with `403 Forbidden`.

To fix this, restart the server with `--public-url` set to the exact origin you
open in the browser:

```bash
# Browser opens http://127.0.0.1:18080 via `ssh -L 18080:127.0.0.1:8080 host`
agentsview serve --public-url http://127.0.0.1:18080

# Browser opens a forwarded hostname
agentsview serve --public-url https://your-workspace.exe.dev
```

Use `--public-origin` (repeatable or comma-separated) to trust additional
browser origins. If you expose the UI beyond loopback, also enable
`--require-auth`.

## Docker

The container image defaults to local `agentsview serve`. Set `PG_SERVE=1` to
switch the startup command to `agentsview pg serve` instead.

`docker-compose.prod.yaml` is included as a production example:

```bash
docker compose -f docker-compose.prod.yaml up -d
```

The included compose file persists the agentsview data directory in a named
volume and mounts Claude, Codex, Forge, and OpenCode session roots read-only.
The container runs as root, so prefer a named volume for `/data` over a host
bind mount; if you do bind-mount, pre-create the directory with the desired
ownership to avoid root-owned files in your home directory.

The examples publish the UI on loopback only (`127.0.0.1`). If you need to
expose it beyond localhost, enable `--require-auth` and publish the port
intentionally.

Important: a containerized agentsview instance can only discover agent sessions
from directories you explicitly mount into the container. If you do not mount an
agent's session directory and point the matching env var at it, that agent will
not appear in the UI.

Example PostgreSQL-backed startup:

```bash
docker run --rm -p 127.0.0.1:8080:8080 \
  -e PG_SERVE=1 \
  -e AGENTSVIEW_PG_URL='postgres://user:password@postgres.example.com:5432/agentsview?sslmode=require' \
  ghcr.io/kenn-io/agentsview:latest
```

Example DuckDB mirror startup:

```bash
# Populate /data/sessions.duckdb from the mounted SQLite archive.
docker run --rm \
  -v agentsview-data:/data \
  -v "$HOME/.claude/projects:/agents/claude:ro" \
  -e CLAUDE_PROJECTS_DIR=/agents/claude \
  ghcr.io/kenn-io/agentsview:latest duckdb push --full

# Serve the populated mirror read-only.
docker run --rm -p 127.0.0.1:8080:8080 \
  -v agentsview-data:/data \
  ghcr.io/kenn-io/agentsview:latest duckdb serve
```

Example Quack startup:

```bash
# Expose the local DuckDB mirror over Quack from the host/container.
QUACK_TOKEN="$(openssl rand -base64 32)"
docker run --rm -p 127.0.0.1:9494:9494 \
  -v agentsview-data:/data \
  ghcr.io/kenn-io/agentsview:latest \
  duckdb quack serve \
    --bind quack:0.0.0.0:9494 \
    --token "$QUACK_TOKEN" \
    --allow-insecure

# Serve the web UI from a remote Quack endpoint.
docker run --rm -p 127.0.0.1:8080:8080 \
  -e AGENTSVIEW_DUCKDB_URL='quack:https://duckdb.example.com' \
  -e AGENTSVIEW_DUCKDB_TOKEN="$QUACK_TOKEN" \
  ghcr.io/kenn-io/agentsview:latest duckdb serve
```

Keep Quack on loopback or behind TLS. Plain HTTP Quack on a non-loopback bind
requires `--allow-insecure` and should only be used behind a trusted tunnel or
reverse proxy.

## Token Usage and Cost Tracking

`agentsview usage` is a fast, local replacement for ccusage and similar tools.
It tracks token consumption and compute costs across **all** your coding agents
-- not just Claude Code. Because session data is already indexed in SQLite,
queries are over 100x faster than tools that re-parse raw session files on every
run.

```bash
# Daily cost summary (default: last 30 days)
agentsview usage daily

# Per-model breakdown
agentsview usage daily --breakdown

# Filter by agent and date range
agentsview usage daily --agent claude --since 2026-04-01

# One-line summary for shell prompts / status bars
agentsview usage daily --all --json
agentsview usage statusline
```

Features:

- Automatic pricing via LiteLLM rates (with offline fallback)
- Prompt-caching-aware cost calculation (cache creation / read tokens)
- Per-model breakdown with `--breakdown`
- Date filtering (`--since`, `--until`, `--all`), agent filtering (`--agent`)
- JSON output (`--json`) for scripting
- Timezone-aware date bucketing (`--timezone`)
- Works standalone -- no server required, just run the command

## Per-Session Details

`agentsview session usage <id>` prints per-session token statistics plus a cost


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/SECURITY.md =====

# Security and Privacy Posture

## Status

Foundational document. Describes agentsview's current security and privacy
behavior and the assumptions that behavior rests on, much of which is already
enforced in code but has not been written down in one place. It is intentionally
descriptive rather than prescriptive — several questions are flagged as open and
will be resolved by future proposals rather than decided here.

If you are reporting a vulnerability, see [Reporting](#reporting) below.

## Audience and deployment model

agentsview is designed to run on a single-user workstation, alongside the agent
tools whose sessions it indexes. Single-user laptop or developer workstation is
the assumed deployment; other deployments (shared hosts, public exposure,
multi-machine sync) are possible but require the user to opt into additional
risk via documented flags and config.

## Threat model

### In scope

- A local, authenticated user reading their own session archive through the
  agentsview UI, CLI, or API.
- Network attackers who cannot already execute code as the local user. The
  default loopback bind, Host-header allowlist (DNS rebinding defense), CORS
  restrictions, and CSP / `X-Frame-Options: DENY` headers are aimed at this
  attacker.
- Parser crashes, excessive resource use, or active-content injection triggered
  by content inside supported session files. Session files often contain
  web/tool output that agentsview did not author, and defensive parsing of that
  content is a security-relevant concern.
- Inadvertent exposure of secrets that appear in transcripts. agentsview ships a
  best-effort secret detector and redacts findings in the UI and CLI by default
  (see [Secrets subsystem](#secrets-subsystem)).

### Explicitly out of scope (today)

- Hostile peers on the same OS account. agentsview's data dir inherits
  permissions from the user's umask; no defense is offered against another
  process running as the same user.
- Same-user arbitrary file write or code execution. If an attacker can drop
  files into the configured session directories as the local user, they are
  inside the trust base.
- Multi-user machines with hostile peer accounts.
- Side-channel attacks against the local SQLite database.
- Strong isolation between projects, agents, or time periods within a single
  agentsview instance. The database is a unified archive; any caller able to
  read it can read all of it.
- Strong guarantees about data destruction. Deletion removes rows but does not
  promise SQLite page, WAL, or filesystem-level erasure.

## Trust boundaries

| Boundary                          | Posture                                                          | Notes                                                                |
| --------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------- |
| Session files → parser            | Treated as untrusted data                                        | Parsers should not exec/eval; bugs are security-relevant.            |
| Imports and new readers           | Treated as untrusted structured data                             | Same posture as parsers; imported archives may be remote-origin.     |
| SSH remote sync                   | Treated as user-provisioned and user-authenticated               | Pulled archives are parsed locally as untrusted data.                |
| Parser → SQLite / FTS5            | Trusted                                                          | Indexed content is preserved verbatim.                               |
| HTTP server → caller              | Loopback-trusted; bearer-gated for `/api/` when `--require-auth` | Static assets are not gated.                                         |
| Browser → HTTP server             | Host-header allowlist + CORS + CSP + X-Frame-Options enforced    | DNS-rebinding, framing, and cross-origin defenses.                   |
| agentsview → PostgreSQL (pg push) | TLS required for non-loopback hosts                              | Plaintext rejected unless `allow_insecure = true` is set explicitly. |
| agentsview → update endpoint      | One-way outbound, opt-out                                        | Disable with `--no-update-check`.                                    |
| agentsview → LiteLLM pricing      | One-way outbound, on-demand                                      | Public JSON fetched from GitHub raw; no session data sent.           |

## Data at rest

- The local archive (SQLite + FTS5 index) stores indexed session data in
  plaintext. This includes assistant responses, user prompts, tool arguments,
  command output, file contents fetched by agents, and any secrets that may have
  been pasted into an agent session.
- File permissions follow the user's umask. agentsview does not chmod the data
  directory and does not encrypt at rest.
- Treat the agentsview data directory with the same care you would treat your
  shell history or your editor's swap files. It is at least as sensitive.
- Deletion semantics: the UI supports both a soft-delete (trash) and a
  permanent-delete path. Permanent delete removes rows from the primary tables
  and the FTS5 index; it does not promise erasure of SQLite pages, the WAL,
  on-disk backups, OS file caches, or any external copy that was made via
  `pg push` or SSH sync.

## Data in transit

agentsview makes several distinct outbound connections. Each is listed
explicitly because "data stays on your machine" is the default but is not a
complete description of the system once optional features are in use.

- **Local UI / API.** The HTTP server binds to `127.0.0.1` by default. When
  exposed beyond loopback, `--require-auth` should be enabled. Authentication is
  a bearer token applied to `/api/` routes only; static assets remain ungated.
  Browser-facing defenses (Host-header allowlist, CORS restrictions, CSP,
  `X-Frame-Options: DENY`) are always on. See the CLI reference for token
  configuration.
- **PostgreSQL sync.** `agentsview pg push` exports the local archive to a
  user-supplied PostgreSQL instance. Non-loopback DSNs are rejected unless TLS
  is enabled (`sslmode=require` or stronger), or the user has explicitly set
  `allow_insecure = true` under `[pg]`. The destination database itself is
  treated as user-provisioned infrastructure; agentsview asserts nothing about
  its access controls.
- **SSH remote sync.** agentsview can pull session archives from another machine
  over SSH. Authentication is whatever the user's SSH configuration provides.
  Pulled files are parsed locally as untrusted data and merged into the unified
  archive.
- **Imports.** Imported archives from other agentsview instances or third-party
  exports are treated as untrusted structured data, no different from session
  files written by local agents.
- **LiteLLM pricing.** Pricing metadata is fetched on demand from
  `raw.githubusercontent.com/BerriAI/litellm/...` to compute token costs. No
  session data is sent.
- **Update check.** On startup agentsview makes one outbound HTTPS request to
  check for new releases. No session data is sent; the request is opt-out via
  `--no-update-check`.

## Browser-facing hardening

The HTTP server applies the following defenses unconditionally:

- **Host-header allowlist.** Requests whose `Host` does not match the configured
  listen address (or a configured public URL/origin) are rejected, defending
  against DNS-rebinding attacks where an attacker domain resolves to
  `127.0.0.1`.
- **CORS restrictions.** Cross-origin API requests must come from an allowed
  origin or carry the bearer token; preflight handling is explicit.
- **Content-Security-Policy.** A policy pinning the server's exact origin for
  script/style/image/font/default-src is set on non-API responses. `connect-src`
  is intentionally widened to allow the remote-server feature in the SPA; this
  is a documented tradeoff.
- **X-Frame-Options: DENY.** Framing is disallowed on non-API responses.

## Secrets subsystem

agentsview includes best-effort detection of secrets that appear in session
content (API keys, tokens, credentials). Detected secrets are:

- recorded as findings in the database;
- redacted by default in CLI and UI views;
- revealable only via localhost-gated paths.

This is a defense-in-depth feature, not data-loss prevention. It does not catch
every secret pattern, does not retroactively remove secrets from the on-disk
archive, and does not make plaintext-at-rest storage safe. Treat the archive as
if it contains every secret that ever appeared in any indexed session.

## Contributing features that touch sensitive data

Contributors adding parsers, indexes, readers, or sync targets that expand the
data agentsview ingests, retains, or transmits should:

1. State explicitly which trust boundary the change crosses.
1. Make a deliberate opt-in vs opt-out decision and document it.
1. Add any new egress channel to the Data-in-transit section of this document,
   with a clear description of what is sent.
1. Treat any new structured input source (file format, RPC, import) as untrusted
   by default.

Configuration ergonomics (one boolean vs many granular toggles) is a maintainer
design call and out of scope for this document.

## Reporting

Security issues should be reported privately, not via public GitHub issues.

\[TODO: maintainer to enable GitHub private vulnerability reporting on the
repository and/or provide a private contact (email, PGP key). Until that contact
is published, please open a non-detailed GitHub issue requesting a private
channel and a maintainer will follow up out-of-band; do not include exploit
details in the public issue.\]

## Open questions

These are intentionally not resolved in this document. Each is a candidate for
its own proposal.

1. **Encryption at rest.** Should the SQLite archive support optional at-rest
   encryption (e.g., SQLCipher)? At what UX cost?
1. **Auth model evolution.** Should the bearer-token model grow (per-client
   tokens, expiry, rotation), and how should tokens be stored on disk?


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/desktop/README.md =====

# AgentsView Desktop (Tauri)

This directory contains an experimental Tauri desktop wrapper for AgentsView.

The wrapper does not reimplement the web app. Instead, it:

1. Builds the existing Go `agentsview` binary.
1. Packages it as a Tauri sidecar.
1. Starts it with `serve --no-browser` on a local port.
1. Loads the local URL in a native webview.

## Requirements

- Rust toolchain (`rustc`, `cargo`)
- Node.js and npm
- Go (with CGO enabled; same requirements as the main project)

## Usage

```bash
npm install
npm run tauri:dev
npm run tauri:build
npm run tauri:build:macos-app
npm run tauri:build:windows
```

The `prepare-sidecar` step runs automatically for `tauri:dev` and `tauri:build`.
It builds `agentsview` and copies it to
`src-tauri/binaries/agentsview-<target-triple>`.

## Environment Notes (Desktop)

When launched from Finder/Explorer, desktop apps usually do not inherit your
shell profile (`.zshrc`, `.bashrc`), which can hide CLIs like `claude`, `codex`,
and `gemini` from `PATH`.

On macOS/Linux, the Tauri wrapper loads login-shell env (`$SHELL -lic 'env -0'`)
for the sidecar (with a short timeout to avoid startup hangs). On Windows this
probing is skipped by default.

Optional escape hatch:

- Add overrides in `~/.agentsview/desktop.env`:
  - Example: `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin`
  - Example: `ANTHROPIC_API_KEY=...`
- On Windows, this file resolves to `%USERPROFILE%\\.agentsview\\desktop.env`.
- Force a custom PATH with `AGENTSVIEW_DESKTOP_PATH`.
- Skip login-shell env loading with `AGENTSVIEW_DESKTOP_SKIP_LOGIN_SHELL_ENV=1`.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/docs/desktop-release-setup.md =====

# Desktop Release: Signing and Configuration Guide

This document covers the one-time setup for desktop release signing (macOS
notarization, Tauri update signing) and the GitHub secrets required by the
`desktop-release.yml` workflow.

## Overview

The desktop release workflow (`.github/workflows/desktop-release.yml`) triggers
on `v*` tag pushes and produces:

- **macOS**: Signed and notarized `.dmg` installer + `.app.tar.gz` updater
  bundle
- **Windows**: `.exe` NSIS installer + `.nsis.zip` updater bundle
- **Updater manifest**: `latest.json` with platform URLs and Ed25519 signatures

Three separate credential sets are needed:

| Credential Set                  | Purpose                       | Platforms       |
| ------------------------------- | ----------------------------- | --------------- |
| Apple Developer certificate     | Code signing                  | macOS           |
| Apple App Store Connect API key | Notarization                  | macOS           |
| Tauri signing key               | Update signature verification | macOS + Windows |

## 1. Apple Developer Certificate (macOS code signing)

Code signing proves the app was built by a known developer. macOS Gatekeeper
blocks unsigned apps. The CI workflow imports this certificate into a temporary
keychain, signs the `.app` bundle and DMG, then deletes the keychain.

### Prerequisites

- An [Apple Developer Program](https://developer.apple.com/programs/) membership
  ($99/year, required for "Developer ID" certificates)
- A Mac with Keychain Access (needed to generate the CSR and export the `.p12`)

### Step 1: Create a Certificate Signing Request (CSR)

1. Open **Keychain Access** (in `/Applications/Utilities/`)
1. Menu bar: **Keychain Access > Certificate Assistant > Request a Certificate
   from a Certificate Authority...**
1. Fill in:
   - **User Email Address**: your Apple ID email
   - **Common Name**: your name (can be anything)
   - **CA Email Address**: leave blank
   - Select **Saved to disk**
1. Click **Continue** and save the `.certSigningRequest` file

### Step 2: Create the certificate on Apple's portal

1. Go to
   [developer.apple.com/account/resources/certificates/list](https://developer.apple.com/account/resources/certificates/list)
1. Click the **+** button
1. Under "Software", select **Developer ID Application** (this is for apps
   distributed outside the App Store — do **not** choose "Mac App Distribution"
   or "Apple Development")
1. Click **Continue**, upload the `.certSigningRequest` file from step 1
1. Click **Continue**, then **Download** to get the `.cer` file
1. Double-click the `.cer` file to install it into Keychain Access

### Step 3: Export as .p12

The CI runner needs the certificate as a `.p12` file (which bundles the
certificate and its private key).

1. Open **Keychain Access**
1. In the left sidebar, select **login** keychain, then **My Certificates**
   category
1. Find the certificate named `Developer ID Application: Your Name (TEAMID)` —
   it should have a disclosure triangle showing a private key underneath
1. Right-click the certificate (not the private key) > **Export "Developer ID
   Application: ..."**
1. Format: **Personal Information Exchange (.p12)**
1. Set a strong password when prompted — you will need this for the
   `APPLE_CERTIFICATE_PASSWORD` secret

Base64-encode the `.p12` for storage as a GitHub secret:

```bash
base64 -i "Developer_ID_Application.p12" | pbcopy
# The base64 string is now on your clipboard
```

The output is a long base64 string (typically 3000-5000 characters). It starts
with something like `MIIKcQIBAzCCCjcGCS...`. This entire string goes into the
`APPLE_CERTIFICATE` secret.

### Step 4: Find your signing identity

Run this to list available code signing identities:

```bash
security find-identity -v -p codesigning
```

You should see output like:

```
  1) A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2 "Developer ID Application: Jane Smith (ABC123XYZ)"
     1 valid identities found
```

The full quoted string — `Developer ID Application: Jane Smith (ABC123XYZ)` — is
your signing identity. The 10-character code in parentheses is your Team ID.

If you see multiple identities, use the one that matches the certificate you
just created. If you see no identities, the certificate wasn't installed
correctly — check that the `.cer` was imported and that the private key from the
CSR is in the same keychain.

### GitHub secrets for code signing

| Secret                       | Example value                                      | Notes                                                             |
| ---------------------------- | -------------------------------------------------- | ----------------------------------------------------------------- |
| `APPLE_CERTIFICATE`          | `MIIKcQIBAzCCCjcGCS...` (long base64)              | The entire base64-encoded `.p12` file                             |
| `APPLE_CERTIFICATE_PASSWORD` | `your-p12-export-password`                         | The password you set when exporting the `.p12`                    |
| `APPLE_SIGNING_IDENTITY`     | `Developer ID Application: Jane Smith (ABC123XYZ)` | Exact string from `security find-identity`, including the Team ID |

## 2. Apple App Store Connect API Key (notarization)

Notarization sends the signed app to Apple's servers for automated malware
scanning. After approval (usually 1-5 minutes), macOS recognizes the app as
checked by Apple and won't show the "unidentified developer" warning. The CI
workflow uses an App Store Connect API key to authenticate with Apple's notary
service.

### Step 1: Create the API key

1. Go to
   [appstoreconnect.apple.com/access/integrations/api](https://appstoreconnect.apple.com/access/integrations/api)
   - If you haven't used the API before, you'll need to click **Request Access**
     first
1. Note the **Issuer ID** displayed at the top of the page. It looks like a
   UUID:
   ```
   Issuer ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
   ```
1. Click **Generate API Key** (or the **+** button)
1. Name: `AgentsView Notarization` (or any descriptive name)
1. Access: **Developer** (minimum role needed for notarization)
1. Click **Generate**

### Step 2: Download the key

After generating, the key appears in the table with a **Download** link.

**Download the `.p8` file immediately.** Apple only lets you download it once.
If you lose it, you must revoke the key and create a new one.

The downloaded file is named `AuthKey_XXXXXXXXXX.p8` where `XXXXXXXXXX` is the
Key ID. For example: `AuthKey_ABC123DEF0.p8`.

The Key ID is also shown in the "Key ID" column of the table. It is a
10-character alphanumeric string like `ABC123DEF0`.

### Step 3: Inspect what you have

At this point you should have three pieces of information:

```
Issuer ID:  a1b2c3d4-e5f6-7890-abcd-ef1234567890    (from the top of the API keys page)
Key ID:     ABC123DEF0                                 (from the table, also in the filename)
Key file:   ~/Downloads/AuthKey_ABC123DEF0.p8          (the downloaded file)
```

The `.p8` file is a short PEM-encoded private key (about 300 bytes). It looks
like:

```
-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQg...
(2-3 lines of base64)
-----END PRIVATE KEY-----
```

### Step 4: Base64-encode the key file

```bash
base64 -i ~/Downloads/AuthKey_ABC123DEF0.p8 | pbcopy
# The base64 string is now on your clipboard


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/docs/duckdb-backend-plan.md =====

# DuckDB Backend Plan

Status: planned

Last checked: 2026-06-08

## Context

agentsview currently has two storage modes:

- SQLite is the local primary archive. File sync, parser writes, full resync,
  trash, insights, upload, and per-session repair all write through
  `internal/db`.
- PostgreSQL is an optional shared backend. `agentsview pg push` mirrors local
  SQLite into PG, and `agentsview pg serve` exposes the web UI from a read-only
  `db.Store` implementation under `internal/postgres`.

DuckDB should follow the PostgreSQL shape first: keep SQLite as the primary
ingestion source, mirror data into DuckDB, and serve the UI from a DuckDB
read-store. That makes local DuckDB files and remote Quack endpoints useful
without forcing the parser/sync engine to support multiple primary write paths
up front.

## Quack Notes

DuckDB released Quack on 2026-05-12. The protocol turns a DuckDB instance into
an HTTP-accessible server that other DuckDB instances can connect to. DuckDB
v1.5.3 ships Quack as a core extension, but it is still beta/experimental and
the protocol, function names, and defaults may change before DuckDB v2.0.0.

Useful current behavior:

- Quack uses `quack:` URIs and defaults to port `9494`.
- Local URIs use plain HTTP by default; non-local URIs use HTTPS by default.
- Clients authenticate with either a Quack secret or explicit `TOKEN` on
  `ATTACH` / `quack_query`.
- `ATTACH 'quack:host' AS remote` exposes remote tables as a DuckDB catalog and
  forwards transactions.
- The current DuckDB Go driver is `github.com/duckdb/duckdb-go/v2`; the first
  tag carrying DuckDB v1.5.3 is `v2.10503.0`.

Primary references:

- https://duckdb.org/docs/current/quack/overview
- https://duckdb.org/docs/current/core_extensions/quack
- https://duckdb.org/2026/05/20/announcing-duckdb-153
- https://github.com/duckdb/duckdb-go

## Recommended Shape

Add a new `internal/duckdb` package, mirroring the responsibilities of
`internal/postgres` without copying implementation blindly.

The package should provide:

- Connection helpers for local DuckDB files and remote `quack:` endpoints.
- Non-secret diagnostics that redact tokens and local filesystem details.
- DuckDB DDL and schema compatibility checks.
- Push sync from SQLite to DuckDB with the same machine/project filtering
  semantics as PG push.
- A `db.Store` implementation for `duckdb serve`.
- Quack serving support for exposing a local DuckDB file when a user opts in.

Before the DuckDB `db.Store` port, extract the narrow query helpers that are
already duplicated between SQLite and PostgreSQL. This should cover dialect
differences such as placeholder style, boolean literals, timestamp/date
expressions, LIKE/ILIKE behavior, regex predicates, pagination, NULL ordering,
and safe catalog/table qualification. It should not grow into an ORM, and
backend-specific SQL should stay local where the engines genuinely differ.

The CLI should add a sibling command group:

```text
agentsview duckdb push
agentsview duckdb status
agentsview duckdb serve
agentsview duckdb quack serve
```

Configuration should be explicit and separate from PG:

```toml
[duckdb]
path = "~/.agentsview/sessions.duckdb"
url = "quack:localhost"
token = "$AGENTSVIEW_DUCKDB_TOKEN"
machine_name = "my-machine"
allow_insecure = false
projects = []
exclude_projects = []
```

Environment variables should follow the existing naming style:

```text
AGENTSVIEW_DUCKDB_PATH
AGENTSVIEW_DUCKDB_URL
AGENTSVIEW_DUCKDB_TOKEN
AGENTSVIEW_DUCKDB_MACHINE
```

## Implementation Phases

1. Prove the DuckDB driver and Quack protocol from Go. Create a small
   integration spike that opens DuckDB through `database/sql`, creates a local
   DuckDB file, starts a Quack server from one connection, attaches it from
   another connection, and verifies a read/write round trip.

1. Add config and CLI skeleton. Add `DuckDBConfig`, config-file/env loading,
   resolver defaults, command help, and empty command handlers that fail clearly
   when required settings are missing.

1. Add DuckDB schema and push sync. Port the PG mirror schema to DuckDB SQL,
   preserve local SQLite watermarks, implement full and incremental push, and
   keep project include/exclude filtering aligned with PG.

1. Add backend contract tests and shared query helpers. Use a contract suite to
   compare `db.Store` behavior across backends, then extract the common
   session-filter, child-expansion, cursor-pagination, and content-search
   scoping fragments needed before DuckDB becomes a third SQL implementation.

1. Add the DuckDB read store. Implement `db.Store` over DuckDB for sessions,
   messages, tool calls, search, secrets, metadata, analytics, trends, usage,
   stars, and pins. Start read-only for destructive session-management methods.

1. Add remote Quack serving and consuming. Support `duckdb serve` from either a
   local DuckDB file or a remote `quack:` URI. Add `duckdb quack serve` for
   exposing the local DuckDB mirror with explicit token handling and safe local
   defaults.

1. Add operational docs, Docker examples, and end-to-end validation. Document
   the beta Quack constraints, TLS expectations, remote token handling, and how
   DuckDB differs from SQLite primary mode and PG shared mode.

## Important Non-goals For The First Cut

- Do not replace SQLite as the primary file-sync archive.
- Do not make parser writes target DuckDB directly.
- Do not expose Quack beyond loopback without an explicit token and TLS/proxy
  story.
- Do not require Quack for local DuckDB file mode.
- Do not depend on DuckDB FTS parity before the read backend works; use
  substring/regex search first and add a separate search optimization task if
  needed.

## Validation Targets

- `go test ./internal/duckdb/...` with a local DuckDB file.
- `go test -tags "duckdbtest" ./internal/duckdb/...` for Quack integration.
- `go test ./internal/config ./cmd/agentsview`.
- A fixture push from SQLite to DuckDB followed by `duckdb serve` API checks for
  session list, session detail, messages, search, analytics, usage, stars, and
  pins.
- Manual Quack smoke test: local server on loopback, token-protected remote
  attach, and `duckdb serve` against the `quack:` endpoint.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/docs/huma-api-routes.md =====

# Huma API Routes

The server API is registered with Huma route groups. Keep each route group
self-contained so OpenAPI ownership stays close to runtime behavior.

## File Ownership

- Put route registration, endpoint-specific input types, response wrapper types,
  enums, and handlers in the route group file that owns the path.
- Keep `internal/server/huma_routes.go` limited to shared Huma plumbing: API
  configuration, route registration helpers, common path/query inputs, error
  conversion, schema naming, SSE/write helpers, and middleware.
- Move a helper into shared plumbing only when at least two route groups use it
  and it has no domain-specific policy.
- Do not add new typed handlers to a catch-all API file. Add a new group file
  when a new API area does not fit an existing group.

## Compatibility Guardrails

When changing route registration or generated client contracts:

- Preserve existing paths, methods, status codes, response events, and content
  types unless the change is intentional and covered by tests.
- Add or update parity tests for JSON bodies, raw downloads, multipart imports,
  SSE terminal events, and error responses touched by the change.
- Run `npm run generate:api` from `frontend/` and verify generated output only
  changes when the OpenAPI contract intentionally changed.
- Keep generated frontend code under `frontend/src/lib/api/generated/`; it is
  marked as generated in `.gitattributes` and should not be hand-edited.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/frontend/AGENTS.md =====

<!--VITE PLUS START-->

# Using Vite+, the Unified Toolchain for the Web

This project is using Vite+, a unified toolchain built on top of Vite, Rolldown,
Vitest, tsdown, Oxlint, Oxfmt, and Vite Task. Vite+ wraps runtime management,
package management, and frontend tooling in a single global CLI called `vp`.
Vite+ is distinct from Vite, and it invokes Vite through `vp dev` and
`vp build`. Run `vp help` to print a list of commands and `vp <command> --help`
for information about a specific command.

Docs are local at `node_modules/vite-plus/docs` or online at
https://viteplus.dev/guide/.

## Review Checklist

- [ ] Run `vp install` after pulling remote changes and before getting started.
- [ ] Run `vp check` and `vp test` to format, lint, type check and test changes.
- [ ] Check if there are `vite.config.ts` tasks or `package.json` scripts
  necessary for validation, run via `vp run <script>`.
- [ ] If setup, runtime, or package-manager behavior looks wrong, run
  `vp env doctor` and include its output when asking for help.

<!--VITE PLUS END-->


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/internal/duckdb/README.md =====

# DuckDB Backend

This package implements the optional DuckDB mirror backend. SQLite remains the
primary archive for parser ingestion and file sync; DuckDB is populated by
`agentsview duckdb push` and read by `agentsview duckdb serve`.

The backend supports two read paths:

- local file mode via `[duckdb].path` or `AGENTSVIEW_DUCKDB_PATH`
- remote Quack mode via `AGENTSVIEW_DUCKDB_URL` plus `AGENTSVIEW_DUCKDB_TOKEN`

Quack is treated as beta infrastructure. Serving defaults to loopback, uses an
explicit or generated token, and rejects plain non-loopback binds unless
`--allow-insecure` is set. Remote operators should prefer TLS or a trusted
tunnel/proxy.

The DuckDB schema intentionally avoids `TIMESTAMP DEFAULT current_timestamp`
columns because current Quack attach rejects catalogs with those dynamic
defaults. Writers supply `current_timestamp` explicitly where the mirror needs a
created timestamp. Existing mirrors are additively migrated by `EnsureSchema`.

Search currently keeps substring/regex fallback behavior. The DuckDB FTS
extension is available locally in the pinned runtime, but BM25 lookup does not
resolve through Quack-attached catalogs, so indexed DuckDB search is deferred
until local and remote behavior line up.

Run the local file smoke test with:

```bash
go test -tags fts5 ./internal/duckdb -v
```

Run the Quack loopback integration test with:

```bash
go test -tags duckdbtest ./cmd/agentsview ./internal/duckdb -run Quack -v
```

The Quack test starts a loopback server with an explicit token, attaches it from
a second DuckDB connection, verifies a remote read, writes through the attached
catalog, and stops the server in test cleanup.

Run the DuckDB-backed browser smoke test with:

```bash
make e2e-duckdb
```


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/agentsview/internal/parser/testdata/kiro_sqlite/malformed_payload.txt =====

{"conversation_id":"broken-session","history":[
