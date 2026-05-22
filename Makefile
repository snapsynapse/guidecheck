.PHONY: eval verify-fixtures

eval:
	python3 scripts/eval_guidecheck.py

verify-fixtures:
	python3 scripts/check_reference_verifier.py
