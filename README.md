# LittleLovies Creche Management Demo

A small Flask application for a student-run toddler creche. It demonstrates child and guardian registration, consent and care-note capture, an owner-managed opening calendar, booking confirmations, cancellations, daily capacity monitoring, and basic operational totals. 

## To run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. Demo sign-in: `owner` / `littleloves123`.

## Current scope

- The owner can register a child with guardian contact, emergency contact, consent, allergy and medical-note fields.
- The owner can add and close opening dates. A date with active bookings cannot be closed until those bookings are cancelled.
- Confirmed reservations are counted against the five-child daily limit. Cancellations free a place, and the same child cannot have two active bookings on one date.
- The dashboard deliberately avoids showing care notes in its booking list.
