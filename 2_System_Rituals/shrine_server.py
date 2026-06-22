import http.server
import json
import subprocess
import os

PORT = 8080
DIRECTORY = os.path.expanduser("~/2_System_Rituals")

class ShrineHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve files from the correct system directory
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        # Handle API calls from the dashboard modules
        if self.path == "/api/recovery":
            try:
                # Execute the Phoenix Recovery script and capture output
                script_path = os.path.join(DIRECTORY, "phoenix_recovery.sh")
                result = subprocess.run(
                    [script_path], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                
                response = {
                    "status": "success",
                    "log": result.stdout.strip()
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))

            except subprocess.CalledProcessError as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                
                response = {
                    "status": "error",
                    "log": f"Recovery script failed:\n{e.stderr.strip()}"
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint Not Found")

if __name__ == "__main__":
    print(f"📡 CathedralOS API Bridge spinning up on port {PORT}...")
    print(f"📂 Serving Cathedral rituals from: {DIRECTORY}")
    server = http.server.HTTPServer(("0.0.0.0", PORT), ShrineHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down API Bridge safely.")
