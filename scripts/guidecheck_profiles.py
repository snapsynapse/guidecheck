"""Pure, request-local selection of explicitly supported profile policies."""
from dataclasses import dataclass
import hashlib
import re

LEGACY_VERSIONS = frozenset({"0.1.0", "0.2.0", "0.3.0", "0.3.1", "0.4.0", "0.5.0", "0.6.0", "0.7.0", "0.7.1"})
STRICT_PROFILE_VERSION = "1.0.0"
CORRECTED_PROFILE_VERSION = "2.0.0"
SUPPORTED_VERSIONS = LEGACY_VERSIONS | {STRICT_PROFILE_VERSION, CORRECTED_PROFILE_VERSION}
# Draft, unreleased. Selected only for a caller that passes allow_draft, which
# today is the local reference CLI. Every other caller, the hosted verifier
# included, keeps refusing it as unsupported.
DRAFT_PROFILE_VERSION = "3.0.0"
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

    @property
    def corrected(self):
        return self.policy_version == CORRECTED_PROFILE_VERSION

    @property
    def restricted(self):
        return self.policy_version == DRAFT_PROFILE_VERSION

    @property
    def modern(self):
        return self.policy_version in {STRICT_PROFILE_VERSION, CORRECTED_PROFILE_VERSION, DRAFT_PROFILE_VERSION}


def policy_key(value, *, allow_draft=False):
    if not isinstance(value, str) or not _RELEASE.fullmatch(value):
        raise ProfileError("profile-version-unsupported", "profile version must name a supported release, optionally with valid build metadata")
    if allow_draft and value == DRAFT_PROFILE_VERSION:
        # Exact only. Build metadata does not select the draft profile.
        return DRAFT_PROFILE_VERSION
    key = value.split("+", 1)[0]
    if key not in SUPPORTED_VERSIONS:
        raise ProfileError("profile-version-unsupported", f"unsupported guide profile version: {value}")
    return key


def select_profile(data: bytes, required_profile_version=None, *, allow_draft=False):
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
    selected = policy_key(declared, allow_draft=allow_draft) if declared is not None else "0.7.1"
    if selected == DRAFT_PROFILE_VERSION:
        # The draft profile is declared by exact bytes only. Its own selector
        # decides; a guide it does not accept is ambiguous, never re-read as
        # another profile. A guide over its size limit is refused by the
        # evaluator before that selector runs.
        import guidecheck_restricted as restricted

        if len(data) <= restricted.MAX_GUIDE_BYTES and not restricted.declares_profile(data):
            raise ProfileError("profile-version-ambiguous", "draft profile 3.0.0 requires one exact metadata block with one profile name and one version selector")
    # Malformed unambiguous old selectors still receive legacy diagnostics.
    if selected == STRICT_PROFILE_VERSION and (len(versions) != 1 or names != [PROFILE_NAME]):
        raise ProfileError("profile-version-ambiguous", "strict profile requires one profile name and one version selector")
    if selected == CORRECTED_PROFILE_VERSION and (len(versions) != 1 or names != [PROFILE_NAME]):
        raise ProfileError("profile-version-ambiguous", "corrected profile requires one profile name and one version selector")
    if required_profile_version is not None:
        required = policy_key(required_profile_version, allow_draft=allow_draft)
        if declared is None or required != selected:
            raise ProfileError("profile-version-requirement-mismatch", "guide declaration does not satisfy the required profile version")
    return ProfileSelection(declared, selected, hashlib.sha256(data).hexdigest())


def check_legacy_manifest(selection, manifest_text):
    if selection.modern or not manifest_text:
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
