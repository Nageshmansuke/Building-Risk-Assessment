# SEISMOS - AI & ML Building Seismic Risk Assessment Platform

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3-F7931E?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=flat&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F61?style=flat)](https://www.trychroma.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

An intelligent web application that evaluates the seismic vulnerability of residential buildings and structures. The platform combines a **Dual-Engine Machine Learning core** for damage grade classification with an **AI Structural Engineering Consultant** powered by **Retrieval-Augmented Generation (RAG)** referencing verified Bureau of Indian Standards (IS 4326 and IS 13828) codes.

---

## Key Features

- **Dual-Engine ML Prediction**: Predicts building damage severity (Grades 1 to 5: Low, Medium, High, Critical) using both **Decision Tree** (hierarchical split interpretability) and **Logistic Regression** (calibrated risk probability).
- **AI Structural Consultant (RAG)**: Generates localized, professional retrofitting and structural strengthening reports authored by *Aditya Khandre (Lead AI Structural Consultant)* citing Indian Standard codes (`IS 4326` & `IS 13828`).
- **Flexible Database Architecture**: Production-ready support for **MySQL 8.0** with an automatic, zero-config fallback to **SQLite (`seismos.db`)** so the app runs without database connection issues.
- **Dynamic Risk Visualization**: Interactive frontend charts displaying factor contribution percentages (foundation, superstructure, building age, floor system, and plinth area).
- **Historical Assessment Audit**: Filterable and exportable history table tracking previous assessments.
- **Production-Ready**: Equipped with `Dockerfile`, `docker-compose.yml`, `Procfile`, and `wsgi.py` for cloud deployment on Render, Railway, AWS, or Docker containers.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.11, Flask 3.0, Flask-SQLAlchemy, Gunicorn (Linux), Waitress (Windows) |
| **Machine Learning** | Scikit-learn, Category Encoders, Pandas, NumPy |
| **AI & RAG** | LangChain, Google Gemini 2.5 Flash, HuggingFace Embeddings (`all-MiniLM-L6-v2`), ChromaDB |
| **Databases** | MySQL (Production) / SQLite (Zero-config local) |
| **Frontend** | HTML5, CSS3 (Modern Dark Theme), JavaScript (Fetch API, Chart.js, Marked.js) |
| **DevOps & Containers** | Docker, Docker Compose, Procfile |

---

## Project Structure

```text
Building-Risk-Assesment/
├── app.py                  # Main Flask application and API routing
├── wsgi.py                 # Production WSGI server entrypoint
├── models.py               # Original model definition and database schema
├── train_models.py         # Retraining script for Decision Tree & Logistic Regression
├── init_db.py              # Database initialization utility (MySQL & SQLite)
├── buiild_database.py      # Chroma vector database builder from PDF codes
├── decision_tree.pkl       # Trained Decision Tree model
├── logistic_regression.pkl # Trained Logistic Regression model
├── my_local_database/      # Chroma vector DB containing indexed IS codes
├── docs/                   # Structural engineering reference standards
│   ├── IS4326.pdf          # Earthquake Resistant Design and Construction of Buildings
│   └── IS13828.pdf         # Improving Earthquake Resistance of Low Strength Masonry Buildings
├── static/
│   └── style.css           # Custom modern UI styling
├── templates/
│   ├── base.html           # Master layout template
│   ├── home.html           # Landing page
│   ├── predict.html        # Interactive prediction dashboard & AI report modal
│   ├── history.html        # Historical prediction logs with risk filtering
│   └── about.html          # Methodology, research, and acknowledgments
├── .env.example            # Environment variables template
├── .gitignore              # Production gitignore rules
├── requirements.txt        # Production Python dependencies
├── Procfile                # Heroku / Render / Railway process file
├── Dockerfile              # Container image specification
├── docker-compose.yml      # Multi-container orchestration (App + MySQL)
├── run.bat                 # One-click Windows development launcher
└── run_waitress.bat        # Windows production server launcher (Waitress WSGI)
```

---

## Quick Start (Local Development)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Building-Risk-Assessment.git
cd Building-Risk-Assessment
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
*(Optional)* Add your `GOOGLE_API_KEY` for live Gemini 2.5 Flash generations. If omitted, the platform uses an intelligent offline structural engineering report generator with local RAG context.

### 5. Run the Application
```bash
python app.py
```
Open your browser at **`http://127.0.0.1:5000`**.

---

## Production Deployment Guide

### Option 1: Deploy on Render.com (Recommended - Free & Easy)

1. **Push your code to GitHub** (follow the Git instructions below).
2. Go to [Render.com](https://render.com/) and create a free account.
3. Click **New +** → **Web Service**.
4. Connect your GitHub repository.
5. Configure the service settings:
   - **Name**: `seismos-risk-predictor`
   - **Region**: Choose the closest region (e.g., Singapore, Frankfurt, Oregon)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
6. Under **Environment Variables**, add:
   - `SECRET_KEY`: `<generate-a-random-32-char-string>`
   - `GOOGLE_API_KEY`: `<your-google-gemini-key>` *(optional)*
7. Click **Deploy Web Service**. Your app will be live on a free `https://<app-name>.onrender.com` URL!

---

### Option 2: Deploy with Docker & Docker Compose

To deploy as a containerized stack (including a managed MySQL container):

```bash
# Build and run in detached mode
docker compose up -d --build

# View logs
docker compose logs -f web

# Stop containers
docker compose down
```
The application will be accessible at `http://localhost:5000`.

---

### Option 3: Deploy on Linux VPS (Ubuntu / Debian + Nginx + Gunicorn)

1. **Clone and setup repository on your server:**
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv nginx git
   git clone https://github.com/your-username/Building-Risk-Assessment.git /var/www/seismos
   cd /var/www/seismos
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. **Create a Systemd Service:**
   ```bash
   sudo nano /etc/systemd/system/seismos.service
   ```
   Add:
   ```ini
   [Unit]
   Description=SEISMOS Gunicorn Application
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/seismos
   Environment="PATH=/var/www/seismos/.venv/bin"
   ExecStart=/var/www/seismos/.venv/bin/gunicorn wsgi:app --workers 3 --bind 127.0.0.1:5000 --timeout 120

   [Install]
   WantedBy=multi-user.target
   ```
   Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start seismos
   sudo systemctl enable seismos
   ```

3. **Configure Nginx Reverse Proxy:**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   Test and reload:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

---

## Environment Variables Reference

| Variable | Description | Required | Default |
|---|---|---|---|
| `SECRET_KEY` | Flask session encryption key | Recommended | `seismos_default_secret_key_2026` |
| `GOOGLE_API_KEY` | Google Gemini API key for live AI Consultant | Optional | *(Uses offline RAG template if omitted)* |
| `MYSQL_HOST` | MySQL hostname or IP | Optional | `localhost` |
| `MYSQL_PORT` | MySQL connection port | Optional | `3306` |
| `MYSQL_USER` | MySQL database user | Optional | `root` |
| `MYSQL_PASSWORD` | MySQL password | Optional | `""` *(Uses SQLite fallback if blank)* |
| `MYSQL_DATABASE` | MySQL database name | Optional | `seismos` |

---

## API Endpoints

### 1. `POST /predict`
Submits building parameters to the ML engine and saves result to history.

**Request Body (JSON):**
```json
{
  "model": "decision_tree",
  "age_building": 30,
  "plinth_area_sq_ft": 800,
  "superstructure": "Stone, mud mortar",
  "foundation_type": "Mud mortar-Stone/Brick",
  "other_floor_type": "TImber/Bamboo-Mud"
}
```

**Response (JSON):**
```json
{
  "damage_grade": 5,
  "risk_level": "Critical",
  "confidence": 1.0,
  "model_used": "decision_tree",
  "factors": {
    "foundation": 0.35,
    "superstructure": 0.28,
    "age": 0.17,
    "floor_type": 0.12,
    "plinth_area": 0.08
  }
}
```

### 2. `POST /api/get_consultant`
Generates a structural engineering consultation report using RAG and building codes.

---

## Maintenance & Utilities

- **Retrain Machine Learning Models:**
  ```bash
  python train_models.py
  ```
- **Reindex PDF Vector Store (ChromaDB):**
  ```bash
  python buiild_database.py
  ```
- **Initialize Database Tables:**
  ```bash
  python init_db.py
  ```

---

## Acknowledgments
- **Bureau of Indian Standards (BIS)**: Indian Standards `IS 4326` (Earthquake Resistant Design and Construction) and `IS 13828` (Improving Earthquake Resistance of Low Strength Masonry Buildings).
- **National Society for Earthquake Technology (NSET)**: 2015 Gorkha Nepal Earthquake structural survey datasets.
- **Hugging Face**: Pre-trained sentence embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
