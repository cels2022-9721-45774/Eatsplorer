"""
Eatsplorer - Custom RASA Actions
Queries the restaurant_scores.csv database to power aspect-based recommendations.

Aspects tracked:
  - food_quality (food_quality_avg, food_quality_polarity, food_quality_review_count)
  - service      (service_avg, service_polarity, service_review_count)
  - ambiance     (ambiance_avg, ambiance_polarity, ambiance_review_count)
  - price_value  (price_value_avg, price_value_polarity, price_value_review_count)
  - overall      (overall_score, overall_polarity, total_reviews)
"""

import os
import re
import pandas as pd
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# ─────────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────────

# Load the restaurant scores database once at startup
_SCORES_PATH = os.path.join(os.path.dirname(__file__), "..", "restaurant_scores.csv")

def load_scores() -> pd.DataFrame:
    df = pd.read_csv(_SCORES_PATH)
    # Normalize restaurant names for fuzzy matching
    df["_name_lower"] = df["restaurant_name"].str.lower().str.strip()
    return df

SCORES_DB: pd.DataFrame = load_scores()

# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────

ASPECT_MAP = {
    "food_quality": ("food_quality_avg", "food_quality_polarity", "food_quality_review_count", "🍴 Food Quality"),
    "service":      ("service_avg",      "service_polarity",      "service_review_count",      "🛎️ Service"),
    "ambiance":     ("ambiance_avg",     "ambiance_polarity",     "ambiance_review_count",     "🌿 Ambiance"),
    "price_value":  ("price_value_avg",  "price_value_polarity",  "price_value_review_count",  "💰 Price/Value"),
}

POLARITY_EMOJI = {"Positive": "✅", "Neutral": "🟡", "Negative": "❌", "N/A": "⬜"}

DEFAULT_TOP_N = 5


def normalize_aspect(raw: str) -> str:
    """Map raw entity value to canonical aspect key."""
    if not raw:
        return None
    raw = raw.lower().strip()
    mappings = {
        "food_quality": ["food quality", "food", "cuisine", "dishes", "taste", "flavors", "the food"],
        "service":      ["service", "staff", "customer service", "hospitality", "waiters", "waiter", "servers"],
        "ambiance":     ["ambiance", "atmosphere", "vibe", "decor", "environment", "setting", "place"],
        "price_value":  ["price value", "price-to-value", "value for money", "value", "price",
                         "affordability", "budget", "cost"],
    }
    for key, synonyms in mappings.items():
        if raw == key or raw in synonyms:
            return key
    return None


def format_score(avg, polarity, count) -> str:
    """Format a single aspect score for display."""
    if pd.isna(avg) or count == 0:
        return "⬜ N/A (no reviews)"
    emoji = POLARITY_EMOJI.get(polarity, "⬜")
    return f"{emoji} {avg:.2f}/5.00 ({polarity}, {int(count)} reviews)"


def format_restaurant_card(row: pd.Series, rank: int = None, aspect_key: str = None) -> str:
    """Build a formatted restaurant summary string."""
    name = row["restaurant_name"]
    overall = f"{row['overall_score']:.2f}" if not pd.isna(row["overall_score"]) else "N/A"
    overall_pol = POLARITY_EMOJI.get(row.get("overall_polarity", "N/A"), "⬜")
    total = int(row["total_reviews"]) if not pd.isna(row["total_reviews"]) else 0

    prefix = f"**#{rank}** " if rank else ""

    lines = [f"{prefix}**{name}**"]
    lines.append(f"   Overall: {overall_pol} {overall}/5.00  ({total} total reviews)")

    if aspect_key and aspect_key in ASPECT_MAP:
        avg_col, pol_col, cnt_col, label = ASPECT_MAP[aspect_key]
        lines.append(f"   {label}: {format_score(row[avg_col], row[pol_col], row[cnt_col])}")
    
    return "\n".join(lines)


def fuzzy_match_restaurant(query: str, df: pd.DataFrame) -> pd.Series | None:
    """Find closest matching restaurant by name substring matching."""
    if not query:
        return None
    q = query.lower().strip()
    # Exact match first
    exact = df[df["_name_lower"] == q]
    if not exact.empty:
        return exact.iloc[0]
    # Substring match
    sub = df[df["_name_lower"].str.contains(q, na=False, regex=False)]
    if not sub.empty:
        return sub.iloc[0]
    # Word-level partial match
    words = q.split()
    for word in words:
        if len(word) > 3:
            partial = df[df["_name_lower"].str.contains(word, na=False, regex=False)]
            if not partial.empty:
                return partial.iloc[0]
    return None


