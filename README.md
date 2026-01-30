# OneClick DataScrape

OneClick DataScrape is a Django-based web application designed for scraping data, managing users, and exporting results.

## Project Structure

```
oneclick_datascrape/
│
├── config/                    # Main Django project settings
├── apps/                      # Django apps
│   ├── users/                 # Authentication & user management
│   ├── scraper/               # Scraping logic & services
│   ├── tasks/                 # Celery tasks
│   └── exports/               # Export services
├── core/                      # Core utilities & middleware
├── templates/                 # HTML templates
├── static/                    # Static assets
└── docker/                    # Docker configuration
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- MongoDB
- Redis (for Celery)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd oneclick_datascrape
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/macOS
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables:**
    Copy `.env` and update the values (especially `MONGO_URI`).

5.  **Run Migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Run the Server:**
    ```bash
    python manage.py runserver
    ```

7.  **Run Celery Worker:**
    ```bash
    celery -A apps.tasks worker --loglevel=info
    ```

## Architecture

- **Backend:** Django, Django REST Framework
- **Database:** MongoDB
- **Task Queue:** Celery + Redis
- **Scraping:** Service layer pattern
