# InsightAI — Backend

Python/Flask service that turns a raw tennis match video into a structured match log and a set of analytics reports.

You upload a video, mark the four corners of the court, and the pipeline detects the ball frame by frame, reconstructs shots, rallies, and points from the trajectory, and then runs a series of analysis modules over that reconstructed match. The output is a dashboard of insights about how you actually play, not a box score.

---

## Table of contents

- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [Analytics modules](#analytics-modules)
- [API reference](#api-reference)
- [Project structure](#project-structure)
- [Configuration](#configuration)
- [Frontend integration](#frontend-integration)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)

---

## Quick start

**Requirements:** Python 3.10+, ffmpeg available on your PATH.

```bash
cd python_backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The server starts on `http://0.0.0.0:8080`.

Then open the app in a browser and walk through the four steps: upload → configure → calibrate → process.

---

## How it works

The pipeline runs in five stages.

**1. Upload.** The user submits a match video. The file is validated before anything expensive happens — wrong sport, unusable resolution, and files that contain no detectable gameplay are rejected with a message explaining why instead of failing silently halfway through processing.

**2. Configure.** The user sets the match format: best of 3 or 5, tiebreak rules, ad or no-ad scoring, which side each player starts on. This tells the scoring engine how to assemble points into games, sets, and a final result.

**3. Calibrate.** The user clicks the four court corners on the first frame. Those points define a perspective transform that maps pixel coordinates to real court coordinates, so every bounce and contact point can be expressed in feet from the baseline and center line rather than in pixels.

**4. Process.** The heavy stage:

- Frame-by-frame ball detection using HSV color-space filtering tuned for yellow-green tennis balls, with fallback strategies for broadcast footage and low-quality phone video
- Intro and dead-time skipping, so broadcast clips with commentary and replays don't pollute the data
- Shot event detection from trajectory discontinuities — a sharp change in direction or velocity marks a contact
- Rally and point structure built from shot sequences and the configured scoring rules
- The analytics modules run in sequence over the reconstructed match

**5. Results.** Everything is returned as JSON and rendered into a results dashboard.

Processing is asynchronous. Kick it off with `/process/<match_id>` and poll `/api/status/<match_id>` for progress.

---

## Analytics modules

Each module answers a question a scoreline can't.

| Module | File | What it tells you |
|---|---|---|
| **Shot DNA** | `shot_dna.py` | Your unconscious pattern fingerprint. Uses entropy over shot-sequence transitions to find the choices you make on autopilot — and the ones an opponent could learn to predict. |
| **Counterfactual Simulator** | `counterfactual.py` | Monte Carlo simulation over critical points. Replays the moment thousands of times with a different shot choice to estimate how much a single decision actually cost you. |
| **Momentum Topology** | `momentum.py` | Momentum as a surface rather than a streak. Time-series analysis of point outcomes, rally length, and error type to show where the psychological turns happened. |
| **Shadow Self** | `shadow_ai.py` | A Markov model of your own decision-making, then a search for the strategy that beats it. Effectively scouting yourself. |
| **Fatigue Fingerprint** | `fatigue.py` | How your game degrades over time — which shot loses accuracy first, and at what point in the match it starts. |
| **Decision Heatmap** | `decision_heatmap.py` | Error rate and shot-selection quality by court zone, so you can see where you're making bad choices rather than just bad contact. |
| **Chaos / Butterfly Effect** | `chaos.py` | Identifies the low-leverage-looking points whose outcomes cascaded furthest through the rest of the match. |

`match_scoring.py` sits underneath all of them and owns the scoring state machine.

---

## API reference

### Upload

| Method | Route | Description |
|---|---|---|
| `POST` | `/upload-video` | Upload a match video. Returns a `match_id` used by every subsequent call. |

### Configuration

| Method | Route | Description |
|---|---|---|
| `GET` | `/configure/<match_id>` | Match configuration interface |
| `POST` | `/save-config/<match_id>` | Persist match format and scoring rules |

### Court calibration

| Method | Route | Description |
|---|---|---|
| `GET` | `/calibrate/<match_id>` | Calibration interface — first frame with corner picker |
| `POST` | `/save-calibration/<match_id>` | Persist the four court corner points |

### Processing

| Method | Route | Description |
|---|---|---|
| `GET` | `/process/<match_id>` | Start the detection and analysis pipeline |
| `GET` | `/api/status/<match_id>` | Poll processing progress and stage |

### Results

| Method | Route | Description |
|---|---|---|
| `GET` | `/results/<match_id>` | Full analysis output for the match |

---

## Project structure

```
python_backend/
├── main.py                     # Flask entry point and route definitions
├── config.py                   # Tunable settings (frame skip, thresholds, court dims)
├── models.py                   # Match, Shot, Rally, Point data models
├── requirements.txt
├── analysis/
│   ├── video_processor.py      # Pipeline orchestrator
│   ├── video_validator.py      # Pre-flight checks on uploaded video
│   ├── ball_detector.py        # HSV ball detection with multi-strategy fallback
│   ├── match_scoring.py        # Scoring state machine
│   ├── shot_dna.py
│   ├── counterfactual.py
│   ├── momentum.py
│   ├── shadow_ai.py
│   ├── fatigue.py
│   ├── decision_heatmap.py
│   └── chaos.py
├── templates/                  # Server-rendered views (upload, processing, results, error)
└── uploads/                    # Created at runtime
```

---

## Configuration

All tuning lives in `config.py`:

| Setting | Default | Notes |
|---|---|---|
| Frame skip | every 2nd frame | Lower for accuracy on fast rallies, higher for speed |
| Ball detection confidence | tuned for yellow-green balls | Loosen for low-light or low-resolution footage |
| Max upload size | large enough for full-match video | Raise if you're processing broadcast-length matches |
| Court dimensions | ITF singles/doubles | Used by the perspective transform |
| Analysis parameters | per module | Entropy windows, simulation counts, fatigue window size |

---

## Frontend integration

The backend is designed to run alongside the React frontend, and there are three reasonable setups:

1. **Standalone** — Flask serves its own templates. Fastest way to test the pipeline end to end.
2. **Direct** — React calls the Flask endpoints directly. Requires CORS configuration.
3. **Proxied** — the Node service handles auth and payments and proxies analysis requests to Flask. This is the intended production shape.

All three share the same JSON contract, so switching between them doesn't change the analysis code.

---

## Known limitations

Being honest about what's still rough:

- Matches and results are held in memory. Anything beyond local testing needs a real database.
- Ball detection is color-based, so it degrades on unusual court colors, heavy shadow, and low-contrast backgrounds.
- Shot classification (forehand/backhand/slice/volley) is currently a placeholder. It needs a trained pose model to be trustworthy.
- Player identification uses court-position heuristics rather than tracking, so it can confuse players after changeovers.
- Highlight reels and heavily edited footage produce unreliable rally structure.

---

## Roadmap

1. Persistence layer for matches, results, and users
2. Pose estimation for real shot classification and contact-point analysis
3. Proper player tracking instead of position heuristics
4. Auth and per-user match libraries
5. Object storage for video, so the app isn't tied to local disk
6. Joint deployment of the Python and Node services
