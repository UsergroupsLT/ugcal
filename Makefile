pytest := py.test
python := python
flake8 := flake8


.PHONY: run
run:
	$(python) ugcal.py

.PHONY: test
test:
	$(pytest)

.PHONY: lint
lint:
	$(flake8) .
