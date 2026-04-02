# Eatsplorer — Full Project

> Eatsplorer: Enhancing Food Tourism in Legazpi City Through a Conversational AI Chatbot
> Using Aspect-Based Sentiment Analysis
> Bicol University College of Science — Department of Computer Science

---

## Project Layout

```
eatsplorer/
├── chatbot/          ← RASA (NLU, stories, custom actions)
├── web_backend/      ← FastAPI (REST API + RASA proxy)
├── web_frontend/     ← React + Vite (UI)
└── README.md
```

```
Browser  (React :5173)
  └─→  FastAPI  (:8000)
          └─→  RASA  (:5005)
                  └─→  RASA Actions  (:5055)
```

---

## Before You Start — Two Things

1. You need Python 3.10 exactly for RASA.
   Python 3.11 and above will fail.
   Download from: https://www.python.org/downloads/release/python-3100/
   During install on Windows, check "Add Python to PATH".

2. RASA and FastAPI use incompatible pydantic versions (v1 vs v2)
   so they must be installed in separate virtual environments.

---

## One-Time Setup

### Step 1 — Chatbot venv (Python 3.10, Windows)

Open a terminal in the eatsplorer/ folder and run:

    py -3.10 -m venv venv_chatbot
    venv_chatbot\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r chatbot\requirements.txt

This will take a while — TensorFlow is large (~500MB).

Note: tensorflow-text is intentionally excluded from the Windows
requirements because no Windows wheel exists for version 2.12.
RASA's own metadata marks it as non-Windows too, so this is fine.

### Step 2 — Train the RASA model

    venv_chatbot\Scripts\activate
    cd chatbot
    rasa train
    cd ..

This generates a model file in chatbot\models\

### Step 3 — Web backend venv

    py -m venv venv_web
    venv_web\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r web_backend\requirements.txt
    deactivate

### Step 4 — Frontend

    cd web_frontend
    npm install
    cd ..

---

## Running the Full System (4 terminals)

Open 4 separate Command Prompt or PowerShell windows
from the eatsplorer\ folder.

Terminal 1 — RASA Actions server
    venv_chatbot\Scripts\activate
    cd chatbot
    rasa run actions

Terminal 2 — RASA REST API
    venv_chatbot\Scripts\activate
    cd chatbot
    rasa run --enable-api --cors "*"

Terminal 3 — FastAPI backend
    venv_web\Scripts\activate
    cd web_backend
    uvicorn main:app --reload --port 8000

Terminal 4 — React frontend
    cd web_frontend
    npm run dev

Then open http://localhost:5173

Terminals 1 and 2 must both be running for chat to work.
The restaurant browser works with just Terminals 3 and 4.

---

## Thesis Evaluation Metrics

    venv_chatbot\Scripts\activate
    cd chatbot

    # NLU metrics: accuracy, precision, recall, F1, confusion matrix
    rasa test nlu --nlu tests\test_nlu.yml --out results\nlu\

    # 5-fold cross-validation (recommended for thesis reporting)
    rasa test nlu --nlu data\nlu.yml --cross-validation --folds 5 --out results\cv\

    # Dialogue metrics
    rasa test --stories tests\test_stories.yml --out results\core\

Results are saved to chatbot\results\

---

## FastAPI Endpoints

    POST  /api/chat                     send a message, get RASA response
    GET   /api/restaurants              list restaurants (filter by aspect, polarity, search, limit)
    GET   /api/restaurants/{name}       single restaurant detail
    GET   /api/stats                    database-level stats
    GET   /api/health                   health check

Swagger UI: http://localhost:8000/docs (when backend is running)


## CHANGES MADE TO UI

# In App.css
''' css
.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  height: 80px; /* Added a fixed height to the parent */
}

.header-icon {
  display: block;
  max-height: 75%; /* Now this knows to be 100% of 80px */
  width: auto;
}

.header-logo {
  height: 5vh; /* Swapped max-height: 100% for a fixed pixel value */
  width: auto; 
  object-fit: contain;
  margin-bottom: 0;
}
'''

## In "Header" inside App.jsx
''' html
<div className="header-brand">
  <img className="header-icon" src="/eatsplorer_icon_logo.png" alt="Eatsplorer Logo" />
  <div>
    <img className="header-logo" src="/eatsplorer_long_logo.png" alt="Eatsplorer Long Logo" />
    <p className="header-sub">Legazpi City Dining Discovery</p>
  </div>
</div>
'''
