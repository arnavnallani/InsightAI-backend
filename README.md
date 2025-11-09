# AI Tennis Coach - Python Backend

This is the Python/Flask backend that handles video processing and AI analysis for the AI Tennis Coach application.

## Structure

```
python_backend/
├── main.py                    # Flask application entry point
├── config.py                  # Configuration settings
├── models.py                  # Data models (Match, Shot, Rally, etc.)
├── requirements.txt           # Python dependencies
├── analysis/                  # Analysis modules
│   ├── __init__.py
│   ├── video_processor.py     # Video processing orchestrator
│   ├── ball_detector.py       # Tennis ball detection (OpenCV)
│   ├── shot_dna.py           # Shot DNA pattern analysis
│   ├── counterfactual.py     # What-if scenario analysis
│   ├── momentum.py           # Momentum topology mapping
│   ├── shadow_ai.py          # AI clone and counter-strategies
│   ├── fatigue.py            # Fatigue fingerprint analysis
│   ├── decision_heatmap.py   # Decision quality heatmap
│   ├── chaos.py              # Butterfly effect analysis
│   └── match_scoring.py      # Match scoring system
└── uploads/                   # Video upload directory (created at runtime)
```

## Features

### 7 Advanced Analytics

1. **Shot DNA** - Pattern fingerprinting showing unconscious decision patterns
2. **Counterfactual Simulator** - What-if analysis for critical moments
3. **Momentum Topology Map** - Psychological flow visualization
4. **Shadow Self** - AI clone that plays like you and finds counter-strategies
5. **Fatigue Fingerprint** - Performance degradation analysis
6. **Decision Heatmap** - Court zone error rate visualization
7. **Chaos Theory** - Butterfly effect moment identification

## Setup

### Installation

```bash
cd python_backend
pip install -r requirements.txt
```

### Running the Server

```bash
python main.py
```

The server will start on `http://0.0.0.0:8080`

## API Endpoints

### Video Upload
- `POST /upload-video` - Upload match video file

### Configuration
- `GET /configure/<match_id>` - Configure match settings
- `POST /save-config/<match_id>` - Save match configuration

### Court Calibration
- `GET /calibrate/<match_id>` - Court calibration interface
- `POST /save-calibration/<match_id>` - Save court corner points

### Processing
- `GET /process/<match_id>` - Start video processing and analysis
- `GET /api/status/<match_id>` - Check processing status

### Results
- `GET /results/<match_id>` - View complete analysis results

## Data Flow

1. **Upload** - User uploads match video
2. **Configure** - Set match format (best of 3, scoring rules, etc.)
3. **Calibrate** - Mark 4 court corners on first frame
4. **Process** - Video processing pipeline:
   - Frame-by-frame ball detection
   - Shot event detection (trajectory analysis)
   - Rally/point structure building
   - 7 analytics modules run in sequence
5. **Results** - Display comprehensive analysis dashboard

## Integration with Frontend

The Python backend is designed to work alongside the existing Node.js/React frontend. You can:

- **Replace mock endpoints** - Connect the React frontend to these real Python endpoints
- **Hybrid approach** - Use Python for video processing, Node for payment/auth
- **Standalone** - Run as independent Flask application with its own templates

## Technical Details

### Video Processing
- Uses OpenCV for ball detection (HSV color-space filtering)
- Court calibration via perspective transform
- Frame skip optimization (process every Nth frame)

### Analysis Algorithms
- Pattern detection using entropy calculations
- Monte Carlo simulation for counterfactual scenarios
- Time-series analysis for momentum and fatigue
- Markov models for player behavior prediction

## Configuration

Edit `config.py` to customize:
- Frame skip rate (default: every 2 frames)
- Ball detection confidence
- Court dimensions
- Analysis parameters

## Next Steps

To fully integrate with the existing app:

1. Update Node.js backend to proxy requests to Python server
2. Or connect React frontend directly to Python Flask endpoints
3. Share data models between systems (use JSON API)
4. Add authentication/authorization layer
5. Deploy both services (Node + Python) together

## Development Notes

- Currently stores matches/results in memory (use database for production)
- Ball detection tuned for yellow-green tennis balls
- Shot classification requires ML model (currently placeholder)
- Player detection uses simple court-position heuristics
