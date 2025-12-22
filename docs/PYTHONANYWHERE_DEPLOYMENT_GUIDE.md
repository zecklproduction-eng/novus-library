# 🚀 PYTHONANYWHERE DEPLOYMENT GUIDE - NOVUS E-Library

This comprehensive guide will help you deploy your NOVUS E-Library Flask application to PythonAnywhere.com in 20-30 minutes.

## 📋 **PRE-DEPLOYMENT CHECKLIST**

Before starting, ensure you have:
- [ ] PythonAnywhere account (free tier works for testing)
- [ ] All your project files ready
- [ ] Required environment variables noted down
- [ ] Database backup (if migrating existing data)

---

## **STEP 1: CREATE PYTHONANYWHERE ACCOUNT** ⏱️ 3 minutes

### 1.1 Sign Up
1. Go to [pythonanywhere.com](https://pythonanywhere.com)
2. Click "Start running Python in the cloud"
3. Choose "Sign up" and create your account
4. Select a username (e.g., `yourusername`)

### 1.2 Access Dashboard
- You'll be redirected to your dashboard
- Note your PythonAnywhere URL: `https://yourusername.pythonanywhere.com`

---

## **STEP 2: UPLOAD YOUR PROJECT FILES** ⏱️ 5 minutes

### Option A: Web File Manager (Recommended for beginners)

#### 2.1 Create Project Directory
1. In your PythonAnywhere dashboard, click "Files" tab
2. Navigate to `/home/yourusername/`
3. Click "+ Add another file" → "Directory"
4. Name it: `novus-library`

#### 2.2 Upload Files
1. Create these subdirectories in `novus-library`:
   - `templates/`
   - `static/`
   - `logs/` (for application logs)

2. **Upload all your files:**
   - `app.py` (main Flask app)
   - `requirements.txt` (create if missing - see below)
   - All template files to `templates/`
   - All static files to `static/`
   - Any additional Python files

#### 2.3 Create requirements.txt
Create a `requirements.txt` file in your project root with:
```txt
Flask==2.3.3
Werkzeug==2.3.7
python-dotenv==1.0.0
requests==2.31.0
pdf2image==1.17.0
Pillow==10.0.1
gunicorn==21.2.0
```

### Option B: Git Deployment (Advanced)

#### 2.1 Push to GitHub
```bash
# In your local project directory
git init
git add .
git commit -m "NOVUS E-Library ready for PythonAnywhere"
git remote add origin https://github.com/yourusername/novus-library.git
git push -u origin main
```

#### 2.2 Clone in PythonAnywhere Console
1. Go to "Consoles" tab
2. Click "Bash" console
3. Run:
```bash
cd /home/yourusername/
git clone https://github.com/yourusername/novus-library.git
```

---

## **STEP 3: SET UP VIRTUAL ENVIRONMENT** ⏱️ 3 minutes

### 3.1 Open Bash Console
1. Go to "Consoles" tab
2. Click "Start a Bash console"
3. Wait for the terminal to load

### 3.2 Create Virtual Environment
```bash
# Navigate to your project directory
cd /home/yourusername/novus-library

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3.3 Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

---

## **STEP 4: CONFIGURE WEB APP** ⏱️ 7 minutes

### 4.1 Create Web App
1. Go to "Web" tab
2. Click "+ Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10
5. Click "Next"

### 4.2 Configure Web App Settings

#### Source Code Directory
- Set to: `/home/yourusername/novus-library`

#### Working Directory  
- Set to: `/home/yourusername/novus-library`

#### Virtualenv Path
- Set to: `/home/yourusername/novus-library/venv`

### 4.3 Configure WSGI File
1. Click the WSGI configuration file link (usually shows full path)
2. Replace the entire content with:
```python
import os
import sys

# Add your project directory to the system path
project_home = '/home/yourusername/novus-library'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'your-super-secret-key-change-this-in-production'
os.environ['DEBUG'] = 'False'

# Import the Flask app
from app import app

application = app
```

3. Save the file

---

## **STEP 5: SET UP DATABASE** ⏱️ 3 minutes

### 5.1 Initialize Database
In your Bash console:
```bash
# Activate virtual environment
source /home/yourusername/novus-library/venv/bin/activate

# Navigate to project directory
cd /home/yourusername/novus-library

# Initialize database
python -c "from app import init_db; init_db()"

# Verify database was created
ls -la library.db
```

### 5.2 Create Upload Directories
```bash
# Create required upload directories
mkdir -p /home/yourusername/novus-library/static/uploads/avatars
mkdir -p /home/yourusername/novus-library/static/books
mkdir -p /home/yourusername/novus-library/static/audio
mkdir -p /home/yourusername/novus-library/static/covers
mkdir -p /home/yourusername/novus-library/static/manga

# Set proper permissions
chmod -R 755 /home/yourusername/novus-library/static/
```

---

## **STEP 6: CONFIGURE ENVIRONMENT VARIABLES** ⏱️ 2 minutes

### 6.1 Set Environment Variables
In the "Web" tab:

1. Click "Environment variables" section
2. Add these variables:
```
FLASK_ENV = production
SECRET_KEY = your-super-secret-key-change-this-in-production
DEBUG = False
DATABASE_URL = sqlite:///library.db
USE_OPENAI = 0
AI_SUMMARY_TTL_DAYS = 7
```

3. Click "Save changes"

---

## **STEP 7: RELOAD AND TEST** ⏱️ 3 minutes

### 7.1 Reload Web App
1. In the "Web" tab, click the green "Reload" button
2. Wait for the reload to complete (usually 10-30 seconds)

### 7.2 Test Your Application
1. Visit your site: `https://yourusername.pythonanywhere.com`
2. You should see the login page
3. Test login with: `admin` / `123`

### 7.3 Check for Errors
1. Go to "Web" tab → "Log files" section
2. Click "Server log" to check for any errors
3. Common issues and solutions:

#### Issue: "Module not found" error
**Solution:** Check that all dependencies are installed in virtual environment

#### Issue: "Database error"
**Solution:** Re-run database initialization

#### Issue: "Permission denied" for uploads
**Solution:** Check directory permissions and ownership

#### Issue: "Template not found"
**Solution:** Verify file structure matches expected paths

---

## **STEP 8: POST-DEPLOYMENT CONFIGURATION** ⏱️ 5 minutes

### 8.1 Test Core Features
Verify these features work:
- [ ] User login/logout
- [ ] View books on home page
- [ ] Upload new content (if publisher/admin)
- [ ] View book details
- [ ] Add to favorites/watchlist
- [ ] Manga reader (if applicable)
- [ ] Admin panel access

### 8.2 Configure Static File Serving
If static files aren't loading properly:

1. In "Web" tab, find "Static files" section
2. Add these mappings:
```
/static/  →  /home/yourusername/novus-library/static/
```

### 8.3 Set Up Custom Domain (Optional)
1. In "Web" tab → "Custom domains"
2. Follow the instructions to point your domain to PythonAnywhere

---

## **STEP 9: BACKUP AND MAINTENANCE** ⏱️ 2 minutes

### 9.1 Create Database Backup
```bash
# Create backup directory
mkdir -p /home/yourusername/backups

# Backup database
cp /home/yourusername/novus-library/library.db /home/yourusername/backups/library_$(date +%Y%m%d).db
```

### 9.2 Regular Maintenance Tasks
- **Weekly:** Check application logs for errors
- **Monthly:** Update dependencies (`pip install --upgrade -r requirements.txt`)
- **Quarterly:** Backup database and files

---

## **TROUBLESHOOTING GUIDE** 🔧

### Common Issues and Solutions

#### 1. Application Won't Start
**Symptoms:** 500 Internal Server Error
**Check:**
- WSGI file configuration
- Python path in WSGI file
- Virtual environment path
- Database initialization

**Solution:**
```bash
# Check logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log

# Verify database
python -c "import sqlite3; conn = sqlite3.connect('library.db'); print('Database OK')"

# Test app locally in console
source venv/bin/activate
python app.py  # Should run without errors
```

#### 2. Static Files Not Loading
**Symptoms:** CSS/JS files return 404
**Solution:**
- Check static file mappings in web app settings
- Verify file paths are correct
- Ensure proper permissions (755)

#### 3. Upload Functionality Not Working
**Symptoms:** File upload fails
**Solution:**
- Check upload directory permissions
- Verify MAX_CONTENT_LENGTH settings
- Check available disk space

#### 4. Database Errors
**Symptoms:** "database is locked" or similar errors
**Solution:**
```bash
# Restart web app
# Go to Web tab → Reload button

# Or restart fully
sudo service uwsgi restart
```

#### 5. Performance Issues
**Symptoms:** Slow loading times
**Solutions:**
- Enable gzip compression in web app settings
- Optimize database queries
- Use PythonAnywhere's CDN for static files

---

## **ENVIRONMENT VARIABLES REFERENCE**

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Application environment | `production` |
| `SECRET_KEY` | Flask secret key | `your-secret-key-here` |
| `DEBUG` | Debug mode | `False` |
| `DATABASE_URL` | Database connection | `sqlite:///library.db` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | `sk-...` |
| `USE_OPENAI` | Enable OpenAI features | `0` (disabled) |
| `AI_SUMMARY_TTL_DAYS` | AI summary cache duration | `7` |

---

## **DEPLOYMENT CHECKLIST** ✅

**Before going live:**
- [ ] All files uploaded correctly
- [ ] Virtual environment created and packages installed
- [ ] Database initialized
- [ ] Environment variables set
- [ ] Upload directories created with proper permissions
- [ ] WSGI file configured correctly
- [ ] Application reloads without errors
- [ ] Core functionality tested
- [ ] Admin account accessible
- [ ] Static files loading properly
- [ ] Error logging configured

**After deployment:**
- [ ] Performance monitoring set up
- [ ] Backup strategy implemented
- [ ] SSL certificate active (automatic on PythonAnywhere)
- [ ] Custom domain configured (if applicable)
- [ ] Documentation updated with new URL

---

## **QUICK REFERENCE COMMANDS**

```bash
# Activate virtual environment
source /home/yourusername/novus-library/venv/bin/activate

# Run database initialization
python -c "from app import init_db; init_db()"

# Check application logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log

# Test Flask app locally
python app.py

# Install new package
pip install package_name

# Update requirements
pip freeze > requirements.txt

# Create database backup
cp library.db backups/library_$(date +%Y%m%d).db
```

---

## **SUPPORT RESOURCES**

- **PythonAnywhere Documentation:** [pythonanywhere.com/help](https://pythonanywhere.com/help)
- **Flask Documentation:** [flask.palletsprojects.com](https://flask.palletsprojects.com)
- **Community Forums:** PythonAnywhere forums
- **Live Chat:** PythonAnywhere dashboard chat support

---

## **SECURITY NOTES** 🔒

1. **Change default passwords** immediately after deployment
2. **Use strong SECRET_KEY** for production
3. **Enable HTTPS** (automatic on PythonAnywhere)
4. **Regular backups** of database and files
5. **Monitor logs** for suspicious activity
6. **Update dependencies** regularly for security patches

---

**🎉 Congratulations! Your NOVUS E-Library is now live on PythonAnywhere!**

**Access your site at:** `https://yourusername.pythonanywhere.com`

**Default admin login:** `admin` / `123` (change immediately)

---

## **NEXT STEPS**

1. **Customize your site** with your branding
2. **Add your content** (books, manga, etc.)
3. **Set up user registration** and permissions
4. **Configure payment processing** (if applicable)
5. **Implement monitoring** and analytics
6. **Scale up** as your user base grows

For scaling options, consider upgrading to PythonAnywhere's paid plans for better performance and additional features.
