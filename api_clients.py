# api_clients.py
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class ThreatIntelligenceAPI:
    """Client for fetching real threat intelligence data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SIEMSpeak-Enterprise/2.1.0',
            'Accept': 'application/json'
        })
    
    def fetch_malware_bazaar(self, limit: int = 100) -> List[Dict]:
        """
        Fetch recent malware samples from MalwareBazaar
        API: https://bazaar.abuse.ch/api/
        """
        try:
            url = "https://mb-api.abuse.ch/api/v1/"
            data = {
                'query': 'get_recent',
                'selector': 'time',
                'limit': limit
            }
            
            response = self.session.post(url, data=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('query_status') == 'ok':
                    return result.get('data', [])
            return []
        except Exception as e:
            logger.error(f"MalwareBazaar API error: {str(e)}")
            return []
    
    def fetch_cybercrime_tracker(self) -> List[Dict]:
        """
        Fetch malicious IPs and domains from Cybercrime Tracker
        API: https://cybercrime-tracker.net/
        """
        try:
            url = "https://cybercrime-tracker.net/ccam.php"
            params = {'api': '1', 'format': 'json'}
            
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json().get('ccam', [])
            return []
        except Exception as e:
            logger.error(f"Cybercrime Tracker API error: {str(e)}")
            return []
    
    def fetch_circl_passive_dns(self, domain: str) -> List[Dict]:
        """
        Fetch DNS and IP threat data from CIRCL
        API: https://www.circl.lu/services/passive-dns/
        """
        try:
            url = f"https://www.circl.lu/pdns/query/{domain}"
            headers = {
                'Accept': 'application/json'
            }
            
            response = self.session.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"CIRCL Passive DNS API error: {str(e)}")
            return []
    
    def fetch_mitre_attack_techniques(self) -> List[Dict]:
        """
        Fetch MITRE ATT&CK techniques
        Using MITRE's official API
        """
        try:
            url = "https://attack.mitre.org/api.php"
            params = {
                'action': 'ask',
                'format': 'json',
                'query': '[[Technique]]|?ID|?Tactic|?Platform|limit=500'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Parse MITRE ATT&CK data
                techniques = []
                if 'query' in data and 'results' in data['query']:
                    for technique_name, technique_data in data['query']['results'].items():
                        techniques.append({
                            'name': technique_name,
                            'id': technique_data.get('printouts', {}).get('ID', [''])[0],
                            'tactics': technique_data.get('printouts', {}).get('Tactic', []),
                            'platforms': technique_data.get('printouts', {}).get('Platform', [])
                        })
                return techniques
            return []
        except Exception as e:
            logger.error(f"MITRE ATT&CK API error: {str(e)}")
            return []

class WazuhAPIClient:
    """Client for Wazuh SIEM API"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()
        
    def authenticate(self) -> bool:
        """Authenticate with Wazuh API"""
        try:
            auth_url = f"{self.base_url}/security/user/authenticate"
            response = self.session.post(
                auth_url,
                auth=(self.username, self.password),
                verify=False  # For demo, in production use proper certificates
            )
            if response.status_code == 200:
                self.token = response.json()['data']['token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                })
                return True
            return False
        except Exception as e:
            logger.error(f"Wazuh authentication error: {str(e)}")
            return False
    
    def get_security_events(self, limit: int = 1000) -> List[Dict]:
        """Fetch security events from Wazuh"""
        if not self.token and not self.authenticate():
            return []
        
        try:
            events_url = f"{self.base_url}/events"
            params = {
                'limit': limit,
                'sort': '-timestamp',
                'search': 'alert'
            }
            
            response = self.session.get(events_url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json().get('data', {}).get('items', [])
            return []
        except Exception as e:
            logger.error(f"Wazuh events API error: {str(e)}")
            return []

class ElasticSecurityClient:
    """Client for Elastic Security Sample Data"""
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_sample_security_events(self) -> List[Dict]:
        """
        Generate sample security events in Elastic format
        This simulates adding sample data via Elastic's sample data feature
        """
        # This is a simulation since Elastic's sample data API requires
        # a running Elastic instance. We'll create realistic sample data.
        
        events = []
        base_time = datetime.utcnow()
        
        # Common event patterns
        event_templates = [
            {
                'event_type': 'failed_login',
                'message': 'Failed login attempt for user {user} from {ip}',
                'severity': 'medium',
                'risk_score': 65
            },
            {
                'event_type': 'successful_login', 
                'message': 'Successful login for user {user} from {ip}',
                'severity': 'low',
                'risk_score': 10
            },
            {
                'event_type': 'malware_detected',
                'message': 'Malware detection alert: {malware_name}',
                'severity': 'critical', 
                'risk_score': 95
            },
            {
                'event_type': 'brute_force',
                'message': 'Multiple failed login attempts from {ip}',
                'severity': 'high',
                'risk_score': 80
            },
            {
                'event_type': 'suspicious_download',
                'message': 'Suspicious file download detected',
                'severity': 'medium',
                'risk_score': 55
            }
        ]
        
        users = ['admin', 'user1', 'service_account', 'rahul.sharma', 'priya.patel']
        ips = ['192.168.1.{}'.format(i) for i in range(1, 50)] + \
              ['10.0.0.{}'.format(i) for i in range(1, 30)]
        
        for i in range(500):  # Generate 500 sample events
            template = random.choice(event_templates)
            hours_ago = random.randint(0, 720)  # Last 30 days
            
            event = {
                'id': f"elastic-{i:06d}",
                'timestamp': (base_time - timedelta(hours=hours_ago)).isoformat() + 'Z',
                'event_type': template['event_type'],
                'source_ip': random.choice(ips),
                'user': random.choice(users),
                'severity': template['severity'],
                'message': template['message'].format(
                    user=random.choice(users),
                    ip=random.choice(ips),
                    malware_name=random.choice(['Trojan.Generic', 'Ransomware.Crypto', 'Backdoor.Agent'])
                ),
                'risk_score': template['risk_score'] + random.randint(-10, 10),
                'country': random.choice(['IN', 'US', 'CN', 'RU', 'DE', 'FR', 'UK', 'JP']),
                'bytes_sent': random.randint(0, 1000000),
                'bytes_received': random.randint(0, 500000),
                'data_source': 'Elastic Security Sample'
            }
            events.append(event)
        
        return events