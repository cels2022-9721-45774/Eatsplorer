# Eatsplorer Chatbot — RASA Setup & Evaluation Guide

> **Eatsplorer: Enhancing Food Tourism in Legazpi City Through a Conversational AI Chatbot Using Aspect-Based Sentiment Analysis**  
> Bicol University College of Science — Department of Computer Science  
> Baltasar, Bolaños, San Jose · November 2025

---

## Project Structure

```
eatsplorer_chatbot/
├── config.yml                  # RASA pipeline (DIETClassifier + SpaCy)
├── domain.yml                  # Intents, entities, slots, responses, actions
├── credentials.yml             # Channel configs (REST, SocketIO)
├── endpoints.yml               # Custom actions server URL
├── requirements.txt            # Python dependencies
├── restaurant_scores.csv       # ABSA-scored restaurant database (knowledge base)
│
├── data/
│   ├── nlu.yml                 # NLU training data (intents, entities, synonyms)
│   ├── stories.yml             # Conversation flow stories
│   └── rules.yml               # Deterministic conversation rules
│
├── actions/
│   └── actions.py              # Custom actions querying restaurant_scores.csv
│
└── tests/
    ├── test_stories.yml        # E2E conversation tests
    └── test_nlu.yml            # NLU intent/entity test data
```

---

## 1. Environment Setup

> ⚠️ Use **Python 3.10** for RASA 3.x compatibility (as documented in your thesis).

```bash
# Create and activate a virtual environment
python3.10 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download SpaCy English model (medium, for word vectors)
python -m spacy download en_core_web_md
```

---

## 2. Training the RASA Model

```bash
# Train both NLU and Core (stories + rules)
rasa train

# This generates a model in: ./models/
# Filename: models/YYYYMMDD-HHMMSS-<hash>.tar.gz
```

The pipeline uses:
- **SpacyNLP** with `en_core_web_md` for tokenization and word vectors
- **RegexFeaturizer** for pattern-based features
- **CountVectorsFeaturizer** (word-level + character n-grams)
- **DIETClassifier** (100 epochs) for **intent classification** and **entity extraction**
- **FallbackClassifier** (threshold: 0.3) for out-of-scope handling
- **TEDPolicy** (5 max history) for dialogue management

---

## 3. Running the Chatbot

You need **two terminals** running simultaneously.

### Terminal 1 — Start the Custom Actions Server
```bash
rasa run actions
# Starts on: http://localhost:5055/webhook
```

### Terminal 2 — Start the RASA Server
```bash
# For command-line chat (quick testing):
rasa shell

# For API access (web integration):
rasa run --enable-api --cors "*"
# REST API available at: http://localhost:5005/webhooks/rest/webhook
```

### Sending a message via REST API (for web integration):
```bash
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "user1", "message": "top 5 restaurants with best food quality"}'
```

---

## 4. Evaluation — Getting Your Thesis Metrics

### 4.1 NLU Evaluation (Intent Classification + Entity Extraction)

```bash
rasa test nlu --nlu tests/test_nlu.yml --out results/nlu/
```

**Output files** (in `results/nlu/`):
| File | Contents |
|------|----------|
| `intent_report.json` | Precision, Recall, F1-score per intent |
| `intent_confusion_matrix.png` | Confusion matrix image |
| `intent_errors.json` | Misclassified intents |
| `DIETClassifier_report.json` | Entity extraction metrics |

**Metrics you'll get for your thesis:**
- ✅ **Accuracy** — overall intent classification accuracy
- ✅ **Precision** — per intent
- ✅ **Recall** — per intent  
- ✅ **F1-score** — per intent (macro and weighted averages)
- ✅ **Confusion Matrix** — visual misclassification analysis

### 4.2 Core / Dialogue Evaluation (Story Testing)

```bash
rasa test --stories tests/test_stories.yml --out results/core/
```

**Output files** (in `results/core/`):
| File | Contents |
|------|----------|
| `story_report.json` | Action prediction accuracy |
| `failed_test_stories.yml` | Stories where predictions failed |

### 4.3 Full Combined Test

```bash
# Run both NLU + Core together
rasa test --nlu tests/test_nlu.yml --stories tests/test_stories.yml --out results/
```

