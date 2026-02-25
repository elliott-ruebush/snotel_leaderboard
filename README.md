# SNOTEL Leaderboard (WIP)

Fun little web vis of the current winners and losers in the race to SNOTEL fame!

## Backend SNOTEL Leaderboard Generation

```bash
cd backend && uv run src/generate_leaderboard.py
```

## Web Server

### Start Server
Run from the root to start the server in the background:
```bash
cd frontend && nohup python3 -m http.server 8000 &
```
*Note: Logs are written to `frontend/nohup.out`.*

### Stop Server
To stop the server running on port 8000:
```bash
lsof -ti :8000 | xargs kill
```
*Or manually find the PID and kill it:*
```bash
lsof -i :8000
kill <PID>
```

### View Logs
```bash
tail -f frontend/nohup.out
```