"""Pure, request-local selection of explicitly supported profile policies."""
from dataclasses import dataclass
import hashlib
import re

LEGACY_VERSIONS = frozenset({"0.1.0", "0.2.0", "0.3.0", "0.3.1", "0.4.0", "0.5.0", "0.6.0", "0.7.0", "0.7.1"})
STRICT_PROFILE_VERSION = "1.0.0"
SUPPORTED_VERSIONS = LEGACY_VERSIONS | {STRICT_PROFILE_VERSION}
PROFILE_NAME = "human-verifiable-assistant-guide"
_RELEASE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?")


class ProfileError(ValueError):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


@dataclass(frozen=True)
class ProfileSelection:
    declared_version: str | None
    policy_version: str
    guide_sha256: str

    @property
    def strict(self):
        return self.policy_version == STRICT_PROFILE_VERSION


def policy_key(value):
    if not isinstance(value, str) or not _RELEASE.fullmatch(value):
        raise ProfileError("profile-version-unsupported", "profile version must name a supported release, optionally with valid build metadata")
    key = value.split("+", 1)[0]
    if key not in SUPPORTED_VERSIONS:
        raise ProfileError("profile-version-unsupported", f"unsupported guide profile version: {value}")
    return key


def select_profile(data: bytes, required_profile_version=None):
    # Collect selectors only within metadata, including malformed near-markers
    # that the legacy parser diagnoses. Never use its last-value-wins dictionary
    # to choose between conflicting versions.
    versions, names = [], []
    active = False
    for line in data.decode("utf-8", errors="replace").splitlines():
        marker = line.strip().lower()
        if marker == "[assistant-guide-metadata]":
            active = True
        elif marker == "[/assistant-guide-metadata]":
            active = False
        elif active and ":" in line:
            field, value = line.split(":", 1)
            if field.strip().lower() == "profile-version":
                versions.append(value[1:] if value.startswith(" ") else value)
            elif field.strip().lower() == "profile":
                names.append(value.strip())
    if len(set(versions)) > 1 or len(set(names)) > 1:
        raise ProfileError("profile-version-ambiguous", "conflicting guide profile selectors")
    declared = versions[0] if versions else None
    selected = policy_key(declared) if declared is not None else "0.7.1"
    # Malformed unambiguous old selectors still receive legacy diagnostics.
    if selected == STRICT_PROFILE_VERSION and (len(versions) != 1 or names != [PROFILE_NAME]):
        raise ProfileError("profile-version-ambiguous", "strict profile requires one profile name and one version selector")
    if required_profile_version is not None:
        required = policy_key(required_profile_version)
        if declared is None or required != selected:
            raise ProfileError("profile-version-requirement-mismatch", "guide declaration does not satisfy the required profile version")
    return ProfileSelection(declared, selected, hashlib.sha256(data).hexdigest())


def check_legacy_manifest(selection, manifest_text):
    if selection.strict or not manifest_text:
        return
    for line in manifest_text.splitlines():
        if ":" not in line:
            continue
        field, value = line.split(":", 1)
        if field.strip().lower() == "profile-version":
            # Old-only optional metadata retains baseline handling. A new or
            # unsupported major must not be hidden by a legacy guide selector.
            token = value.strip()
            if not token.startswith("0."):
                raise ProfileError("profile-version-ambiguous", "legacy guide and manifest have contradictory profile versions")
