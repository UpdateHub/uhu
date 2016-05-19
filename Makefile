test:
	python3 setup.py pytest --addopts '-v --cov=efu --cov-report=xml --junitxml=test-report.xml --pep8'

egg: test
	python3 setup.py bdist_egg

wheel: test
	python3 setup.py bdist_wheel

dist: egg wheel
