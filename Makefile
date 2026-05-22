.PHONY: eval verify-fixtures test-fetch-safety

eval:
	python3 scripts/eval_guidecheck.py

verify-fixtures:
	python3 scripts/check_reference_verifier.py

test-fetch-safety:
	python3 scripts/test_fetch_safety.py
