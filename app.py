#!/usr/bin/env python3

"""
FiberTrace Flask Dashboard

Web-based dashboard to monitor bale purity statistics in real-time.
Access at: http://raspberry-pi-ip:5000
"""

from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "fibertrace_data.json"

def load_data():
    """Load statistics from JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'total_scanned': 0,
        'good_count': 0,
        'bad_count': 0,
        'last_update': 0
    }

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """API endpoint to get current statistics."""
    data = load_data()
    
    total = data.get('total_scanned', 0)
    good = data.get('good_count', 0)
    bad = data.get('bad_count', 0)
    
    if total > 0:
        purity = (good / total) * 100.0
    else:
        purity = 0.0
    
    last_update = data.get('last_update', 0)
    if last_update > 0:
        last_update_str = datetime.fromtimestamp(last_update).strftime('%Y-%m-%d %H:%M:%S')
    else:
        last_update_str = "Never"
    
    return jsonify({
        'total_scanned': total,
        'good_count': good,
        'bad_count': bad,
        'purity': round(purity, 1),
        'last_update': last_update_str
    })

if __name__ == '__main__':
    print("Starting FiberTrace Dashboard...")
    print("Access at: http://localhost:5000")
    print("Or from another device: http://<raspberry-pi-ip>:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