def get_top_n(df: pd.DataFrame, sort_col: str, n: int, polarity_col: str = None,
              min_reviews_col: str = None, min_reviews: int = 1) -> pd.DataFrame:
    """Return top N restaurants sorted by a score column, excluding NaN."""
    filtered = df[df[sort_col].notna()]
    if min_reviews_col:
        filtered = filtered[filtered[min_reviews_col] >= min_reviews]
    return filtered.sort_values(sort_col, ascending=False).head(n)


# ─────────────────────────────────────────────
# ACTION: Top Restaurants (Overall)
# ─────────────────────────────────────────────

class ActionRecommendTopRestaurants(Action):
    def name(self) -> Text:
        return "action_recommend_top_restaurants"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        top = get_top_n(SCORES_DB, "overall_score", DEFAULT_TOP_N,
                        min_reviews_col="total_reviews", min_reviews=1)

        if top.empty:
            dispatcher.utter_message(text="Sorry, I couldn't find any restaurant data right now.")
            return []

        lines = [f"🍽️ **Top {len(top)} Restaurants in Legazpi City** (by overall score):\n"]
        for i, (_, row) in enumerate(top.iterrows(), 1):
            lines.append(format_restaurant_card(row, rank=i))
            lines.append("")  # blank line between restaurants

        lines.append("💡 *Tip: Ask me about a specific restaurant or filter by food quality, service, ambiance, or value!*")
        dispatcher.utter_message(text="\n".join(lines))
        return []


# ─────────────────────────────────────────────
# ACTION: Best Overall (Single #1 Restaurant)
# ─────────────────────────────────────────────

class ActionBestOverall(Action):
    def name(self) -> Text:
        return "action_best_overall"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        top = get_top_n(SCORES_DB, "overall_score", 1,
                        min_reviews_col="total_reviews", min_reviews=1)

        if top.empty:
            dispatcher.utter_message(text="Sorry, I couldn't find any restaurant data right now.")
            return []

        row = top.iloc[0]
        name = row["restaurant_name"]
        overall = f"{row['overall_score']:.2f}"
        total = int(row["total_reviews"])

        msg = (
            f"🏆 **The highest-rated restaurant in Legazpi City is:**\n\n"
            f"**{name}**\n"
            f"   Overall Score: ✅ {overall}/5.00 ({total} reviews)\n\n"
        )

        # Add aspect breakdown
        aspect_lines = []
        for key, (avg_col, pol_col, cnt_col, label) in ASPECT_MAP.items():
            if not pd.isna(row[avg_col]) and row[cnt_col] > 0:
                aspect_lines.append(f"   {label}: {format_score(row[avg_col], row[pol_col], row[cnt_col])}")
        
        if aspect_lines:
            msg += "**Aspect Breakdown:**\n" + "\n".join(aspect_lines)

        dispatcher.utter_message(text=msg)
        return []


# ─────────────────────────────────────────────
# ACTION: Restaurant by Aspect
# ─────────────────────────────────────────────

class ActionRestaurantByAspect(Action):
    def name(self) -> Text:
        return "action_restaurant_by_aspect"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        raw_aspect = tracker.get_slot("aspect") or tracker.get_entity_value("aspect")
        aspect_key = normalize_aspect(raw_aspect)

        if not aspect_key or aspect_key not in ASPECT_MAP:
            dispatcher.utter_message(
                text="Which aspect would you like to filter by? Please choose:\n"
                     "🍴 **Food Quality** | 🛎️ **Service** | 🌿 **Ambiance** | 💰 **Price/Value**"
            )
            return []

        avg_col, pol_col, cnt_col, label = ASPECT_MAP[aspect_key]
        top = get_top_n(SCORES_DB, avg_col, DEFAULT_TOP_N, 
                        min_reviews_col=cnt_col, min_reviews=1)

        if top.empty:
            dispatcher.utter_message(text=f"Sorry, I couldn't find restaurants with data for {label}.")
            return []

        lines = [f"{label} — **Top {len(top)} Restaurants:**\n"]
        for i, (_, row) in enumerate(top.iterrows(), 1):
            name = row["restaurant_name"]
            score_str = format_score(row[avg_col], row[pol_col], row[cnt_col])
            overall_str = f"{row['overall_score']:.2f}" if not pd.isna(row["overall_score"]) else "N/A"
            lines.append(f"**#{i} {name}**")
            lines.append(f"   {label}: {score_str}")
            lines.append(f"   Overall: {overall_str}/5.00")
            lines.append("")

        lines.append("💡 *Ask me for more details about any of these restaurants!*")
        dispatcher.utter_message(text="\n".join(lines))
        return [SlotSet("aspect", aspect_key)]


