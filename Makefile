pytest := py.test
python := python
flake8 := flake8


.PHONY: run
run:
	$(python) ugcal.py

.PHONY: test
test: clean
	$(pytest)

.PHONY: lint
lint:
	$(flake8) .

.PHONY: clean
clean:
	@find  -name "*.pyc" -delete

.PHONY: bootstrap
bootstrap:
	pip install -r requirements.txt
	pip install -r requirements-test.txt
