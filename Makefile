configure:
	pip install -r requirements-test.txt

test: pylint test-unit test-functional

pylint: configure
	@echo
	@echo "### Running pylint code checker"
	@echo
	pylint efu --disable=R,C

test-unit:
	@echo
	@echo "### Running unit tests and PEP 8 checker"
	@echo
	python3 setup.py pytest --addopts '--pep8 --cache-clear -v --cov . --cov-report=xml --junitxml=test-report.xml --ignore tests/functional --ignore venv-test'

test-functional: configure
	@echo
	@echo "### Running functional tests inside virtualenv venv-test"
	@echo
	rm -rf venv-test
	@virtualenv -p `which python` venv-test
	@( \
		. venv-test/bin/activate && \
		pip install . && \
		py.test --cache-clear -v tests/functional && \
		deactivate; \
	)

egg: test
	python3 setup.py bdist_egg

wheel: test
	python3 setup.py bdist_wheel

dist: egg wheel
