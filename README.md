# SNOTEL Leaderboard (WIP)

Fun little web vis of the current winners and lows in the race to SNOTEL fame!

## Quick Start (Root Commands)

The project is structured with a Python backend and a TypeScript frontend. You can control everything from the root directory:

| Command | Action |
| --- | --- |
| `npm run data` | Fetch fresh SNOTEL data using the Python backend. |
| `npm run dev` | Refresh data and start the Vite development server (auto-reloads). |
| `npm run preview` | Full end-to-end update (Fetch data -> Build -> Serve). |
| `npm run build` | Refresh data and build the production static site in `frontend/dist`. |

## Manual & Submodule Commands

If you need more granular control, you can still run commands within the subdirectories:

### Backend
```bash
cd backend && uv run src/generate_leaderboard.py
```

### Frontend
```bash
cd frontend && npm run dev
```

## Validation & Deployment

### Local Validation
To run a clean end-to-end update (fetch data + build site) exactly like the deployment environment:
```bash
npm run build
```

### GitHub Pages Deployment
A GitHub Action is configured in `.github/workflows/deploy.yml` to automatically handle data fetching and deployment every 6 hours.