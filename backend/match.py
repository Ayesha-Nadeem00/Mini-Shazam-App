"""
match.py
Ye script ek CHHOTI recording (jaise 5-10 second ka clip, mic se record kiya
hua ya bheja hua) leta hai, aur database mein se best matching song dhoondta hai.

BASIC IDEA:
1. Clip ka fingerprint banayein (wahi function jo add_song.py mein use hua)
2. In fingerprints ke hashes ko database ke fingerprints se match karein
3. Jis song ke sabse zyada "consistent" matches milein, wahi asal gaana hai

"Consistent" ka matlab: agar clip database wale gaane ka hi hissa hai, to
clip_time aur original_song_time ka FARQ (offset) hamesha ek jaisa rahega
saare matching hashes mein. Yehi trick shor/noise ke bawajood sahi match
dhoondne mein madad karti hai.
"""

import sys
from collections import defaultdict
from db_config import get_connection
from fingerprint import generate_fingerprint


def find_match(audio_clip_path):
    """
    Recorded clip ka path lekar, best matching song return karta hai.
    """

    print("🎤 Recording ka fingerprint bana rahe hain...")
    clip_fingerprints = generate_fingerprint(audio_clip_path)
    print(f"✅ {len(clip_fingerprints)} fingerprints bane clip ke.")

    if len(clip_fingerprints) == 0:
        print("❌ Clip se koi fingerprint nahi bana. Audio check karein.")
        return None

    conn = get_connection()
    cur = conn.cursor()

    # Step 1: Clip ke saare hashes ek list mein nikal lein
    clip_hashes = [h for h, t in clip_fingerprints]

    # Step 2: Database mein in hashes ko dhoondein
    # (IN query se ek hi baar mein saare match check ho jate hain — fast hai)
    cur.execute(
        "SELECT song_id, hash, time_offset FROM fingerprints WHERE hash = ANY(%s);",
        (clip_hashes,)
    )
    db_matches = cur.fetchall()  # [(song_id, hash, db_time_offset), ...]
    cur.close()
    conn.close()

    if not db_matches:
        print("❌ Database mein koi bhi matching hash nahi mila.")
        return None

    # Step 3: Clip ke hash -> clip_time ka ek dictionary banayein (jaldi dhoondne ke liye)
    clip_hash_to_time = {}
    for h, t in clip_fingerprints:
        clip_hash_to_time[h] = t

    # Step 4: Har match ke liye "offset" nikalein: db_time - clip_time
    # Agar ye offset kayi hashes mein baar baar ek jaisa aaye,
    # to us song ka match bohot strong hai.
    song_offset_votes = defaultdict(lambda: defaultdict(int))
    # structure: song_offset_votes[song_id][offset] = kitni baar aaya

    for song_id, db_hash, db_time in db_matches:
        clip_time = clip_hash_to_time.get(db_hash)
        if clip_time is None:
            continue
        offset = round(db_time - clip_time, 1)  # 0.1 sec tak round karke thora tolerance dete hain
        song_offset_votes[song_id][offset] += 1

    # Step 5: Har song ka sabse bara "vote count" nikalein
    # (yani: us song mein sabse zyada baar konsa offset repeat hua)
    best_song_id = None
    best_score = 0

    for song_id, offsets in song_offset_votes.items():
        max_votes_for_this_song = max(offsets.values())
        if max_votes_for_this_song > best_score:
            best_score = max_votes_for_this_song
            best_song_id = song_id

    # Step 6: Agar score bohot kam hai, to "no match" bol dein (galat match se bachne ke liye)
    MIN_CONFIDENCE_VOTES = 5  # ye number aap test karke tune kar sakte hain

    if best_song_id is None or best_score < MIN_CONFIDENCE_VOTES:
        print(f"❌ Koi confident match nahi mila (best score: {best_score}).")
        return None

    # Step 7: Best song ki details nikal kar dikhayein
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, artist, album FROM songs WHERE id = %s;", (best_song_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        title, artist, album = result
        print(f"🎉 Match mil gaya! '{title}' by {artist} (confidence score: {best_score})")
        return {"title": title, "artist": artist, "album": album, "score": best_score}

    return None


# ==============================
# Isay terminal se is tarah chalayein:
# python match.py "recorded_clip.mp3"
# ==============================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Use: python match.py "path/to/clip.mp3"')
        sys.exit(1)

    clip_path = sys.argv[1]
    find_match(clip_path)