# ─────────────────────────────────────────────
# ACTION: Top N by Aspect
# ─────────────────────────────────────────────

class ActionTopNByAspect(Action):
    def name(self) -> Text:
        return "action_top_n_by_aspect"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Extract number and aspect from entities
        n_raw = tracker.get_slot("number")
        n = int(n_raw) if n_raw else DEFAULT_TOP_N
        n = max(1, min(n, 20))  # clamp to reasonable range

        raw_aspect = tracker.get_slot("aspect") or tracker.get_entity_value("aspect")
        aspect_key = normalize_aspect(raw_aspect)

        if aspect_key and aspect_key in ASPECT_MAP:
            avg_col, pol_col, cnt_col, label = ASPECT_MAP[aspect_key]
            top = get_top_n(SCORES_DB, avg_col, n, min_reviews_col=cnt_col, min_reviews=1)
            header = f"{label} — **Top {len(top)} Restaurants:**\n"
        else:
            # No aspect — use overall score
            top = get_top_n(SCORES_DB, "overall_score", n,
                            min_reviews_col="total_reviews", min_reviews=1)
            header = f"🍽️ **Top {len(top)} Restaurants in Legazpi City** (Overall):\n"
            aspect_key = None

        if top.empty:
            dispatcher.utter_message(text="Sorry, I couldn't find restaurant data for that query.")
            return []

        lines = [header]
        for i, (_, row) in enumerate(top.iterrows(), 1):
            lines.append(format_restaurant_card(row, rank=i, aspect_key=aspect_key))
            lines.append("")

        dispatcher.utter_message(text="\n".join(lines))
        return [SlotSet("number", None)]  # reset number slot


# ─────────────────────────────────────────────
# ACTION: Multi-Aspect Query
# ─────────────────────────────────────────────

class ActionMultiAspect(Action):
    def name(self) -> Text:
        return "action_multi_aspect"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Extract all aspect entities from the message
        entities = tracker.latest_message.get("entities", [])
        aspect_keys = []
        for ent in entities:
            if ent["entity"] == "aspect":
                key = normalize_aspect(ent["value"])
                if key and key not in aspect_keys:
                    aspect_keys.append(key)

        if len(aspect_keys) < 2:
            # Fall back to single aspect or overall
            dispatcher.utter_message(
                text="I can filter by multiple aspects at once! Try asking like:\n"
                     "'Restaurants with great food quality and good service'\n"
                     "'Places with nice ambiance and good value'"
            )
            return []

        # Compute combined score: average of the specified aspect scores
        df = SCORES_DB.copy()
        score_cols = [ASPECT_MAP[k][0] for k in aspect_keys]
        labels = [ASPECT_MAP[k][3] for k in aspect_keys]

        # Only include rows where all requested aspects have data
        df_filtered = df.dropna(subset=score_cols)
        if df_filtered.empty:
            dispatcher.utter_message(
                text="Sorry, I couldn't find restaurants scored across all those aspects. Try fewer aspects!"
            )
            return []

        df_filtered = df_filtered.copy()
        df_filtered["_combined"] = df_filtered[score_cols].mean(axis=1)
        top = df_filtered.sort_values("_combined", ascending=False).head(DEFAULT_TOP_N)

        aspect_label = " + ".join(labels)
        lines = [f"**Top {len(top)} Restaurants** combining {aspect_label}:\n"]
        for i, (_, row) in enumerate(top.iterrows(), 1):
            name = row["restaurant_name"]
            combined = row["_combined"]
            lines.append(f"**#{i} {name}** (Combined: {combined:.2f}/5.00)")
            for key in aspect_keys:
                avg_col, pol_col, cnt_col, lbl = ASPECT_MAP[key]
                lines.append(f"   {lbl}: {format_score(row[avg_col], row[pol_col], row[cnt_col])}")
            lines.append("")

        dispatcher.utter_message(text="\n".join(lines))
        return []


