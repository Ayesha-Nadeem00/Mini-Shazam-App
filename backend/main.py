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


@app.get("/songs")
def list_songs():
    """Saare songs ki list return karta hai (Library page ke liye)."""
    from db_config import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, artist, album FROM songs ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    songs = [
        {"id": r[0], "title": r[1], "artist": r[2], "album": r[3]}
        for r in rows
    ]
    return {"songs": songs}


@app.delete("/songs/{song_id}")
def delete_song(song_id: int):
    """
    Ek song ko database se delete karta hai.
    Uske fingerprints bhi apne aap delete ho jayenge
    (schema mein ON DELETE CASCADE laga hua hai).
    """
    from db_config import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title FROM songs WHERE id = %s;", (song_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return {"status": "error", "message": "Song nahi mila."}

    cur.execute("DELETE FROM songs WHERE id = %s;", (song_id,))
    conn.commit()
    cur.close()
    conn.close()

    return {"status": "success", "message": f"'{row[0]}' delete ho gaya."}


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


@app.get("/songs")
def list_songs():
    """Saare songs ki list deta hai (Library page ke liye)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, artist, album FROM songs ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    songs = [
        {"id": r[0], "title": r[1], "artist": r[2], "album": r[3]}
        for r in rows
    ]
    return {"songs": songs}


@app.delete("/songs/{song_id}")
def delete_song(song_id: int):
    """
    Ek song ko database se delete karta hai.
    Uske saare fingerprints bhi apne aap delete ho jate hain
    (kyunke schema mein ON DELETE CASCADE lagaya tha).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM songs WHERE id = %s RETURNING id;", (song_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if deleted:
        return {"status": "success", "message": f"Song {song_id} delete ho gaya."}
    else:
        return {"status": "error", "message": "Ye song nahi mila."}


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