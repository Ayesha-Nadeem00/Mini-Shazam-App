"""
add_song.py
Ye script ek gaana leta hai, uska fingerprint banata hai,
aur database mein save kar deta hai.

Isay hum 500 baar chalayenge (har gaane ke liye ek baar)
taake hamari poori library ban jaye.
"""

import sys
from db_config import get_connection
from fingerprint import generate_fingerprint

MAX_SONGS = 500  # Aapki limit


def get_song_count():
    """Database mein abhi kitne songs hain, ye check karta hai."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM songs;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


def add_song(audio_path, title, artist, album=None):
    """
    Ek song ko poori tarah process karke database mein daalta hai:
    1. Pehle check: limit (500) to nahi cross ho rahi
    2. songs table mein entry banata hai
    3. Us song ka fingerprint banata hai
    4. Saare fingerprints ko fingerprints table mein save karta hai
    """

    # Step 1: Limit check karein
    current_count = get_song_count()
    if current_count >= MAX_SONGS:
        print(f"❌ Limit poori ho chuki hai! Abhi {current_count} songs hain, "
              f"max {MAX_SONGS} allowed hain. Naya song add nahi ho sakta.")
        return

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Step 2: songs table mein basic info save karein
        cur.execute(
            "INSERT INTO songs (title, artist, album) VALUES (%s, %s, %s) RETURNING id;",
            (title, artist, album)
        )
        song_id = cur.fetchone()[0]
        print(f"📀 Song save hua, ID = {song_id}")

        # Step 3: Fingerprint banayein
        print("🎵 Fingerprint bana rahe hain, thora time lagega...")
        fingerprints = generate_fingerprint(audio_path)
        print(f"✅ {len(fingerprints)} fingerprints bane.")

        # Step 4: Saare fingerprints ko ek saath (bulk) database mein daalein
        # Ek ek karke insert karna slow hota, isliye executemany use karte hain
        data_to_insert = [
            (song_id, hash_val, time_offset)
            for hash_val, time_offset in fingerprints
        ]
        cur.executemany(
            "INSERT INTO fingerprints (song_id, hash, time_offset) VALUES (%s, %s, %s);",
            data_to_insert
        )

        # Changes ko permanently save karein
        conn.commit()
        print(f"🎉 '{title}' by {artist} successfully add ho gaya! "
              f"(Total songs ab: {current_count + 1}/{MAX_SONGS})")

    except Exception as e:
        conn.rollback()  # Kuch ghalat hua to changes wapas revert kar dein
        print("❌ Error aaya:", e)

    finally:
        cur.close()
        conn.close()


# ==============================
# Isay terminal se is tarah chalayein:
# python add_song.py "song.mp3" "Song Title" "Artist Name" "Album Name"
# ==============================
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print('Use: python add_song.py "path/to/song.mp3" "Title" "Artist" "Album(optional)"')
        sys.exit(1)

    audio_path = sys.argv[1]
    title = sys.argv[2]
    artist = sys.argv[3]
    album = sys.argv[4] if len(sys.argv) > 4 else None

    add_song(audio_path, title, artist, album)