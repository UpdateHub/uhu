test-module:
	py.test $(test) --cov=${cov} --cov-report=term-missing

unit:
	py.test tests/unit --pep8 --cov=efu --cov-report=term-missing

functional:
	py.test tests/functional

linter:
	pylint efu --disable=R,C
