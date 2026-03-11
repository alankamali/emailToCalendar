# emailToGoogleCalendar

Parses a shift schedule email from Gmail account and then exports found shifts into the linked Google Calendar. 

---
## Google Scripts Version (NEW)
Setup the same project on GS so coworkers can access the functionality on a browser. 
Click on this link and follow the prompts. 

[Google Scripts Link](https://script.google.com/macros/s/AKfycbziDZf5dSdWqWeDZdHTOQegOr2dyeRS3WZzTKHuakDe7nEgTUZ-0bX4olhmJ_Li6XDs/exec)

Since project is still only for personal use, have not got it verified yet. You will need to click on "Advanced" and then "Proceed" when warned about safety.

### Privilage Disclaimer: 
- GS can READ all your emails.
- GS has full auth control to your Calendar.

authScopes:
```
  "oauthScopes": [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar"
  ]
```
## Setup on Local Device

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Google Cloud credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Go to **APIs & Services → Library** and enable the **Gmail API**
4. Go to **APIs & Services → Credentials**
5. Click **Create Credentials → OAuth client ID**
6. Choose **Desktop App**, give it a name, and click **Create**
7. Download the credentials JSON and rename it `credentials.json`
8. Place `credentials.json` in the project root

> **Note:** On first run, a browser window will open for you to authorise access. A `token.json` file will be saved for future runs.

---

## Usage

### Fetch from Gmail (default)

```bash
python main.py
```

The app will search your Gmail for emails with subjects containing "rota", "schedule", "shifts", or "roster". You'll be shown up to 5 matching emails to choose from.

### Parse a local text file (useful for testing)

```bash
python main.py --file sample_email.txt
```

### Options

| Flag | Short | Description |
|------|-------|-------------|
| `--file PATH` | `-f` | Parse a local plain-text file instead of fetching from Gmail |
| `--query QUERY` | `-q` | Override the Gmail search query (e.g. `--query "subject:weekly rota"`) |
| `--week YYYY-MM-DD` | `-w` | Specify the Monday of the shift week to help resolve day names |

---

## Customising the parser

The shift format varies between employers. Once you have a sample email, open [shift_parser.py](shift_parser.py) and update:

- **`TIME_RANGE_PATTERN`** — the regex that detects time ranges like `09:00 - 17:00`
- **`DAY_NAME_PATTERN`** — day-of-week names to anchor each shift to a date
- **`DAY_OFF_KEYWORDS`** — words that indicate a rest day (line is skipped)

Run with a local file to test:

```bash
python main.py --file your_email.txt
```

Unmatched lines are printed to the console to help you debug the parser.

---

## Importing into Google Calendar

1. Run the app — a file named `shifts_YYYY-MM-DD.ics` will be created
2. Open [Google Calendar](https://calendar.google.com/)
3. Go to **Settings (gear icon) → Import & Export → Import**
4. Select the `.ics` file and choose which calendar to import into

---

## Timezone

The default timezone is `Europe/London`. To change it, edit `TIMEZONE` in [calendar_generator.py](calendar_generator.py).
