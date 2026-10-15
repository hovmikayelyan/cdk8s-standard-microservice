PY := .venv/bin/python
export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1

.PHONY: install synth synth-prod test update-snapshots clean

install:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

synth:
	ENVIRONMENT=dev $(PY) main.py ../dist/dev

synth-prod:
	ENVIRONMENT=prod $(PY) main.py ../dist/prod

test:
	$(PY) -m pytest -q

update-snapshots:
	$(PY) -m pytest -q --snapshot-update

clean:
	rm -rf ../dist
