# lumaStay PMS

A deployable hotel operations dashboard built with Flask, HTML, CSS, and vanilla JavaScript.

## Run locally

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3 -m pip install -r requirements.txt
py -3 app.py
```

Open `http://127.0.0.1:5000` in your browser. The deployment health check is available at `http://127.0.0.1:5000/health`.

For production, run the WSGI server with:

```powershell
gunicorn --bind 0.0.0.0:$env:PORT app:app
```

The dashboard includes occupancy and revenue reporting, arrivals and departures, a live room board, housekeeping priorities, responsive navigation, and an interactive arrival confirmation action. Replace the in-memory data in `app.py` with a database layer when persistence is needed.
