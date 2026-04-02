"""
Eatsplorer FastAPI Backend
- Proxies chat messages to the RASA REST webhook
- Serves restaurant data directly from restaurant_scores.csv
- CORS enabled for the React frontend
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx
import pandas as pd
import math
import os

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────

app = FastAPI(
    title="Eatsplorer API",
    description="Backend for the Eatsplorer conversational AI chatbot for Legazpi City dining discovery.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RASA_URL = os.getenv("RASA_URL", "http://localhost:5005")
DATA_PATH = os.path.join(os.path.dirname(__file__), "restaurant_scores.csv")

# ─────────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────────

DB: pd.DataFrame = pd.read_csv(DATA_PATH)

ASPECT_COLS = {
    "food_quality": ("food_quality_avg", "food_quality_polarity", "food_quality_review_count"),
    "service":      ("service_avg",      "service_polarity",      "service_review_count"),
    "ambiance":     ("ambiance_avg",     "ambiance_polarity",     "ambiance_review_count"),
    "price_value":  ("price_value_avg",  "price_value_polarity",  "price_value_review_count"),
}

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def safe_float(val) -> Optional[float]:
    """Return float or None — handles NaN, None, and strings like 'N/A'."""
    try:
        if val is None:
            return None
        f = float(val)
        if math.isnan(f):
            return None
        return round(f, 4)
    except (TypeError, ValueError):
        return None

def safe_int(val, default: int = 0) -> int:
    """Return int or default — handles NaN and None."""
    try:
        if val is None:
            return default
        f = float(val)
        if math.isnan(f):
            return default
        return int(f)
    except (TypeError, ValueError):
        return default

def safe_str(val) -> Optional[str]:
    """Return str or None — handles NaN."""
    if val is None:
        return None
    try:
        if isinstance(val, float) and math.isnan(val):
            return None
    except TypeError:
        pass
    s = str(val).strip()
    return None if s in ("", "nan", "None", "N/A") else s

# ─────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    sender: str = "user"
    message: str

class BotResponse(BaseModel):
    text: str
    image: Optional[str] = None
    buttons: Optional[list] = None

class AspectScore(BaseModel):
    avg: Optional[float] = None
    polarity: Optional[str] = None
    review_count: int = 0

class Restaurant(BaseModel):
    restaurant_name: str
    food_quality: AspectScore
    service: AspectScore
    ambiance: AspectScore
    price_value: AspectScore
    overall_score: Optional[float] = None
    overall_polarity: Optional[str] = None
    total_reviews: int = 0
    aspects_scored: int = 0

class StatsResponse(BaseModel):
    total_restaurants: int
    positive_count: int
    neutral_count: int
    negative_count: int
    avg_overall_score: float
    fully_scored_count: int
    aspect_coverage: dict

# ─────────────────────────────────────────────
# Row Serializer
# ─────────────────────────────────────────────

def row_to_restaurant(row) -> Restaurant:
    def asp(key) -> AspectScore:
        avg_col, pol_col, cnt_col = ASPECT_COLS[key]
        return AspectScore(
            avg=safe_float(row.get(avg_col)),
            polarity=safe_str(row.get(pol_col)),
            review_count=safe_int(row.get(cnt_col)),
        )

    return Restaurant(
        restaurant_name=str(row.get("restaurant_name", "")),
        food_quality=asp("food_quality"),
        service=asp("service"),
        ambiance=asp("ambiance"),
        price_value=asp("price_value"),
        overall_score=safe_float(row.get("overall_score")),
        overall_polarity=safe_str(row.get("overall_polarity")),
        total_reviews=safe_int(row.get("total_reviews")),
        aspects_scored=safe_int(row.get("aspects_scored")),
    )

# ─────────────────────────────────────────────
# Routes — Chat (RASA Proxy)
# ─────────────────────────────────────────────

@app.post("/api/chat", response_model=List[BotResponse])
async def chat(msg: ChatMessage):
    payload = {"sender": msg.sender, "message": msg.message}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{RASA_URL}/webhooks/rest/webhook",
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return [BotResponse(text="I'm sorry, I didn't get a response. Please try again.")]
            return [BotResponse(
                text=item.get("text", ""),
                image=item.get("image"),
                buttons=item.get("buttons")
            ) for item in data if item.get("text") or item.get("image")]
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="RASA server is not running. Please start it with: rasa run --enable-api --cors '*'"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# Routes — Restaurants
# ─────────────────────────────────────────────

@app.get("/api/restaurants", response_model=List[Restaurant])
def get_restaurants(
    aspect: Optional[str] = Query(None),
    polarity: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
):
    df = DB.copy()

    if search:
        df = df[df["restaurant_name"].str.lower().str.contains(search.lower(), na=False)]

    if polarity:
        if aspect and aspect in ASPECT_COLS:
            pol_col = ASPECT_COLS[aspect][1]
            df = df[df[pol_col] == polarity]
        else:
            df = df[df["overall_polarity"] == polarity]

    if aspect and aspect in ASPECT_COLS:
        avg_col = ASPECT_COLS[aspect][0]
        df = df[df[avg_col].notna()].sort_values(avg_col, ascending=False)
    else:
        df = df[df["overall_score"].notna()].sort_values("overall_score", ascending=False)

    df = df.head(limit)
    return [row_to_restaurant(row) for _, row in df.iterrows()]


@app.get("/api/restaurants/{name}", response_model=Restaurant)
def get_restaurant(name: str):
    name_lower = name.lower().strip()
    match = DB[DB["restaurant_name"].str.lower() == name_lower]
    if match.empty:
        match = DB[DB["restaurant_name"].str.lower().str.contains(name_lower, na=False)]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Restaurant '{name}' not found.")
    return row_to_restaurant(match.iloc[0])


@app.get("/api/stats", response_model=StatsResponse)
def get_stats():
    pol_counts = DB["overall_polarity"].value_counts().to_dict()
    valid_scores = DB["overall_score"].dropna()
    coverage = {}
    for aspect, (avg_col, _, cnt_col) in ASPECT_COLS.items():
        coverage[aspect] = int((DB[cnt_col].fillna(0) > 0).sum())

    return StatsResponse(
        total_restaurants=len(DB),
        positive_count=int(pol_counts.get("Positive", 0)),
        neutral_count=int(pol_counts.get("Neutral", 0)),
        negative_count=int(pol_counts.get("Negative", 0)),
        avg_overall_score=round(float(valid_scores.mean()), 3) if len(valid_scores) > 0 else 0.0,
        fully_scored_count=int((DB["aspects_scored"] == 4).sum()),
        aspect_coverage=coverage,
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "restaurants_loaded": len(DB)}