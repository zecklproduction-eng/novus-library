# 📦 DEPLOYMENT GUIDE - NOVUS E-Library

## **PHASE 1: LOCAL PREPARATION** ✅

### Step 1.1: Verify Python & Virtual Environment
```bash
# Check Python version (need 3.8+)
python --version

# Create virtual environment if not exists
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

### Step 1.2: Install All Dependencies
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installations
pip list
```

### Step 1.3: Setup Environment Variables
Create `.env` file in project root:
```bash
# Database
DATABASE_URL=sqlite:///library.db

# Flask settings
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here-change-this
DEBUG=False

# Optional: OpenAI (if using AI summaries)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxx
USE_OPENAI=0

# Optional: AI Summary TTL
AI_SUMMARY_TTL_DAYS=7
```

**⚠️ IMPORTANT:** Never commit `.env` to git!

### Step 1.4: Initialize Database
```bash
# Run this once to create database
python setup_db.py

# Verify database created
ls library.db  # Should exist
```

### Step 1.5: Test Locally
```bash
# Start development server
python app.py

# Test in browser
# Navigate to: http://localhost:5000
# Login with: admin / 123

# Check if working:
# ✅ Home page loads
# ✅ Can login
# ✅ Can upload books
# ✅ No error logs
```

---

## **PHASE 2: PREPARE FOR PRODUCTION** 🔧

### Step 2.1: Create Production Requirements
```bash
# Add production-specific packages
pip install gunicorn psycopg2-binary  # For production server + PostgreSQL

# Update requirements.txt
pip freeze > requirements.txt
```

### Step 2.2: Update app.py for Production
Your app.py already has this (check bottom):
```python
if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
```
✅ This is correct for production!

### Step 2.3: Create Procfile (for Render/Heroku)
Create file `Procfile` in root:
```
web: gunicorn app:app
```

### Step 2.4: Create Runtime.txt (optional but recommended)
```bash
python-3.11.7
```

### Step 2.5: Create .gitignore (if deploying via git)
Create `.gitignore`:
```
.env
__pycache__/
*.pyc
.venv/
venv/
library.db
*.log
.DS_Store
```

---

## **PHASE 3: CHOOSE HOSTING & PREPARE** 🚀

### Option A: **Render** (RECOMMENDED - Free tier available)

**Advantages:**
- Free tier works great for small projects
- Auto-deploys from GitHub
- PostgreSQL database included
- Easy environment variable setup

**Steps:**

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - NOVUS e-library"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Go to render.com**
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repository
   - Name: `novus-library`

3. **Configure in Render:**
   - **Runtime:** Python 3.11
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free (or Starter if you want better performance)

4. **Add Environment Variables in Render:**
   - Click "Environment"
   - Add these variables:
     ```
     FLASK_ENV=production
     SECRET_KEY=<generate-random-string>
     DEBUG=False
     DATABASE_URL=<will-provide-postgresql-url>
     ```

5. **Add PostgreSQL Database:**
   - In Render dashboard
   - Click "New +"
   - Select "PostgreSQL"
   - Name: `novus-db`
   - Copy connection string to `DATABASE_URL`

6. **Deploy**
   - Click "Deploy"
   - Wait 5-10 minutes
   - Your site will be live at: `https://novus-library.onrender.com`

---

### Option B: **Railway.app** (Good alternative)

1. Go to railway.app
2. Login with GitHub
3. Create new project
4. Select "Deploy from GitHub repo"
5. Select your repo
6. Railway auto-detects Python
7. Add PostgreSQL plugin
8. Set environment variables same as above
9. Deploy!

---

### Option C: **PythonAnywhere** (Easiest for beginners)

1. Go to pythonanywhere.com
2. Create free account
3. Upload your files via web interface
4. Configure in "Web" tab:
   - Python version: 3.11
   - Source code: /home/username/mysite
   - WSGI file: Configure to import app
5. Add environment variables in "Web" > "Environment variables"
6. Reload website
7. Live at: `https://yourusername.pythonanywhere.com`

---

## **PHASE 4: DATABASE MIGRATION** 💾

### Important: Convert SQLite → PostgreSQL (for production)

**⚠️ SQLite won't work reliably on shared hosting!**

#### Step 4.1: Create Migration Script
Create `migrate_to_postgres.py`:
```python
import sqlite3
import psycopg2
import os

sqlite_db = "library.db"
postgres_url = os.getenv("DATABASE_URL")

# Connect to both databases
sqlite_conn = sqlite3.connect(sqlite_db)
sqlite_cursor = sqlite_conn.cursor()

postgres_conn = psycopg2.connect(postgres_url)
postgres_cursor = postgres_conn.cursor()

# Get all tables
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = sqlite_cursor.fetchall()

for table_name in tables:
    table_name = table_name[0]
    print(f"Migrating {table_name}...")
    
    # Get schema
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = sqlite_cursor.fetchall()
    
    # Create table in PostgreSQL
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
    for col in columns:
        col_name = col[1]
        col_type = col[2].upper()
        # Convert SQLite types to PostgreSQL
        col_type = col_type.replace("INTEGER", "INT").replace("TEXT", "VARCHAR(255)")
        create_sql += f"{col_name} {col_type}, "
    create_sql = create_sql.rstrip(", ") + ")"
    
    try:
        postgres_cursor.execute(create_sql)
    except:
        pass
    
    # Copy data
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if rows:
        cols = [col[1] for col in columns]
        placeholders = ", ".join(["%s"] * len(cols))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders})"
        
        for row in rows:
            try:
                postgres_cursor.execute(insert_sql, row)
            except Exception as e:
                print(f"Error: {e}")

postgres_conn.commit()
postgres_cursor.close()
postgres_conn.close()
sqlite_cursor.close()
sqlite_conn.close()

print("✅ Migration complete!")
```

