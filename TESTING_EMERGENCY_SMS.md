# Testing Emergency Coordination SMS System

## Quick Reference

**Endpoint:** `POST http://localhost:5001/api/emergency-coordination`

**Purpose:** Trigger LLM-powered emergency coordination alerts via SMS and Email

---

## Testing Scenarios

### 1. Test with Current Real Weather (Production Mode)

**Request:**
```bash
curl -X POST http://localhost:5001/api/emergency-coordination \
  -H "Content-Type: application/json"
```

**No JSON body needed** - uses live weather data from OpenWeatherMap API

**What Happens:**
- Fetches current weather conditions
- Calculates line ratings based on real temperature and wind
- If any lines are ≥95% loaded, generates coordination plan and sends SMS

---

### 2. Test with HOT Weather (Guaranteed to Trigger Alerts)

**Request:**
```bash
curl -X POST http://localhost:5001/api/emergency-coordination \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 45,
    "wind_speed": 2.0,
    "hour": 14
  }'
```

**JSON Body Breakdown:**
```json
{
  "temperature": 45,     // 45°C (113°F) - very hot
  "wind_speed": 2.0,     // 2 ft/s - very low wind (poor cooling)
  "hour": 14             // 2 PM - peak solar heating
}
```

**Why This Triggers Alerts:**
- High temperature reduces line capacity significantly
- Low wind reduces convective cooling
- Peak sun time (2 PM) adds solar heating
- **Result:** Multiple lines will exceed 95% loading

---

### 3. Test with EXTREME Conditions (Maximum Stress)

**Request:**
```bash
curl -X POST http://localhost:5001/api/emergency-coordination \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 50,
    "wind_speed": 1.0,
    "hour": 14,
    "description": "extreme heat wave conditions"
  }'
```

**JSON Parameters:**
```json
{
  "temperature": 50,      // 50°C (122°F) - extreme heat
  "wind_speed": 1.0,      // 1 ft/s - almost no wind
  "hour": 14,             // 2 PM - worst solar gain
  "description": "..."    // Optional: adds context to alerts
}
```

**Expected:** 10+ critical lines, comprehensive coordination plan

---

### 4. Test with MILD Conditions (Should NOT Trigger)

**Request:**
```bash
curl -X POST http://localhost:5001/api/emergency-coordination \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 20,
    "wind_speed": 10.0,
    "hour": 8
  }'
```

**JSON Parameters:**
```json
{
  "temperature": 20,      // 20°C (68°F) - cool
  "wind_speed": 10.0,     // 10 ft/s - good cooling
  "hour": 8               // 8 AM - low solar gain
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "No critical lines detected. Emergency coordination not required.",
  "scenario_mode": true,
  "critical_count": 0,
  "max_loading": 65.2
}
```

---

### 5. Test Different Times of Day

**Early Morning (Coolest):**
```json
{
  "temperature": 25,
  "wind_speed": 6.0,
  "hour": 6
}
```

**Noon (Peak Heat):**
```json
{
  "temperature": 38,
  "wind_speed": 4.0,
  "hour": 12
}
```

**Late Afternoon (Worst Case):**
```json
{
  "temperature": 40,
  "wind_speed": 3.0,
  "hour": 15
}
```

**Evening (Cooling):**
```json
{
  "temperature": 30,
  "wind_speed": 5.0,
  "hour": 18
}
```

---

## Response Format

### Success with Critical Lines:
```json
{
  "success": true,
  "message": "Emergency coordination alert sent for 3 critical lines",
  "scenario_mode": true,
  "scenario_params": {
    "temperature": 45,
    "wind_speed": 2.0,
    "hour": 14
  },
  "critical_lines": [
    "LINE_HONOL69_SUNSE69",
    "LINE_SUNSE138_KAWAI138",
    "LINE_FLOWER69_TURTLE69"
  ],
  "critical_count": 3,
  "coordination_plan": "1. HONOL Station - Transfer 69kV load to backup circuit...\n2. SUNSE Station - Lower transformer taps...",
  "coordination_steps": [
    "HONOL Station - Transfer 69kV load to backup circuit reducing flow by 20 MVA",
    "SUNSE Station - Lower transformer taps by 2 positions",
    "KAWAI Station - Shed non-critical industrial loads (15 MVA target)"
  ],
  "sms_sent": 2,
  "email_sent": 2,
  "errors": []
}
```

### Success with No Critical Lines:
```json
{
  "success": true,
  "message": "No critical lines detected. Emergency coordination not required.",
  "scenario_mode": true,
  "scenario_params": {
    "temperature": 20,
    "wind_speed": 10.0
  },
  "critical_count": 0,
  "max_loading": 65.2
}
```

### Error (OpenAI Not Configured):
```json
{
  "success": false,
  "error": "OpenAI API not configured. Add OPENAI_API_KEY to your .env file."
}
```

---

## Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `temperature` | float | No | Current | Ambient temperature in °C |
| `wind_speed` | float | No | Current | Wind speed in ft/s |
| `hour` | int | No | 12 | Hour of day (0-23) for solar calculations |
| `description` | string | No | "test scenario" | Weather description for context |

