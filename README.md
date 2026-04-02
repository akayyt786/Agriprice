<p align="center">
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green" alt="Django" />
  <img src="https://img.shields.io/badge/REST_API-ff1709?style=for-the-badge&logo=django&logoColor=white" alt="DRF" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind" />
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=JSON%20web%20tokens&logoColor=white" alt="JWT" />
  <img src="https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white" alt="Render" />
  <img src="https://img.shields.io/badge/Cloudinary-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white" alt="Cloudinary" />
</p>

<h1 align="center">🌾 AgriPrice — Farmer Market Price Alert System</h1>

<p align="center">
  <strong>A real-time agricultural market price monitoring and alert platform for Indian farmers.</strong><br/>
  Stay ahead of market fluctuations with live mandi prices, smart alerts, and email notifications — powered by the official Government of India Open Data API.
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-api-reference">API Reference</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="#-environment-variables">Environment Variables</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-screenshots">Screenshots</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-license">License</a>
</p>

---

## 🎯 Overview

AgriPrice bridges the gap between Indian farmers and real-time agricultural market data. The platform fetches live commodity prices from the **Government of India's Open Data Portal** (data.gov.in), enabling farmers to:

- 📊 Monitor real-time mandi (market) prices for commodities like Wheat, Rice, Cotton, Soybean, and Sugarcane
- 🔔 Set custom price alerts with min/max thresholds and receive email notifications when prices match
- 📍 Filter prices by State, District, Commodity, and specific Mandis
- 👤 Manage their profile, location preferences, and alert subscriptions

---

## ✨ Features

### 🏠 Dashboard
- Live price cards for top 5 commodities (Wheat, Rice, Cotton, Soybean, Sugarcane)
- Recent mandi price table with real-time data
- Quick alert creation form with market search autocomplete
- Notification bell with real-time alert updates

### 📈 Market Prices Explorer
- Full-page market price browser with advanced filters
- Pagination support for browsing thousands of records
- Server-side filtering by State, District, Commodity, and Mandi
- Automatic fallback to local cache when Government API is unavailable

### 🔔 Smart Price Alerts
- Create alerts with custom crop, market, min and max price thresholds
- Automatic alert triggering when market prices match user-defined ranges
- Email notifications sent on alert trigger (via Gmail SMTP)
- Alert history with full audit trail of past triggers
- Edit, delete, and manage active alerts

### 🔐 Authentication & Security
- **Dual Authentication**: Cookie-based JWT + Django Session
- **Google OAuth 2.0**: One-click sign-in via Google account
- **Email Verification**: Account activation via email link
- **Password Reset**: Secure token-based password reset flow
- **CSRF Protection**: Django CSRF middleware enabled
- **HTTP-Only Cookies**: JWT tokens stored securely in httpOnly cookies

### 👤 User Profile
- Profile image upload (via Cloudinary)
- Location preferences (State & District) for personalized dashboard
- Password change functionality
- Account deletion option

### 🔔 Notification System
- Real-time notification dropdown with unseen count badge
- Auto-refresh every 30 seconds
- Mark-all-as-seen functionality

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.11** | Programming language |
| **Django 4.2+** | Web framework |
| **Django REST Framework** | RESTful API layer |
| **SimpleJWT** | JWT token authentication |
| **django-allauth** | Google OAuth 2.0 social login |
| **django-cors-headers** | Cross-Origin Resource Sharing |
| **drf-spectacular** | OpenAPI/Swagger documentation |
| **Gunicorn** | Production WSGI server |
| **WhiteNoise** | Static file serving in production |
| **Pillow** | Image processing |

### Database
| Technology | Purpose |
|---|---|
| **SQLite** | Local development database |
| **PostgreSQL** | Production database (via Railway) |
| **dj-database-url** | Database URL configuration |
| **psycopg2-binary** | PostgreSQL adapter |

### Cloud Services
| Service | Purpose |
|---|---|
| **Cloudinary** | Media storage (profile images, dashboard images) |
| **Gmail SMTP** | Transactional emails (alerts, verification, password reset) |
| **data.gov.in API** | Live Government mandi price data |
| **Render** | Production hosting (PaaS) |
| **Railway** | Managed PostgreSQL hosting |

