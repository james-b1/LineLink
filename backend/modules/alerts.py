"""
Alert Generation and Management Module
Determines when to send alerts based on line loading predictions
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()


class AlertManager:
    """Manage alert generation and tracking"""
    
    def __init__(self):
        self.critical_threshold = float(os.getenv('CRITICAL_THRESHOLD', 95))
        self.warning_threshold = float(os.getenv('WARNING_THRESHOLD', 80))
        
        # Track sent alerts to avoid spam
        self.sent_alerts = {}  # {line_name: last_alert_time}
        self.alert_cooldown = timedelta(hours=1)  # Don't re-alert for 1 hour
    
    def analyze_forecast(self, forecast_data: List[Dict]) -> Dict:
        """
        Analyze forecast data to generate alerts
        
        Args:
            forecast_data: List of dicts, each containing:
                {
                    'timestamp': datetime,
                    'hour': int,
                    'lines': DataFrame with line ratings
                }
        
        Returns:
            dict: {
                'critical_alerts': List[Dict],
                'warning_alerts': List[Dict],
                'peak_stress_time': datetime,
                'summary': str
            }
        """
        critical_alerts = []
        warning_alerts = []
        peak_stress = None
        max_loading = 0
        
        for forecast in forecast_data:
            timestamp = forecast['timestamp']
            lines_df = forecast['lines']
            
            # Find overloaded or critical lines
            critical_lines = lines_df[lines_df['loading_pct'] >= self.critical_threshold]
            warning_lines = lines_df[
                (lines_df['loading_pct'] >= self.warning_threshold) & 
                (lines_df['loading_pct'] < self.critical_threshold)
            ]
            
            # Track peak stress
            max_in_period = lines_df['loading_pct'].max()
            if max_in_period > max_loading:
                max_loading = max_in_period
                peak_stress = timestamp
            
            # Generate critical alerts
            for _, line in critical_lines.iterrows():
                if self._should_send_alert(line['line_name']):
                    critical_alerts.append({
                        'severity': 'CRITICAL',
                        'line_name': line['line_name'],
                        'branch_name': line.get('branch_name', line['line_name']),
                        'loading_pct': line['loading_pct'],
                        'timestamp': timestamp,
                        'time_str': timestamp.strftime('%I:%M %p'),
                        'rating_mva': line['rating_mva'],
                        'flow_mva': line['flow_mva'],
                        'voltage_kv': line['voltage_kv']
                    })
            
            # Generate warning alerts
            for _, line in warning_lines.iterrows():
                if self._should_send_alert(line['line_name'], is_critical=False):
                    warning_alerts.append({
                        'severity': 'WARNING',
                        'line_name': line['line_name'],
                        'branch_name': line.get('branch_name', line['line_name']),
                        'loading_pct': line['loading_pct'],
                        'timestamp': timestamp,
                        'time_str': timestamp.strftime('%I:%M %p'),
                        'rating_mva': line['rating_mva'],
                        'flow_mva': line['flow_mva'],
                        'voltage_kv': line['voltage_kv']
                    })
        
        # Generate summary
        summary = self._generate_summary(critical_alerts, warning_alerts, peak_stress)
        
        return {
            'critical_alerts': critical_alerts,
            'warning_alerts': warning_alerts,
            'peak_stress_time': peak_stress,
            'peak_loading': max_loading,
            'summary': summary,
            'alert_count': len(critical_alerts) + len(warning_alerts)
        }
    
    def prioritize_alerts(self, alerts: List[Dict]) -> List[Dict]:
        """
        Sort alerts by priority
        
        Priority order:
        1. Highest loading percentage
        2. Earliest time
        3. Higher voltage (more important lines)
        
        Args:
            alerts: List of alert dicts
        
        Returns:
            Sorted list of alerts
        """
        return sorted(alerts, key=lambda x: (
            -x['loading_pct'],  # Higher loading first
            x['timestamp'],     # Earlier time first
            -x['voltage_kv']    # Higher voltage first
        ))
    
    def _should_send_alert(self, line_name: str, is_critical: bool = True) -> bool:
        """
        Check if alert should be sent (avoid spam)
        
        Args:
            line_name: Name of the line
            is_critical: True for critical alerts (always send)
        
        Returns:
            bool: True if alert should be sent
        """
        # Always send critical alerts
        if is_critical:
            return True
        
        # Check cooldown for warnings
        if line_name in self.sent_alerts:
            last_alert = self.sent_alerts[line_name]
            if datetime.now() - last_alert < self.alert_cooldown:
                return False
        
        return True
    
    def mark_alert_sent(self, line_name: str):
        """Record that an alert was sent"""
        self.sent_alerts[line_name] = datetime.now()
    
    def _generate_summary(self, critical: List[Dict], warning: List[Dict], 
                         peak_time: datetime) -> str:
        """Generate human-readable summary"""
        total = len(critical) + len(warning)
        
        if total == 0:
            return "No alerts for the forecast period. System operating normally."
        
        summary_parts = []
        
        if critical:
            summary_parts.append(f"{len(critical)} CRITICAL alert(s)")
        if warning:
            summary_parts.append(f"{len(warning)} WARNING alert(s)")
        
        summary = f"⚠️ {' and '.join(summary_parts)} detected."
        
        if peak_time:
            summary += f" Peak stress expected at {peak_time.strftime('%I:%M %p')}."
        
        return summary
    
    def format_alert_message(self, alerts: List[Dict], message_type: str = 'sms') -> str:
        """
        Format alerts for SMS or email
        
        Args:
            alerts: List of alert dicts
            message_type: 'sms' or 'email'
        
        Returns:
            Formatted message string
        """
        if not alerts:
            return "No alerts at this time."
        
        if message_type == 'sms':
            return self._format_sms(alerts)
        else:
            return self._format_email(alerts)
    
    def _format_sms(self, alerts: List[Dict]) -> str:
        """Format for SMS (160 char limit consideration)"""
        prioritized = self.prioritize_alerts(alerts)[:3]  # Top 3 only
        
        lines = ["GridGuard Alert:"]
        
        for alert in prioritized:
            severity_icon = "🔴" if alert['severity'] == 'CRITICAL' else "⚠️"
            lines.append(
                f"{severity_icon} {alert['branch_name']}: {alert['loading_pct']:.0f}% at {alert['time_str']}"
            )
        
        if len(alerts) > 3:
            lines.append(f"+ {len(alerts) - 3} more. Check dashboard.")
        
        return "\n".join(lines)
    
    def _format_email(self, alerts: List[Dict]) -> str:
        """Format for email (HTML)"""
        prioritized = self.prioritize_alerts(alerts)
        
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .critical { color: #dc3545; font-weight: bold; }
                .warning { color: #ffc107; font-weight: bold; }
                table { border-collapse: collapse; width: 100%; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h2>GridGuard: Transmission Line Alerts</h2>
            <p>The following lines are predicted to exceed safe operating limits:</p>
            <table>
                <tr>
                    <th>Severity</th>
                    <th>Line</th>
                    <th>Time</th>
                    <th>Loading</th>
                    <th>Flow/Rating</th>
                </tr>
        """
        
        for alert in prioritized:
            severity_class = alert['severity'].lower()
            html += f"""
                <tr class="{severity_class}">
                    <td>{alert['severity']}</td>
                    <td>{alert['branch_name']}</td>
                    <td>{alert['time_str']}</td>
                    <td>{alert['loading_pct']:.1f}%</td>
                    <td>{alert['flow_mva']:.1f} / {alert['rating_mva']:.1f} MVA</td>
                </tr>
            """
        
        html += """
            </table>
            <br>
            <p><em>This is an automated alert from GridGuard. Please review the dashboard for more details.</em></p>
        </body>
        </html>
        """
        
        return html


