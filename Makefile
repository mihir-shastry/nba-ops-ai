.PHONY: install data backend frontend dev stop help

# Default target
help:
	@echo "NBA Operations AI Assistant"
	@echo "==========================="
	@echo ""
	@echo "Quick Start:"
	@echo "  make install    - Install dependencies"
	@echo "  make data       - Build/refresh the database"
	@echo "  make backend    - Start the API server"
	@echo "  make frontend   - Start the Streamlit UI"
	@echo "  make dev        - Start both backend + frontend"
	@echo ""
	@echo "Configuration:"
	@echo "  Create a .env file with: GEMINI_API_KEY=your_key_here"
	@echo "  Get yours at: https://aistudio.google.com/apikey"
	@echo ""
	@echo "API Docs: http://localhost:8000/docs"

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
	@echo "⚠️  Make sure .env file exists with GEMINI_API_KEY!"
	@echo ""
	@python -m backend.main &
	@sleep 3
	@streamlit run app.py

stop:
	@pkill -f "uvicorn backend.main" || true
	@pkill -f "streamlit run app.py" || true
	@echo "Servers stopped"
