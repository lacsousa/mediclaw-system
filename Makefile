.PHONY: dev backend frontend

dev:
	@echo "Iniciando backend e frontend..."
	@trap 'kill %1 %2 2>/dev/null; exit' INT TERM; \
	(cd django-api && uv run python manage.py runserver) & \
	(cd react-painel && npm run dev) & \
	wait

backend:
	cd django-api && uv run python manage.py runserver

frontend:
	cd react-painel && npm run dev
