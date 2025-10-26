# LineLink - Real-Time Transmission Line Stress Predictor

**OSU Hackathon - AEP Challenge Submission**

A predictive alert system that monitors transmission line stress under changing weather conditions and sends automated notifications when lines approach dangerous loading levels.

---

## 🎯 Project Overview

### The Challenge
The electrical grid is at risk of being pushed past its limits as weather conditions change. AEP Transmission Planners need real-time visibility into:
1. When lines will exceed safe limits under different weather conditions
2. Which lines show stress first as temperatures rise
3. Overall system stress severity

### Our Solution
LineLink is a web-based dashboard that:
- **Fetches live weather data** from OpenWeatherMap API
- **Calculates dynamic line ratings** using IEEE-738 standard
- **Predicts 24-hour ahead** line loading conditions
- **Sends automated alerts** via SMS/Email when lines approach limits
- **Visualizes stress** on interactive maps and charts

---

## ✨ Key Features

### 1. Real-Time Monitoring
- Live weather conditions (temperature, wind speed)
- Current line loading percentages for all 40+ lines
- System health dashboard (normal/warning/critical counts)

### 2. 24-Hour Predictive Alerts
- Hourly forecast of line ratings
- Automated identification of critical periods
- "Peak stress time" detection

### 3. Multi-Channel Notifications
- **SMS alerts** via Twilio (top 3 critical lines)
- **Email alerts** with detailed tables
- Configurable thresholds (default: 80% warning, 95% critical)

### 4. Interactive Visualization
- **Color-coded map**: Lines change color based on loading (green → yellow → red → gray)
- **Forecast charts**: Multi-axis chart showing temperature, loading, and critical line count
- **Priority tables**: Auto-sorted by loading percentage

### 5. Scenario Testing
- Sliders to test different temperatures (20-50°C) and wind speeds (0-20 ft/s)
- Instant recalculation of all line ratings
- "What-if" analysis for planning

---

## 🏗️ Architecture

```
Frontend (HTML/JS/Bootstrap)
    ↓ HTTP Requests
Backend (Flask API)
    ↓ Coordinates
├── Weather Service → OpenWeatherMap API
├── Calculation Engine → IEEE-738 Library
├── Alert Manager → Logic for thresholds
└── Notification Service → Twilio/SendGrid APIs
```

### Tech Stack
- **Backend**: Python 3.12, Flask, Pandas
- **Frontend**: Bootstrap 5, Chart.js, Leaflet.js
- **APIs**: OpenWeatherMap, Twilio (SMS), SendGrid (Email)
- **Data**: IEEE-738 calculations, CSV grid data

---

## 📦 Installation

### Prerequisites
- Python 3.12+
- Git
- API Keys (see Step 3)

### Step 1: Clone and Setup Environment

```bash
# Create project directory
mkdir LineLink
cd LineLink

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### Step 2: Install Dependencies

Create `requirements.txt`:
```
Flask==3.0.0
Flask-CORS==4.0.0
pandas==2.1.4
requests==2.31.0
python-dotenv==1.0.0
APScheduler==3.10.4
twilio==8.10.0
sendgrid==6.11.0
geojson==3.1.0
pydantic==2.5.0
```

Install:
```bash
pip install -r requirements.txt
```

### Step 3: Get API Keys

#### OpenWeatherMap (Required)
1. Sign up: https://openweathermap.org/api
2. Free tier: 1,000 calls/day
3. Copy your API key

#### Twilio (Optional - for SMS)
1. Sign up: https://www.twilio.com/try-twilio
2. Free $15 credit
3. Get: Account SID, Auth Token, Phone Number
4. Verify your personal phone

#### SendGrid (Optional - for Email)
1. Sign up: https://sendgrid.com/
2. Free tier: 100 emails/day
3. Create API key with "Mail Send" permission
4. Verify sender email

### Step 4: Configure Environment

**Copy the `.env.example` file to create your `.env` file:**

```bash
cd backend
cp .env.example .env
```

Then edit `.env` with your actual API keys:
```bash
# REQUIRED: OpenWeatherMap API Key
OPENWEATHER_API_KEY=your_actual_api_key_here

# OPTIONAL: Twilio (SMS alerts)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890

# OPTIONAL: SendGrid (Email alerts)
SENDGRID_API_KEY=your_key
SENDGRID_FROM_EMAIL=verified@email.com

