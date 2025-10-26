"""
LLM-Powered Emergency Coordination Module
Uses OpenAI to generate intelligent worker coordination plans for critical transmission lines
"""

import os
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


class LLMCoordinator:
    """Generates intelligent emergency coordination plans using LLM"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("⚠ Warning: OPENAI_API_KEY not configured. Emergency coordination will be unavailable.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # Default to mini for cost efficiency

    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.client is not None

    def extract_station_name(self, bus_name: str) -> str:
        """
        Extract base station name from bus name
        Example: HONOLULU69 -> HONOL, SUNSET138 -> SUNSE
        """
        # Remove voltage suffix (last 2-3 digits)
        import re
        match = re.match(r'^([A-Z]+)', bus_name.upper())
        if match:
            base = match.group(1)
            # Truncate to 5 chars (standard station naming)
            return base[:5] if len(base) > 5 else base
        return bus_name[:5]

    def group_lines_by_station(self, critical_lines: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        Group critical lines by their endpoint stations
        Returns dict of station -> list of affected lines
        """
        station_groups = {}

        for _, line in critical_lines.iterrows():
            bus0 = line.get('bus0', '')
            bus1 = line.get('bus1', '')
            station0 = self.extract_station_name(bus0)
            station1 = self.extract_station_name(bus1)

            line_info = {
                'line_name': line['line_name'],
                'loading_pct': line['loading_pct'],
                'bus0': bus0,
                'bus1': bus1,
                'voltage_kv': line.get('voltage_kv', 'N/A'),
                'flow_mva': line.get('flow_mva', 0),
                'rating_mva': line.get('rating_mva', 0)
            }

            # Add to both endpoint stations
            for station in [station0, station1]:
                if station not in station_groups:
                    station_groups[station] = []
                station_groups[station].append(line_info)

        return station_groups

    def build_coordination_prompt(self, critical_lines: pd.DataFrame, weather_data: Dict) -> str:
        """
        Build comprehensive prompt for LLM to generate coordination plan
        """
        station_groups = self.group_lines_by_station(critical_lines)

        # Sort lines by loading percentage (most critical first)
        sorted_lines = critical_lines.sort_values('loading_pct', ascending=False)

        prompt = f"""You are an emergency coordinator for an electrical transmission grid experiencing critical overload conditions.

CURRENT SITUATION:
- Temperature: {weather_data.get('temperature', 'N/A')}°C ({(weather_data.get('temperature', 0) * 9/5 + 32):.1f}°F)
- Wind Speed: {weather_data.get('wind_speed', 'N/A'):.1f} ft/s
- Conditions: {weather_data.get('description', 'Unknown')}
- Number of Critical Lines: {len(critical_lines)}

CRITICAL TRANSMISSION LINES (sorted by severity):
"""

        for idx, (_, line) in enumerate(sorted_lines.iterrows(), 1):
            prompt += f"""
{idx}. {line['line_name']}
   - Loading: {line['loading_pct']:.1f}% (CRITICAL - exceeds safe limits)
   - Endpoints: {line.get('bus0', 'N/A')} ↔ {line.get('bus1', 'N/A')}
   - Voltage: {line.get('voltage_kv', 'N/A')} kV
   - Flow: {line.get('flow_mva', 0):.1f} MVA / Rating: {line.get('rating_mva', 0):.1f} MVA
   - Status: {"OVERLOAD" if line['loading_pct'] >= 100 else "CRITICAL"}
"""

        prompt += f"""

STATION GROUPINGS:
Multiple lines may connect to the same substation. Stations often have buses at different voltage levels (69kV, 138kV, etc.).

"""

        for station, lines in sorted(station_groups.items(), key=lambda x: len(x[1]), reverse=True):
            if len(lines) > 1:  # Only show stations with multiple affected lines
                prompt += f"\n{station} Station ({len(lines)} affected lines):\n"
                for line_info in lines:
                    prompt += f"  - {line_info['line_name']}: {line_info['loading_pct']:.1f}% loading at {line_info.get('voltage_kv', 'N/A')} kV\n"

        prompt += """

YOUR TASK:
Generate an EFFICIENT, COORDINATED action plan for field workers to reduce power flow and prevent cascading failures.

CRITICAL CONSTRAINTS:
1. Workers must coordinate actions to avoid creating new overloads when reducing flow on one line
2. Prioritize lines with highest loading percentages first
3. When multiple lines share a station, coordinate actions at that station together
4. Consider voltage levels - higher voltage lines carry more power
5. Actions should be sequenced to minimize risk of cascading failures

REQUIRED OUTPUT FORMAT:
Provide a numbered list of coordinated actions in this EXACT format:

1. [Station Name] - [Specific Action]
2. [Station Name] - [Specific Action]
...

Each action should:
- Specify the station name clearly
- Describe what to do (e.g., "reduce load by switching to backup circuit", "lower transformer tap", "shed non-critical load")
- Be specific enough for field workers to execute
- Be ordered for maximum safety and efficiency

EXAMPLE OUTPUT FORMAT:
1. HONOL Station - Reduce 138kV line loading by 15% via backup circuit transfer
2. SUNSE Station - Lower transformer taps to reduce flow on critical 69kV lines
3. KAWAI Station - Shed non-critical industrial loads (est. 25 MVA reduction)

Generate the coordination plan now (maximum 8 steps for SMS delivery):
"""

        return prompt

    def generate_coordination_plan(self, critical_lines: pd.DataFrame, weather_data: Dict) -> Dict:
        """
        Generate LLM-powered coordination plan for emergency response

        Returns:
            dict: {
                'success': bool,
                'plan': str,  # Formatted action plan
                'summary': str,  # Brief summary for SMS
                'steps': List[str],  # Individual action steps
                'error': str  # Error message if failed
            }
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'OpenAI API not configured',
                'plan': None,
                'summary': None,
                'steps': []
            }

        try:
            # Build the prompt
            prompt = self.build_coordination_prompt(critical_lines, weather_data)

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert electrical grid operator with deep knowledge of transmission line management, load balancing, and emergency response coordination. Provide clear, actionable guidance for field workers."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent, reliable output
                max_tokens=800
            )

            plan_text = response.choices[0].message.content.strip()

            # Parse steps from the plan
            steps = []
            for line in plan_text.split('\n'):
                line = line.strip()
                # Match numbered lines like "1. Station - Action"
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering
                    step = line.lstrip('0123456789.-) ').strip()
                    if step:
                        steps.append(step)

            # Generate SMS-friendly summary
            num_lines = len(critical_lines)
            max_loading = critical_lines['loading_pct'].max()
            summary = f"{num_lines} critical lines detected (max {max_loading:.0f}% loading). Immediate coordination required."

            return {
                'success': True,
                'plan': plan_text,
                'summary': summary,
                'steps': steps,
                'error': None
            }

        except Exception as e:
            print(f"Error generating coordination plan: {e}")
            return {
                'success': False,
                'error': str(e),
                'plan': None,
                'summary': None,
                'steps': []
            }

    def format_sms_message(self, coordination_result: Dict) -> str:
        """
        Format coordination plan as emergency SMS message
        """
        if not coordination_result['success']:
            return "EMERGENCY ALERT: Critical transmission line overload detected. Unable to generate coordination plan. Contact dispatch immediately."

        steps = coordination_result['steps']
        summary = coordination_result['summary']

        # Build SMS message (SMS limit is 160 chars, but carriers support up to 1600 for concatenated)
        message = f"⚡ EMERGENCY ALERT ⚡\n\n{summary}\n\nCOORDINATION PLAN:\n\n"

        for idx, step in enumerate(steps[:8], 1):  # Limit to 8 steps for SMS
            message += f"{idx}. {step}\n"

        message += f"\nRespond immediately. Time: {pd.Timestamp.now().strftime('%H:%M')}"

        return message


# Test function
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from modules.weather import WeatherService
    from modules.calculations import LineRatingCalculator

    # Initialize services
    weather_service = WeatherService()
    calculator = LineRatingCalculator()
    coordinator = LLMCoordinator()

    # Get current conditions
    weather = weather_service.get_current_weather()
    weather_params = weather_service.format_for_ieee738(weather)

    # Calculate line ratings
    all_lines = calculator.calculate_all_lines(weather_params)

    # Filter critical lines (>=95%)
    critical_lines = all_lines[all_lines['loading_pct'] >= 95]

    if len(critical_lines) == 0:
        print("No critical lines detected. Testing with top 3 most loaded lines...")
        critical_lines = all_lines.nlargest(3, 'loading_pct')

    print(f"\n{'='*60}")
    print("LLM Emergency Coordination Test")
    print(f"{'='*60}\n")
    print(f"Critical Lines: {len(critical_lines)}")
    print(f"Weather: {weather['temperature']:.1f}°C, {weather['wind_speed']:.1f} ft/s\n")

    # Generate coordination plan
    result = coordinator.generate_coordination_plan(critical_lines, weather)

    if result['success']:
        print("✓ Coordination Plan Generated\n")
        print(result['plan'])
        print(f"\n{'='*60}")
        print("SMS MESSAGE:")
        print(f"{'='*60}\n")
        print(coordinator.format_sms_message(result))
    else:
        print(f"✗ Failed: {result['error']}")
