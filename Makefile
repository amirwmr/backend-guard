# BEGIN managed-by-backend-guard:makefile
BACKEND_GUARD = $(shell if command -v uv >/dev/null 2>&1 && uv run backend-guard --help >/dev/null 2>&1; then \
	echo "uv run backend-guard"; \
	elif [ -x ./.venv/bin/backend-guard ] && ./.venv/bin/backend-guard --help >/dev/null 2>&1; then \
	echo ./.venv/bin/backend-guard; \
	elif command -v backend-guard >/dev/null 2>&1; then \
	echo backend-guard; \
	elif command -v python3 >/dev/null 2>&1 && python3 -m backend_guard --help >/dev/null 2>&1; then \
	echo "python3 -m backend_guard"; \
	elif command -v python >/dev/null 2>&1 && python -m backend_guard --help >/dev/null 2>&1; then \
	echo "python -m backend_guard"; \
	else \
		echo backend-guard; \
	fi)

guard-init:
	$(BACKEND_GUARD) init

guard-audit:
	$(BACKEND_GUARD) audit

guard-fix:
	$(BACKEND_GUARD) fix

guard-doctor:
	$(BACKEND_GUARD) doctor
# END managed-by-backend-guard:makefile
