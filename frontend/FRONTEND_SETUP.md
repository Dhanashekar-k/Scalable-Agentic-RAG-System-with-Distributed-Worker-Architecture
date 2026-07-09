# Frontend - Quick Start Guide

## What's New? 🎉

Your frontend now has:

✅ **Modern Landing Page** - Beautiful gradient design with system overview
✅ **User Login System** - Unique user IDs for each login session  
✅ **Protected Routes** - Dashboard only accessible after login
✅ **Multi-User Support** - Each user has isolated history and queries
✅ **User Dashboard** - Shows current user info and query history

---

## File Structure

```
frontend/src/
├── App.jsx                          # Main app with routing
├── App.css                          # Global styles
├── index.css                        # Tailwind imports
├── main.jsx                         # Entry point
├── context/
│   └── AuthContext.jsx              # User auth & session management
├── components/
│   └── ProtectedRoute.jsx           # Route guard for authenticated users
├── pages/
│   ├── LandingPage.jsx              # Home page (public)
│   ├── LoginPage.jsx                # User login (public)
│   ├── UserDashboard.jsx            # Query interface (protected)
│   ├── AdminLogin.jsx               # Admin access (existing)
│   └── AdminDashboard.jsx           # Admin panel (existing)
└── assets/
```

---

## How to Run

### 1. Install Dependencies (if not already done)

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

Server runs on: **http://localhost:5173** (or shown in terminal)

### 3. Open in Browser

```
http://localhost:5173
```

---

## Navigation Flow

```
Home Page (/)
     ↓
   [Sign In Button]
     ↓
Login Page (/login)
   ↓ Enter credentials
   ↓
Dashboard (/dashboard)
   ↓ Protected - auto-redirect to login if not authenticated
```

---

## Demo Credentials

Try logging in with any of these:

```
┌───────────┬──────────┐
│ Username  │ Password │
├───────────┼──────────┤
│ alice     │ alice123 │
│ bob       │ bob12345 │
│ demo      │ demo123  │
└───────────┴──────────┘
```

**Note:** Minimum requirements are:
- Username: 3+ characters
- Password: 6+ characters

You can use any credentials that meet these requirements!

---

## Multi-User Testing

### Test with Two Users

**Terminal 1:**
```bash
npm run dev
```

**Browser 1:**
- Open http://localhost:5173
- Click "Sign In"
- Login as: `alice` / `alice123`
- Ask a question
- See it in history

**Browser 2 (new incognito window):**
- Open http://localhost:5173
- Click "Sign In"
- Login as: `bob` / `bob12345`
- Ask a different question
- See ONLY your question in history

✅ **Each user has isolated session!**

---

## Key Features

### 1. Landing Page
- Modern gradient background
- System architecture overview
- Features highlight
- Call-to-action buttons
- Responsive design

### 2. Login Page
- Username/password input
- Error messages
- Demo credentials display
- Smooth animations
- Loading states

### 3. User Dashboard
- **Sidebar:**
  - Current user info with online status
  - Query history (per-user isolated)
  - Clear history button
  - Logout button

- **Main Area:**
  - Query input form
  - Response with markdown rendering
  - Metadata (pipeline, cache, confidence, time)
  - Source documents
  - Loading states

### 4. Session Management
- Auto-login on page reload
- Logout clears session
- User ID in all requests
- localStorage-based persistence

---

## How Multi-User Works

### User A's Request
```
Login → Gets user_id = "user_1234_abc"
          ↓
Query → sent with headers: X-User-ID: user_1234_abc
          ↓
History → stored in localStorage['niyanta_history_user_1234_abc']
          ↓
Backend → processes with user_id context
```

### User B's Request
```
Login → Gets user_id = "user_5678_xyz"
          ↓
Query → sent with headers: X-User-ID: user_5678_xyz
          ↓
History → stored in localStorage['niyanta_history_user_5678_xyz']
          ↓
Backend → processes with user_id context
```

**Result:** No mixing! Each user sees only their own queries.

---

## User Context Hook

Use user info anywhere in components:

```javascript
import { useAuth } from '../context/AuthContext';

function MyComponent() {
  const { user, logout, isAuthenticated } = useAuth();
  
  return (
    <div>
      <p>Hello, {user?.username}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

**Available properties:**
- `user.id` - Unique user identifier
- `user.username` - Login username
- `user.sessionToken` - Session token
- `user.loginTime` - ISO timestamp
- `isAuthenticated` - Boolean
- `login(username, password)` - Login function
- `logout()` - Logout function

---

## Protected Routes

Wrap routes that need authentication:

```javascript
<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <UserDashboard />
    </ProtectedRoute>
  }
/>
```

Unauthenticated users are auto-redirected to `/login`.

---

## Styling

Built with **Tailwind CSS v4**:

```javascript
// gradient buttons
className="bg-gradient-to-r from-purple-600 to-pink-600"

// Modern inputs
className="bg-gray-800 border border-gray-700 rounded-lg"

// Responsive grid
className="grid md:grid-cols-2 gap-8"
```

---

## API Integration

Queries now include user identification:

```javascript
// With user ID
const res = await fetch('/api/query', {
  headers: {
    'X-User-ID': user?.id,
    'X-Session-Token': user?.sessionToken,
  },
  body: JSON.stringify({
    user_id: user?.id,
    username: user?.username,
    query: query,
  }),
});
```

---

## Troubleshooting

### "Not authenticated" error
- Check localStorage has user session
- Clear cache: DevTools → Application → Clear Storage
- Try logging in again

### History not showing
- Make sure you're looking at the right user
- Each user has separate history
- Use incognito window to test multiple users

### Styling looks broken
- Run `npm install` to install Tailwind
- Check browser console for errors
- Hard refresh (Ctrl+Shift+R)

### Build errors
- Delete `node_modules/` and `package-lock.json`
- Run `npm install` again
- Restart dev server

---

## Production Build

```bash
npm run build
# Creates optimized build in dist/
```

---

## Environment Setup

No additional .env needed for frontend!

Backend API location is auto-detected:
- Dev: `http://localhost:8000/api`
- Production: Remote backend

---

## Next Steps

1. **Start frontend** → `npm run dev`
2. **Visit landing page** → http://localhost:5173
3. **Login** → Use any valid credentials
4. **Query** → Ask questions and get answers
5. **Test multi-user** → Open incognito window, login as different user

---

## Need Help?

Check out:
- `MULTI_USER_GUIDE.md` - Multi-user architecture details
- `README.md` - Project overview
- Backend logs - See what's happening server-side

Enjoy! 🚀
