# Kingston Waste Collection Assistant

Hackathon prototype that answers Kingston waste collection questions in plain language.

## Run backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="YOUR_KEY"  # optional
python backend.py

## Run frontend
cd frontend
python3 -m http.server 8000

Open http://127.0.0.1:8000
