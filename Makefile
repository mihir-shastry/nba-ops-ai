.PHONY: install data backend frontend dev stop

install:
	pip install -r requirements.txt

data:
	python data_pipeline.py

backend:
	uvicorn backend.main:app --reload --port 8000

frontend:
	streamlit run app.py

dev:
	@echo "Starting NBA Operations AI Assistant..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:8501"
	@echo "API Docs: http://localhost:8000/docs"
	@echo ""
	@python -m backend.main &
	@sleep 3
	@streamlit run app.py

stop:
	@pkill -f "uvicorn backend.main" || true
	@pkill -f "streamlit run app.py" || true
	@echo "Servers stopped"
