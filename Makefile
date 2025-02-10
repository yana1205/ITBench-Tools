
.PHONY: test
test: test-unit test-e2e-filesystem test-e2e-postgresql

.PHONY: test-unit
test-unit:
	@echo "Running Unit Tests"
	@pytest tests --ignore=tests/e2e

.PHONY: test-e2e-filesystem
test-e2e-filesystem:
	@echo "Running E2E tests with storage type: filesystem"
	@DEFAULT_MAX_INTERVAL=1 DEFAULT_MAX_RETRY=1 pytest tests/e2e --storage-type filesystem

.PHONY: test-e2e-postgresql
test-e2e-postgresql:
	@echo "Running E2E tests with storage type: postgresql"
	@echo "Starting Docker services for PostgreSQLDB"
	@docker-compose -f ./postgresql/docker-compose.yaml up -d; \
	trap 'echo "Stopping Docker services for PostgreSQLDB"; docker-compose -f ./postgresql/docker-compose.yaml down' EXIT; \
	DEFAULT_MAX_INTERVAL=1 DEFAULT_MAX_RETRY=1 pytest tests/e2e --storage-type postgresql

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