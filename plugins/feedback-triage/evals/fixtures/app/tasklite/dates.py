from datetime import datetime, timedelta, timezone


def parse_due(text, now=None):
    """Parse 'today', 'tomorrow', or YYYY-MM-DD into a date string."""
    now = now or datetime.now(timezone.utc)
    text = text.strip().lower()
    if text == "today":
        return now.date().isoformat()
    if text == "tomorrow":
        return (now + timedelta(days=1)).date().isoformat()
    return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
