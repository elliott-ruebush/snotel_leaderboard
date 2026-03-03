# SNOTEL Leaderboard

Fun little web vis of the current highs and lows in the race to SNOTEL fame! 

Best viewed during the months with snow :)

See it live at: https://elliott-ruebush.github.io/snotel_leaderboard/

Updated every ~6 hours

Depends on: https://github.com/elliott-ruebush/snotel_lib

## Quick Start (Root Commands)

The project is structured with a Python backend and a TypeScript frontend. You can control everything from the root directory:

| Command | Action |
| --- | --- |
| `npm run data` | Refresh SNOTEL data using the Python backend. |
| `npm run dev` | Refresh data and start the local dev server. |
| `npm run build` | Refresh data and build the production site. |
| `npm run test` | Run all frontend (Vitest) and backend (pytest) tests. |
| `npm run test:coverage` | Run all tests and generate coverage reports. |
| `npm run validate` | Full check: run all tests and build the site. |
| `npm run preview` | Build the site and serve the production preview. |

## Manual & Submodule Commands

If you need more granular control, you can still run commands within the subdirectories:

### Backend
```bash
cd backend && uv run python -m src.generate_leaderboard
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