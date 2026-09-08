"""Shared GuideCheck code-level constants."""

# Release identity is independent of engine and anchored self-guide identities.
GUIDECHECK_VERSION = "1.0.0"
LATEST_RELEASED_PROFILE_VERSION = "1.0.0"
SELF_GUIDE_VERSION = "0.7.1"
SELF_GUIDE_PROFILE_VERSION = "0.7.1"
LEGACY_ENGINE_VERSION = "0.7.1"
STRICT_ENGINE_VERSION = "1.0.0"
CORRECTED_ENGINE_VERSION = "2.0.0"

GUIDE_PROFILE = "human-verifiable-assistant-guide"
GUIDE_PROFILE_VERSION = LATEST_RELEASED_PROFILE_VERSION

VERIFIER_PROFILE = "human-verifiable-assistant-guide-verifier"
VERIFIER_PROFILE_VERSION = LEGACY_ENGINE_VERSION

LOCAL_VERIFIER_NAME = "guidecheck-reference-local"
HOSTED_VERIFIER_NAME = "guidecheck-hosted"
STANDARD_PRIMARY_VERIFIER = "https://guidecheck.org/verify"

HOSTED_USER_AGENT = f"{HOSTED_VERIFIER_NAME}/{LEGACY_ENGINE_VERSION} (+https://guidecheck.org/verify/)"
