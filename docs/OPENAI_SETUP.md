# 🔑 OpenAI API Key Setup Guide

## ⚠️ SECURITY NOTE
**Your previous API key was exposed.** You MUST:
1. Delete the old key immediately
2. Create a new key
3. Configure it following this guide

---

## Step-by-Step Setup

### Step 1: Create New API Key
1. Go to **[https://platform.openai.com/api-keys](https://platform.openai.com/account/api-keys)**
2. Click **"Create new secret key"**
3. Copy the key (⚠️ you can only see it once!)
4. Keep it safe

### Step 2: Add Key to Your Project

**OPTION A: Using .env File (RECOMMENDED)**

1. Create a file named `.env` in your project root:
   ```
   d:\nist project\computer\e-library\.env
   ```

2. Add your key to the file:
   ```
   OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE
   USE_OPENAI=true
   OPENAI_MODEL=gpt-4-turbo
   ```

3. **NEVER commit this to GitHub** - it's in `.gitignore`

4. Save and close

---

**OPTION B: Using Windows Environment Variables**

1. Edit the batch file:
   ```
   d:\nist project\computer\e-library\setup_openai_key.bat
   ```

2. Replace `PASTE_YOUR_NEW_KEY_HERE` with your actual key

3. Run the batch file as Administrator

4. **Close all terminals** and reopen

---

### Step 3: Verify Configuration

Run this command:
```powershell
cd "d:\nist project\computer\e-library"
python -c "import os; key = os.environ.get('OPENAI_API_KEY'); print('✓ API Key configured!' if key and len(key) > 20 else '✗ API Key NOT configured')"
```

Expected output:
```
✓ API Key configured!
```

---

## Testing the Setup

### Test OLD AI Feature (Text Summaries)

Create this test file:

```python
import os
from app import call_openai_summary

text = "Once upon a time, there was a brave hero who saved the kingdom..."
summary = call_openai_summary(text)
print("Old AI Works:", summary)
```

### Test NEW AI Feature (Image Summary)

Create this test file:

```python
from image_summary_ai import ImageSummaryAI

ai = ImageSummaryAI()
# Test with an image from static/covers
summary = ai.summarize_book_cover('static/covers/cover.jpg')
print("New AI Works:", summary)
```

---

## 🔄 How Both AI Features Work Together

```
┌─────────────────────────────────────────────────────┐
│          Your E-Library Application                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. TEXT SUMMARIZATION (Existing)                   │
│     - Summarizes book/chapter text                  │
│     - Uses: /api/summarize                          │
│     - Model: gpt-3.5-turbo or gpt-4-turbo          │
│                                                      │
│  2. IMAGE ANALYSIS (NEW)                            │
│     - Reads manga pages                             │
│     - Analyzes book covers                          │
│     - Uses: /api/manga/page/.../summarize           │
│     - Uses: /api/book/.../cover/analyze             │
│     - Model: gpt-4-turbo (vision enabled)          │
│                                                      │
│  Both use the SAME OpenAI API Key                   │
│  ⚠️ If key changes, BOTH must be reconfigured       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## ✅ Checklist Before Starting Server

- [ ] Created new API key at platform.openai.com
- [ ] Added key to `.env` file OR environment variables
- [ ] Verified key with test command above
- [ ] Old AI text summaries work
- [ ] New AI image analysis works

---

## 🚀 Start Your Application

Once configured:

```powershell
cd "d:\nist project\computer\e-library"
python app.py
```

Both AI features will work automatically!

---

## 🆘 Troubleshooting

### "API Key not configured"
- [ ] Check `.env` file exists
- [ ] Verify OPENAI_API_KEY line has correct format
- [ ] Make sure there are no extra spaces or quotes

### "Invalid API Key"
- [ ] Copy key again from platform.openai.com
- [ ] Make sure you copied the entire key
- [ ] Verify no extra characters

### "Old summaries stopped working"
- [ ] They use the SAME API key
- [ ] Check if key has quota remaining
- [ ] Verify model setting is correct

### "Image analysis very slow"
- [ ] Normal - GPT-4 Vision takes 3-10 seconds
- [ ] Check your internet connection
- [ ] Verify image format (JPG/PNG/GIF/WebP)

---

## 💰 Cost Considerations

**GPT-4 Turbo (Vision) is more expensive than GPT-3.5:**
- Text summaries: ~$0.01-0.05 per call
- Image analysis: ~$0.01-0.10 per image (depends on size)
- Consider caching summaries to save costs

**Monitor usage at:** https://platform.openai.com/account/usage

---

## 📝 Summary

| Feature | Status | API Key | Model |
|---------|--------|---------|-------|
| Text Summaries | ✅ Working | Shared | gpt-4-turbo |
| Manga Summaries | ⏳ Needs Key | Shared | gpt-4-turbo |
| Cover Analysis | ⏳ Needs Key | Shared | gpt-4-turbo |
| Text Extraction | ⏳ Needs Key | Shared | gpt-4-turbo |

**Everything uses ONE API key - keep it secure!**

---

Got questions? Let me know! 🚀
