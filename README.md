# SNOTEL Leaderboard (WIP)

Fun little web vis of the current winners and losers in the race to SNOTEL fame!

## Backend SNOTEL Leaderboard Generation

```bash
cd backend && uv run src/generate_leaderboard.py
```

## Web Server (Frontend)

This project uses **TypeScript** and **Vite**.

### Development
To start the development server with hot-reloading:
```bash
cd frontend && npm run dev
```

### Build & Validate
To run an end-to-end update (fetch data + build site), use the helper script:
```bash
./validate.sh
```

### GitHub Pages Deployment
A GitHub Action is configured in `.github/workflows/deploy.yml` to automatically:
1. Run the Python backend to fetch fresh SNOTEL data.
2. Build the TypeScript frontend.
3. Deploy the results to GitHub Pages every 6 hours.