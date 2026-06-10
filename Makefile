.PHONY: eval verify-fixtures validate-contracts test-contract-schema-validation test-parser-edge-cases check-guide-artifacts check-version-sync test-fetch-safety test-hosted-anchors test-hosted-api test-fetch-replay test-cli-contract test release-archive conformance-kit

VERSION := $(shell python3 -c "import sys; sys.path.insert(0, 'scripts'); from guidecheck_constants import GUIDECHECK_VERSION; print(GUIDECHECK_VERSION)")

eval:
	python3 scripts/eval_guidecheck.py

verify-fixtures:
	python3 scripts/check_reference_verifier.py

validate-contracts:
	python3 scripts/validate_contracts.py

test-contract-schema-validation:
	python3 scripts/test_contract_schema_validation.py

test-parser-edge-cases:
	python3 scripts/test_parser_edge_cases.py

check-guide-artifacts:
	python3 scripts/check_guide_artifacts.py

check-version-sync:
	python3 scripts/check_version_sync.py

test-fetch-safety:
	python3 scripts/test_fetch_safety.py

test-hosted-anchors:
	python3 scripts/test_hosted_anchors.py

test-hosted-api:
	python3 scripts/test_hosted_api.py

test-fetch-replay:
	python3 scripts/test_fetch_replay.py

test-cli-contract:
	python3 scripts/test_cli_contract.py

test: eval verify-fixtures validate-contracts test-contract-schema-validation test-parser-edge-cases check-guide-artifacts check-version-sync test-fetch-safety test-hosted-anchors test-hosted-api test-fetch-replay test-cli-contract

# Full source archive for a GitHub release, matching prior build/ layout.
release-archive:
	mkdir -p build
	git archive --format=tar.gz --prefix=guidecheck-$(VERSION)/ -o build/guidecheck-$(VERSION).tar.gz HEAD
	git archive --format=zip --prefix=guidecheck-$(VERSION)/ -o build/guidecheck-$(VERSION).zip HEAD
	cd build && shasum -a 256 guidecheck-$(VERSION).tar.gz guidecheck-$(VERSION).zip > guidecheck-$(VERSION).SHA256SUMS
	cat build/guidecheck-$(VERSION).SHA256SUMS

# Standalone conformance kit: the fixture corpus and schemas an independent
# verifier implementation targets, pinned to one profile version.
conformance-kit:
	mkdir -p build
	git archive --format=tar.gz --prefix=guidecheck-conformance-kit-$(VERSION)/ \
		-o build/guidecheck-conformance-kit-$(VERSION).tar.gz HEAD \
		fixtures schemas finding-ids.md verifier-conformance.md CHANGELOG.md
	cd build && shasum -a 256 guidecheck-conformance-kit-$(VERSION).tar.gz > guidecheck-conformance-kit-$(VERSION).SHA256SUMS
	cat build/guidecheck-conformance-kit-$(VERSION).SHA256SUMS
