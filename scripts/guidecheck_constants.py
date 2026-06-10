"""Shared GuideCheck code-level constants."""

GUIDECHECK_VERSION = "0.6.0"

GUIDE_PROFILE = "human-verifiable-assistant-guide"
GUIDE_PROFILE_VERSION = GUIDECHECK_VERSION

VERIFIER_PROFILE = "human-verifiable-assistant-guide-verifier"
VERIFIER_PROFILE_VERSION = GUIDECHECK_VERSION

LOCAL_VERIFIER_NAME = "guidecheck-reference-local"
HOSTED_VERIFIER_NAME = "guidecheck-hosted"
STANDARD_PRIMARY_VERIFIER = "https://guidecheck.org/verify"

HOSTED_USER_AGENT = f"{HOSTED_VERIFIER_NAME}/{GUIDECHECK_VERSION} (+https://guidecheck.org/verify/)"
