# Quick Start - 3 Steps

## Step 1: Install

```bash
npm install
```

## Step 2: Start Backend

In a separate terminal:

```bash
cd ../backend
python main.py
```

Backend should be running on `http://localhost:8000`

## Step 3: Start Frontend

```bash
npm run dev
```

Frontend will open on `http://localhost:3000`

## That's It!

Open `http://localhost:3000` in your browser.

### Try It Out

1. **Add a Source**
   - Go to Sources page
   - Paste: `https://github.com/expressjs/express`
   - Click "Ingest Source"
   - Wait ~2 minutes for completion

2. **Ask Questions**
   - Go to Chat page
   - Select "expressjs/express" from dropdown
   - Ask: "What are the main features of Express?"
   - See answer with citations

3. **Generate Digest**
   - Go to Sources page
   - Click "Generate Digest" on the Express source
   - View summarized issues, PRs, and commits

## Troubleshooting

**Backend not running?**
```bash
cd ../backend
python main.py
```

**Port 3000 in use?**
Edit `vite.config.js` and change port to 3001

**Dependencies not installed?**
```bash
rm -rf node_modules package-lock.json
npm install
```

## What You Get

- 🎨 Claude AI-inspired design
- 📥 Multi-source ingestion (GitHub, web, PDF, YouTube, Reddit, RSS)
- 💬 Q&A with cited sources
- 📊 Auto-generated digests
- 🔍 Source filtering
- ⚡ Real-time progress updates

Enjoy! 🚀
