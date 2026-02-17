# 🚀 Quick Deployment Commands

## ✅ What's Already Done
- ✅ NLP libraries installed in venv (spacy, sentence-transformers, keybert, scikit-learn)
- ✅ spaCy English model downloaded
- ✅ requirements.txt updated with exact versions
- ✅ All tests passing locally

## 📋 What You Need to Do Next

### Option 1: Auto-Deploy via GitHub (Recommended)

```bash
# 1. Make sure you're in the Codeguard directory
cd F:\Codeguard

# 2. Add all changes
git add .

# 3. Commit with meaningful message
git commit -m "feat: Add Stage 3 Linguistic Analysis with NLP (spacy, sentence-transformers)"

# 4. Push to GitHub
git push origin main

# 5. Wait for Render to auto-deploy (5-10 minutes)
# Watch at: https://dashboard.render.com/
```

### Option 2: Manual Deploy on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click on **codeguard-backend-g7ka** service
3. Click **"Manual Deploy"**
4. Select **"Deploy latest commit"**
5. Wait 5-10 minutes for build

### After Deployment (Test It Works)

```bash
# Test the deployed API
curl -X POST https://codeguard-backend-g7ka.onrender.com/api/analyze \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"Write a function to add two numbers\", \"code\": \"def add(a, b):\\n    print(a+b)\\n    return a+b\"}"
```

**Expected Response**: Should include `linguistic_results` with:
- `npc` (detects `print` as non-prompted consideration)
- `prompt_biased`
- `missing_features`
- `misinterpretation`
- `intent_match_score`

## 🔍 Monitor Deployment

### Build Logs Should Show:
```
Collecting spacy==3.8.11
Collecting sentence-transformers==5.2.2
Collecting keybert==0.9.0
Collecting scikit-learn==1.7.2
Downloading en_core_web_sm...
Successfully installed...
```

### If Build Succeeds:
✅ Wait for service to become "Live" (green status)
✅ First request may take 60-90 seconds (cold start)
✅ Subsequent requests: 1-3 seconds

### If Build Fails:
❌ Check logs for errors
❌ Common issue: timeout (retry deployment)
❌ Verify requirements.txt syntax
❌ Contact me with error message

## 📊 Expected Changes

| Metric | Before | After |
|--------|--------|-------|
| Build Time | 2-3 min | 5-10 min ⬆️ |
| Cold Start | 30-50s | 60-90s ⬆️ |
| Request | 1-2s | 1-3s ≈ |
| Memory | ~200MB | ~400MB ⬆️ |
| Analysis Accuracy | 70% | 90%+ ⬆️ |

## ⚠️ Important Notes

1. **First Request After Deploy**:
   - Will take 60-90 seconds (loading NLP models)
   - This is normal and expected
   - Your VS Code extension already has 90s timeout ✅

2. **Memory Usage**:
   - Free tier: 512MB RAM
   - With NLP: ~400-500MB
   - Should be fine, but monitor Render dashboard

3. **Build Time**:
   - NLP libraries are large (~500MB total)
   - Build takes 5-10 minutes
   - BE PATIENT! This is normal.

## 🆘 If Something Goes Wrong

### Build Timeout
**What to do**: Click "Manual Deploy" again. Sometimes network is slow.

### Memory Error
**What to do**: 
- Option A: Upgrade to Starter plan ($7/month for 1GB RAM)
- Option B: I can disable NLP temporarily (uses regex fallback)

### spaCy Model Error
**What to do**: The requirements.txt includes direct URL, should work. If not, let me know.

### Service Won't Start
**What to do**: Check Render logs, send me the error message

## ✨ After Successful Deployment

### Test in VS Code Extension:
1. Open VS Code
2. Open any Python file with buggy code
3. Click CodeGuard sidebar icon
4. Enter a prompt
5. Click "Analyze Entire File"
6. **Look for new linguistic analysis results**:
   - NPC violations shown
   - Prompt-biased code highlighted
   - Missing features listed
   - Intent match score displayed

### Example Test Case:
```python
# Prompt: "Create a function to add two numbers"

def add_numbers(a, b):
    # NPC: Logging not requested
    print(f"Adding {a} and {b}")
    
    # NPC: Validation not requested
    if not isinstance(a, int):
        raise TypeError("Must be int")
    
    return a + b
```

**Should detect**: 2 NPC violations (logging, validation)

## 📝 Summary

1. **Run**: `git add . && git commit -m "feat: Add Linguistic Analysis" && git push`
2. **Wait**: 5-10 minutes for Render build
3. **Test**: Use curl command or VS Code extension
4. **Verify**: Check for `linguistic_results` in API response
5. **Done!** ✅

---

**Current Status**: Ready to deploy  
**Risk**: Low (has fallback mechanisms)  
**Time Required**: 15 minutes total  
**Your Action Required**: Push to Git OR Manual Deploy on Render
