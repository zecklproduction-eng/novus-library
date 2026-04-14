import sqlite3

def seed_achievements():
    achievements = [
        # Manga
        ("Manga Rookie", "manga_rookie_1", "Read your first manga series.", "fa-book-open", "cyan", 1, "manga", "manga_read", 1),
        ("Manga Explorer", "manga_explorer_5", "Explore 5 different manga series.", "fa-search", "purple", 2, "manga", "manga_read", 5),
        ("Manga Enthusiast", "manga_enthusiast_10", "A dedicated manga fan. Read 10 series.", "fa-fire", "yellow", 3, "manga", "manga_read", 10),
        ("Otaku", "otaku_50_ch", "Read 50 manga chapters.", "fa-glasses", "cyan", 4, "manga", "manga_chapters", 50),
        ("Master Otaku", "master_otaku_200_ch", "The ultimate manga reader. 200 chapters completed!", "fa-crown", "purple", 5, "manga", "manga_chapters", 200),
        
        # Social
        ("Voice of Novus", "voice_novus_1", "Make your first community post.", "fa-comment-dots", "cyan", 1, "social", "posts", 1),
        ("Active Talker", "active_talker_10", "A regular in the forums. 10 posts made.", "fa-bullhorn", "purple", 2, "social", "posts", 10),
        
        # Critic / Engagement
        ("Insightful Peer", "insightful_peer_5", "Help the community with 5 comments.", "fa-lightbulb", "cyan", 1, "critic", "comments", 5),
        ("Community Regular", "community_regular_25", "Your presence is felt. 25 comments total.", "fa-users", "purple", 2, "critic", "comments", 25),
        
        # Reading / Favorites
        ("Curator", "curator_10_fav", "Build your collection with 10 favorites.", "fa-heart", "cyan", 1, "reading", "favorites", 10),
    ]

    conn = sqlite3.connect('library.db')
    c = conn.cursor()

    for name, slug, desc, icon, color, level, cat, req_type, req_val in achievements:
        try:
            # Check if slug exists
            c.execute("SELECT 1 FROM achievements WHERE slug = ?", (slug,))
            if c.fetchone():
                print(f"Skipping {name} (slug '{slug}' already exists)")
                continue
            
            c.execute("""
                INSERT INTO achievements 
                (name, slug, description, icon, badge_color, level, category, requirement_type, requirement_value, rarity, icon_type, animation_type) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'none', 'fontawesome', 'rotating')
            """, (name, slug, desc, icon, color, level, cat, req_type, req_val))
            print(f"Added achievement: {name}")
        except Exception as e:
            print(f"Error adding {name}: {e}")

    conn.commit()
    conn.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed_achievements()