# Alert Recipients (comma-separated)
ALERT_RECIPIENTS_SMS=+1234567890
ALERT_RECIPIENTS_EMAIL=your@email.com

# Grid Location (Hawaii test data)
GRID_LATITUDE=21.3099
GRID_LONGITUDE=-157.8581

# Alert Thresholds (%)
CRITICAL_THRESHOLD=95
WARNING_THRESHOLD=80

# Database (SQLite)
DATABASE_URL=sqlite:///linelink.db
```

**Note:** The system will work with just the OpenWeatherMap API key. SMS and email notifications are optional.

### Step 5: Copy Data Files

Copy hackathon data to `backend/data/`:
- `lines.csv`
- `line_flows_nominal.csv`
- `conductor_library.csv`
- `buses.csv`
- `oneline_lines.geojson`

### Step 6: Project Structure

Your project should be organized as follows:
```
LineLink/
├── backend/
│   ├── app.py                    # Main Flask app
│   ├── init_db.py                # Database initialization script
│   ├── .env                      # API keys (copy from .env.example)
│   ├── .env.example              # Environment variable template
│   ├── requirements.txt          # Python dependencies
│   ├── linelink.db              # SQLite database (created on first run)
│   │
│   ├── data/                     # Grid data
│   │   ├── lines.csv
│   │   ├── line_flows_nominal.csv
│   │   ├── conductor_library.csv
│   │   ├── buses.csv
│   │   └── oneline_lines.geojson
│   │
│   ├── modules/                  # Business logic modules
│   │   ├── __init__.py
│   │   ├── weather.py           # OpenWeatherMap integration
│   │   ├── calculations.py       # IEEE-738 line rating calculator
│   │   ├── alerts.py            # Alert generation logic
│   │   └── notifications.py      # SMS/Email notifications
│   │
│   ├── database/                 # Database layer
│   │   ├── __init__.py
│   │   ├── db.py                # Connection management
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── repositories.py      # Data access layer
│   │
│   └── ieee738/                  # IEEE-738 calculation library
│       ├── __init__.py
│       └── conductor.py         # Thermal rating calculations
│
└── frontend/
    ├── index.html
    └── static/
        ├── css/
        │   └── style.css
        └── js/
            ├── dashboard.js
            ├── map.js
            └── charts.js
```

---

## 🚀 Running the Application

### Step 1: Initialize the Database (First Time Only)

```bash
cd backend
python init_db.py
```

You should see:
```
============================================================
LineLink Database Initialization
============================================================

Initializing database...
✓ Database tables created successfully

Running health check...
✓ Database is healthy
  Location: linelink.db
  Tables created: alert_history, weather_readings, line_rating_history, system_logs

============================================================
Database initialization complete!
============================================================
```

**Optional**: Initialize with test data:
```bash
python init_db.py --test-data
```

**Database Management Commands:**
```bash
# Check database health
python init_db.py --health-check

# Reset database (WARNING: deletes all data)
python init_db.py --reset
```

### Step 2: Start the Backend Server

```bash
cd backend
python app.py
```

You should see:
```
============================================================
LineLink - Transmission Line Stress Predictor
============================================================

Database: ✓ Connected
  Tables: alert_history, weather_readings, line_rating_history, system_logs

Loaded 77 transmission lines
Weather service: ✓ Active
SMS alerts: ✓ Enabled (or ⚠ Disabled if not configured)
Email alerts: ✓ Enabled (or ⚠ Disabled if not configured)

Starting server...
Dashboard: http://localhost:5000
API Docs: http://localhost:5000/api/health

Press Ctrl+C to stop
```

### Step 3: Access the Dashboard

Open browser: **http://localhost:5000**

Test the API health endpoint:
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2025-01-25T14:30:00",
  "services": {
    "weather": true,
    "calculations": true,
    "notifications": true,
    "database": true
  },
  "database": {
    "healthy": true,
    "tables": ["alert_history", "weather_readings", "line_rating_history", "system_logs"]
  }
}
```

---

## 📖 User Guide

### Dashboard Overview

#### Left Column
- **Current Conditions**: Live temperature and wind speed
- **System Health**: Count of lines in each status (normal/warning/critical/overload)
- **Active Alerts**: Lines currently exceeding thresholds
- **Test Scenario**: Sliders to simulate different weather conditions