### 4.4 Cross-Validation (for more robust thesis metrics)

```bash
# 5-fold cross-validation on NLU data
rasa test nlu --nlu data/nlu.yml --config config.yml --cross-validation --folds 5 --out results/cv/
```

This is especially useful if your NLU training dataset is small. The cross-validation gives you more reliable precision/recall/F1 estimates.

---

## 5. Chatbot Capabilities (Intents)

| Intent | Example Query | Action |
|--------|--------------|--------|
| `greet` | "hi", "hello" | `utter_greet` |
| `ask_top_restaurants` | "best restaurants in legazpi?" | `action_recommend_top_restaurants` |
| `ask_best_overall` | "which restaurant scores highest?" | `action_best_overall` |
| `ask_restaurant_by_aspect` | "restaurants with great food quality" | `action_restaurant_by_aspect` |
| `ask_top_n_by_aspect` | "top 5 restaurants for ambiance" | `action_top_n_by_aspect` |
| `ask_multi_aspect` | "great food and service restaurants" | `action_multi_aspect` |
| `ask_restaurant_info` | "tell me about Brew Print Cafe" | `action_restaurant_info` |
| `ask_positive_only` | "only positive restaurants" | `action_positive_only` |
| `ask_negative_warning` | "restaurants to avoid" | `action_negative_warning` |
| `bot_challenge` | "are you a bot?" | `utter_iamabot` |
| `out_of_scope` | "book a table for me" | `utter_out_of_scope` |

---

## 6. Restaurant Scores Database Schema

The `restaurant_scores.csv` serves as the chatbot's knowledge base:

| Column | Description |
|--------|-------------|
| `restaurant_name` | Restaurant identifier |
| `food_quality_avg` | Avg score for food quality (1–5) |
| `food_quality_polarity` | Positive / Neutral / Negative |
| `food_quality_review_count` | Number of reviews scored |
| `service_avg` | Avg score for service (1–5) |
| `service_polarity` | Positive / Neutral / Negative |
| `service_review_count` | Number of reviews scored |
| `ambiance_avg` | Avg score for ambiance (1–5) |
| `ambiance_polarity` | Positive / Neutral / Negative |
| `ambiance_review_count` | Number of reviews scored |
| `price_value_avg` | Avg score for price/value (1–5) |
| `price_value_polarity` | Positive / Neutral / Negative |
| `price_value_review_count` | Number of reviews scored |
| `overall_score` | Weighted overall score |
| `overall_polarity` | Overall sentiment |
| `total_reviews` | Total reviews analyzed |
| `aspects_scored` | How many of 4 aspects have data |

---

## 7. Adding More NLU Training Data

To improve model performance, add more examples to `data/nlu.yml`:

```yaml
- intent: ask_restaurant_by_aspect
  examples: |
    - where should I go if I want [great food](aspect)?
    - recommend places with [amazing service](aspect)
    - (add more examples here...)
```

**Rule of thumb:** At least **10–15 examples per intent** for reliable classification. More is better, especially for similar intents like `ask_restaurant_by_aspect` vs `ask_top_n_by_aspect`.

---

## 8. Troubleshooting

| Issue | Fix |
|-------|-----|
| SpaCy model not found | `python -m spacy download en_core_web_md` |
| Actions server not connecting | Make sure `rasa run actions` is running before `rasa shell` |
| Low intent accuracy | Add more NLU training examples; run cross-validation to diagnose |
| Restaurant not found | Check name spelling; the chatbot does partial/fuzzy matching |
| CUDA/GPU errors | Set `TF_FORCE_GPU_ALLOW_GROWTH=true` or run CPU-only |

---

## 9. For the Expert Evaluation (CustomGPT Comparison)

As required by the panel, the expert evaluation includes a **comparative analysis with CustomGPT**.

To set up the CustomGPT baseline:
1. Export `restaurant_scores.csv` as a knowledge file
2. Upload it to CustomGPT with a system prompt defining the recommendation task
3. Use the same test queries from `tests/test_nlu.yml` on both systems
4. Have domain experts rate responses using your Likert-scale rubric (MCDA + SBE)

The evaluators should assess: **Recommendation Relevance**, **Conversational Precision**, and **Contextual Performance** — as specified in your evaluation scope.