**Temperature Guidelines:**
- **15-25°C (59-77°F)**: Normal, low loading
- **25-35°C (77-95°F)**: Moderate, some lines may approach warning
- **35-45°C (95-113°F)**: High stress, multiple critical lines likely
- **45-50°C (113-122°F)**: Extreme, many overloads guaranteed

**Wind Speed Guidelines:**
- **10+ ft/s**: Excellent cooling
- **6-10 ft/s**: Good cooling (normal)
- **3-6 ft/s**: Reduced cooling, increased loading
- **1-3 ft/s**: Poor cooling, high risk
- **<1 ft/s**: Minimal cooling, extreme risk

---

## Testing Workflow

### Step 1: Verify Configuration
```bash
# Check that Twilio and OpenAI are configured
grep -E "TWILIO|OPENAI" backend/.env
```

### Step 2: Start Backend Server
```bash
cd backend
python app.py
```

### Step 3: Test Mild Conditions (Should NOT Send SMS)
```bash
curl -X POST http://localhost:5001/api/emergency-coordination \
  -H "Content-Type: application/json" \
  -d '{"temperature": 20, "wind_speed": 10}'
```

**Expected:** `"critical_count": 0` - No SMS sent

### Step 4: Test Hot Conditions (SHOULD Send SMS)
```bash
curl -X POST http://localhost:5001/api/emergency-coordination \
  -H "Content-Type: application/json" \
  -d '{"temperature": 45, "wind_speed": 2, "hour": 14}'
```

**Expected:**
- `"critical_count": 3` (or more)
- `"sms_sent": 2` (if you have 2 recipients configured)
- SMS received on your phone with coordination plan

### Step 5: Check Your Phone
You should receive an SMS like:
```
⚡ EMERGENCY ALERT ⚡

3 critical lines detected (max 98% loading). Immediate coordination required.

COORDINATION PLAN:

1. HONOL Station - Transfer 69kV load to backup circuit
2. SUNSE Station - Lower transformer taps
3. KAWAI Station - Shed non-critical loads
...
```

---

## Troubleshooting

### "OpenAI API not configured"
**Fix:** Add `OPENAI_API_KEY=sk-your-key-here` to `backend/.env`

### "SMS not sent" or `sms_sent: 0`
**Possible causes:**
1. Twilio not configured - Check `.env` for `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
2. No recipients - Add phone numbers to `ALERT_RECIPIENTS_SMS=+1234567890` in `.env`
3. Twilio trial limitations - Verify recipient phone numbers in Twilio console

### No critical lines detected in hot scenario
**Check:**
```bash
curl -X POST http://localhost:5001/api/scenario \
  -H "Content-Type: application/json" \
  -d '{"temperature": 45, "wind_speed": 2}'
```

Look at the `system_health` response to see loading percentages. If max loading is still <95%, try:
- Higher temperature: `"temperature": 50`
- Lower wind: `"wind_speed": 1.0`
- Peak solar: `"hour": 14`

---

## Cost Monitoring

Each emergency coordination request costs:
- **OpenAI API**: ~$0.0005 per request (GPT-4o-mini)
- **Twilio SMS**: $0.0075 per SMS sent (varies by region)
- **SendGrid Email**: Free (up to 100/day)

**Example:** 3 critical lines, 2 SMS recipients, 2 email recipients:
- OpenAI: $0.0005
- SMS: $0.015 (2 messages)
- Email: $0.00
- **Total: $0.0155 per alert** (about 1.5 cents)

---

## Production vs Test Mode

**Test Mode** (includes JSON body):
- Uses your provided weather parameters
- Ideal for demos and testing
- Sends real SMS/emails
- Includes `"scenario_mode": true` in response

**Production Mode** (empty JSON or no body):
- Uses live weather from OpenWeatherMap
- Calculates actual grid conditions
- Sends real alerts when conditions warrant
- Includes `"scenario_mode": false` in response

---

## Integration with Frontend

To add an "Emergency Alert" button to your dashboard:

```javascript
// In your Dashboard component
const sendEmergencyAlert = async (testScenario = null) => {
  try {
    const response = await api.post('/emergency-coordination', testScenario);

    if (response.data.success) {
      alert(`Alert sent! ${response.data.critical_count} critical lines detected.`);
      console.log('Coordination plan:', response.data.coordination_plan);
    } else {
      alert(`Error: ${response.data.error}`);
    }
  } catch (error) {
    alert('Failed to send emergency alert');
  }
};

// Test button (hot scenario)
<button onClick={() => sendEmergencyAlert({
  temperature: 45,
  wind_speed: 2,
  hour: 14
})}>
  Test Emergency Alert (Hot Scenario)
</button>

// Production button (real conditions)
<button onClick={() => sendEmergencyAlert()}>
  Send Emergency Alert (Current Conditions)
</button>
```

---

## Next Steps

1. **Test the system** with the hot scenario above
2. **Verify SMS delivery** on your phone
3. **Check email** for detailed HTML coordination plan
4. **Review coordination steps** - are they logical and actionable?
5. **Adjust temperature/wind** to find your grid's breaking point

**Happy Testing!** 🚀