#### Right Column
- **Transmission Network Map**: Interactive map with color-coded lines
  - 🟢 Green: <80% loading (normal)
  - 🟡 Yellow: 80-95% (warning)
  - 🔴 Red: 95-100% (critical)
  - ⚫ Gray: >100% (overload)
- **24-Hour Forecast**: Chart showing predicted conditions
- **Critical Lines Table**: List of lines requiring attention

### Using the System

#### View Line Details
1. Click any line on the map
2. Popup shows: loading %, flow, rating, status

#### Run Scenario Test
1. Adjust temperature slider (20-50°C)
2. Adjust wind speed slider (0-20 ft/s)
3. Click "Run Scenario"
4. Dashboard updates with new calculations

#### Send Manual Alerts
1. Click "📤 Send Alerts Now"
2. System sends SMS + Email to configured recipients
3. Toast notification confirms delivery

#### Monitor Forecast
- Chart auto-updates every 5 minutes
- Red zone indicates predicted critical periods
- Hover over chart for detailed values

---

## 🔌 API Reference

### GET `/api/current-conditions`
Returns current weather and line ratings

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-01-25T14:30:00",
  "weather": {
    "temperature": 28.5,
    "wind_speed": 8.2,
    "description": "clear sky"
  },
  "system_health": {
    "total_lines": 40,
    "overloaded": 0,
    "critical": 2,
    "warning": 5,
    "normal": 33,
    "avg_loading": 45.3,
    "max_loading": 96.2
  },
  "lines": [...]
}
```

### GET `/api/forecast`
Returns 24-hour forecast with predictions

### GET `/api/line/<line_name>`
Returns detailed data for specific line

### POST `/api/send-alerts`
Triggers manual alert sending

### POST `/api/scenario`
Run custom weather scenario
```json
{
  "temperature": 45,
  "wind_speed": 3.0,
  "hour": 14
}
```

### GET `/api/geojson/lines`
Returns GeoJSON with current loading data

---

## 🏗️ Backend Architecture Details

### IEEE-738 Implementation

The project includes a custom implementation of the IEEE-738 standard for calculating transmission line thermal ratings. Located in `backend/ieee738/`, this module:

**Key Features:**
- Calculates steady-state thermal rating (ampacity) based on heat balance
- Accounts for:
  - **Solar heat gain** (time of day, season, atmospheric clarity)
  - **Resistive heating** (I²R losses in the conductor)
  - **Convective cooling** (wind speed and direction)
  - **Radiative cooling** (surface emissivity and ambient temperature)
- Uses Pydantic for type-safe parameter validation
- Implements air property calculations (density, viscosity, thermal conductivity)

**Usage Example:**
```python
from ieee738 import Conductor, ConductorParams

params = ConductorParams(
    Ta=35,                    # Ambient temp (°C)
    WindVelocity=6.56,        # Wind speed (ft/s)
    WindAngleDeg=90,          # Perpendicular wind
    SunTime=14,               # 2 PM
    Date='21 Jun',            # Summer
    Diameter=0.741,           # Conductor diameter (inches)
    TLo=25, THi=50,          # Reference temperatures
    RLo=0.0001, RHi=0.00011, # Resistance at ref temps
    Tc=85,                    # Max operating temp
    Latitude=21.31,
    Elevation=1000
)

conductor = Conductor(params)
rating_amps = conductor.steady_state_thermal_rating()
```

### Database Schema

The SQLite database stores historical data for analysis and trend detection:

**Tables:**

1. **alert_history**
   - Tracks all alerts sent (when, severity, recipients)
   - Enables alert deduplication to prevent spam
   - Provides analytics on system performance

2. **weather_readings**
   - Caches weather API responses
   - Reduces API calls (1000/day limit on free tier)
   - Links to line_rating_history for correlation

3. **line_rating_history**
   - Stores calculated ratings over time
   - Enables trend analysis and ML training
   - Foreign key to weather_readings

4. **system_logs**
   - Application event logging
   - Error tracking and debugging
   - Audit trail

**Data Access Layer:**

The `database/repositories.py` module provides clean interfaces:
```python
from database.repositories import AlertRepository
from database.db import get_db

# Save an alert
with get_db() as db:
    alert_data = {
        'line_name': 'L5',
        'severity': 'CRITICAL',
        'loading_pct': 97.5,
        'predicted_time': datetime.now(),
        # ... more fields
    }
    AlertRepository.save_alert(db, alert_data)

