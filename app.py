from flask import Flask, render_template, request, jsonify, session
import json
import logging
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Any, Tuple
import re
import random
import pandas as pd
from collections import Counter
import numpy as np

app = Flask(__name__)
app.secret_key = 'siemspeak-production-secure-key-2024'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('siemspeak.log'),
        logging.StreamHandler()
    ]
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
    
    def generate_events(self, query_context: Dict, count: int = 1000) -> List[Dict]:
        """Generate realistic security events based on query context"""
        events = []
        base_time = datetime.utcnow()
        
        # Adjust distribution based on query intent
        intent = query_context.get('intent', 'general_search')
        entities = query_context.get('entities', {})
        event_distribution = self._get_event_distribution(intent)
        
        for i in range(count):
            event = self._generate_single_event(base_time, event_distribution, intent, entities)
            events.append(event)
        
        return events
    
    def _get_event_distribution(self, intent: str) -> Dict[str, float]:
        """Get event type distribution based on intent"""
        distributions = {
            'failed_logins': {'failed_login': 0.6, 'brute_force_attempt': 0.3, 'other': 0.1},
            'successful_logins': {'successful_login': 0.8, 'other': 0.2},
            'malware_detection': {'malware_detected': 0.7, 'suspicious_connection': 0.3},
            'brute_force': {'brute_force_attempt': 0.5, 'failed_login': 0.4, 'other': 0.1},
            'general_search': {et: 1/len(self.event_types) for et in self.event_types}
        }
        return distributions.get(intent, distributions['general_search'])
    
    def _generate_single_event(self, base_time: datetime, distribution: Dict, intent: str, entities: Dict) -> Dict:
        """Generate a single security event"""
        event_type = self._weighted_choice(distribution)
        
        # Adjust timestamp based on intent (create realistic patterns)
        hours_ago = self._get_time_offset(intent)
        timestamp = base_time - timedelta(hours=hours_ago)
        
        # Generate realistic IP addresses with India focus
        source_ip = self._generate_ip(entities.get('country'))
        destination_ip = self._generate_ip()
        
        # Generate event data with India focus
        event = {
            'id': f"evt_{random.randint(100000, 999999)}",
            'timestamp': timestamp.isoformat() + 'Z',
            'event_type': event_type,
            'source_ip': source_ip,
            'destination_ip': destination_ip,
            'user': random.choice(self.users),
            'severity': self._assign_severity(event_type),
            'country': self._assign_country(entities.get('country')),
            'message': self._generate_message(event_type),
            'risk_score': int(random.randint(1, 100)),
            'bytes_sent': int(random.randint(0, 1000000)),
            'bytes_received': int(random.randint(0, 1000000))
        }
        
        return event
    
    def _weighted_choice(self, weights: Dict) -> str:
        """Make weighted random choice"""
        choices = list(weights.keys())
        probabilities = list(weights.values())
        return random.choices(choices, weights=probabilities, k=1)[0]
    
    def _get_time_offset(self, intent: str) -> int:
        """Get time offset in hours based on intent"""
        if intent == 'brute_force':
            return random.randint(0, 24)
        elif intent == 'failed_logins':
            return random.randint(0, 168)
        else:
            return random.randint(0, 720)
    
    def _generate_ip(self, country_filter: str = None) -> str:
        """Generate realistic IP address with India focus"""
        if country_filter == 'IN' or random.random() < 0.6:  # 60% Indian IPs
            # Indian IP ranges
            return f"103.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        elif random.random() < 0.7:  # Internal IPs
            return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        else:  # External IPs
            return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    
    def _assign_country(self, country_filter: str = None) -> str:
        """Assign country with India focus"""
        if country_filter:
            return country_filter
        # Weighted towards India
        if random.random() < 0.4:  # 40% chance for India
            return 'IN'
        else:
            return random.choice([c for c in self.countries if c != 'IN'])
    
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
    
    def _generate_message(self, event_type: str) -> str:
        """Generate realistic event message"""
        messages = {
            'failed_login': 'Failed authentication attempt for user {user} from {ip}',
            'successful_login': 'Successful login for user {user} from {ip}',
            'malware_detected': 'Potential malware activity detected from {ip}',
            'firewall_block': 'Firewall blocked connection attempt from {ip}',
            'privilege_escalation': 'Privilege escalation attempt detected for user {user}',
            'data_exfiltration': 'Large data transfer detected from {ip}',
            'port_scan': 'Port scanning activity detected from {ip}',
            'brute_force_attempt': 'Multiple failed login attempts from {ip}',
            'suspicious_connection': 'Suspicious network connection from {ip}'
        }
        base_msg = messages.get(event_type, 'Security event detected')
        return base_msg.format(
            user=random.choice(self.users),
            ip=self._generate_ip()
        )

class AnalyticsEngine:
    """Advanced analytics and insights generation"""
    
    def __init__(self):
        self.data_generator = SecurityDataGenerator()
    
    def process_query(self, parsed_query: Dict) -> Dict[str, Any]:
        """Process parsed query and generate comprehensive results"""
        # Generate realistic data based on query
        events = self.data_generator.generate_events(parsed_query, 1000)
        
        # Apply time filter
        time_range = parsed_query['entities']['time_range']
        filtered_events = self._filter_by_time(events, time_range)
        
        # Apply other filters
        filtered_events = self._apply_filters(filtered_events, parsed_query['entities'])
        
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
            'table_data': filtered_events[:50],  # Sample for display
            'total_events': len(filtered_events),
            'sampled_events': min(50, len(filtered_events)),
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
        
        return [e for e in events if cutoff <= datetime.fromisoformat(e['timestamp'].replace('Z', '')) <= now]
    
    def _apply_filters(self, events: List[Dict], entities: Dict) -> List[Dict]:
        """Apply additional filters"""
        filtered = events
        
        if entities.get('severity'):
            filtered = [e for e in filtered if e['severity'] == entities['severity']]
        
        if entities.get('country'):
            filtered = [e for e in filtered if e['country'] == entities['country']]
        
        return filtered
    
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
        if analysis.get('countries', {}).get('IN', 0) > 100:
            insights.append({
                'type': 'info',
                'title': 'High Activity from India',
                'message': f"Significant security events ({analysis['countries']['IN']}) originating from India.",
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
        
        time_phrase = f"in the last {time_range['value']} {time_range['unit']}"
        
        if intent == 'failed_logins':
            failed_analysis = analysis.get('failed_login_analysis', {})
            return f"Found {failed_analysis.get('total_failed', 0)} failed login attempts {time_phrase} across {failed_analysis.get('unique_users', 0)} unique users. Peak activity occurred around {failed_analysis.get('peak_hour', 'unknown time')}."
        
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
        
        # Generate sample data based on filters
        events = analytics_engine.data_generator.generate_events({'intent': 'general_search', 'entities': filters}, 200)
        
        # Apply time filter
        if 'time_range' in filters:
            filtered_events = analytics_engine._filter_by_time(events, filters['time_range'])
        else:
            filtered_events = events
        
        # Apply other filters
        filtered_events = analytics_engine._apply_filters(filtered_events, filters)
        
        return jsonify({
            'success': True,
            'events': filtered_events[:50],
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