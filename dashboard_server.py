"""Web dashboard server for Agent Stamina.

Provides a real-time web interface for monitoring agent stamina.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading


class StaminaDashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for stamina dashboard."""
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/' or path == '/index.html':
            self._serve_dashboard()
        elif path == '/api/stamina':
            self._serve_api()
        elif path == '/api/history':
            self._serve_history()
        else:
            self._serve_404()
    
    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/record':
            self._handle_record()
        else:
            self._serve_404()
    
    def _serve_dashboard(self):
        """Serve the main dashboard HTML."""
        try:
            with open('dashboard.html', 'r') as f:
                content = f.read()
            
            self._send_response(200, 'text/html', content)
        except FileNotFoundError:
            self._send_response(500, 'text/plain', 'dashboard.html not found')
    
    def _serve_api(self):
        """Serve current stamina data as JSON."""
        data = self._get_current_stamina()
        self._send_response(200, 'application/json', json.dumps(data))
    
    def _serve_history(self):
        """Serve historical stamina data."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        minutes = int(params.get('minutes', ['60'])[0])
        data = self._get_history(minutes)
        
        self._send_response(200, 'application/json', json.dumps(data))
    
    def _handle_record(self):
        """Handle recording a new stamina snapshot."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            # Here you would insert into database
            response = {'success': True}
        except json.JSONDecodeError:
            response = {'success': False, 'error': 'Invalid JSON'}
        
        self._send_response(200, 'application/json', json.dumps(response))
    
    def _get_current_stamina(self) -> dict:
        """Get current stamina from database."""
        try:
            conn = sqlite3.connect('.agent_stamina.db')
            row = conn.execute(
                "SELECT * FROM stamina_snapshots ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            conn.close()
            
            if row:
                return {
                    'timestamp': row[2],
                    'session_id': row[1],
                    'context_health': row[3],
                    'memory_freshness': row[4],
                    'error_rate': row[5],
                    'repetition_score': row[6],
                    'overall_score': row[7]
                }
        except Exception:
            pass
        
        # Return default if no data
        return {
            'timestamp': datetime.now().isoformat(),
            'session_id': 'unknown',
            'context_health': 0.8,
            'memory_freshness': 0.9,
            'error_rate': 0.0,
            'repetition_score': 0.0,
            'overall_score': 85.0
        }
    
    def _get_history(self, minutes: int = 60) -> list:
        """Get stamina history."""
        try:
            since = (datetime.now() - timedelta(minutes=minutes)).isoformat()
            conn = sqlite3.connect('.agent_stamina.db')
            rows = conn.execute(
                """SELECT timestamp, context_health, memory_freshness, 
                   error_rate, repetition_score, overall_score
                   FROM stamina_snapshots 
                   WHERE timestamp > ? 
                   ORDER BY timestamp""",
                (since,)
            ).fetchall()
            conn.close()
            
            return [
                {
                    'timestamp': row[0],
                    'context_health': row[1],
                    'memory_freshness': row[2],
                    'error_rate': row[3],
                    'repetition_score': row[4],
                    'overall_score': row[5]
                }
                for row in rows
            ]
        except Exception:
            return []
    
    def _send_response(self, code: int, content_type: str, content: str):
        """Send HTTP response."""
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content.encode())
    
    def _serve_404(self):
        """Serve 404 response."""
        self._send_response(404, 'text/plain', 'Not Found')


class StaminaDashboard:
    """Web dashboard for Agent Stamina."""
    
    def __init__(self, port: int = 8080, db_path: str = '.agent_stamina.db'):
        self.port = port
        self.db_path = db_path
        self.server = None
        self.thread = None
    
    def start(self, blocking: bool = False):
        """Start the dashboard server."""
        self.server = HTTPServer(('localhost', self.port), StaminaDashboardHandler)
        
        if blocking:
            print(f"🌐 Stamina Dashboard running at http://localhost:{self.port}")
            self.server.serve_forever()
        else:
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            print(f"🌐 Stamina Dashboard running at http://localhost:{self.port}")
    
    def stop(self):
        """Stop the dashboard server."""
        if self.server:
            self.server.shutdown()
            if self.thread:
                self.thread.join()


def main():
    """Run the dashboard server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Agent Stamina Web Dashboard')
    parser.add_argument('--port', type=int, default=8080, help='Port to run on')
    parser.add_argument('--db', default='.agent_stamina.db', help='Database path')
    
    args = parser.parse_args()
    
    dashboard = StaminaDashboard(port=args.port, db_path=args.db)
    
    try:
        dashboard.start(blocking=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down dashboard...")
        dashboard.stop()


if __name__ == '__main__':
    main()
