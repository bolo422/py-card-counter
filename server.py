import http.server
import socketserver
import json
import os
import poker_lib

PORT = 8000
DATA_FILE = 'cards.json'

class CardHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/save':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Verify valid JSON before saving
                try:
                    data = json.loads(post_data)
                except json.JSONDecodeError:
                    self.send_error(400, "Invalid JSON")
                    return

                with open(DATA_FILE, 'wb') as f:
                    f.write(post_data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
            except Exception as e:
                 print(f"Error saving data: {e}")
                 self.send_error(500, f"Server error: {e}")
        elif self.path == '/api/calculate':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                
                marked = data.get('marked_cards', [])
                to_draw = int(data.get('cards_to_draw', 0))
                
                probs = poker_lib.calculate_probabilities(marked, to_draw)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(probs).encode('utf-8'))
            except Exception as e:
                 print(f"Error calculating: {e}")
                 self.send_error(500, f"Server error: {e}")
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        # Prevent caching for the data file
        if self.path == '/' + DATA_FILE or self.path.endswith('/' + DATA_FILE):
             self.send_response(200)
             self.send_header('Content-Type', 'application/json')
             self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
             self.end_headers()
             if os.path.exists(DATA_FILE):
                 with open(DATA_FILE, 'rb') as f:
                     self.wfile.write(f.read())
             else:
                 self.wfile.write(b'[]')
             return
             
        super().do_GET()

if __name__ == "__main__":
    # Change to directory of script to invoke from anywhere
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), CardHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server")
            httpd.server_close()
