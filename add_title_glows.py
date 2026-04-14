import sqlite3

def add_title_glows():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    glows = [
        ('Gold Aura', 'Premium gold shining animation', 400, 'title_glow', 'title-glow-gold'),
        ('Neon Pulse', 'Cyberpunk neon flashing colors', 500, 'title_glow', 'title-glow-neon'),
        ('Hellfire Glow', 'Intense fiery animated text', 600, 'title_glow', 'title-glow-fire'),
        ('Matrix Core', 'Digital green scrolling matrix effect', 450, 'title_glow', 'title-glow-matrix'),
        ('Ethereal Shine', 'Heavenly white glowing effect', 700, 'title_glow', 'title-glow-ethereal')
    ]
    
    for name, desc, price, type_, val in glows:
        c.execute("SELECT id FROM shop_items WHERE value=?", (val,))
        if not c.fetchone():
            c.execute("INSERT INTO shop_items (name, price, type, value) VALUES (?, ?, ?, ?)",
                      (name, price, type_, val))
            print(f"Added {name}")
    
    conn.commit()
    conn.close()
    print("Done")

if __name__ == '__main__':
    add_title_glows()
