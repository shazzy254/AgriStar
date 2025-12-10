# 1. Project Scaffold & Setup

## File Tree
```text
AgriStar/
├── manage.py
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
├── AgriStar/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
├── community/
│   └── ... (standard app structure)
├── marketplace/
│   └── ...
├── ai_assistant/
│   └── ...
├── core/
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── img/
└── templates/
    ├── base.html
    ├── users/
    ├── community/
    └── marketplace/
```

## Terminal Commands (PowerShell)

Run these commands to initialize the project structure and apps.

```powershell
# 1. Create Project Directory
New-Item -ItemType Directory -Force -Path AgriStar
Set-Location AgriStar

# 2. Create Virtual Environment
python -m venv venv
.\venv\Scripts\Activate

# 3. Install Django
pip install django djangorestframework django-cors-headers Pillow python-dotenv

# 4. Start Project
django-admin startproject AgriStar .

# 5. Create Apps
python manage.py startapp users
python manage.py startapp community
python manage.py startapp marketplace
python manage.py startapp ai_assistant
python manage.py startapp core

# 6. Create Static/Template Dirs
New-Item -ItemType Directory -Force -Path static/css, static/js, static/img
New-Item -ItemType Directory -Force -Path templates/users, templates/community, templates/marketplace
New-Item -ItemType Directory -Force -Path media
```
