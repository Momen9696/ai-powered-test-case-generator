.PHONY: test test-backend test-frontend build e2e

test: test-backend test-frontend

test-backend:
	cd backend && .venv/bin/pytest

test-frontend:
	cd frontend && npm test

build:
	cd frontend && npm run build

e2e:
	cd frontend && npm run e2e
