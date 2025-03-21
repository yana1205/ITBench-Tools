
.PHONY: test
test:
	@echo "Running Unit Tests"
	@pytest tests

.PHONY: format
format:
	python -m black .

# Direct dependency is not allowed for Pypi packaging even if the dependant module is defined as extra dependencies. 
# Workaround: Move to manual installation by make
.PHONY: install-detect-descret
install-detect-descret:
	python -m pip install detect-secrets@git+https://github.com/ibm/detect-secrets.git@master#egg=detect-secrets

.PHONY: clean
clean:
	@rm -rf build *.egg-info dist
	python -m pyclean -v .