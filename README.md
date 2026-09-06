# ScholarHub

ScholarHub is a Flask + SQLAlchemy workspace for discovering scholarships and organizing university applications.

## Included

- Student registration, login, logout, and role-aware admin access
- Dashboard with application, deadline, and saved-opportunity summaries
- Scholarship search and filters for country, degree level, and funding
- Saved scholarships and scholarship detail pages
- University explorer with official links and tuition context
- Application tracker with status updates and deadlines
- Personal document manager
- Seeded demo data for immediate exploration
- SQLite by default, with MySQL support through `DATABASE_URL`
- Responsive interface for desktop and mobile screens
- Google-powered scholarship and university admissions update feed with caching

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`.

The database is created automatically in `instance/scholarhub.db` on first run.

## Demo accounts

- Student: `hafiz@example.com` / `password`
- Admin: `admin@example.com` / `password`

Change the secret key and demo passwords before deployment.

## Google updates feed

The Live updates page uses Google's Programmable Search JSON API to collect public results for scholarship and admissions queries. It refreshes at most every 30 minutes and keeps results in the local database so students can browse them inside Afghan ScolarHub.

1. Create a Programmable Search Engine and configure it to search the web or a curated set of official university and scholarship domains.
2. Enable the Custom Search JSON API in Google Cloud and create an API key.
3. Add `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` to `.env`.
4. Adjust `GOOGLE_SEARCH_QUERIES` if you want different searches.
5. Open **Live updates**, or use **Sync now** in the admin console.

Google results are discovery signals, not verified eligibility decisions. Students should always open the official source before acting on a deadline or requirement.

## MySQL

Set `DATABASE_URL` in `.env` to a SQLAlchemy URL, for example:

```text
mysql+pymysql://username:password@localhost/scholarhub
```

## Production notes

Use a production WSGI server, disable Flask debug mode, set a strong `SECRET_KEY`, and add CSRF protection and file storage before accepting public uploads.
