import sqlite3

conn = sqlite3.connect("library.db")
c = conn.cursor()

mapping = {
    "Kshitiz Lamsal":  "img/team/kshitiz.png",
    "Satkar Sapkota":  "img/team/Satkar Sapkota.jpg",
    "Susan Regmi":     "img/team/Susan Regmi.jpeg",
    "Ashish Gahatraj": "img/team/Ashish Gahatraj.jpg",
    "Eron Shrestha":   "img/team/Eron Shrestha.jpg",
}

for full_name, rel_path in mapping.items():
    initials = "".join([p[0] for p in full_name.split()[:2]]).upper()
    c.execute("""
        UPDATE team
           SET avatar_path = ?, initials = COALESCE(initials, ?)
         WHERE full_name = ?
    """, (rel_path, initials, full_name))

conn.commit()
conn.close()
print("Updated team avatars.")
