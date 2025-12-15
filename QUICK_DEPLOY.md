# 🚀 QUICK START - DEPLOY IN 15 MINUTES

## **The Fastest Way: Render.com**

### 1️⃣ Push to GitHub (2 min)
```bash
cd d:\nist project\computer\e-library
git init
git add .
git commit -m "Deploy to production"
git remote add origin https://github.com/YOUR_USERNAME/novus-library.git
git push -u origin main
```

### 2️⃣ Create Render Account (1 min)
- Go to **render.com**
- Sign up with GitHub
- Authorize access

### 3️⃣ Deploy Web Service (5 min)
- Click "New +" → "Web Service"
- Select your GitHub repo
- **Name:** `novus-library`
- **Build:** `pip install -r requirements.txt`
- **Start:** `gunicorn app:app`
- Click "Deploy"

### 4️⃣ Add Database (3 min)
- Click "New +" → "PostgreSQL"
- **Name:** `novus-db`
- Copy connection string

### 5️⃣ Set Environment Variables (4 min)
In Render Web Service settings:
```
FLASK_ENV=production
SECRET_KEY=<paste: python -c "import secrets; print(secrets.token_hex(32))">
DEBUG=False
DATABASE_URL=<paste PostgreSQL connection string>
USE_OPENAI=0
```

### ✅ DONE! 
Your site is live at: `https://novus-library.onrender.com`

---

## **If You Have Issues**

| Issue | Solution |
|-------|----------|
| Build fails | Check requirements.txt, Procfile exists |
| Blank page | Check DATABASE_URL in environment variables |
| Login doesn't work | Wait 2 min, refresh browser |
| Slow to load | Upgrade to paid instance on Render |

---

## **Still Stuck?**
Read the full **DEPLOYMENT_GUIDE.md** for detailed troubleshooting!
