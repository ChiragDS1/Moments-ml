# Moments — ML Edition

Enhancements to **Moments** (Flask photo-sharing app) that add two Gemini-powered features:

- **Automatic alternative text (ALT) generation** for images when users don’t provide a description.
- **Image search by recognized objects** (keywords detected in each image).

These changes are additive and backwards-compatible with the original project structure. You can still run `init-app`, seed with `lorem`, and start the server exactly as before. fileciteturn0file0

---

## What’s new

### 1) ML-powered features
- **Auto ALT text**: On upload, if a photo has no description, the app calls Google’s Gemini to generate a concise, objective ALT text (<=160 chars) and stores it in `Photo.auto_alt_text`.
- **Recognized objects**: On upload, the app extracts salient objects/labels from the image and stores them as JSON in `Photo.auto_tags_json` (e.g., `["bridge","sunset","dog"]`). These power keyword search and UI badges on the photo page.
- **Backfill**: A CLI command generates these fields for existing photos.

### 2) Minimal data model changes
The `Photo` model adds:
```py
auto_alt_text = mapped_column(String(160))
auto_tags_json = mapped_column(Text)
```
Run a migration (see setup) or apply to your DB directly for development.

### 3) Search enhancements
- Default search still uses Whooshee. You can either:
  - **Option A (cleaner):** add `auto_alt_text` and an `objects_index` property to the Whooshee index and reindex once.
  - **Option B (quick):** augment the `/search` route to include ML matches in results (keeps pagination for Whooshee but appends ML-only matches).

### 4) UI improvements
- The image `<img>` now uses **manual description** if present, otherwise **auto ALT** (and shows a small “Auto” badge).
- “**Convert to manual**” button lets the author adopt the AI text into the `description` field in one click.
- **Recognized objects** render as clickable pills beneath tags; clicking runs `/search?q=<object>`.

---

## Requirements

- Python 3.10+
- [PDM](https://pdm.fming.dev) (or a venv + pip)
- Packages: `google-generativeai`, `Pillow`, `flask-migrate` (plus the app’s existing dependencies)

---

## Installation

Clone the repo:

```
$ git https://github.com/ChiragDS1/Moments-ml.git
$ cd Moments-ml
```

With PDM (recommended):
Install dependencies with [PDM](https://pdm.fming.dev):
```
python -m pip install --user pdm
pdm venv create -w
pdm install
```
Or with virtualenv + pip:
python -m venv .venv
# Windows:
```
.venv\Scripts\activate
```
# macOS/Linux:
```
source .venv/bin/activate

pip install -r requirements.txt

```

## Configure environment variables:
Create a file named .env in the project root:
```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

## Initialize the database:
# If migrations/ doesn’t exist yet
```
pdm run flask db init
```
# Create and apply the schema
```
pdm run flask db migrate -m "init schema"
pdm run flask db upgrade
```
> [!TIP]
> If you don't have PDM installed, you can create a virtual environment with `venv` and install dependencies with `pip install -r requirements.txt`.

To initialize the app, run the `flask init-app` command:

```
$ pdm run flask init-app
```

If you just want to try it out, generate fake data with `flask lorem` command then run the app:

```
$ pdm run flask lorem
```

It will create a test account:

* email: `admin@helloflask.com`
* password: `moments`

Now you can run the app:

```
$ pdm run flask run
* Running on http://127.0.0.1:5000/
```
