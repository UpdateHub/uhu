init:
	pip install -r requirements-test.txt

test: init pep8 test-unit test-functional

pep8:
	pep8 --show-source efu tests

test-unit:
	python3 setup.py pytest --addopts 'tests/unit -v --cov=efu --cov-report=xml --junitxml=test-report.xml'

test-functional:
	pip install .
	py.test -v tests/functional

egg: test
	python3 setup.py bdist_egg

wheel: test
	python3 setup.py bdist_wheel

dist: egg wheel
