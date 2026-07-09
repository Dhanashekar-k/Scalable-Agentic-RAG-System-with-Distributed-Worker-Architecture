# Scalable RAG Frontend - Complete Setup Guide

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager
- Scalable RAG backend running on `http://localhost:8000`

## Installation Steps

### 1. Navigate to Frontend Directory

```bash
cd ingestion-frontend
```

### 2. Install Dependencies

```bash
npm install
```

This will install:
- React 18.2.0
- React Router DOM 6.20.1
- React Markdown 9.0.1
- Remark GFM 4.0.0
- Vite 5.0.8
- Tailwind CSS 3.4.0
- And all dev dependencies

### 3. Start Development Server

```bash
npm run dev
```

The app will start on `http://localhost:3000`

### 4. Open in Browser

Navigate to `http://localhost:3000`

## Verify Backend Connection

The frontend expects the backend to be running on `http://localhost:8000`.

Test the connection:

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "services": {...}
}
```

## Usage Guide

### Adding a Source

1. Go to **Sources** page
2. Paste a URL in the input field:
   - GitHub: `https://github.com/expressjs/express`
   - Webpage: `https://docs.python.org/3/tutorial/`
   - YouTube: `https://www.youtube.com/watch?v=VIDEO_ID`
   - Reddit: `https://www.reddit.com/r/Python/comments/...`
   - RSS: `https://example.com/feed.xml`
3. Or upload a PDF file
4. Click "Ingest Source"
5. Watch the progress update every 3 seconds

### Asking Questions

1. Go to **Chat** page
2. (Optional) Select a source from the dropdown to filter
3. Type your question in the input field
4. Press Enter or click "Send"
5. View the answer with citations
6. Click on source links to view original documents

### Generating Digests

1. Go to **Sources** page
2. Find a completed ingestion
3. Click "Generate Digest"
4. View the summarized sections
5. Copy to clipboard if needed

## Troubleshooting

### Port Already in Use

If port 3000 is already in use, edit `vite.config.js`:

```js
export default defineConfig({
  server: {
    port: 3001, // Change to any available port
    // ...
  }
})
```

### Backend Connection Failed

Check if backend is running:

```bash
curl http://localhost:8000/health
```

If not running, start the backend:

```bash
cd ../backend
python main.py
```

### CORS Errors

The Vite proxy should handle CORS automatically. If you see CORS errors:

1. Check `vite.config.js` proxy configuration
2. Ensure backend is running on port 8000
3. Restart the dev server

### Styling Issues

If Tailwind styles aren't loading:

1. Check `tailwind.config.js` content paths
2. Ensure `postcss.config.js` exists
3. Restart the dev server

### Module Not Found

If you see "Module not found" errors:

```bash
rm -rf node_modules package-lock.json
npm install
```

## Development Tips

### Hot Module Replacement

Vite provides instant HMR. Changes to React components will update without full page reload.

### Component Development

Components are in `src/components/`:
- `Layout.jsx` - Main layout wrapper
- `SourceCard.jsx` - Individual source display
- `SourceFilter.jsx` - Source dropdown filter
- `DigestModal.jsx` - Digest generation modal

### Page Development

Pages are in `src/pages/`:
- `HomePage.jsx` - Landing page
- `SourcesPage.jsx` - Source management
- `ChatPage.jsx` - Q&A interface

### Styling

Tailwind utility classes are used throughout. Custom colors are defined in `tailwind.config.js`:

```js
colors: {
  'claude-bg': '#F5F5F3',
  'claude-surface': '#FFFFFF',
  'claude-border': '#E5E5E0',
  'claude-text': '#2C2C2C',
  'claude-accent': '#CC785C',
  // ...
}
```

### API Calls

All API calls use the `/api` prefix which is proxied to `http://localhost:8000`:

```js
// This calls http://localhost:8000/ingest/list
fetch('/api/ingest/list')
```

## Building for Production

### 1. Build

```bash
npm run build
```

Output: `dist/` directory

### 2. Preview

```bash
npm run preview
```

Serves the production build locally.

### 3. Deploy

Deploy the `dist/` directory to any static hosting:
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

**Important**: Update the API proxy configuration for production. You'll need to:

1. Set the backend URL as an environment variable
2. Update API calls to use the production backend URL
3. Configure CORS on the backend to allow your frontend domain

Example production API configuration:

```js
// Create .env.production
VITE_API_URL=https://api.yourdomain.com

// Update API calls
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
fetch(`${API_URL}/ingest/list`)
```

## Performance Optimization

### Code Splitting

Vite automatically code-splits by route. Each page is loaded on demand.

### Image Optimization

Place images in `public/` directory for static assets.

### Bundle Analysis

```bash
npm run build -- --mode analyze
```

## Testing

### Manual Testing Checklist

- [ ] Home page loads correctly
- [ ] Navigation works (Home, Sources, Chat)
- [ ] Can add a GitHub repo URL
- [ ] Can upload a PDF
- [ ] Ingestion progress updates
- [ ] Can view source list
- [ ] Can delete a source
- [ ] Can generate digest
- [ ] Can ask questions in chat
- [ ] Source filter works
- [ ] Citations are clickable
- [ ] Markdown renders correctly

### Browser Testing

Test in:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Common Issues

### Issue: Blank Page

**Solution**: Check browser console for errors. Usually a missing dependency or import error.

### Issue: Styles Not Loading

**Solution**: 
```bash
npm run dev -- --force
```

### Issue: API Calls Failing

**Solution**: Check Network tab in browser DevTools. Verify backend is running and accessible.

### Issue: Slow Performance

**Solution**: 
- Check if backend is responding slowly
- Reduce polling interval in SourcesPage (currently 3 seconds)
- Enable React DevTools Profiler to identify bottlenecks

## Next Steps

1. **Customize Design**: Edit `tailwind.config.js` to change colors
2. **Add Features**: Create new components in `src/components/`
3. **Improve UX**: Add loading states, error boundaries, toast notifications
4. **Add Analytics**: Integrate Google Analytics or similar
5. **Add Tests**: Set up Jest and React Testing Library

## Support

For issues or questions:
1. Check browser console for errors
2. Check Network tab for failed API calls
3. Verify backend is running and healthy
4. Review this setup guide

## Success! 🎉

You now have a fully functional, Claude AI-inspired frontend for Scalable RAG's knowledge ingestion and Q&A platform.

Key features:
- ✅ Clean, professional design
- ✅ Multi-source ingestion
- ✅ Real-time progress tracking
- ✅ Q&A with citations
- ✅ Source filtering
- ✅ Auto-generated digests
- ✅ Responsive layout
- ✅ Fast performance with Vite