### Frontend
| Technology | Purpose |
|---|---|
| **Django Templates** | Server-side HTML rendering |
| **Tailwind CSS (CDN)** | Utility-first CSS framework |
| **Vanilla JavaScript** | Client-side interactivity |
| **Lucide Icons** | Icon library |
| **Google Fonts** | Typography (Inter, Outfit, Playfair Display) |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                           │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  ┌───────────┐  │
│  │  Login Page  │  │  Dashboard   │  │  Alerts   │  │  Profile  │  │
│  │  (Glassmorp. │  │  (Live Data) │  │  (CRUD)   │  │  (Upload) │  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  └─────┬─────┘  │
└─────────┼──────────────────┼───────────────┼───────────────┼────────┘
          │       REST API (JSON)            │               │
          ▼                  ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DJANGO BACKEND (Gunicorn)                      │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Middleware Stack                           │   │
│  │  EnsureSiteDomain → CORS → Security → WhiteNoise → Session  │   │
│  │  → CSRF → AuthMiddleware → JWTAuthMiddleware → allauth       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Views/API   │  │  Auth Layer  │  │  Management Commands     │  │
│  │  - Register  │  │  - Cookie JWT│  │  - create_superuser      │  │
│  │  - Login     │  │  - Session   │  │  - setup_social_apps     │  │
│  │  - Alerts    │  │  - Google    │  │  - seed_database          │  │
│  │  - Prices    │  │    OAuth 2.0 │  │  - debug_oauth            │  │
│  │  - Profile   │  │  - Adapter   │  │  - setup_google_oauth    │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────────────┘  │
│         │                                                           │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────┐   ┌────────────────────────────────────┐
│     PostgreSQL / SQLite   │   │        External Services           │
│  ┌──────────────────────┐ │   │  ┌──────────────────────────────┐  │
│  │ User (AbstractUser)  │ │   │  │  data.gov.in API             │  │
│  │ UserProfile          │ │   │  │  (Live Mandi Prices)         │  │
│  │ Crop                 │ │   │  ├──────────────────────────────┤  │
│  │ Market               │ │   │  │  Cloudinary                  │  │
│  │ MarketPrice          │ │   │  │  (Media Storage)             │  │
│  │ AlertSubscription    │ │   │  ├──────────────────────────────┤  │
│  │ AlertHistory         │ │   │  │  Gmail SMTP                  │  │
│  │ SiteContent          │ │   │  │  (Emails & Notifications)    │  │
│  │ DashboardImage       │ │   │  └──────────────────────────────┘  │
│  └──────────────────────┘ │   └────────────────────────────────────┘
└───────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **pip** — Comes with Python
- **Git** — [Download](https://git-scm.com/downloads)
- **Government API Key** — [Get one from data.gov.in](https://data.gov.in/)

### 1. Clone the Repository

```bash
git clone https://github.com/akayyt786/farmerpricealert.git
cd farmerpricealert
```

### 2. Create a Virtual Environment

```bash
cd backend
python -m venv .venv
```

**Activate the virtual environment:**

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

<details>
<summary><strong>📦 Full Dependency List (click to expand)</strong></summary>

| Package | Purpose |
|---|---|
| `Django>=4.2,<5.1` | Web framework |
| `djangorestframework` | REST API |
| `djangorestframework_simplejwt` | JWT authentication |
| `django-allauth` | Social authentication (Google OAuth) |
| `django-cors-headers` | CORS headers |
| `django-cloudinary-storage` | Cloudinary media backend |
| `cloudinary` | Cloudinary SDK |
| `drf-spectacular` | OpenAPI schema generation |
| `gunicorn` | WSGI HTTP server |
| `whitenoise` | Static file serving |
| `psycopg2-binary` | PostgreSQL adapter |
| `dj-database-url` | Database URL config |
| `python-dotenv` | `.env` file loading |
| `python-decouple` | Settings management |
| `pillow` | Image processing |
| `requests` | HTTP client (Gov API) |
| `PyJWT` | JWT encoding/decoding |
| `social-auth-app-django` | Social auth framework |
| `social-auth-core` | Social auth core |

</details>

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Required for development
SECRET_KEY=django-insecure-replace-me-in-production
DEBUG=True

# Government API (Required for live prices)
GOV_API_KEY=your_api_key_from_data_gov_in

# Optional for local development
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_16_char_app_password
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

> **Note**: For local development, only `SECRET_KEY`, `DEBUG=True`, and `GOV_API_KEY` are strictly required. The app will use SQLite and skip email/OAuth features gracefully.

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Create a Superuser

```bash
python manage.py createsuperuser
```

### 7. Seed the Database (Optional)

```bash
python manage.py seed_database
```

This will:
- Create initial crops (Wheat, Rice, Cotton, Soybean, Sugarcane)
- Create dashboard image placeholders
- Fetch sample prices from the Gov API (if `GOV_API_KEY` is set)

### 8. Run the Development Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000** in your browser 🎉

---

## 📡 API Reference

All API endpoints require authentication (JWT cookie or session) unless noted.

### 🔓 Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/register/` | Register a new user account | ❌ Public |
| `POST` | `/api/login-cookie/` | Login and receive JWT cookies | ❌ Public |
| `GET` | `/api/logout/` | Logout and clear JWT cookies | ✅ Required |
| `GET` | `/api/verify-email/<token>/` | Verify email address | ❌ Public |
| `POST` | `/api/password-reset/` | Request password reset email | ❌ Public |
| `POST` | `/api/password-reset/confirm/` | Confirm password reset | ❌ Public |

### 👤 Profile

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/profile/me/` | Get current user profile |
| `POST/PUT` | `/api/profile/update/` | Update profile (supports multipart for image) |
| `POST` | `/api/profile/change-password/` | Change password |
| `POST/DELETE` | `/api/profile/delete/` | Delete user account |

### 📈 Market Prices

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/gov/market-prices/` | Fetch live Government mandi prices |
| `GET` | `/api/market-prices/recent/` | Get dashboard prices (top 5 + card data) |
| `GET` | `/api/markets/` | List all available markets/mandis |

**Query Parameters for `/api/gov/market-prices/`:**

| Param | Type | Description |
|---|---|---|
| `crop` | string | Filter by commodity name |
| `state` | string | Filter by state |
| `district` | string | Filter by district |
| `mandi` | string | Filter by mandi/market name |
| `page` | integer | Page number (default: 1) |

### 🔔 Alerts

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/alerts/` | Get all active alerts + history |
| `POST` | `/api/alerts/create/` | Create a new price alert |
| `PUT` | `/api/alerts/<id>/update/` | Update alert thresholds |
| `DELETE` | `/api/alerts/<id>/delete/` | Delete an alert |
| `GET` | `/api/alerts/past/` | Get past triggered alerts |

**Create Alert Request Body:**
```json
{
  "crop": "wheat",
  "market_id": 42,
  "min_price": 2000,
  "max_price": 2500
}
```

### 🔔 Notifications

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/notifications/` | Get notifications with unseen count |
| `POST` | `/api/notifications/mark-seen/` | Mark all notifications as seen |

### 📚 API Documentation (Swagger)

| Endpoint | Description |
|---|---|
| `/api/schema/` | OpenAPI 3.0 schema (JSON) |
| `/api/docs/` | Swagger UI interactive docs |
| `/api/redoc/` | ReDoc documentation |

### 🔑 Google OAuth

| Endpoint | Description |
|---|---|
| `/accounts/google/login/` | Initiate Google OAuth flow |
| `/accounts/google/login/callback/` | Google OAuth callback |

---

## 🗃 Database Models

```
┌──────────────────┐     ┌──────────────────┐
│      User        │────→│   UserProfile    │
│  (AbstractUser)  │ 1:1 │  - full_name     │
│  - email (unique)│     │  - phone         │
│  - role          │     │  - profile_image │
└──────┬───────────┘     │  - location_*    │
       │                 └──────────────────┘
       │ 1:N
       ▼
┌──────────────────┐     ┌──────────────────┐
│ AlertSubscription│────→│   AlertHistory   │
│  - target_min    │ 1:N │  - message       │
│  - target_max    │     │  - is_seen       │
│  - status        │     │  - created_at    │
└──┬───────────┬───┘     └────────┬─────────┘
   │           │                  │
   ▼           ▼                  ▼
┌──────┐  ┌────────┐      ┌─────────────┐
│ Crop │  │ Market │      │ MarketPrice │
│-name │  │-name   │◀────→│ -min_price  │
│-image│  │-state  │ N:1  │ -max_price  │
│      │  │-district│     │ -modal_price│
└──────┘  └────────┘      │ -arrival_date│
                          └──────────────┘
```

---

## 📁 Project Structure

```
farmerpricealert/
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
├── DEPLOYMENT.md                 # Deployment guide for Render + Railway
├── render.yaml                   # Render PaaS configuration
│
└── backend/                      # Django project root
    ├── .env.example              # Environment variable template
    ├── build.sh                  # Production build script (Render)
    ├── manage.py                 # Django management entry point
    ├── requirements.txt          # Python dependencies
    │
    ├── backend/                  # Django project settings
    │   ├── __init__.py
    │   ├── settings.py           # Main settings (DB, Auth, CORS, etc.)
    │   ├── urls.py               # Root URL configuration
    │   ├── wsgi.py               # WSGI application
    │   └── asgi.py               # ASGI application
    │
    └── farmerpricealert/         # Main Django app
        ├── __init__.py
        ├── admin.py              # Django admin registration
        ├── apps.py               # App configuration
        ├── models.py             # Database models (8 models)
        ├── views.py              # Views & API endpoints (~1100 lines)
        ├── urls.py               # App-level URL patterns
        ├── serializers.py        # DRF serializers
        ├── authenticate.py       # Custom Cookie JWT authentication
        ├── adapters.py           # Google OAuth social account adapter
        ├── middleware.py          # Custom middleware (JWT + Site domain)
        ├── views_oauth_debug.py  # OAuth debugging endpoints
        │
        ├── management/
        │   └── commands/
        │       ├── create_superuser_from_env.py  # Auto superuser creation
        │       ├── setup_social_apps.py          # Google OAuth DB setup
        │       ├── setup_google_oauth.py         # OAuth configuration
        │       ├── seed_database.py              # DB seeding script
        │       └── debug_oauth.py                # OAuth debugging tool
        │
        ├── templates/            # Django HTML templates
        │   ├── login.html        # Login page (glassmorphism design)
        │   ├── registration.html # Registration page
        │   ├── dashboard.html    # Main dashboard with price cards
        │   ├── marketprices.html # Market price explorer
        │   ├── alertpage.html    # Alerts management page
        │   ├── profile.html      # User profile page
        │   └── reset_password.html # Password reset flow
        │
        ├── static/
        │   └── farmerpricealert/
        │       └── images/       # Static images (backgrounds)
        │
        ├── templatetags/         # Custom Django template tags
        ├── migrations/           # Database migrations
        └── socialaccount_migrations/ # Social account migrations
```

---

## 🌍 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ Production | Django secret key (auto-generated in dev) |
| `DEBUG` | ✅ | `True` for development, `False` for production |
| `DATABASE_URL` | ✅ Production | PostgreSQL connection URL |
| `GOV_API_KEY` | ✅ | Government of India data.gov.in API key |
| `SITE_DOMAIN` | ⬜ | Production domain (default: `farmerpricealert.onrender.com`) |
| `GOOGLE_CLIENT_ID` | ⬜ | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | ⬜ | Google OAuth client secret |
| `CLOUDINARY_CLOUD_NAME` | ⬜ | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | ⬜ | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | ⬜ | Cloudinary API secret |
| `EMAIL_HOST_USER` | ⬜ | Gmail address for sending emails |
| `EMAIL_HOST_PASSWORD` | ⬜ | Gmail App Password (16-char) |
| `FRONTEND_URL` | ⬜ | Frontend URL for CORS (if separate frontend) |
| `DJANGO_SUPERUSER_EMAIL` | ⬜ | Auto-created admin email (Render deploy) |
| `DJANGO_SUPERUSER_USERNAME` | ⬜ | Auto-created admin username (Render deploy) |
| `DJANGO_SUPERUSER_PASSWORD` | ⬜ | Auto-created admin password (Render deploy) |

---

## 🚢 Deployment

### Production Stack

| Component | Service | Free Tier |
|---|---|---|
| **Web Server** | [Render](https://render.com) | ✅ Yes |
| **Database** | [Railway](https://railway.app) (PostgreSQL) | ✅ Yes |
| **Media Storage** | [Cloudinary](https://cloudinary.com) | ✅ Yes |

### Quick Deploy to Render

1. **Fork & Connect** — Fork this repo, then connect it to a new **Web Service** on Render
2. **Set Root Directory** — `backend`
3. **Set Build Command** — `./build.sh`
4. **Set Start Command** — `gunicorn backend.wsgi:application`
5. **Add Environment Variables** — See the [Environment Variables](#-environment-variables) section
6. **Deploy** — Click *Manual Deploy → Deploy latest commit*

> 📖 For a detailed step-by-step deployment guide, see **[DEPLOYMENT.md](DEPLOYMENT.md)**

### What `build.sh` Does Automatically

```bash
pip install -r requirements.txt        # Install dependencies
python manage.py collectstatic --no-input  # Bundle static files
python manage.py migrate               # Apply DB migrations
python manage.py setup_social_apps     # Configure Google OAuth in DB
python manage.py create_superuser_from_env # Create admin user
```

---

## 🔧 Management Commands

| Command | Description |
|---|---|
| `python manage.py migrate` | Apply database migrations |
| `python manage.py createsuperuser` | Create admin user interactively |
| `python manage.py create_superuser_from_env` | Create admin user from environment variables |
| `python manage.py seed_database` | Seed crops, dashboard images, and sample prices |
| `python manage.py setup_social_apps` | Configure Google OAuth social app in database |
| `python manage.py setup_google_oauth` | Full Google OAuth setup and configuration |
| `python manage.py debug_oauth` | Debug OAuth configuration and print diagnostic info |
| `python manage.py collectstatic` | Collect static files for production |
| `python manage.py runserver` | Start development server |

---

## 🔒 Security Features

- **Password Hashing**: Django's PBKDF2 with SHA256
- **JWT in httpOnly Cookies**: Prevents XSS token theft
- **CSRF Protection**: Django CSRF middleware + token validation
- **Secure Proxy Headers**: `SECURE_PROXY_SSL_HEADER` configured for Render
- **Session/CSRF Cookie Security**: `Secure` flag enabled in production
- **Password Validators**: Length, common password, numeric, and user-attribute checks
- **Email Enumeration Prevention**: Generic responses on password reset
- **Input Sanitization**: Username slugification, email normalization

---

## 🐛 Troubleshooting

| Issue | Solution |
|---|---|
| `SECRET_KEY` error on startup | Set `SECRET_KEY` in `.env` or ensure `DEBUG=True` |
| Google OAuth "third-party error" | Ensure callback URL is added to Google Cloud Console |
| Emails not sending | Use a Gmail **App Password** (not login password) |
| Database connection error | Check `DATABASE_URL` or ensure SQLite is accessible |
| Static files 404 | Run `python manage.py collectstatic` |
| `ModuleNotFoundError` | Activate virtual environment and run `pip install -r requirements.txt` |
| Admin login fails | Re-create superuser or set `DJANGO_SUPERUSER_*` env vars and redeploy |
| Gov API returns empty | Verify `GOV_API_KEY` is valid at data.gov.in |

---

## 🗺 Roadmap

- [ ] 📱 Progressive Web App (PWA) support
- [ ] 📊 Price trend charts and historical analytics
- [ ] 🌐 Multi-language support (Hindi, Marathi, Punjabi, etc.)
- [ ] 📲 SMS/WhatsApp alert notifications
- [ ] 🤖 ML-based price prediction and recommendations
- [ ] 🗓 Seasonal crop calendar integration
- [ ] 🧑‍🌾 Farmer community forum

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m "Add amazing feature"`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Arman Katia** — [@akayyt786](https://github.com/akayyt786)

---

<p align="center">
  <strong>⭐ Star this repo if it helped you! ⭐</strong><br/>
  <sub>Built with ❤️ for Indian farmers</sub>
</p>