# Example usage
if __name__ == "__main__":
    manager = AlertManager()
    
    # Simulate forecast data
    forecast_data = [
        {
            'timestamp': datetime.now() + timedelta(hours=1),
            'hour': 14,
            'lines': pd.DataFrame([
                {'line_name': 'L0', 'branch_name': 'ALOHA138 TO HONOLULU138', 
                 'loading_pct': 87, 'rating_mva': 200, 'flow_mva': 174, 'voltage_kv': 138},
                {'line_name': 'L5', 'branch_name': 'SURF69 TO TURTLE69', 
                 'loading_pct': 96, 'rating_mva': 100, 'flow_mva': 96, 'voltage_kv': 69},
            ])
        },
        {
            'timestamp': datetime.now() + timedelta(hours=4),
            'hour': 17,
            'lines': pd.DataFrame([
                {'line_name': 'L0', 'branch_name': 'ALOHA138 TO HONOLULU138', 
                 'loading_pct': 92, 'rating_mva': 195, 'flow_mva': 174, 'voltage_kv': 138},
                {'line_name': 'L5', 'branch_name': 'SURF69 TO TURTLE69', 
                 'loading_pct': 102, 'rating_mva': 95, 'flow_mva': 96, 'voltage_kv': 69},
            ])
        }
    ]
    
    # Analyze
    result = manager.analyze_forecast(forecast_data)
    
    print("Alert Summary:")
    print(result['summary'])
    
    print("\nCritical Alerts:")
    for alert in result['critical_alerts']:
        print(f"  {alert['branch_name']}: {alert['loading_pct']:.1f}% at {alert['time_str']}")
    
    print("\nWarning Alerts:")
    for alert in result['warning_alerts']:
        print(f"  {alert['branch_name']}: {alert['loading_pct']:.1f}% at {alert['time_str']}")
    
    # Format messages
    print("\nSMS Format:")
    print(manager.format_alert_message(result['critical_alerts'] + result['warning_alerts'], 'sms'))
    
    print("\nEmail Format:")
    print(manager.format_alert_message(result['critical_alerts'] + result['warning_alerts'], 'email')[:500] + "...")