# ─────────────────────────────────────────────
# ACTION: Restaurant Info (Specific Restaurant)
# ─────────────────────────────────────────────

class ActionRestaurantInfo(Action):
    def name(self) -> Text:
        return "action_restaurant_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        restaurant_name = tracker.get_slot("restaurant_name") or tracker.get_entity_value("restaurant_name")

        if not restaurant_name:
            dispatcher.utter_message(
                text="Which restaurant would you like to know about? Please mention the name!"
            )
            return []

        row = fuzzy_match_restaurant(restaurant_name, SCORES_DB)

        if row is None:
            dispatcher.utter_message(
                text=f"Sorry, I couldn't find **'{restaurant_name}'** in my database. "
                     f"It may not be listed yet or the name might be slightly different. "
                     f"Try asking for top restaurants and look for it in the list!"
            )
            return [SlotSet("restaurant_name", None)]

        name = row["restaurant_name"]
        overall = f"{row['overall_score']:.2f}" if not pd.isna(row["overall_score"]) else "N/A"
        overall_pol = POLARITY_EMOJI.get(str(row.get("overall_polarity", "N/A")), "⬜")
        total = int(row["total_reviews"]) if not pd.isna(row["total_reviews"]) else 0

        lines = [
            f"📍 **{name}**",
            f"",
            f"⭐ **Overall Score:** {overall_pol} {overall}/5.00 ({total} total reviews)",
            f"",
            f"**Aspect Breakdown:**",
        ]

        for key, (avg_col, pol_col, cnt_col, label) in ASPECT_MAP.items():
            score_str = format_score(row[avg_col], row[pol_col], row[cnt_col])
            lines.append(f"   {label}: {score_str}")

        lines.append("")
        lines.append("💡 *Scores are based on real customer reviews analyzed by our ABSA model.*")

        dispatcher.utter_message(text="\n".join(lines))
        return [SlotSet("restaurant_name", name)]


# ─────────────────────────────────────────────
# ACTION: Positive Only
# ─────────────────────────────────────────────

class ActionPositiveOnly(Action):
    def name(self) -> Text:
        return "action_positive_only"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        positive = SCORES_DB[SCORES_DB["overall_polarity"] == "Positive"]
        top = positive.sort_values("overall_score", ascending=False).head(DEFAULT_TOP_N)

        if top.empty:
            dispatcher.utter_message(text="No positively reviewed restaurants found.")
            return []

        lines = [f"✅ **Top {len(top)} Positively Reviewed Restaurants:**\n"]
        for i, (_, row) in enumerate(top.iterrows(), 1):
            lines.append(format_restaurant_card(row, rank=i))
            lines.append("")

        dispatcher.utter_message(text="\n".join(lines))
        return []


# ─────────────────────────────────────────────
# ACTION: Negative Warning
# ─────────────────────────────────────────────

class ActionNegativeWarning(Action):
    def name(self) -> Text:
        return "action_negative_warning"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        raw_aspect = tracker.get_slot("aspect") or tracker.get_entity_value("aspect")
        aspect_key = normalize_aspect(raw_aspect)

        if aspect_key and aspect_key in ASPECT_MAP:
            avg_col, pol_col, cnt_col, label = ASPECT_MAP[aspect_key]
            negative = SCORES_DB[SCORES_DB[pol_col] == "Negative"]
            sort_col = avg_col
            header = f"⚠️ Restaurants with **Negative {label}** ratings:"
        else:
            negative = SCORES_DB[SCORES_DB["overall_polarity"] == "Negative"]
            sort_col = "overall_score"
            header = "⚠️ Restaurants with **Negative** overall ratings:"

        if negative.empty:
            dispatcher.utter_message(
                text="Good news! No restaurants with negative ratings found in my current database. 🎉"
            )
            return []

        neg_sorted = negative.sort_values(sort_col, ascending=True).head(DEFAULT_TOP_N)

        lines = [f"{header}\n",
                 "*(Consider these places carefully based on customer feedback)*\n"]
        for i, (_, row) in enumerate(neg_sorted.iterrows(), 1):
            lines.append(format_restaurant_card(row, rank=i, aspect_key=aspect_key))
            lines.append("")

        dispatcher.utter_message(text="\n".join(lines))
        return []
