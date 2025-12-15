# 📚 NOVUS E-Library to Replit: Complete Step-by-Step Tutorial

## **⏱️ Time Required: 30 minutes**

---

## **PART 1: PREPARE YOUR PROJECT (5 minutes)**

### **Step 1.1 - Open Your Project Folder**

1. Open **File Explorer** (Windows)
2. Navigate to: `d:\nist project\computer\e-library`
3. Right-click in empty space
4. Select **"Open in Terminal"** (or **"Open PowerShell here"**)

**You should see:**
```
PS D:\nist project\computer\e-library>
```

---

### **Step 1.2 - Check Your Files**

Run this command to list your project files:
```powershell
ls
```

**You should see files like:**
- app.py
- requirements.txt
- Procfile
- static/ (folder)
- templates/ (folder)
- library.db (database)

---

### **Step 1.3 - Create .replit Configuration File**

This tells Replit how to run your Flask app.

**Run this command:**
```powershell
New-Item -Path ".replit" -ItemType File -Force
```

**Then open `.replit` in VS Code and add this content:**

```ini
run = "python app.py"
onBoot = "pip install -r requirements.txt"

[env]
PYTHONUNBUFFERED = "1"
FLASK_ENV = "production"

[nix]
channel = "stable-23_05"
```

**Save the file** (Ctrl+S)

---

### **Step 1.4 - Check requirements.txt**

Make sure your `requirements.txt` has everything needed:

```powershell
cat requirements.txt
```

**It should look like:**
```
flask>=2.0
python-dotenv
requests>=2.28.0
pdf2image
werkzeug
Pillow
gunicorn>=20.1.0
```

If `gunicorn` is missing, add it:
```powershell
echo "gunicorn>=20.1.0" >> requirements.txt
```

---

## **PART 2: INITIALIZE GIT & PUSH TO GITHUB (10 minutes)**

### **Step 2.1 - Initialize Git Repository**

In your terminal, run:

```powershell
git init
```

**Expected output:**
```
Initialized empty Git repository in d:\nist project\computer\e-library\.git
```

---

### **Step 2.2 - Add All Files to Git**

```powershell
git add .
```

This stages all your files for commit (no output = success).

---

### **Step 2.3 - Check Git Status**

```powershell
git status
```

**You should see:**
```
On branch master/main

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   app.py
        new file:   requirements.txt
        ... (more files)
```

---

### **Step 2.4 - Create Your First Commit**

```powershell
git config --global user.email "your.email@example.com"
git config --global user.name "Your Name"
```

Replace with your actual name and email.

Then commit:
```powershell
git commit -m "NOVUS E-Library - Initial commit for Replit deployment"
```

**Expected output:**
```
[master (root-commit) abc1234] NOVUS E-Library - Initial commit
 XX files changed, XXXXX insertions(+)
```

---

### **Step 2.5 - Create GitHub Repository**

1. Go to **https://github.com** in your browser
2. Click the **"+"** icon (top right)
3. Select **"New repository"**

**Fill in:**
- **Repository name:** `novus-library` (or any name you like)
- **Description:** "NOVUS E-Library - Free hosting platform"
- **Public/Private:** Public (so Replit can access it)
- **Do NOT initialize with README** (you already have code)

**Click "Create repository"**

---

### **Step 2.6 - Connect Your Local Git to GitHub**

GitHub will show you commands to run. In your PowerShell terminal:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/novus-library.git
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME`** with your actual GitHub username.

**Expected output:**
```
Enumerating objects: XX, done.
Counting objects: 100% (XX/XX), done.
...
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

### **Step 2.7 - Verify on GitHub**

1. Go to **https://github.com/YOUR_USERNAME/novus-library**
2. You should see all your project files there ✅

---

## **PART 3: CREATE REPLIT ACCOUNT (3 minutes)**

### **Step 3.1 - Sign Up on Replit**

1. Go to **https://replit.com** in your browser
2. Click **"Sign up"** (top right)

**Two options:**
- **Option A (Easier):** Click **"Sign up with GitHub"** → Authorize Replit
- **Option B:** Enter email and create password

**I recommend Option A.**

---

### **Step 3.2 - Verify Email**

If you signed up with email, check your inbox and click the verification link.

---

## **PART 4: IMPORT PROJECT TO REPLIT (5 minutes)**

### **Step 4.1 - Import from GitHub**

1. After logging into Replit, click **"+ Create"** (top left)
2. Click **"Import from GitHub"**
3. Paste your GitHub URL:
   ```
   https://github.com/YOUR_USERNAME/novus-library
   ```
4. Click **"Import"**

**Wait 2-3 minutes** while Replit clones your project...

---

### **Step 4.2 - Replit Sets Up Your Project**

You'll see a screen with your project files on the left.

**On the right, you'll see:** Code editor

**At the bottom:** Shell terminal

---

## **PART 5: ADD ENVIRONMENT VARIABLES (3 minutes)**

### **Step 5.1 - Open Secrets Panel**

On the left sidebar, click the **🔒 Secrets** icon (below "Files")

---

### **Step 5.2 - Add Environment Variables**

Click **"+ New Secret"** and add these (one by one):

**Secret 1:**
- **key:** `FLASK_ENV`
- **value:** `production`
- Click **"Add Secret"**

**Secret 2:**
- **key:** `FLASK_APP`
- **value:** `app.py`
- Click **"Add Secret"**

**Secret 3:**
- **key:** `PORT`
- **value:** `5000`
- Click **"Add Secret"**

