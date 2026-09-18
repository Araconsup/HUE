# HUE — AI Makeup Intelligence & Visual Styling Engine (Part 1)

HUE is a modern, luxury AI-powered beauty and makeup assistant built as a Progressive Web App (PWA). It acts as an intelligent virtual makeup consultant, analyzing visual information from portraits, outfits, or both to deliver personalized, visually-harmonized makeup guidance.

---

## 🌟 Core Capabilities

1. **Intelligent Visual Analysis Options**:
   - **Option A — Face Analysis**: Analyzes facial structure, complexion balance, visible undertones, lip/brow/eye geometry, and natural contrast.
   - **Option B — Outfit Analysis**: Evaluates dominant and secondary clothing colors, pattern, formality, temperature, and visual aesthetics.
   - **Option C — Combined Analysis**: Synthesizes the relationship between the user's features and their outfit for complete visual harmony.
2. **Multi-Stage AI Vision Pipeline**:
   - **Stage 1: Image Validation**: Rejects unusable images (too dark, blurry, low-resolution, obstructed) with helpful, friendly guidance before processing.
   - **Stage 2: Feature Observation**: Structured extraction of cosmetic attributes (avoiding all medical, racial, ethnic, or age assumptions).
   - **Stage 3: Styling Synthesis**: Translates observations into dynamic concepts (*Soft Everyday*, *Clean Girl*, *Golden Luminous Glow*, *Warm Sunset*, *Soft Glam*).
3. **Structured Recommendation Engine**:
   - Comprehensive category recommendations: Base, Blush, Bronzer/Contour, Highlighter, Eyeshadow, Eyeliner, Mascara, Brows, and Lips.
   - Normalized Color System (`color_name`, `hex`, `temperature`, `saturation`, `brightness`).
   - Ordered 10-step application routine with professional stylist reasoning.
4. **Product Catalog & "Use What I Own" Mode**:
   - Built-in cosmetics database spanning top brands (Rare Beauty, Fenty, NARS, MAC, Charlotte Tilbury, Maybelline, Glossier, Laura Mercier, etc.).
   - Live search with instant brand & category filtering.
   - Personal **My Makeup Bag** collection.
   - **"Use What I Own" Mode**: Re-prioritizes the routine around the products the user already owns, calculating compatibility scores and tailored application advice.
5. **Provider-Independent AI Architecture**:
   - Connects to any OpenAI-compatible AI Gateway through environment variables.
   - Includes high-fidelity offline fallback intelligence for local development, tests, and zero-configuration demos.
6. **Modern Luxury Beauty PWA**:
   - Mobile-first, responsive luxury dark-mode design (`Cormorant Garamond` + `Plus Jakarta Sans`).
   - Camera capture and drag-and-drop file upload.
   - Multi-stage animated pipeline progress indicator.
   - Offline-capable service worker and installable Web App Manifest.

---

## 🏗️ Architecture

```text
HUE/
├── hue/                       # Django project configuration
│   ├── settings.py            # Gateway config & app settings
│   ├── urls.py                # Root router
│   └── wsgi.py                # WSGI & Vercel entrypoint
├── core/                      # Main application
│   ├── models.py              # Products, Bag, AnalysisSession, Looks
│   ├── views.py               # REST API & PWA views
│   ├── urls.py                # Endpoint routes
│   ├── admin.py               # Django administration
│   ├── tests.py               # Automated test suite (16 test cases)
│   ├── management/commands/   # Seed database command
│   └── ai/                    # Provider-independent AI Engine
│       ├── client.py          # AIClient (urllib stdlib HTTP client + simulated engine)
│       ├── gateway.py         # ImageProcessor (Pillow resize/compression/base64)
│       ├── vision.py          # VisionAnalyzer (Stage 1 validation & feature analysis)
│       ├── recommendations.py # RecommendationEngine (Categories & 10-step routine)
│       ├── products.py        # ProductRecommendationEngine & "Use What I Own"
│       ├── prompts.py         # Modular prompt templates
│       ├── schemas.py         # Structured JSON schema contracts
│       └── validators.py      # Output sanitization & medical safety filters
├── static/
│   ├── css/app.css            # Luxury beauty aesthetic stylesheet
│   ├── js/app.js              # PWA client app & UI controller
│   └── icons/                 # PWA icons (192x192, 512x512)
├── templates/
│   └── index.html             # Single-page PWA shell
├── api/
│   └── index.py               # Vercel serverless function
├── vercel.json                # Vercel deployment configuration
├── requirements.txt           # Python dependencies (django, pillow)
└── .env.example               # Environment variables template
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+
- Virtual environment

### 2. Installation
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Migrations & Seeding
```bash
# Run migrations
python manage.py migrate

# Seed cosmetic products catalog
python manage.py seed_products
```

### 4. Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000` in your browser.

### 5. Running Tests
```bash
python manage.py test
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env`:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*

# AI Gateway (Compatible with OpenAI, LiteLLM, OpenRouter, Cloudflare, etc.)
AI_GATEWAY_URL=https://api.openai.com/v1
AI_GATEWAY_API_KEY=your-api-key-here
AI_VISION_MODEL=gpt-4o
AI_TEXT_MODEL=gpt-4o-mini
AI_REQUEST_TIMEOUT=45
AI_MAX_IMAGE_SIZE=10485760
```

> **Note:** If `AI_GATEWAY_API_KEY` is omitted, HUE automatically uses its internal luxury styling engine, allowing complete local evaluation and UI testing without incurring API costs.

---

## 🌐 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/ai/analyze/face/` | Stage 1 check -> Face analysis -> 10-step routine |
| `POST` | `/api/ai/analyze/outfit/` | Stage 1 check -> Outfit analysis -> Harmonized recommendations |
| `POST` | `/api/ai/analyze/combined/` | Checks both -> High-level visual harmony synthesis |
| `POST` | `/api/products/search/` | Search products with brand and category filters |
| `POST` | `/api/products/match/` | Product-to-recommendation compatibility score & usage role |
| `POST` | `/api/looks/generate/` | Generates look routine (supports `use_my_products` flag) |
| `POST` | `/api/looks/save/` | Saves look to user profile / session |
| `GET`  | `/api/looks/saved/` | Lists saved looks |
| `GET`  | `/api/user/products/` | Lists products in My Makeup Bag |
| `POST` | `/api/user/products/` | Adds product to My Makeup Bag |
| `DELETE`| `/api/user/products/<id>/` | Removes product from My Makeup Bag |

---

## 🚀 Vercel Deployment

HUE is preconfigured for Vercel:
1. Connect your repository to Vercel.
2. In Project Settings > Environment Variables, add:
   - `DJANGO_SECRET_KEY`
   - `AI_GATEWAY_URL`
   - `AI_GATEWAY_API_KEY`
   - `AI_VISION_MODEL`
   - `AI_TEXT_MODEL`
3. Deploy!
