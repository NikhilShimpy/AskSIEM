from flask import Flask, render_template, request, jsonify, session
import json
import logging
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Any
import spacy
import dateparser
from elasticsearch import Elasticsearch
import pandas as pd
import re

app = Flask(__name__)
app.secret_key = 'siemspeak-hackathon-demo'
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize components
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback to simple regex if spaCy not available
    nlp = None

# Sample Elasticsearch configuration (replace with actual)
es_config = {
    'hosts': ['http://localhost:9200'],
    'timeout': 30
}

class SIEMQueryGenerator:
    """Converts natural language to SIEM queries"""
    
    def __init__(self):
        self.field_mappings = {
            'login': ['event.action', 'event.category', 'winlog.event_id'],
            'failed': ['event.outcome', 'winlog.event_data.Status'],
            'successful': ['event.outcome', 'winlog.event_data.Status'],
            'ip': ['source.ip', 'destination.ip', 'client.ip'],
            'user': ['user.name', 'winlog.event_data.TargetUserName'],
            'timestamp': ['@timestamp'],
            'server': ['host.name', 'server.name'],
            'vpn': ['network.transport', 'service.name', 'message']
        }
    
    def parse_query(self, text: str) -> Dict[str, Any]:
        """Extract intent and entities from natural language"""
        entities = {
            'intent': 'search',
            'time_range': None,
            'event_type': None,
            'status': None,
            'ips': [],
            'users': [],
            'servers': [],
            'filters': []
        }
        
        # Simple time parsing
        time_patterns = [
            (r'(today|now)', 'now'),
            (r'yesterday', 'yesterday'),
            (r'last (\d+) (hour|hours|hr|hrs)', 'hours'),
            (r'last (\d+) (day|days)', 'days'),
            (r'last (\d+) (week|weeks)', 'weeks')
        ]
        
        text_lower = text.lower()
        
        # Time extraction
        if 'yesterday' in text_lower:
            entities['time_range'] = {'unit': 'day', 'value': 1}
        elif 'today' in text_lower or 'now' in text_lower:
            entities['time_range'] = {'unit': 'now', 'value': 0}
        else:
            for pattern, unit in time_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    if unit in ['hours', 'days', 'weeks']:
                        entities['time_range'] = {'unit': unit, 'value': int(match.group(1))}
                    else:
                        entities['time_range'] = {'unit': unit, 'value': 1}
                    break
        
        # Event type detection
        if any(word in text_lower for word in ['login', 'authentication', 'auth']):
            entities['event_type'] = 'authentication'
        elif any(word in text_lower for word in ['malware', 'virus', 'threat']):
            entities['event_type'] = 'malware'
        elif any(word in text_lower for word in ['vpn', 'remote']):
            entities['filters'].append('vpn')
        
        # Status detection
        if 'failed' in text_lower or 'failure' in text_lower:
            entities['status'] = 'failed'
        elif 'success' in text_lower or 'successful' in text_lower:
            entities['status'] = 'success'
        
        # IP extraction
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        entities['ips'] = re.findall(ip_pattern, text)
        
        return entities
    
    def generate_elasticsearch_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Elasticsearch DSL from parsed entities"""
        
        # Base query structure
        query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            },
            "aggs": {
                "top_ips": {
                    "terms": {
                        "field": "source.ip",
                        "size": 10
                    }
                },
                "timeline": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "fixed_interval": "1h"
                    }
                }
            },
            "size": 100
        }
        
        # Time range filter
        if entities['time_range']:
            time_range = self._calculate_time_range(entities['time_range'])
            query['query']['bool']['filter'].append({
                "range": {
                    "@timestamp": {
                        "gte": time_range['start'],
                        "lte": time_range['end']
                    }
                }
            })
        
        # Event type filters
        if entities['event_type'] == 'authentication':
            query['query']['bool']['must'].append({
                "terms": {
                    "event.category": ["authentication"]
                }
            })
        
        # Status filters
        if entities['status'] == 'failed':
            query['query']['bool']['must'].append({
                "terms": {
                    "event.outcome": ["failure"]
                }
            })
        elif entities['status'] == 'success':
            query['query']['bool']['must'].append({
                "terms": {
                    "event.outcome": ["success"]
                }
            })
        
        # IP filters
        for ip in entities['ips']:
            query['query']['bool']['must'].append({
                "term": {
                    "source.ip": ip
                }
            })
        
        # VPN filters
        if 'vpn' in entities['filters']:
            query['query']['bool']['should'] = [
                {"wildcard": {"service.name": "*vpn*"}},
                {"wildcard": {"network.transport": "*vpn*"}},
                {"wildcard": {"message": "*vpn*"}}
            ]
            query['query']['bool']["minimum_should_match"] = 1
        
        return query
    
    def _calculate_time_range(self, time_config: Dict) -> Dict[str, str]:
        """Calculate time range for queries"""
        now = datetime.utcnow()
        
        if time_config['unit'] == 'now':
            return {
                'start': (now - timedelta(hours=1)).isoformat() + 'Z',
                'end': now.isoformat() + 'Z'
            }
        elif time_config['unit'] == 'yesterday':
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1) - timedelta(seconds=1)
        elif time_config['unit'] == 'hours':
            start = now - timedelta(hours=time_config['value'])
            end = now
        elif time_config['unit'] == 'days':
            start = now - timedelta(days=time_config['value'])
            end = now
        elif time_config['unit'] == 'weeks':
            start = now - timedelta(weeks=time_config['value'])
            end = now
        else:
            # Default to last 24 hours
            start = now - timedelta(hours=24)
            end = now
        
        return {
            'start': start.isoformat() + 'Z',
            'end': end.isoformat() + 'Z'
        }

class ResultsFormatter:
    """Formats query results for display"""
    
    @staticmethod
    def format_results(raw_results: Dict, query_entities: Dict) -> Dict[str, Any]:
        """Format Elasticsearch results for frontend display"""
        
        hits = raw_results.get('hits', {}).get('hits', [])
        aggregations = raw_results.get('aggregations', {})
        
        # Format table data
        table_data = []
        for hit in hits[:50]:  # Limit for display
            source = hit.get('_source', {})
            table_data.append({
                'timestamp': source.get('@timestamp', ''),
                'source_ip': source.get('source', {}).get('ip', ''),
                'event_action': source.get('event', {}).get('action', ''),
                'user': source.get('user', {}).get('name', ''),
                'message': source.get('message', '')[:100] + '...' if source.get('message') and len(source.get('message', '')) > 100 else source.get('message', '')
            })
        
        # Format chart data
        chart_data = {}
        if 'timeline' in aggregations:
            timeline_data = aggregations['timeline']['buckets']
            chart_data['timeline'] = {
                'labels': [bucket['key_as_string'] for bucket in timeline_data],
                'values': [bucket['doc_count'] for bucket in timeline_data]
            }
        
        if 'top_ips' in aggregations:
            top_ips_data = aggregations['top_ips']['buckets']
            chart_data['top_ips'] = {
                'labels': [bucket['key'] for bucket in top_ips_data],
                'values': [bucket['doc_count'] for bucket in top_ips_data]
            }
        
        # Generate summary
        summary = f"Found {len(hits)} events"
        if query_entities.get('time_range'):
            summary += f" in the last {query_entities['time_range'].get('value', '')} {query_entities['time_range'].get('unit', '')}"
        
        return {
            'table_data': table_data,
            'chart_data': chart_data,
            'summary': summary,
            'total_hits': len(hits)
        }

# Initialize components
query_generator = SIEMQueryGenerator()
results_formatter = ResultsFormatter()

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    """Process natural language query and return results"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Empty question'}), 400
        
        # Initialize session if not exists
        if 'conversation' not in session:
            session['conversation'] = []
        
        # Parse query
        entities = query_generator.parse_query(question)
        
        # Generate Elasticsearch query
        es_query = query_generator.generate_elasticsearch_query(entities)
        
        # In demo mode, use synthetic data
        # In production, this would connect to real Elasticsearch:
        # es = Elasticsearch(**es_config)
        # raw_results = es.search(index="logs-*", body=es_query)
        
        # For demo, generate synthetic results
        raw_results = generate_synthetic_results(es_query, entities)
        
        # Format results
        formatted_results = results_formatter.format_results(raw_results, entities)
        
        # Store in conversation history
        conversation_entry = {
            'question': question,
            'entities': entities,
            'query': es_query,
            'results': formatted_results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        session['conversation'].append(conversation_entry)
        session.modified = True
        
        response_data = {
            'reply': formatted_results,
            'generated_query': es_query,
            'entities': entities
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        logging.error(f"Error processing question: {str(e)}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/conversation', methods=['GET'])
def get_conversation():
    """Get current conversation history"""
    return jsonify({
        'conversation': session.get('conversation', [])
    })

@app.route('/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history"""
    session['conversation'] = []
    return jsonify({'status': 'cleared'})

def generate_synthetic_results(query: Dict, entities: Dict) -> Dict:
    """Generate synthetic Elasticsearch results for demo"""
    # This function creates realistic-looking demo data
    # In production, this would be replaced with actual Elasticsearch queries
    
    import random
    from datetime import datetime, timedelta
    
    base_time = datetime.utcnow()
    events = []
    
    # Generate synthetic events based on query intent
    event_count = random.randint(50, 200)
    
    for i in range(event_count):
        event_time = base_time - timedelta(hours=random.randint(0, 24))
        
        event = {
            '_source': {
                '@timestamp': event_time.isoformat() + 'Z',
                'source': {'ip': f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}'},
                'event': {
                    'action': random.choice(['login', 'logout', 'access', 'failure']),
                    'category': 'authentication',
                    'outcome': random.choice(['success', 'failure'])
                },
                'user': {'name': f'user{random.randint(1, 20)}'},
                'message': f"Authentication attempt from {random.choice(['VPN', 'local', 'remote'])} network"
            }
        }
        events.append(event)
    
    # Generate aggregations
    timeline_buckets = []
    for i in range(24):
        hour_time = base_time - timedelta(hours=23-i)
        timeline_buckets.append({
            'key_as_string': hour_time.isoformat() + 'Z',
            'key': hour_time.timestamp() * 1000,
            'doc_count': random.randint(0, 20)
        })
    
    top_ips_buckets = []
    for i in range(10):
        top_ips_buckets.append({
            'key': f'10.0.{i}.{random.randint(1, 255)}',
            'doc_count': random.randint(5, 50)
        })
    
    return {
        'hits': {
            'hits': events,
            'total': {'value': event_count}
        },
        'aggregations': {
            'timeline': {
                'buckets': timeline_buckets
            },
            'top_ips': {
                'buckets': top_ips_buckets
            }
        }
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)