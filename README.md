# GeneRX

GeneRX is a Django class project for CSIT327. It helps a patient look up a brand-name medicine, compare sample generic alternatives, check which sample pharmacy lists it in stock, and keep a simple scan history.

The app uses plain Django function-based views, Django templates, and small vanilla JavaScript files. There is no DRF, React, or build step.

## What works

- Register, log in, log out, edit a profile, and save settings.
- Search medicines by brand or generic name through JSON endpoints.
- View generic alternatives with sample prices.
- Filter a pharmacy list by medicine and see sample stock.
- Sort pharmacies A-Z or nearest-first with browser geolocation.
- Open Google Maps directions from a pharmacy's latitude and longitude.
- Upload a prescription image (JPG, PNG, WebP, max 5 MB) and/or type a medicine name.
- Match a typed name with `difflib`, confirm medium-confidence matches, and save scan history.
- Toggle dark mode across the signed-in pages.
- Seed the database with repeatable sample medicines and pharmacies.

## Stack

- Python 3.12+ / Django 5 or 6
- PostgreSQL on Supabase through `DATABASE_URL`
- SQLite fallback when `DATABASE_URL` is empty
- `python-dotenv` for local `.env` loading
- HTML templates, CSS, and vanilla JavaScript

## Project structure

```text
CSIT327-GeneProj/
|-- apps/
|   |-- home/              Home page (search screen)
|   |-- login/             Login and POST-only logout
|   |-- register/          Registration with password validation
|   |-- user_profile/      Profile page and Profile model
|   |-- user_settings/     Settings page, model, and context processor
|   |-- medicines/         Medicine models, JSON search, seed_medicines
|   |-- pharmacies/        Pharmacy models, locator page, seed_pharmacies
|   `-- scans/             Scan models, upload view, difflib matching, OCR placeholder
|-- config/                Settings, root URL conf, WSGI/ASGI
|-- templates/
|   |-- home/
|   |-- login/
|   |-- register/
|   |-- profile/
|   |-- user_settings/
|   |-- pharmacies/
|   `-- scans/
|-- static/
|   |-- css/shared/theme.css   Shared design tokens and shell
|   |-- css/<feature>/         Page-specific styles
|   |-- js/<feature>/          Page-specific scripts
|   `-- images/<feature>/
|-- media/                 Uploaded scans (git-ignored)
|-- manage.py
|-- requirements.txt
`-- README.md
```

Each feature owns its app, template folder, and static folders. Feature apps do not import each other in Python; cross-feature lookups use string model references or `django.apps.apps.get_model()`.

## Setup

Open PowerShell in the project folder.

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# If "python" is not on PATH, use the py launcher:
# py -m venv .venv

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Create your local environment file
Copy-Item .env.example .env
# Edit .env and replace the placeholders.

# 4. Apply the existing migrations (no data is dropped)
python manage.py migrate

# 5. Load sample data (safe to run more than once)
python manage.py seed_medicines
python manage.py seed_pharmacies

# 6. Run the development server
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. You will be sent to the login page; create an account at `/register/`.

### Environment variables

| Name | Purpose |
|---|---|
| `SECRET_KEY` | Django signing key. Use a long random value outside development. |
| `DEBUG` | `True` for local work, `False` for anything public. |
| `ALLOWED_HOSTS` | Comma-separated hosts, e.g. `127.0.0.1,localhost`. |
| `DATABASE_URL` | Supabase PostgreSQL connection string. Leave empty to use SQLite. |

Never commit the real `.env` file. Only `.env.example` with placeholders belongs in Git.

## Run the tests on SQLite

PowerShell:

```powershell
$env:DATABASE_URL=""
python manage.py test
```

`load_dotenv` does not override an existing environment variable, so the empty value keeps the test run on SQLite even when `.env` contains a Supabase URL.

Useful checks:

```powershell
python manage.py check
python manage.py test apps.medicines apps.scans
```

## URL map

| URL | Purpose |
|---|---|
| `/` | Home search page (login required) |
| `/medicines/search/?q=...` | JSON search, maximum 10 rows |
| `/medicines/<id>/generics/` | JSON medicine and generic alternatives |
| `/pharmacies/` | Pharmacy locator and stock filter |
| `/scans/` | Upload or type a medicine for matching |
| `/scans/history/` | Current user's scan history |
| `/scans/<id>/confirm/` | POST-only confirmation for a medium match |
| `/login/`, `/register/` | Authentication pages |
| `/profile/`, `/settings/` | Account pages |
| `/admin/` | Django admin |

## How a search request flows

1. `templates/home/home.html` renders the search box and gives JavaScript two URLs from Django's `{% url %}` tag.
2. `static/js/home/home.js` waits for typing, then calls `/medicines/search/?q=...` with `fetch`.
3. `apps/medicines/views.py` checks `login_required`, queries `Medicine` with `Q(brand_name__icontains=...) | Q(generic_name__icontains=...)`, limits to 10, and returns JSON.
4. The script escapes every value and builds the result cards.
5. Clicking a card calls `/medicines/<id>/generics/`, which returns the parent medicine (including `mdrp_price`) and its generic alternatives ordered by price.

## How a scan flows

1. `apps/scans/views.py` accepts `multipart/form-data`.
2. The image is checked for extension, content type, and size, then saved with `FileSystemStorage` under `MEDIA_ROOT/scans`.
3. `extract_text()` is a placeholder that returns `""` with a TODO. The UI says this honestly.
4. `find_best_match()` compares the typed name (or future OCR text) against every brand and generic name with `difflib.SequenceMatcher`.
5. Confidence above 90 saves the match; 70-90 asks for confirmation; below 70 asks for manual entry.
6. Every attempt creates a `PrescriptionScan` row, and history is filtered to `request.user`.

## Sample data warning

All medicines, prices, pharmacies, coordinates, operating hours, and stock rows are **fictional sample data for this class project**. They are not official Maximum Drug Retail Price (MDRP) figures and not live pharmacy stock. Always confirm with a pharmacist or doctor.

## Limitations

- **No real OCR.** `extract_text()` returns an empty string. Images are stored but not read. Typing the name is what produces a match.
- **No live data.** Medicine prices, pharmacy locations, stock, and hours are sample rows.
- **No embedded map.** "Get directions" opens a Google Maps URL. The nearest-first sort uses straight-line distance from browser geolocation, not road distance.
- **No email delivery.** The email toggle is saved only; no message is sent or queued.
- **No offline mode.** There is no service worker or PWA cache.
- **English only.** No translations or locale switching.
- **Development media serving.** Django serves `/media/` only while `DEBUG=True`. Production needs a web server or object storage.
- **No password reset or email verification.** Registration creates the account immediately.
- **No pagination.** Scan history renders every row for the current user.
- **Not medical advice.** The project is for demonstration, not clinical use.

## Security notes

- Rotate any Supabase credentials that were ever committed to this repository. Replacing them in `.env.example` does not remove them from Git history.
- Set `DEBUG=False`, a real `SECRET_KEY`, and the correct `ALLOWED_HOSTS` before deploying.
- Do not upload real prescriptions or personal medical records to a class demo.
