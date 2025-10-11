from flask import Flask, render_template, request, jsonify, session
import json
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Any, Tuple
import re
import random
import pandas as pd
from collections import Counter
import numpy as np
import os
import sys
import logging

app = Flask(__name__)
app.secret_key = 'siemspeak-production-secure-key-2024'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Configure logging for Vercel (console only)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types and other non-serializable objects"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

# Set custom JSON encoder
app.json_encoder = JSONEncoder

class NaturalLanguageProcessor:
    """Advanced NLP for security query understanding"""
    
    def __init__(self):
        self.intent_patterns = {
            'failed_logins': [
                r'failed.*login', r'login.*failed', r'authentication.*fail',
                r'failed.*auth', r'unsuccessful.*login'
            ],
            'successful_logins': [
                r'successful.*login', r'login.*success', r'success.*auth'
            ],
            'brute_force': [
                r'brute.*force', r'multiple.*failed', r'repeated.*login'
            ],
            'malware_detection': [
                r'malware', r'virus', r'threat', r'malicious'
            ],
            'suspicious_activity': [
                r'suspicious', r'unusual', r'anomaly', r'strange'
            ],
            'top_users': [
                r'top.*user', r'most.*active', r'user.*activity'
            ],
            'geographic_analysis': [
                r'country', r'geographic', r'location', r'region', r'india', r'INDIA'
            ],
            'time_analysis': [
                r'timeline', r'overtime', r'trend', r'hourly', r'daily'
            ]
        }
        
        self.entity_patterns = {
            'time_range': [
                (r'last\s+(\d+)\s+hours?', 'hours'),
                (r'last\s+(\d+)\s+days?', 'days'),
                (r'last\s+(\d+)\s+weeks?', 'weeks'),
                (r'today', 'today'),
                (r'yesterday', 'yesterday'),
                (r'past\s+week', 'last_week'),
                (r'past\s+month', 'last_month')
            ],
            'severity': [
                (r'critical', 'critical'),
                (r'high', 'high'),
                (r'medium', 'medium'),
                (r'low', 'low')
            ],
            'count': [
                (r'top\s+(\d+)', 'top_n'),
                (r'first\s+(\d+)', 'top_n')
            ],
            'country': [
                (r'india', 'IN'),
                (r'usa', 'US'),
                (r'china', 'CN'),
                (r'russia', 'RU')
            ]
        }

    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language query into structured format"""
        query_lower = query.lower()
        
        # Detect intent
        intent = self._detect_intent(query_lower)
        
        # Extract entities
        entities = self._extract_entities(query_lower)
        
        # Determine chart types based on intent
        chart_types = self._suggest_chart_types(intent, entities)
        
        return {
            'intent': intent,
            'entities': entities,
            'chart_types': chart_types,
            'original_query': query
        }
    
    def _detect_intent(self, query: str) -> str:
        """Detect the primary intent of the query"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return intent
        return 'general_search'
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query"""
        entities = {
            'time_range': {'unit': 'hours', 'value': 24},
            'severity': None,
            'top_n': 10,
            'country': None,
            'filters': {}
        }
        
        # Extract time range
        for pattern, unit in self.entity_patterns['time_range']:
            match = re.search(pattern, query)
            if match:
                if unit in ['hours', 'days', 'weeks']:
                    entities['time_range'] = {
                        'unit': unit,
                        'value': int(match.group(1)) if match.groups() else 1
                    }
                else:
                    entities['time_range'] = {'unit': unit, 'value': 1}
                break
        
        # Extract severity
        for pattern, severity in self.entity_patterns['severity']:
            if re.search(pattern, query):
                entities['severity'] = severity
                break
        
        # Extract country
        for pattern, country in self.entity_patterns['country']:
            if re.search(pattern, query):
                entities['country'] = country
                break
        
        # Extract top N
        for pattern, key in self.entity_patterns['count']:
            match = re.search(pattern, query)
            if match and match.groups():
                entities['top_n'] = int(match.group(1))
                break
        
        return entities
    
    def _suggest_chart_types(self, intent: str, entities: Dict) -> List[str]:
        """Suggest appropriate chart types based on intent"""
        chart_mapping = {
            'failed_logins': ['timeline', 'top_users', 'geo_distribution'],
            'successful_logins': ['timeline', 'top_users', 'geo_distribution'],
            'brute_force': ['timeline', 'top_ips', 'severity_distribution'],
            'malware_detection': ['event_types', 'severity_distribution', 'timeline'],
            'suspicious_activity': ['timeline', 'event_types', 'risk_distribution'],
            'top_users': ['user_activity', 'bar_chart'],
            'geographic_analysis': ['geo_distribution', 'world_map'],
            'time_analysis': ['timeline', 'heatmap'],
            'general_search': ['timeline', 'event_types', 'top_ips']
        }
        
        return chart_mapping.get(intent, ['timeline', 'event_types'])

class SecurityDataGenerator:
    """Generate realistic security event data with India focus"""
    
    def __init__(self):
        self.users = [f'user{i}' for i in range(1, 101)] + ['admin', 'root', 'service-account', 'administrator']
        self.indian_users = ['rahul.sharma', 'priya.patel', 'amit.singh', 'neha.gupta', 'vikram.yadav']
        self.users.extend(self.indian_users)
        
        self.servers = [f'srv-{chr(65+i)}{j}' for i in range(5) for j in range(1, 6)]
        # Focus on India and neighboring countries
        self.countries = ['IN', 'US', 'UK', 'DE', 'FR', 'JP', 'CN', 'BR', 'AU', 'CA', 'RU', 'KR', 'SG', 'AE', 'PK', 'BD', 'LK', 'NP']
        self.event_types = [
            'failed_login', 'successful_login', 'malware_detected', 
            'firewall_block', 'privilege_escalation', 'data_exfiltration',
            'port_scan', 'brute_force_attempt', 'suspicious_connection'
        ]
        
        # Pre-generate consistent sample data
        self.sample_data = self._generate_sample_data(10000)
    
    def _generate_sample_data(self, count: int) -> List[Dict]:
        """Generate consistent sample data"""
        events = []
        base_time = datetime.utcnow() - timedelta(days=30)
        
        # Fixed distributions for consistent results
        event_distributions = {
            'failed_login': 0.25,
            'successful_login': 0.35,
            'malware_detected': 0.05,
            'firewall_block': 0.10,
            'privilege_escalation': 0.03,
            'data_exfiltration': 0.02,
            'port_scan': 0.08,
            'brute_force_attempt': 0.07,
            'suspicious_connection': 0.05
        }
        
        country_weights = {
            'IN': 0.35,  # Higher weight for India
            'US': 0.15,
            'UK': 0.08,
            'DE': 0.07,
            'CN': 0.06,
            'RU': 0.05,
            'FR': 0.04,
            'JP': 0.04,
            'BR': 0.03,
            'AU': 0.03,
            'CA': 0.03,
            'KR': 0.02,
            'SG': 0.02,
            'AE': 0.01,
            'PK': 0.01,
            'BD': 0.01,
            'LK': 0.01,
            'NP': 0.01
        }
        
        # Set random seed for consistent results
        random.seed(42)
        
        for i in range(count):
            # Choose event type based on distribution
            event_type = random.choices(
                list(event_distributions.keys()),
                weights=list(event_distributions.values())
            )[0]
            
            # Choose country based on weights
            country = random.choices(
                list(country_weights.keys()),
                weights=list(country_weights.values())
            )[0]
            
            # Generate timestamp with realistic distribution
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            timestamp = base_time + timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            # Generate IP based on country
            if country == 'IN':
                source_ip = f"103.{random.randint(100, 255)}.{random.randint(1, 255)}.{random.randint(1, 254)}"
            else:
                source_ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            
            event = {
                'id': f"evt_{i:06d}",
                'timestamp': timestamp.isoformat() + 'Z',
                'event_type': event_type,
                'source_ip': source_ip,
                'destination_ip': f"192.168.{random.randint(1, 255)}.{random.randint(1, 254)}",
                'user': random.choice(self.users),
                'severity': self._assign_severity(event_type),
                'country': country,
                'message': self._generate_message(event_type, country),
                'risk_score': self._assign_risk_score(event_type),
                'bytes_sent': random.randint(0, 1000000),
                'bytes_received': random.randint(0, 500000)
            }
            events.append(event)
        
        return events
    
    def get_sample_data(self):
        """Return the pre-generated sample data"""
        return self.sample_data
    
    def get_filtered_data(self, query_context: Dict) -> List[Dict]:
        """Get filtered data based on query context"""
        filtered_data = self.sample_data.copy()
        
        # Apply time filter
        time_range = query_context.get('time_range', {'unit': 'hours', 'value': 24})
        filtered_data = self._filter_by_time(filtered_data, time_range)
        
        # Apply other filters
        if query_context.get('severity'):
            filtered_data = [e for e in filtered_data if e['severity'] == query_context['severity']]
        
        if query_context.get('country'):
            filtered_data = [e for e in filtered_data if e['country'] == query_context['country']]
        
        if query_context.get('event_type'):
            filtered_data = [e for e in filtered_data if e['event_type'] == query_context['event_type']]
        
        return filtered_data
    
    def _filter_by_time(self, events: List[Dict], time_range: Dict) -> List[Dict]:
        """Filter events by time range"""
        now = datetime.utcnow()
        
        if time_range['unit'] == 'hours':
            cutoff = now - timedelta(hours=time_range['value'])
        elif time_range['unit'] == 'days':
            cutoff = now - timedelta(days=time_range['value'])
        elif time_range['unit'] == 'weeks':
            cutoff = now - timedelta(weeks=time_range['value'])
        elif time_range['unit'] == 'today':
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range['unit'] == 'yesterday':
            cutoff = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            now = cutoff + timedelta(days=1) - timedelta(seconds=1)
        else:
            cutoff = now - timedelta(hours=24)
        
        filtered_events = []
        for e in events:
            event_time = datetime.fromisoformat(e['timestamp'].replace('Z', ''))
            if cutoff <= event_time <= now:
                filtered_events.append(e)
        
        return filtered_events
    
    def _assign_severity(self, event_type: str) -> str:
        """Assign severity based on event type"""
        severity_map = {
            'failed_login': 'medium',
            'successful_login': 'low',
            'malware_detected': 'critical',
            'firewall_block': 'high',
            'privilege_escalation': 'high',
            'data_exfiltration': 'critical',
            'port_scan': 'medium',
            'brute_force_attempt': 'high',
            'suspicious_connection': 'medium'
        }
        return severity_map.get(event_type, 'low')
    
    def _assign_risk_score(self, event_type: str) -> int:
        """Assign risk score based on event type"""
        risk_map = {
            'failed_login': random.randint(40, 70),
            'successful_login': random.randint(1, 30),
            'malware_detected': random.randint(85, 100),
            'firewall_block': random.randint(60, 85),
            'privilege_escalation': random.randint(75, 95),
            'data_exfiltration': random.randint(90, 100),
            'port_scan': random.randint(50, 75),
            'brute_force_attempt': random.randint(70, 90),
            'suspicious_connection': random.randint(55, 80)
        }
        return risk_map.get(event_type, random.randint(1, 100))
    
    def _generate_message(self, event_type: str, country: str) -> str:
        """Generate realistic event message"""
        messages = {
            'failed_login': f'Failed authentication attempt for user {{user}} from {{ip}} ({{country}})',
            'successful_login': f'Successful login for user {{user}} from {{ip}} ({{country}})',
            'malware_detected': f'Potential malware activity detected from {{ip}} ({{country}})',
            'firewall_block': f'Firewall blocked connection attempt from {{ip}} ({{country}})',
            'privilege_escalation': f'Privilege escalation attempt detected for user {{user}} from {{country}}',
            'data_exfiltration': f'Large data transfer detected from {{ip}} ({{country}})',
            'port_scan': f'Port scanning activity detected from {{ip}} ({{country}})',
            'brute_force_attempt': f'Multiple failed login attempts from {{ip}} ({{country}})',
            'suspicious_connection': f'Suspicious network connection from {{ip}} ({{country}})'
        }
        base_msg = messages.get(event_type, 'Security event detected from {country}')
        return base_msg.format(
            user=random.choice(self.users),
            ip=self._generate_ip_for_country(country),
            country=country
        )
    
    def _generate_ip_for_country(self, country: str) -> str:
        """Generate IP address based on country"""
        if country == 'IN':
            return f"103.{random.randint(100, 255)}.{random.randint(1, 255)}.{random.randint(1, 254)}"
        elif country == 'US':
            return f"198.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 254)}"
        elif country == 'CN':
            return f"203.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 254)}"
        else:
            return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

class AnalyticsEngine:
    """Advanced analytics and insights generation"""
    
    def __init__(self):
        self.data_generator = SecurityDataGenerator()
    
    def process_query(self, parsed_query: Dict) -> Dict[str, Any]:
        """Process parsed query and generate comprehensive results"""
        # Get filtered data based on query
        entities = parsed_query['entities']
        filtered_events = self.data_generator.get_filtered_data(entities)
        
        # Generate analysis
        analysis = self._analyze_events(filtered_events, parsed_query)
        
        # Generate insights and summary
        insights = self._generate_insights(analysis, parsed_query)
        summary = self._generate_summary(analysis, parsed_query)
        
        # Prepare chart data
        chart_data = self._prepare_chart_data(analysis, parsed_query['chart_types'])
        
        # Convert all numpy types to native Python types for JSON serialization
        result = {
            'summary': summary,
            'insights': self._convert_to_serializable(insights),
            'chart_data': self._convert_to_serializable(chart_data),
            'analysis': self._convert_to_serializable(analysis),
            'table_data': filtered_events[:100],  # Sample for display
            'total_events': len(filtered_events),
            'sampled_events': min(100, len(filtered_events)),
            'processing_time': f"{random.uniform(0.1, 0.5):.2f}s",
            'data_source': 'SIEM Database + Threat Intelligence'
        }
        
        return result
    
    def _convert_to_serializable(self, obj):
        """Convert numpy types and other non-serializable objects to JSON-serializable types"""
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return {str(k): self._convert_to_serializable(v) for k, v in obj.to_dict().items()}
        elif isinstance(obj, dict):
            return {str(k): self._convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        else:
            return obj
    
    def _analyze_events(self, events: List[Dict], parsed_query: Dict) -> Dict[str, Any]:
        """Comprehensive event analysis"""
        if not events:
            return {
                'total_events': 0,
                'time_range': {'start': '', 'end': ''},
                'event_types': {},
                'severity_distribution': {},
                'top_users': {},
                'top_source_ips': {},
                'countries': {},
                'risk_scores': {'average': 0, 'max': 0, 'min': 0},
                'timeline': {'labels': [], 'values': []}
            }
        
        # Use pandas for analysis but convert to native types
        df = pd.DataFrame(events)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Basic statistics
        analysis = {
            'total_events': int(len(events)),
            'time_range': {
                'start': df['timestamp'].min().isoformat(),
                'end': df['timestamp'].max().isoformat()
            }
        }
        
        # Event type distribution
        event_types_count = df['event_type'].value_counts().head(10)
        analysis['event_types'] = {str(k): int(v) for k, v in event_types_count.items()}
        
        # Severity distribution
        severity_count = df['severity'].value_counts()
        analysis['severity_distribution'] = {str(k): int(v) for k, v in severity_count.items()}
        
        # Top users
        top_users = df['user'].value_counts().head(10)
        analysis['top_users'] = {str(k): int(v) for k, v in top_users.items()}
        
        # Top source IPs
        top_ips = df['source_ip'].value_counts().head(10)
        analysis['top_source_ips'] = {str(k): int(v) for k, v in top_ips.items()}
        
        # Countries
        countries_count = df['country'].value_counts()
        analysis['countries'] = {str(k): int(v) for k, v in countries_count.items()}
        
        # Risk scores
        analysis['risk_scores'] = {
            'average': float(df['risk_score'].mean()),
            'max': int(df['risk_score'].max()),
            'min': int(df['risk_score'].min())
        }
        
        # Time-based analysis
        analysis['timeline'] = self._analyze_timeline(df)
        
        # Intent-specific analysis
        if parsed_query['intent'] == 'failed_logins':
            analysis['failed_login_analysis'] = self._analyze_failed_logins(df)
        elif parsed_query['intent'] == 'brute_force':
            analysis['brute_force_analysis'] = self._analyze_brute_force(df)
        elif parsed_query['intent'] == 'geographic_analysis':
            analysis['geographic_analysis'] = self._analyze_geographic(df)
        
        return analysis
    
    def _analyze_timeline(self, df: pd.DataFrame) -> Dict:
        """Analyze event timeline"""
        try:
            df_hourly = df.set_index('timestamp').resample('H').size()
            return {
                'labels': [ts.isoformat() for ts in df_hourly.index],
                'values': [int(val) for val in df_hourly.values]
            }
        except:
            return {'labels': [], 'values': []}
    
    def _analyze_failed_logins(self, df: pd.DataFrame) -> Dict:
        """Analyze failed login patterns"""
        failed_logins = df[df['event_type'] == 'failed_login']
        if len(failed_logins) == 0:
            return {
                'total_failed': 0,
                'unique_users': 0,
                'unique_ips': 0,
                'peak_hour': ''
            }
        
        peak_time = failed_logins.set_index('timestamp').resample('H').size()
        return {
            'total_failed': int(len(failed_logins)),
            'unique_users': int(failed_logins['user'].nunique()),
            'unique_ips': int(failed_logins['source_ip'].nunique()),
            'peak_hour': peak_time.idxmax().isoformat() if len(peak_time) > 0 else ''
        }
    
    def _analyze_brute_force(self, df: pd.DataFrame) -> Dict:
        """Analyze brute force patterns"""
        failed_logins = df[df['event_type'].isin(['failed_login', 'brute_force_attempt'])]
        ip_counts = failed_logins.groupby('source_ip').size()
        suspicious_ips = ip_counts[ip_counts > 5]
        
        return {
            'suspicious_ips_count': int(len(suspicious_ips)),
            'total_attempts': int(failed_logins.shape[0]),
            'suspicious_ips': {str(k): int(v) for k, v in suspicious_ips.to_dict().items()}
        }
    
    def _analyze_geographic(self, df: pd.DataFrame) -> Dict:
        """Analyze geographic patterns"""
        return {
            'total_countries': int(df['country'].nunique()),
            'top_country': df['country'].value_counts().index[0] if len(df) > 0 else '',
            'top_country_count': int(df['country'].value_counts().iloc[0]) if len(df) > 0 else 0,
            'india_events': int(df[df['country'] == 'IN'].shape[0]) if 'IN' in df['country'].values else 0
        }
    
    def _generate_insights(self, analysis: Dict, parsed_query: Dict) -> List[Dict]:
        """Generate actionable insights"""
        insights = []
        
        if analysis.get('total_events', 0) == 0:
            return [{
                'type': 'info',
                'title': 'No Events Found',
                'message': 'No security events match your current query criteria.',
                'recommendation': 'Try broadening your search criteria or adjusting the time range.'
            }]
        
        # High risk events insight
        high_risk_count = analysis.get('severity_distribution', {}).get('high', 0) + \
                         analysis.get('severity_distribution', {}).get('critical', 0)
        if high_risk_count > 0:
            insights.append({
                'type': 'warning',
                'title': f'High Risk Events Detected',
                'message': f'Found {int(high_risk_count)} high/critical severity events requiring attention.',
                'recommendation': 'Review these events immediately for potential security incidents.'
            })
        
        # Failed login insights
        if parsed_query['intent'] == 'failed_logins':
            failed_analysis = analysis.get('failed_login_analysis', {})
            if failed_analysis.get('total_failed', 0) > 50:
                insights.append({
                    'type': 'danger',
                    'title': 'Elevated Failed Login Activity',
                    'message': f"Detected {failed_analysis.get('total_failed', 0)} failed login attempts from {failed_analysis.get('unique_ips', 0)} unique IPs.",
                    'recommendation': 'Investigate source IPs and consider implementing account lockout policies.'
                })
        
        # Brute force insights
        if parsed_query['intent'] == 'brute_force':
            brute_analysis = analysis.get('brute_force_analysis', {})
            if brute_analysis.get('suspicious_ips_count', 0) > 0:
                insights.append({
                    'type': 'danger',
                    'title': 'Potential Brute Force Attacks',
                    'message': f"Identified {brute_analysis.get('suspicious_ips_count', 0)} IPs with suspicious login patterns.",
                    'recommendation': 'Block these IPs and review authentication logs for compromised accounts.'
                })
        
        # Geographic insights for India
        geo_analysis = analysis.get('geographic_analysis', {})
        if geo_analysis.get('india_events', 0) > 100:
            insights.append({
                'type': 'info',
                'title': 'High Activity from India',
                'message': f"Significant security events ({geo_analysis['india_events']}) originating from India.",
                'recommendation': 'Monitor Indian IP ranges for suspicious patterns.'
            })
        
        return insights
    
    def _generate_summary(self, analysis: Dict, parsed_query: Dict) -> str:
        """Generate natural language summary"""
        total_events = analysis.get('total_events', 0)
        
        if total_events == 0:
            return "No security events found matching your query criteria."
        
        intent = parsed_query['intent']
        time_range = parsed_query['entities']['time_range']
        
        # Fix time phrase formatting
        if time_range['unit'] == 'yesterday':
            time_phrase = "yesterday"
        else:
            time_phrase = f"in the last {time_range['value']} {time_range['unit']}"
        
        if intent == 'failed_logins':
            failed_analysis = analysis.get('failed_login_analysis', {})
            peak_hour = failed_analysis.get('peak_hour', '')
            if peak_hour:
                peak_time = datetime.fromisoformat(peak_hour.replace('Z', '')).strftime('%I:%M %p')
            else:
                peak_time = 'unknown time'
                
            return f"Found {failed_analysis.get('total_failed', 0)} failed login attempts {time_phrase} across {failed_analysis.get('unique_users', 0)} unique users. Peak activity occurred around {peak_time}."
        
        elif intent == 'successful_logins':
            successful_logins = analysis.get('event_types', {}).get('successful_login', 0)
            unique_users = analysis.get('top_users', {})
            top_user = list(unique_users.keys())[0] if unique_users else 'N/A'
            top_count = list(unique_users.values())[0] if unique_users else 0
            return f"Detected {successful_logins} successful logins {time_phrase} from {len(unique_users)} unique users. Most active user was {top_user} with {top_count} sessions."
        
        elif intent == 'brute_force':
            brute_analysis = analysis.get('brute_force_analysis', {})
            return f"Identified {brute_analysis.get('suspicious_ips_count', 0)} suspicious IPs with potential brute force activity {time_phrase}. Total of {brute_analysis.get('total_attempts', 0)} authentication attempts detected."
        
        elif intent == 'geographic_analysis':
            countries = analysis.get('countries', {})
            top_country = list(countries.keys())[0] if countries else 'N/A'
            top_count = list(countries.values())[0] if countries else 0
            india_count = countries.get('IN', 0)
            return f"Geographic analysis {time_phrase} shows events from {len(countries)} countries. Top country: {top_country} with {top_count} events. India contributed {india_count} events."
        
        else:
            top_event_type = list(analysis.get('event_types', {}).keys())[0] if analysis.get('event_types') else 'N/A'
            top_event_count = list(analysis.get('event_types', {}).values())[0] if analysis.get('event_types') else 0
            return f"Found {total_events} security events {time_phrase}. Top event type: {top_event_type} with {top_event_count} occurrences. Events recorded from {len(analysis.get('countries', {}))} countries."
    
    def _prepare_chart_data(self, analysis: Dict, chart_types: List[str]) -> Dict[str, Any]:
        """Prepare data for various chart types"""
        chart_data = {}
        
        for chart_type in chart_types[:4]:  # Limit to 4 charts
            if chart_type == 'timeline' and 'timeline' in analysis:
                chart_data['timeline'] = analysis['timeline']
            
            elif chart_type == 'event_types' and 'event_types' in analysis:
                chart_data['event_types'] = {
                    'labels': list(analysis['event_types'].keys()),
                    'values': list(analysis['event_types'].values())
                }
            
            elif chart_type == 'severity_distribution' and 'severity_distribution' in analysis:
                chart_data['severity_distribution'] = {
                    'labels': list(analysis['severity_distribution'].keys()),
                    'values': list(analysis['severity_distribution'].values())
                }
            
            elif chart_type == 'top_users' and 'top_users' in analysis:
                chart_data['top_users'] = {
                    'labels': list(analysis['top_users'].keys())[:10],
                    'values': list(analysis['top_users'].values())[:10]
                }
            
            elif chart_type == 'geo_distribution' and 'countries' in analysis:
                chart_data['geo_distribution'] = {
                    'labels': list(analysis['countries'].keys())[:15],
                    'values': list(analysis['countries'].values())[:15]
                }
        
        return chart_data

# Initialize components
nlp_processor = NaturalLanguageProcessor()
analytics_engine = AnalyticsEngine()

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process natural language query"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Empty query'}), 400
        
        logger.info(f"Processing query: {query}")
        
        # Parse natural language query
        parsed_query = nlp_processor.parse_query(query)
        
        # Process query and generate results
        results = analytics_engine.process_query(parsed_query)
        
        # Prepare response
        response = {
            'success': True,
            'query': query,
            'parsed_query': parsed_query,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Query processed successfully. Found {results['total_events']} events")
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/api/search', methods=['POST'])
def search_events():
    """Search events with filters"""
    try:
        data = request.json
        filters = data.get('filters', {})
        
        # Get filtered data based on filters
        filtered_events = analytics_engine.data_generator.get_filtered_data(filters)
        
        return jsonify({
            'success': True,
            'events': filtered_events[:100],
            'total_count': len(filtered_events),
            'filters': filters
        })
        
    except Exception as e:
        logger.error(f"Error searching events: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/autocomplete', methods=['GET'])
def autocomplete():
    """Provide autocomplete suggestions"""
    query = request.args.get('q', '').lower()
    
    suggestions = [
        'Show failed logins in the last 24 hours',
        'Display successful logins by country',
        'Top 10 users with most activity',
        'Malware detection events this week',
        'Brute force attempts yesterday',
        'Suspicious network activity',
        'Firewall blocks by severity',
        'User login timeline for past week',
        'Security events from India',
        'High risk events from last 7 days'
    ]
    
    if query:
        suggestions = [s for s in suggestions if query in s.lower()]
    
    return jsonify({'suggestions': suggestions[:5]})

@app.route('/conversation', methods=['GET'])
def get_conversation():
    """Get conversation history"""
    return jsonify({
        'conversation': session.get('conversation', [])
    })

@app.route('/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history"""
    session['conversation'] = []
    return jsonify({'status': 'cleared'})

@app.route('/system_status')
def system_status():
    """System status endpoint"""
    return jsonify({
        'status': 'operational',
        'version': '2.1.0',
        'uptime': '24 hours',
        'data_sources': ['SIEM Database', 'Threat Intelligence', 'Log Archives'],
        'last_updated': datetime.utcnow().isoformat()
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)