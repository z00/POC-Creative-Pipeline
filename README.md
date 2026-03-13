```markdown
# Creative Automation Pipeline (PoC)

## 🚀 Overview
This Proof of Concept (PoC) automates the localization and resizing of creative assets for social media campaigns. It transforms product descriptions and base images into multi-format, marketing-ready assets (1:1, 9:16, 16:9) with localized text overlays using **FastAPI**, **Pillow**, and **Hugging Face Generative AI**.

---

## 🏗️ Key Design Decisions

* **Non-Blocking UX:** Built with FastAPI's `BackgroundTasks`. The API returns a tracking ID immediately, allowing the UI to remain responsive while heavy AI generation runs in the background.
* **Intelligent Layout Logic:** Uses "Contain" scaling to preserve product integrity. The pipeline calculates a "usable area" above the text banner to ensure products are mathematically centered and never obscured by marketing copy.
* **Format Versatility:** Robust image processing normalizes varied inputs (PNG/RGBA, JPEG, JPG) into standardized RGB outputs on clean white backgrounds.
* **Resiliency & Fallbacks:** Implements retries for AI API calls. If the GenAI quota is reached, the system generates "dark-square" placeholders so the resizing and overlay logic can still be verified.
* **Modular Storage:** Designed with an abstraction layer that allows the current local filesystem storage to be easily swapped for AWS S3 or Google Cloud Storage in production.
* **Validation:** Strict schema validation exists on both the UI (JavaScript) and Backend (Pydantic), including a minimum requirement of two products per campaign.

---

## 📂 Project Structure

```text
.
├── app/
│   ├── main.py              # FastAPI application and API endpoints
│   ├── models.py            # Pydantic data models (Campaign, Product, etc.)
│   └── services/
│       └── pipeline.py      # Core logic for AI calls and image processing
├── static/
│   ├── index.html           # Main dashboard UI
│   ├── style.css            # Custom dashboard styling
├── storage/                 # Local filesystem storage (Auto-generated)
│   ├── inputs/              # User-uploaded base images
│   └── outputs/             # AI-generated variations and overlays
├── tests/
│   └── test_main.py          # Unit tests with mocking and auto-cleanup
├── .env                     # Environment variables (HF_TOKEN)
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation

```

---

## 🛠️ How to Run

1. **Clone the repository** and navigate to the project root.
2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

```


3. **Install requirements:**
```bash
pip install -r requirements.txt

```


4. **Set up Configuration:**
Create a `.env` file in the root directory and add your Hugging Face token:
```env
HF_TOKEN=your_hugging_face_token_here

```


5. **Start the server:**
```bash
uvicorn app.main:app --reload

```


6. **Open the Dashboard:**
* **UI:** [http://localhost:8000/]
* **API Docs:** [http://localhost:8000/docs]



---

## 🧪 Testing

The PoC includes a comprehensive test suite to ensure API and logic stability.
Execute the following in the root directory:

```bash
pytest

```

* **API Mocking:** Tests use `unittest.mock` to bypass actual AI calls, ensuring the suite runs in milliseconds without consuming API quotas.
* **Auto-Cleanup:** A custom `pytest` fixture automatically deletes all generated assets in `storage/inputs` and `storage/outputs` after tests finish to keep the workspace clean.

---

## ⚠️ Limitations & Roadmap

* **In-Memory DB:** Campaign state is tracked in a Python dictionary and resets on server restart. **Roadmap:** Migrate to **PostgreSQL** or **MongoDB**.
* **Task Queue:** Background tasks are currently handled by the FastAPI process. **Roadmap:** Implement **Celery + Redis** for distributed worker scaling.
* **Font Handling:** Relies on system `arial.ttf`. **Roadmap:** Bundle brand-specific `.ttf` files in an `/assets` folder for consistent cross-platform rendering.
* **Storage Scale:** Currently uses the local disk. **Roadmap:** Integrate an **S3-compatible Object Store** (AWS S3 / Azure Blob) and a CDN for fast asset delivery.
* **Parallel Processing:** Products are processed serially to stay within free-tier API rate limits. **Roadmap:** Use `asyncio.gather` for concurrent AI generation in paid-tier environments.



