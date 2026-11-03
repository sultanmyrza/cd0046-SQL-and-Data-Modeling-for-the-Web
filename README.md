# Fyyur

A musical venue and artist booking site, built with Flask, SQLAlchemy and PostgreSQL.
The original project brief is in [README.original.md](README.original.md).

## Requirements

- Python 3.9 (newer versions may fail with the pinned dependencies)
- PostgreSQL, or Docker to run it

On Debian/Ubuntu, you may also need: `sudo apt install python3-venv python3-pip`

## 1. Start the database

The app connects to `postgresql://postgres:postgres@localhost:5432/fyyur`, set in `config.py`.

**Option A: Docker**

```bash
docker run -d --name fyyur-db -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fyyur -v fyyur-pgdata:/var/lib/postgresql/data postgres:16
```

**Option B: your own PostgreSQL**

```bash
createdb fyyur
```

If your username, password or port differ, edit `SQLALCHEMY_DATABASE_URI` in `config.py`.

## 2. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Set up the database

```bash
export FLASK_APP=app.py
flask db upgrade     # create the tables
python3 seed.py      # optional: add sample data (this resets all tables)
```

## 4. Run

```bash
export FLASK_ENV=development   # debugger and auto-reload
flask run
```

Then open http://127.0.0.1:5000.

In a new terminal, run `source .venv/bin/activate` and `export FLASK_APP=app.py` again first.
