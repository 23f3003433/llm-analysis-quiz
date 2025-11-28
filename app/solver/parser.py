import re
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import hashlib

def compute_email_cutoff(email: str) -> int:
    h = hashlib.sha1(email.encode()).hexdigest()
    value = int(h[:8], 16)
    return value % 50000

def extract_submit_url(html: str) -> str | None:
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # JS submit_url = "..."
    scripts = soup.find_all("script")
    for s in scripts:
        if s.string:
            m = re.search(r'submit_url\s*=\s*"([^"]+)"', s.string)
            if m:
                return m.group(1)

            m = re.search(r'window\.submit_url\s*=\s*"([^"]+)"', s.string)
            if m:
                return m.group(1)

    # <form action="...">
    form = soup.find("form", action=True)
    if form:
        action = form["action"].strip()
        if "submit" in action:
            return action

    # Audio format
    m = re.search(r"POST to JSON to\s+(https?://\S+/submit)", html)
    if m:
        return m.group(1)

    # Any URL containing /submit
    text = soup.get_text(" ", strip=True)
    m = re.search(r"(https?://\S+/submit\S*)", text)
    if m:
        return m.group(1)

    # <span class="origin">
    origin_el = soup.find(class_="origin")
    if origin_el:
        origin = origin_el.get_text(strip=True)
        return origin.rstrip("/") + "/submit"

    return None


def extract_answer_from_audio(html: str, csv_bytes: bytes, email: str) -> int:
    cutoff = compute_email_cutoff(email)
    df = pd.read_csv(StringIO(csv_bytes.decode()), header=0)
    col = df.iloc[:, 0]
    return int((col > cutoff).sum())
