# 🛒 Price Watcher

A full-stack platform that tracks product prices on Lazada, Shopee, Shein, Amazon, and other e-commerce sites.  
Built with Django 5 + DRF, React 18 (Vite), Tailwind CSS v4, Celery, Redis, and Playwright.

## ✨ Key Features
- **Multi-Platform Scraping** – Playwright scripts collect price, stock, and rating data.
- **Real-Time Notifications** – Email and webhook alerts when prices hit user-defined thresholds.
- **Historical Charts** – Interactive graphs of price history, volatility, and savings.
- **Shared Wish-Lists** – Invite friends or family to track items together.
- **Bulk Tools** – CSV import/export and one-click browser extension.
- **Multi-Currency** – Auto-converts prices with live FX rates.
- **Analytics Dashboard** – Aggregate savings, best-time-to-buy insights, and store comparison.
- **Role-Based Access** – Admin, standard, and read-only roles via JWT auth.

## 🏗️ Tech Stack
| Layer      | Technology |
|------------|------------|
| Backend    | Django 5, Django REST Framework, PostgreSQL 15 |
| Auth       | djangorestframework-simplejwt |
| Tasks      | Celery 5 + Redis 7 |
| Scraping   | Playwright 1.44 (headless Chromium) |
| Frontend   | React 19, Vite 5, Tailwind CSS v4, Zustand |
| Realtime   | Django Channels / WebSocket |
| DevOps     | Docker, Docker Compose, GitHub Actions |
| Monitoring | Sentry, Prometheus, Grafana |

## 🚀 Quick Start

### 1 · Clone & Configure


```sh
git clone https://github.com/lucifron28/Price-Watcher.git
cd price-watcher
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2 · Local Run (Docker)


```sh
docker compose up --build
```

Services:
`backend:8000` `frontend:5173` `redis:6379` `worker/beat`

Services:  
`backend:8000` `frontend:5173` `redis:6379` `worker/beat`

### 3 · Developer Mode

npm i --prefix frontend

#### Backend
```sh
pyenv virtualenv 3.11 pw-env
pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver
```

#### Frontend
```sh
npm i --prefix frontend
npm run dev --prefix frontend
```

### 4 · Background Workers


```sh
celery -A backend worker -l info
celery -A backend beat -l info
```

## 🗂️ Project Structure


```
price-watcher/
├─ backend/
│  ├─ apps/
│  │  ├─ accounts/        # JWT auth & roles
│  │  ├─ products/        # Item & price models
│  │  ├─ scraping/        # Playwright tasks
│  │  ├─ notifications/   # Email & webhook logic
│  │  └─ analytics/       # ML & BI utilities
│  ├─ core/               # Django settings
│  └─ tests/
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  ├─ pages/
│  │  ├─ hooks/
│  │  └─ store/
├─ extension/             # Chrome/Firefox add-on
├─ docs/
└─ docker-compose.yml
```

## 🔌 API Examples


### Auth
```
POST /api/auth/token/
POST /api/auth/token/refresh/
```

### Products
```
GET /api/products/
POST /api/products/
GET /api/products/{id}/
DELETE /api/products/{id}/
```

### Price History
```
GET /api/products/{id}/prices/
```

### Notifications
```
POST /api/notifications/
```

## 🧪 Testing


```sh
pytest -q                # backend unit tests
pytest --cov=apps        # coverage
npm test --prefix frontend  # jest + RTL
```

## 📜 License
MIT

---

Portfolio project by **Ron Vincent Cada**.  
Showcases scalable scraping, background processing, and real-time user experience.