# Query recent alerts
with get_db() as db:
    recent = AlertRepository.get_recent_alerts(db, hours=24)
    stats = AlertRepository.get_alert_statistics(db, days=7)
```

### Module Organization

**modules/weather.py**
- OpenWeatherMap API integration
- Current conditions and hourly forecasts
- Automatic conversion to IEEE-738 format
- Graceful fallback if API unavailable

**modules/calculations.py**
- Line rating calculator using IEEE-738
- Batch processing for all lines
- System health metrics
- Temperature failure analysis

**modules/alerts.py**
- Alert generation based on thresholds
- Forecast analysis (24-hour ahead)
- Alert prioritization logic
- Cooldown to prevent spam

**modules/notifications.py**
- Multi-channel delivery (SMS via Twilio, Email via SendGrid)
- Configurable recipients
- Graceful degradation if services unavailable
- Free alternative (email-to-SMS gateways)

### Interactive Map Generation (map.py)

The `backend/map.py` script generates an interactive HTML visualization of the transmission grid with color-coded stress levels. This standalone tool produces a Folium-based map saved to `backend/data/line_map.html`.

**Key Features:**
- **IEEE-738 Scenario Analysis**: Calculates line ratings under custom weather conditions
- **Color-Coded Visualization**:
  - 🟢 Green: NOMINAL loading (<60%)
  - 🟠 Orange: CAUTION loading (60-90%)
  - 🔴 Red: CRITICAL loading (≥90%)
- **Interactive Elements**:
  - Line tooltips showing name and loading percentage
  - Bus markers with voltage class indicators
  - Marker clustering for cleaner visualization
- **GIS Integration**: Merges calculated data with GeoJSON geometry

**Process Flow:**

1. **Data Loading** (lines 7-9):
   - Loads transmission lines, flows, buses from CSV files
   - Merges voltage data from bus endpoints to each line

2. **IEEE-738 Calculations** (lines 30-87):
   - Reads conductor properties from library
   - Computes thermal ratings using ambient weather parameters
   - Converts ratings from Amps to MVA: `MVA = √3 × I × V × 10⁻⁶`

3. **Scenario Analysis** (lines 96-121):
   - `run_scenario()` function tests different weather conditions
   - Assigns severity labels based on configurable thresholds
   - Saves results to `scenario_results.csv`

4. **GIS Data Preparation** (lines 125-183):
   - Merges calculated loading data with line geometry from GeoJSON
   - Deduplicates and clusters bus locations
   - Projects coordinates to local CRS for spatial operations

5. **Map Visualization** (lines 186-221):
   - Creates Folium map centered on Hawaii (20.9°N, -157.5°W)
   - Renders lines with color based on severity
   - Adds bus markers differentiated by voltage class (69kV vs other)
   - Saves interactive HTML to `backend/data/line_map.html`

**Usage Example:**

```python
# Run a hot weather scenario
hot_day = {
    'Ta': 45,              # 45°C ambient
    'WindVelocity': 2.0,   # Low wind (2 ft/s)
    'SunTime': 14,         # 2 PM (peak solar)
    'Date': '21 Jun',      # Summer
    # ... other parameters
}

results = run_scenario(base_data, hot_day, thresholds=(90, 60))
# Returns DataFrame with loading_pct and severity for each line

# Generate map (automatic at end of script)
# Opens backend/data/line_map.html to view
```

**Customization:**

- **Thresholds**: Adjust `thresholds=(critical, caution)` tuple in `run_scenario()`
- **Weather**: Modify `ambient_defaults` dict (lines 44-56)
- **Map Style**: Change Folium `tiles` parameter (line 189)
- **Bus Voltage Colors**: Edit line 214 conditional

**Output:**

The generated `line_map.html` is a standalone interactive map that can be:
- Opened directly in a browser for offline viewing
- Embedded in web applications via iframe
- Served through the Flask API as a dynamic visualization

This tool complements the real-time dashboard by providing scenario planning capabilities for grid operators to test "what-if" conditions before they occur.

---

## 🎓 How It Works

### IEEE-738 Calculation Process

1. **Input Parameters**:
   - Ambient temperature (°C)
   - Wind speed (ft/s)
   - Conductor properties (resistance, diameter)
   - Maximum Operating Temperature (MOT)

2. **Calculate Heat Balance**:
   - Solar heat gain
   - Resistive heating (I²R losses)
   - Convective cooling (wind)
   - Radiative cooling

3. **Solve for Current**:
   - Find current (Amps) that reaches MOT
   - Convert to MVA: `MVA = √3 × I × V × 10⁻⁶`

4. **Compare to Flow**:
   - Loading % = (Actual Flow / Dynamic Rating) × 100

### Alert Logic

```python
if loading >= 100%:
    status = "OVERLOAD"  # Immediate action