**Secret 4:**
- **key:** `SECRET_KEY`
- **value:** Generate one using this command in your local PowerShell:
  ```powershell
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Copy the output (looks like: `a1b2c3d4e5f6...`)
- Paste it as the value
- Click **"Add Secret"**

---

### **Step 5.3 - Verify Secrets**

Your Secrets panel should now show:
```
FLASK_ENV = production
FLASK_APP = app.py
PORT = 5000
SECRET_KEY = a1b2c3d4e5f6...
```

---

## **PART 6: INSTALL DEPENDENCIES (2 minutes)**

### **Step 6.1 - Open Shell Terminal**

At the bottom of Replit, click the **"Shell"** tab

---

### **Step 6.2 - Install Requirements**

Type this command:
```bash
pip install -r requirements.txt
```

**Wait while packages install** (you'll see scrolling text)

**When done, you should see:**
```
Successfully installed flask-2.X.X python-dotenv-0.X.X ...
```

---

## **PART 7: RUN YOUR APP (2 minutes)**

### **Step 7.1 - Click the Run Button**

At the top of Replit, click the big **"Run"** button

---

### **Step 7.2 - Watch Your App Start**

In the terminal below, you should see:
```
* Running on http://0.0.0.0:5000
```

This means your Flask app is running! ✅

---

### **Step 7.3 - Open Your Live App**

Click the **"Open in new tab"** button that appears (top right)

**Or** click the preview pane on the right to see your app

---

## **PART 8: TEST YOUR APP (5 minutes)**

### **Step 8.1 - Login**

When your app opens, you should see the **login page**

Enter:
- **Username:** `admin`
- **Password:** `123`
- Click **"Login"**

---

### **Step 8.2 - Explore Features**

✅ Click on books to view them
✅ Check if the database is working
✅ Try uploading a new book (if admin)
✅ Check all pages load correctly

---

### **Step 8.3 - Check Your Live URL**

Your app is now live at a URL like:
```
https://novus-library.YOUR_USERNAME.repl.co
```

**This URL is public!** Anyone can access it. Share it with friends/users.

---

## **PART 9: KEEP YOUR APP RUNNING (Optional)**

### **Problem: Free Apps Fall Asleep**

On Replit's free tier, your app goes to sleep after 1 hour with no activity.

**Solution A: Use UptimeRobot (Free)**

1. Go to **https://uptimerobot.com**
2. Sign up (free account)
3. Click **"Add Monitor"**
4. Select **"HTTP(s)"**
5. Enter your Replit URL: `https://novus-library.YOUR_USERNAME.repl.co`
6. Set interval to **5 minutes**
7. Click **"Create"**

Now UptimeRobot pings your app every 5 minutes, keeping it awake! ✅

**Solution B: Pay for Always On**

1. In Replit, click your **username** (top right)
2. Go to **"Account"** → **"Replit Plus"**
3. Pay $7/month for "Always On"

---

## **PART 10: BACKUP YOUR DATABASE (Important!)**

### **Step 10.1 - Download Your Database**

Your SQLite database (`library.db`) contains all your data!

In Replit:
1. Click **"Files"** (left sidebar)
2. Find **`library.db`**
3. Right-click → **"Download"**
4. Save it to your computer (backup location)

**Do this regularly** (weekly recommended) to prevent data loss!

---

## **PART 11: UPDATE YOUR APP (When You Make Changes)**

### **Step 11.1 - Make Changes Locally**

Edit files on your computer in VS Code.

---

### **Step 11.2 - Commit and Push**

In your local PowerShell terminal:

```powershell
git add .
git commit -m "Updated: [describe your changes]"
git push
```

**Example:**
```powershell
git commit -m "Updated: Added new book categories"
```

---

### **Step 11.3 - Pull in Replit**

In Replit:
1. Click **"Tools"** (top right)
2. Click **"Git"**
3. Click **"Pull from main"**
4. Click **"Run"** to restart your app

Your app is now updated! ✅

---

## **TROUBLESHOOTING**

### **Problem: "Module not found" Error**

```bash
pip install -r requirements.txt
```

### **Problem: Database errors**

```bash
python setup_db.py
```

### **Problem: App won't start**

1. Click **"Shell"** tab
2. Run: `python app.py`
3. Look at the error message
4. Fix the issue and try again

### **Problem: Can't upload files**

Make sure folders exist:
```bash
mkdir -p static/books static/covers static/audio static/manga
```

### **Problem: App is too slow**

- This might be Replit's free tier limitations
- Consider upgrading to **Replit Pro** or **Railway.app**

---

## **✅ CONGRATULATIONS! Your App is Live!**

### **What You've Done:**

✅ Prepared your project
✅ Created a GitHub repository
✅ Imported to Replit
✅ Configured environment variables
✅ Installed dependencies
✅ Deployed your Flask app
✅ Tested it works
✅ Set up automatic wake-up
✅ Created a backup

---

## **📱 Share Your App**

Your live URL:
```
https://novus-library.YOUR_USERNAME.repl.co
```

**Send this link to friends, family, or users!**

They can:
- Login with `admin/123`
- Browse books
- Read chapters
- And more!

---

## **🎯 Next Steps**

1. **Add real content:** Upload actual books to your library
2. **Create user accounts:** Let others sign up
3. **Customize branding:** Update site title, logo, colors
4. **Monitor performance:** Check Replit stats regularly
5. **Regular backups:** Download `library.db` weekly

---

## **📞 Need Help?**

- **Replit Docs:** https://docs.replit.com
- **Flask Docs:** https://flask.palletsprojects.com
- **GitHub Help:** https://docs.github.com

---

**Happy hosting! 🎉**
