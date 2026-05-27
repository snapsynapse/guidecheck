.PHONY: eval verify-fixtures validate-contracts test-contract-schema-validation test-parser-edge-cases check-guide-artifacts test-fetch-safety test-hosted-api test-fetch-replay test-cli-contract test

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

test-fetch-safety:
	python3 scripts/test_fetch_safety.py

test-hosted-api:
	python3 scripts/test_hosted_api.py

test-fetch-replay:
	python3 scripts/test_fetch_replay.py

test-cli-contract:
	python3 scripts/test_cli_contract.py

test: eval verify-fixtures validate-contracts test-contract-schema-validation test-parser-edge-cases check-guide-artifacts test-fetch-safety test-hosted-api test-fetch-replay test-cli-contract
