# LittleLovies Creche Management Demo

A small Flask application for a student-run toddler creche. It demonstrates child and guardian registration, consent and care-note capture, an owner-managed opening calendar, booking confirmations, cancellations, daily capacity monitoring, and basic operational totals. JSON file storage keeps the demo simple and does not require a separate database service.

All people and contact details in `data.json` are synthetic. Do not enter real children's or families' information: this demo is not designed or approved for production use.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. Demo sign-in: `owner` / `littleloves123`.

The demo has a deliberately seeded daily-capacity boundary defect for the review and testing exercise. The application stores sensitive registration fields in a local JSON file and uses lightweight demo authentication; production use would require a security, privacy, safeguarding, backup and regulatory review, plus controlled access and durable storage.

## Current scope

- The owner can register a child with guardian contact, emergency contact, consent, allergy and medical-note fields.
- The owner can add and close opening dates. A date with active bookings cannot be closed until those bookings are cancelled.
- Confirmed reservations are counted against the five-child daily limit. Cancellations free a place, and the same child cannot have two active bookings on one date.
- The dashboard deliberately avoids showing care notes in its booking list.

The sample dates are in the JSON file and should be updated there for a fresh demo period. This is a local single-owner teaching prototype, not a multi-user or concurrent booking service.
