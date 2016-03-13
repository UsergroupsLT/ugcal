pytest := py.test
python := python

.PHONY: run
run:
	$(python) ugcal.py

.PHONY: test
test:
	$(pytest)