#### Step 4.2: Run Migration
```bash
# Set DATABASE_URL first
export DATABASE_URL=postgresql://...your-url...

# Run migration
python migrate_to_postgres.py
```

---

## **PHASE 5: PRE-DEPLOYMENT CHECKLIST** ✅

- [ ] All code committed to git
- [ ] `.env` file is in `.gitignore` (not committed)
- [ ] `requirements.txt` updated with all packages
- [ ] `Procfile` created
- [ ] `app.py` has `debug=False` for production
- [ ] Secret key is strong and random
- [ ] Database migrated to PostgreSQL (if using managed hosting)
- [ ] All environment variables configured on hosting platform
- [ ] Static files compressed (CSS, JS minified)
- [ ] No test/debug files in repository

---

## **PHASE 6: DEPLOY STEP-BY-STEP** 🎯

### Using Render (Step-by-step):

**1. Prepare GitHub Repository**
```bash
cd d:\nist project\computer\e-library

# Initialize git (if not done)
git init
git config user.name "Your Name"
git config user.email "your@email.com"

# Add all files
git add .

# Commit
git commit -m "NOVUS E-Library - Ready for deployment"

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/novus-elibrary.git

# Push
git push -u origin main
```

**2. Create Render Account**
- Go to render.com
- Sign up with GitHub
- Authorize Render to access your repos

**3. Create Web Service**
- Dashboard → "New +"
- Select "Web Service"
- Choose your GitHub repo
- Name: `novus-library`
- Region: Select closest to you
- Branch: `main`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Instance Type: Free

**4. Add Database**
- Dashboard → "New +"
- Select "PostgreSQL"
- Name: `novus-db`
- Region: Same as web service
- PostgreSQL Version: 14
- Create

**5. Link Database to Web Service**
- Go to Web Service settings
- Environment tab
- Add variable:
  ```
  DATABASE_URL = <copy from PostgreSQL service>
  ```

**6. Add Other Environment Variables**
```
FLASK_ENV=production
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
DEBUG=False
USE_OPENAI=0
AI_SUMMARY_TTL_DAYS=7
```

**7. Deploy**
- Click "Deploy"
- Wait 5-10 minutes
- Check deployment logs
- Visit your site!

---

## **PHASE 7: POST-DEPLOYMENT TESTS** 🧪

### Step 7.1: Verify Site is Live
```bash
# Visit your deployment URL
# Should see login page
```

### Step 7.2: Test Core Features
- [ ] Login works (`admin` / `123`)
- [ ] View books on home page
- [ ] Upload new book
- [ ] View book details
- [ ] Add review/rating
- [ ] Add to watchlist
- [ ] Manga section working
- [ ] Admin panel accessible
- [ ] User management works

### Step 7.3: Check Logs
```bash
# In Render dashboard
# Logs tab → look for errors
# Should see: "Running on http://0.0.0.0:5000"
```

### Step 7.4: Test Database
```bash
# Login to admin panel
# Add a test book
# Verify it appears on home page
# Check if upload persists after refresh
```

---

## **PHASE 8: OPTIONAL - CUSTOM DOMAIN** 🌐

### Add Custom Domain (Render)
1. Go to Web Service settings
2. "Custom Domains" tab
3. Enter your domain (e.g., `novus-library.com`)
4. Follow DNS instructions
5. Point domain to Render nameservers

**Cost:** Usually $10-15/year for domain

---

## **PHASE 9: MAINTENANCE & MONITORING** 📊

### Regular Tasks:
```bash
# Weekly: Check logs
# Monthly: Backup database
# Quarterly: Update dependencies
  pip install --upgrade -r requirements.txt
  
# Monitor: 
# - Render dashboard for uptime
# - Check error logs
# - Monitor storage usage
```

### Backup Database
```bash
# Export PostgreSQL backup
pg_dump DATABASE_URL > backup.sql

# Keep safe location (cloud storage)
```

---

## **TROUBLESHOOTING** 🔧

### Deployment Fails
**Check:**
1. Logs in Render dashboard
2. All environment variables set
3. `requirements.txt` complete
4. `Procfile` exists
5. No syntax errors in `app.py`

### Site Loads but No Data
**Causes:**
- Database not connected (check `DATABASE_URL`)
- Database not migrated
- Wrong credentials

**Fix:**
```bash
# SSH into deployment
# Run database initialization
python setup_db.py
```

### Slow Performance
**Solutions:**
1. Upgrade to paid instance on Render
2. Enable caching
3. Optimize database queries
4. Compress images

### Static Files Not Loading
**Fix:**
```python
# In app.py, ensure this exists:
app.static_folder = 'static'
app.static_url_path = '/static'
```

---

## **FINAL CHECKLIST** ✅

- [ ] Site is live and accessible
- [ ] All features working
- [ ] Database connected
- [ ] Logging enabled
- [ ] Backups scheduled
- [ ] Domain configured (optional)
- [ ] SSL certificate active
- [ ] Team members notified
- [ ] Documentation updated

---

## **QUICK REFERENCE**

| Platform | Cost | Setup Time | Best For |
|----------|------|-----------|----------|
| **Render** | Free/Paid | 10 min | Small-Medium projects |
| **Railway** | Pay-as-you-go | 10 min | Quick deployment |
| **PythonAnywhere** | Free/Paid | 15 min | Beginners |
| **Heroku** | Paid only | 10 min | Production apps |

---

## **NEED HELP?**

Common issues & solutions:
- **Port already in use:** Change port in `app.py`
- **Module not found:** Update `requirements.txt`
- **Database error:** Check `DATABASE_URL` format
- **Static files missing:** Clear browser cache
- **Login fails:** Check database has users

---

**🎉 Congratulations! Your site is now live!**
