test: test-unit

test-unit:
	python3 setup.py pytest --addopts '-v --cov=efu --cov-report=xml --junitxml=test-report.xml --pep8 --ignore ./tests/functional'

test-functional:
	py.test ./tests/functional

egg: test
	python3 setup.py bdist_egg

wheel: test
	python3 setup.py bdist_wheel

dist: egg wheel
