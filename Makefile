configure:
	pip install -r requirements-test.txt

test: flake8 pylint test-unit test-functional

flake8: configure
	@echo
	@echo "### Running flake8"
	@echo
	flake8 efu
	flake8 tests

pylint: configure
	@echo
	@echo "### Running pylint"
	@echo
	pylint efu --disable=R,C

test-unit:
	@echo
	@echo "### Running unit tests"
	@echo
	python3 setup.py pytest --addopts ' --cache-clear -v --cov . --cov-report=xml --junitxml=test-report.xml --ignore tests/functional --ignore venv-test'


test-functional: configure
	@echo
	@echo "### Running functional tests inside virtualenv venv-test"
	@echo
	rm -rf venv-test
	@virtualenv -p `which python` venv-test
	@( \
		. venv-test/bin/activate; \
		pip install .; \
		py.test --cache-clear -v tests/functional --basetemp=venv-test; \
		deactivate; \
	)

egg: test
	python3 setup.py bdist_egg

wheel: test
	python3 setup.py bdist_wheel

dist: egg wheel
