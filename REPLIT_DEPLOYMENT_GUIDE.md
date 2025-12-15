# 🚀 Deploy NOVUS E-Library to Replit (Free Hosting)

## **📋 Prerequisites (5 minutes)**

✅ GitHub account (free)
✅ Replit account (free)
✅ Your project pushed to GitHub

---

## **Step 1: Push Code to GitHub**

### **On Your Local Machine:**

```bash
# Navigate to your project
cd "d:\nist project\computer\e-library"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "NOVUS E-Library - Ready for Replit deployment"

# Create repo on GitHub (go to github.com, click + New Repository)
# Then link it:
git remote add origin https://github.com/YOUR_USERNAME/novus-library.git
git branch -M main
git push -u origin main
```

**Done!** Your code is now on GitHub.

---

## **Step 2: Create Replit Account**

1. Go to **https://replit.com**
2. Click **"Sign up"**
3. Sign up with GitHub (easiest)
4. Authorize Replit to access your GitHub account

---

## **Step 3: Import Your GitHub Repo to Replit**

1. On Replit, click **"+ Create"**
2. Select **"Import from GitHub"**
3. Paste your repo URL: `https://github.com/YOUR_USERNAME/novus-library`
4. Click **"Import"**
5. Wait for Replit to clone your project (2-3 minutes)

---

## **Step 4: Configure Environment Variables**

1. On the left sidebar, click the **"Secrets"** icon (🔒)
2. Add these environment variables:

```
FLASK_ENV=production
FLASK_APP=app.py
PORT=5000
SECRET_KEY=your-secret-key-here-change-this-to-something-random
```

**Generate a random SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## **Step 5: Install Dependencies**

The `.replit` file should handle this automatically, but if not:

1. Click **"Shell"** tab (terminal)
2. Run:
```bash
pip install -r requirements.txt
```

---

## **Step 6: Create/Configure .replit File**

Create a file named `.replit` in your project root:

```ini
run = "python app.py"
onBoot = "pip install -r requirements.txt"

[env]
PYTHONUNBUFFERED = "1"
FLASK_ENV = "production"

[nix]
channel = "stable-23_05"
```

**Push this to GitHub:**
```bash
git add .replit
git commit -m "Add Replit configuration"
git push
```

Then refresh your Replit project.

---

## **Step 7: Run Your App**

1. Click the **"Run"** button (top of Replit)
2. Your app should start
3. Click the **"Open in new tab"** button to view it
4. You'll get a URL like: `https://novus-library.YOUR_USERNAME.repl.co`

---

## **Step 8: Test the App**

✅ Open the generated URL
✅ Login with: **admin / 123**
✅ Browse books
✅ Check database is working

---

## **Step 9: Enable "Always On" (Optional - Paid Feature)**

For free, your app sleeps after 1 hour of inactivity. To keep it always running:

1. Click your **username** (top right)
2. Go to **"Account"** → **"Replit Plus"**
3. Subscribe ($7/month) for "Always On"

**Or use free alternative:**
- Uptime monitoring (external service pings your app every 5 minutes)
- Services like **UptimeRobot** (free) can prevent sleep

---

## **Step 10: Get a Custom Domain (Optional)**

1. In Replit project, go to **"Tools"** → **"Domains"**
2. Add your custom domain
3. Update DNS settings with your domain registrar
4. Wait 24-48 hours for propagation

---

## **📱 Share Your URL**

Your live app is now at:
```
https://novus-library.YOUR_USERNAME.repl.co
```

Share this with others! They can login and use your e-library.

---

## **⚠️ Important Notes**

### **Database Storage:**
- SQLite database (`library.db`) is stored in Replit's filesystem
- **Data persists between restarts** ✅
- **But** if you delete the Replit project, data is lost
- **For permanent backup:** Download `library.db` periodically

### **File Uploads:**
- Uploads to `static/` folders work fine
- Max storage ~5GB (free tier)
- Files persist between restarts

### **Sleep Behavior (Free Tier):**
- App goes to sleep after 1 hour with no requests
- First request after sleep takes 30-60 seconds to wake up
- Use UptimeRobot (free) to keep it awake

---

## **Troubleshooting**

### **"ModuleNotFoundError" errors:**
```bash
pip install -r requirements.txt
```

### **App won't start:**
1. Click **"Shell"** tab
2. Run: `python app.py`
3. Look for error messages
4. Fix and restart

### **Database not found:**
```bash
# In Shell:
python setup_db.py
```

### **File uploads not working:**
Check that `static/books`, `static/covers`, etc. exist:
```bash
ls -la static/
```

---

## **Keeping Your App Updated**

1. Make changes on your local machine
2. Commit and push to GitHub:
```bash
git add .
git commit -m "Your changes"
git push
```

3. In Replit:
   - Click **"Tools"** → **"Git"**
   - Click **"Pull from main"**
   - Click **"Run"** to restart

---

## **Next Steps**

✅ Your app is live!
✅ Share the URL with users
✅ Monitor usage in Replit dashboard
✅ Download backups of `library.db` regularly

---

## **Quick Reference**

| What | Where |
|------|-------|
| **Run app** | Click "Run" button |
| **View logs** | Shell tab |
| **Add env vars** | Secrets icon (🔒) |
| **Update code** | Tools → Git → Pull |
| **Custom domain** | Tools → Domains |
| **Always On** | Replit Plus ($7/month) |

---

**Questions?** Check Replit's docs: https://docs.replit.com

Happy hosting! 🎉
