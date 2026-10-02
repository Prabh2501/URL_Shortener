from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse,RedirectResponse
from pydantic import BaseModel
from app.db import get_connection
import secrets
import string

app = FastAPI()

class URLRequest(BaseModel):
    url: str

@app.get("/")
def home():
    return FileResponse("app/static/index.html")


@app.get("/healthz")
def health():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception:
        return {"status": "database unavailable"}


@app.post("/shorten")
def shorten_url(request: URLRequest):
    if not request.url.startswith(("http://", "https://")):
        request.url = "https://" + request.url

    characters = string.ascii_letters + string.digits
    short_code = "".join(secrets.choice(characters) for _ in range(6))

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO urls (original_url, short_code) VALUES (%s, %s)",
            (request.url, short_code),
        )
        conn.commit()

    return {
        "original_url": request.url,
        "short_code": short_code
    }
@app.get("/{short_code}")
def redirect_url(short_code: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT original_url FROM urls WHERE short_code = %s",
            (short_code,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    return RedirectResponse(url=row[0])