elif loading >= 95%:
    status = "CRITICAL"  # High priority alert
elif loading >= 80%:
    status = "WARNING"   # Monitor closely
else:
    status = "OK"        # Normal operation
```

### Weather Impact Examples

| Temp | Wind | Rating Change | Example Line |
|------|------|---------------|--------------|
| 25°C | 6.56 ft/s | Baseline (100%) | 795 ACSR @ 138kV = 215 MVA |
| 35°C | 6.56 ft/s | -12% | Same line = 189 MVA |
| 45°C | 6.56 ft/s | -24% | Same line = 163 MVA |
| 35°C | 3.28 ft/s | -18% | Same line = 176 MVA |

**Key Insight**: A 20°C temperature rise can reduce line capacity by ~25%!

---

## 🧪 Testing

### Test Database

```bash
cd backend
python init_db.py --health-check
```

Expected output:
```
Running database health check...
  Status: ✓ Healthy
  Database: linelink.db
  Tables: 4
    - alert_history
    - weather_readings
    - line_rating_history
    - system_logs
```

### Test IEEE-738 Library

```bash
cd backend
python ieee738/conductor.py
```

Expected output:
```
Conductor: 336.4 ACSR 30/7 ORIOLE
Ambient Temperature: 25.0°C
Wind Speed: 6.56 ft/s
Max Operating Temp: 75.0°C
Thermal Rating: 1463 Amps
Rating at 69 kV: 175 MVA
Rating at 138 kV: 350 MVA
```

### Test Weather Integration

```bash
cd backend
python modules/weather.py
```

Expected output:
```
Current Weather:
  Temperature: 25.3°C
  Wind Speed: 8.2 ft/s
  Conditions: clear sky
```

### Test Notifications

```bash
cd backend
python modules/notifications.py
```

Sends test SMS + email to configured recipients.

### Test Full System

```bash
# Start server
cd backend
python app.py

