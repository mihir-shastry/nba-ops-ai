.PHONY: install data backend frontend frontend-streamlit dev dev-streamlit stop help

# Default target
help:
	@echo "NBA Operations AI Assistant"
	@echo "==========================="
	@echo ""
	@echo "Quick Start:"
	@echo "  make install          - Install Python dependencies"
	@echo "  make data             - Build/refresh the database"
	@echo "  make backend          - Start the API server"
	@echo "  make frontend         - Start the Next.js UI (port 3000)"
	@echo "  make frontend-streamlit - Start the Streamlit UI (legacy)"
	@echo "  make dev              - Start backend + Next.js frontend"
	@echo "  make dev-streamlit    - Start backend + Streamlit frontend"
	@echo ""
	@echo "Configuration:"
	@echo "  Create a .env file with: GEMINI_API_KEY=your_key_here"
	@echo "  Get yours at: https://aistudio.google.com/apikey"
	@echo ""
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Next.js Frontend: http://localhost:3000"
	@echo "Streamlit Frontend: http://localhost:8501"

install:
	pip install -r requirements.txt
	cd frontend && npm install

data:
	python data_pipeline.py

backend:
	uvicorn backend.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

frontend-streamlit:
	streamlit run app.py

dev:
	@echo "Starting NBA Operations AI Assistant..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "⚠️  Make sure .env file exists with GEMINI_API_KEY!"
	@echo ""
	@python -m backend.main &
	@sleep 3
	@cd frontend && npm run dev

dev-streamlit:
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
	@pkill -f "next dev" || true
	@echo "Servers stopped"
