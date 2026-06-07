#!/usr/bin/env python3
"""Product demo sites server. Run: python server.py"""
import http.server, socketserver, os

PORT = 8099
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} → {fmt % args}")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"\n✅ Product sites: http://localhost:{PORT}/\n")
    print(f"  🛒 FreshMart   http://localhost:{PORT}/freshmart/")
    print(f"  💳 FastPay     http://localhost:{PORT}/fastpay/")
    print(f"  🚚 GoExpress   http://localhost:{PORT}/goexpress/")
    print(f"  🔌 DevBridge   http://localhost:{PORT}/devbridge/")
    print(f"  👤 MyProfile   http://localhost:{PORT}/myprofile/")
    print(f"  📊 DataPulse   http://localhost:{PORT}/datapulse/\n")
    httpd.serve_forever()