# In another terminal, test the health endpoint
curl http://localhost:5000/api/health
```

Expected:
```json
{
  "status": "ok",
  "timestamp": "2025-01-25T14:30:00",
  "services": {
    "weather": true,
    "calculations": true,
    "notifications": true,
    "database": true
  },
  "database": {
    "healthy": true,
    "tables": ["alert_history", "weather_readings", "line_rating_history", "system_logs"]
  }
}
```

### Test Current Conditions Endpoint

```bash
curl http://localhost:5000/api/current-conditions
```

This will fetch real weather data and calculate ratings for all lines.

---

## 📊 Answering the Challenge Questions

### 1. At what temperature do lines exceed safe limits?

**Answer via Dashboard**:
1. Use scenario sliders to increase temperature
2. Watch system health counters
3. Note when first line turns red (>95%)

**Example Result**:
- At 40°C with 6.56 ft/s wind: 3 lines enter WARNING
- At 45°C with 6.56 ft/s wind: 2 lines enter CRITICAL
- At 48°C with 3 ft/s wind: First OVERLOAD occurs

**Code to Find**:
```python
calc = LineRatingCalculator()
temp, line = calc.find_first_failure_temp()
print(f"First failure at {temp}°C: {line}")
```

### 2. Which lines show stress first?

**Answer via Dashboard**:
- Check "Critical Lines Table" (auto-sorted by loading %)
- Top lines are most vulnerable
- Typically low-voltage lines (69kV) with older conductors

**Example Results**:
1. Line L5: SURF69 TO TURTLE69 (69kV, older ACSR)
2. Line L12: FLOWER69 TO HONOLULU69 (69kV)
3. Line L3: ALOHA138 TO SUNSET138 (138kV, heavily loaded)

### 3. How severe is system stress?

**Answer via Dashboard**:
- System Health card shows distribution
- Forecast chart shows trend over 24 hours
- Peak stress time identified

**Severity Levels**:
- **🟢 Normal**: 90%+ lines <80% loading
- **🟡 Elevated**: 5-10% lines in WARNING
- **🟠 High**: 2+ lines in CRITICAL
- **🔴 Emergency**: Any lines OVERLOADED

---

## 🎨 Demo Script (5 min presentation)

### Opening (30 sec)
"Hi, I'm [name] and this is LineLink. The power grid faces a growing challenge: as temperatures rise, transmission lines can carry less power before overheating. We built a system to predict and alert operators before lines fail."

### Live Demo (3 min)

**Show Current Conditions**:
"Right now at 28°C and moderate wind, all lines are operating normally - average loading is 45%."

**Show Map**:
"Our interactive map shows 40 transmission lines in Hawaii, color-coded by stress level. Green means normal, yellow is caution, red is critical."

**Show Forecast**:
"This chart predicts the next 24 hours. Notice around 2 PM when temperature peaks at 35°C - we see max loading approaching 90%."

**Run Hot Scenario**:
"Let me simulate a hot day: 45°C, low wind. [Move sliders] Now we see 3 lines turn red, exceeding 95% capacity. The system automatically identified these as critical."

**Trigger Alert**:
"[Click Send Alerts] The system just sent SMS and email notifications to operators with a prioritized list of at-risk lines."

### Closing (90 sec)

**Answer Challenge Questions**:
1. "Lines start overloading around 48°C with low wind"
2. "The 69kV lines in coastal areas show stress first"
3. "We provide a real-time severity score plus visual indicators"

**Impact**:
"This lets AEP operators:
- See problems hours before they happen
- Take preventive action (shed load, reconfigure)
- Avoid costly equipment damage and outages"

"All powered by open-source tools, real weather data, and industry-standard IEEE-738 calculations."

---

## 🔮 Future Enhancements

### Phase 2 Features (Post-Hackathon)
- [ ] **N-1 Contingency Analysis**: Show impact of losing any line
- [ ] **Load Profiles**: Account for daily demand changes
- [ ] **Mobile App**: Native iOS/Android with push notifications
- [ ] **Historical Tracking**: Database to store alerts and analyze patterns
- [ ] **Machine Learning**: Predict failures based on historical weather/loading
- [ ] **Integration**: Connect to SCADA systems for real power flows
- [ ] **Multi-Region**: Scale to handle AEP's full 40,000-mile network

### Technical Improvements
- [ ] WebSocket for real-time updates (no page refresh)
- [ ] Background scheduler for automatic alert checks
- [ ] Redis caching for faster API responses
- [ ] Docker containerization for easy deployment
- [ ] User authentication and role-based access
- [ ] Export reports to PDF/Excel

---

## 🐛 Troubleshooting

### "Weather service not configured"
- Check `.env` file exists with `OPENWEATHER_API_KEY`
- Verify API key is valid at openweathermap.org
- Test: `curl "api.openweathermap.org/data/2.5/weather?lat=21.3&lon=-157.8&appid=YOUR_KEY"`

### "No data loading on dashboard"
- Check backend server is running (`python app.py`)
- Check browser console (F12) for CORS errors
- Verify frontend API_BASE URL matches backend port

### "SMS not sending"
- Ensure Twilio credentials in `.env` are correct
- Verify phone numbers include country code (+1 for US)
- Check Twilio console for error logs
- Alternative: Use free email-to-SMS gateways (see notifications.py)

### "Map not displaying"
- Check `oneline_lines.geojson` exists in `backend/data/`
- Verify GeoJSON is valid JSON (use jsonlint.com)
- Check browser console for Leaflet errors

### "Calculations taking too long"
- Normal: 40 lines × 0.5 sec = ~20 seconds for full forecast
- Reduce forecast hours: Change `hours=24` to `hours=12`
- Cache results: Already implemented (30 min TTL)

---

## 👥 Team & Credits

**Team Members**:
- [Your Names]

**Built With**:
- IEEE-738 library (provided by AEP)
- OpenWeatherMap API
- OpenStreetMap / Leaflet.js
- Chart.js
- Bootstrap

**Special Thanks**:
- AEP for the challenge and data
- OSU Hackathon organizers
- IEEE for transmission line standards

---

## 📜 License

MIT License - feel free to use and modify for your needs.

---

## 📞 Contact

For questions or demo requests:
- Email: [your-email]
- GitHub: [your-repo]
- Demo Video: [youtube-link]

---

**LineLink** - Keeping the grid safe, one line at a time ⚡