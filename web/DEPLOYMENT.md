# Deployment Guide

## Quick Start Commands

### To run locally:
```bash
cd web
npm install
npm run dev
```

### To build for production:
```bash
npm run build
npm run preview
```

## Deployment Options

### 1. Vercel (Recommended)
```bash
npm install -g vercel
vercel --prod
```

### 2. Netlify
```bash
npm run build
# Upload dist/ folder to Netlify
```

### 3. GitHub Pages
```bash
npm install --save-dev gh-pages
npm run build
npx gh-pages -d dist
```

## Configuration

### Update API Endpoint
Edit `src/components/TryModel.jsx`:
```javascript
const apiUrl = 'https://your-api-url.onrender.com/predict';
```

### Update Personal Information
Edit the following files:
- `src/components/Contact.jsx` - Contact details
- `src/components/Navbar.jsx` - GitHub links
- `src/components/HeroSection.jsx` - Project links

