"""
main.py
Ye FastAPI server hai — ye hamare Python scripts (add_song, match) ko
WEB API bana deta hai, taake frontend (website) inhe call kar sake.

Chalane ka tareeqa (terminal mein):
    uvicorn main:app --reload

Phir browser mein kholein:
    http://127.0.0.1:8000/docs
(Ye ek automatic testing page hai jahan har API try kar sakte hain)
"""

import os
import shutil
import tempfile

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from add_song import add_song, get_song_count, MAX_SONGS
from match import find_match

app = FastAPI(title="Shazam Clone API")

# CORS: taake frontend (jo alag address/port pe chalega) is backend ko call kar sake
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # abhi ke liye sab allow, production mein specific URL daalna
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    """Sirf check karne ke liye ke server chal raha hai."""
    return {"message": "Shazam Clone API chal raha hai!"}


@app.get("/songs/count")
def songs_count():
    """Abhi tak kitne songs add hue hain, ye batata hai."""
    count = get_song_count()
    return {"count": count, "max": MAX_SONGS}


@app.post("/songs/add")
def api_add_song(
    title: str = Form(...),
    artist: str = Form(...),
    album: str = Form(None),
    file: UploadFile = File(...)
):
    """
    Naya song add karta hai.
    Frontend se ye is tarah call hoga: title, artist, album (text) + file (audio)
    """

    # Uploaded file ko temporarily disk pe save karein
    # (kyunke fingerprint banane ke liye file ka "path" chahiye hota hai)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    try:
        add_song(temp_path, title, artist, album)
        return {"status": "success", "message": f"'{title}' add ho gaya."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        os.remove(temp_path)  # temporary file delete kar dein, jagah bachane ke liye


@app.post("/recognize")
def api_recognize(file: UploadFile = File(...)):
    """
    Recorded audio clip lekar, database mein se match dhoondta hai.
    Frontend yahan recorded audio bhejega, aur ye gaane ka naam wapas dega.
    """

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    try:
        result = find_match(temp_path)
        if result:
            return {"status": "found", "song": result}
        else:
            return {"status": "not_found", "message": "Koi match nahi mila."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        os.remove(temp_path)