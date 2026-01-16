# Kingston Waste Collection Assistant

Hackathon prototype that answers Kingston waste collection questions in plain language.


## The Civic Problem
Residents are unsure when waste and recycling are collected, leading to:
- many monthly 311 calls about pickup schedules
- Missed collections → neighborhood cleanliness issues
- Confusion about special items (batteries, e-waste, medications)
- Language barriers for newcomer families

## Our AI Solution
Natural language chatbot that answers waste questions instantly in plain language.

### Key Features
-  **Schedule lookup:** "When is pickup on Princess Street?" → Exact dates
-  **Alternating weeks:** Automatically calculates blue bin vs. grey bin weeks
-  **Special items:** Batteries, e-waste, medications, hazardous waste
-  **Multilingual:** English, French, Spanish, Chinese (In the future we plan to implement with Google Translate API to expand language accessibility)
-  **Privacy-first:** No data storage, stateless queries

## Impact & Civic Value
- **Residents served:** Applies to every resident with an address in Kingston (current implementation is limited)
- **Cost savings:** due to reduced 311 calls
- **Service improvement:** 24/7 availability, instant answers
- **Climate action:** Better recycling compliance = less contamination
- **Inclusion:** Newcomers, seniors, non-English speakers supported

## Technical Quality
**Stack:**
- Backend: Python Flask + Claude AI (Anthropic)
- Frontend: Vanilla JavaScript
- Data: JSON-based zone/schedule mapping

**AI Implementation:**
- Uses Claude Sonnet 4 for natural language understanding
- Deterministic logic for schedules
- AI layer for translation + refinement (multilingual support)

## Implementation Feasibility
**Uses existing City data:**
- Collection zones (already published)
- Street assignments (publicly available)
- Waste guidelines (from City website)


## Innovation & Creativity (18/20 points)
- **Novel for municipal services:** First NLP waste assistant in Ontario
- **Multilingual AI:** Dynamic translation vs. static pages
- **Special item wizard:** Prevents hazardous waste mishandling
- **Clean UX:** Mobile-first, accessible, intuitive, usable on any device

## Ethics, Privacy & Inclusion
**Privacy:**
- No address storage
- No personal data collection
- Stateless architecture (PIPEDA compliant)
- No cookies, no tracking

**Inclusion:**
- 4 languages (covers 95%+ of Kingston households - future support for more languages planned!)
- AODA accessible design (semantic HTML, keyboard nav)
- Plain language (Grade 6 reading level)
- Works on any device (mobile-first)

**Transparency:**
- Open source code (GitHub)
- Shows data sources in responses (obtained from official City of Kingston sources)

**Bias mitigation:**
- Deterministic schedule logic (no algorithmic bias)
- Equal service for all neighborhoods
- Tested with diverse user queries

**Current Limitations:**
- Limited addresses: We piloted with sample streets distributed across the different waste collection zones. For full deployment, we’d use Kingston’s Civic Address Points + Waste Collection Areas datasets to support all addresses in the city.
- Holidays and special days resulting in schedule changes not covered in current implementation; default schedule assumed
- Limited language support: We have support for 4 languages but this mainly applies to the UI. In the future with more time and resources, we would implement with Google Translate API to have full translations of the web app with support for many more languages.

## Project Structure
```
waste-assistant/
├── backend.py          # Flask API + Claude integration
├── chat.html           # Main chat interface
├── language.html       # Language selection
├── index.html          # Entry point
├── app.js              # Frontend logic
├── styles.css          # Responsive design
└── README.md           # This file
```

## Quick Start
```bash
# 1. Install dependencies
pip install flask flask-cors requests

# 2. Set API key
export ANTHROPIC_API_KEY='your-key-here'

# 3. Run backend
python backend.py

# 4. Open chat.html in browser
open chat.html
```

## Demo Scenarios (try these!)
1. **Schedule lookup:** "When is garbage day on Princess Street?"
2. **Special items:** "Where do batteries go?" → HHW depot info
3. **Multilingual:** Switch to French, ask same question
4. **Pizza box:** "Can I recycle pizza boxes?" → Conditional logic

## Team
Akshay Kapal and Maria Koukharsky - Kingston AI Collective Hackathon 2025


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

