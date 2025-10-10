"""
Synthetic data generator for demo purposes
This creates realistic-looking security event data
"""

import json
from datetime import datetime, timedelta
import random

def generate_sample_events(count=1000):
    """Generate sample security events for demonstration"""
    
    events = []
    base_time = datetime.utcnow()
    event_types = [
        ("login", "authentication", "success"),
        ("login", "authentication", "failure"), 
        ("vpn_connection", "network", "success"),
        ("file_access", "file", "success"),
        ("malware_detection", "threat", "alert")
    ]
    
    users = [f"user{i}" for i in range(1, 21)]
    servers = [f"server-{chr(65+i)}" for i in range(5)]  # server-A to server-E
    ip_ranges = ["192.168", "10.0", "172.16"]
    
    for i in range(count):
        # Random time in last 24 hours
        event_time = base_time - timedelta(
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        event_action, event_category, event_outcome = random.choice(event_types)
        
        # Generate realistic IP
        ip_base = random.choice(ip_ranges)
        source_ip = f"{ip_base}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        
        event = {
            "@timestamp": event_time.isoformat() + "Z",
            "event": {
                "action": event_action,
                "category": event_category,
                "outcome": event_outcome
            },
            "source": {
                "ip": source_ip
            },
            "user": {
                "name": random.choice(users)
            },
            "host": {
                "name": random.choice(servers)
            },
            "message": generate_event_message(event_action, event_outcome, source_ip)
        }
        
        # Add VPN-related fields for some events
        if event_action == "vpn_connection":
            event["network"] = {"transport": "tcp"}
            event["service"] = {"name": "openvpn"}
        
        events.append(event)
    
    return events

def generate_event_message(action, outcome, ip):
    """Generate realistic event messages"""
    messages = {
        "login": {
            "success": f"Successful authentication from {ip}",
            "failure": f"Failed login attempt from {ip}"
        },
        "vpn_connection": {
            "success": f"VPN connection established from {ip}",
            "failure": f"VPN connection failed from {ip}"
        },
        "file_access": {
            "success": f"File access recorded from {ip}",
            "failure": f"File access denied from {ip}"
        },
        "malware_detection": {
            "alert": f"Potential malware detected from {ip}"
        }
    }
    
    return messages.get(action, {}).get(outcome, f"Security event from {ip}")

if __name__ == "__main__":
    events = generate_sample_events(100)
    print(json.dumps(events[:5], indent=2))