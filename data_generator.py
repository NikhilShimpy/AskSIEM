import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from models import SecurityEvent, EventType, SeverityLevel

class AdvancedDataGenerator:
    """Advanced data generator for realistic SIEM events"""
    
    def __init__(self):
        self.setup_data_sources()
    
    def setup_data_sources(self):
        """Initialize data sources and patterns"""
        self.users = self._generate_user_list(150)
        self.departments = ['IT', 'HR', 'Finance', 'Marketing', 'Engineering', 'Sales', 'Support']
        self.countries = ['US', 'UK', 'DE', 'FR', 'JP', 'CN', 'IN', 'BR', 'AU', 'CA', 'RU', 'KR', 'NL', 'SG']
        self.attack_patterns = self._setup_attack_patterns()
        
    def _generate_user_list(self, count: int) -> List[Dict]:
        """Generate realistic user list"""
        first_names = ['john', 'jane', 'mike', 'sara', 'david', 'lisa', 'robert', 'emily', 'michael', 'susan']
        last_names = ['smith', 'johnson', 'williams', 'brown', 'jones', 'miller', 'davis', 'garcia', 'rodriguez', 'wilson']
        
        users = []
        for i in range(count):
            first = random.choice(first_names)
            last = random.choice(last_names)
            users.append({
                'username': f"{first}.{last}{i}",
                'department': random.choice(self.departments),
                'role': random.choice(['user', 'admin', 'manager']),
                'is_active': random.random() > 0.1  # 90% active
            })
        
        return users
    
    def _setup_attack_patterns(self) -> Dict[str, Any]:
        """Setup realistic attack patterns"""
        return {
            'brute_force': {
                'description': 'Multiple failed login attempts from single IP',
                'ip_ranges': ['182.162.', '194.153.', '203.113.'],
                'time_pattern': 'clustered',  # Attempts in short time window
                'user_targets': ['admin', 'root', 'service-account']
            },
            'port_scan': {
                'description': 'Sequential port scanning activity',
                'ip_ranges': ['198.51.', '203.0.', '192.0.2.'],
                'port_ranges': [(1, 1000), (8080, 9000)],
                'duration_hours': [1, 6]
            },
            'data_exfiltration': {
                'description': 'Large data transfers to external IPs',
                'target_countries': ['CN', 'RU', 'KR'],
                'data_threshold_mb': 100,
                'time_pattern': 'off_hours'  # Outside business hours
            }
        }
    
    def generate_training_data(self, sample_size: int = 10000) -> List[Dict]:
        """Generate comprehensive training dataset"""
        events = []
        
        # Generate normal activity (70%)
        normal_events = int(sample_size * 0.7)
        events.extend(self._generate_normal_activity(normal_events))
        
        # Generate attack patterns (30%)
        attack_events = sample_size - normal_events
        events.extend(self._generate_attack_patterns(attack_events))
        
        # Shuffle events
        random.shuffle(events)
        
        return events
    
    def _generate_normal_activity(self, count: int) -> List[Dict]:
        """Generate normal user activity"""
        events = []
        base_time = datetime.utcnow() - timedelta(days=30)
        
        for i in range(count):
            # Normal login patterns
            if random.random() < 0.8:  # 80% successful logins
                event_type = EventType.SUCCESSFUL_LOGIN
                severity = SeverityLevel.LOW
                risk_score = random.randint(1, 30)
            else:  # 20% failed logins (normal user error)
                event_type = EventType.FAILED_LOGIN
                severity = SeverityLevel.MEDIUM
                risk_score = random.randint(31, 60)
            
            user = random.choice(self.users)
            event = self._create_event(
                event_id=f"norm_{i}",
                base_time=base_time,
                event_type=event_type,
                user=user['username'],
                severity=severity,
                risk_score=risk_score,
                is_attack=False
            )
            events.append(event.to_dict())
        
        return events
    
    def _generate_attack_patterns(self, count: int) -> List[Dict]:
        """Generate attack pattern events"""
        events = []
        base_time = datetime.utcnow() - timedelta(days=30)
        
        attack_types = list(self.attack_patterns.keys())
        
        for i in range(count):
            attack_type = random.choice(attack_types)
            pattern = self.attack_patterns[attack_type]
            
            if attack_type == 'brute_force':
                event = self._generate_brute_force_event(f"atk_bf_{i}", base_time, pattern)
            elif attack_type == 'port_scan':
                event = self._generate_port_scan_event(f"atk_ps_{i}", base_time, pattern)
            elif attack_type == 'data_exfiltration':
                event = self._generate_exfiltration_event(f"atk_de_{i}", base_time, pattern)
            else:
                event = self._generate_generic_attack_event(f"atk_gen_{i}", base_time)
            
            if event:
                events.append(event.to_dict())
        
        return events
    
    def _generate_brute_force_event(self, event_id: str, base_time: datetime, pattern: Dict) -> SecurityEvent:
        """Generate brute force attack event"""
        # Use attack pattern IP ranges
        ip_prefix = random.choice(pattern['ip_ranges'])
        source_ip = f"{ip_prefix}{random.randint(1, 255)}.{random.randint(1, 255)}"
        
        # Target admin accounts
        target_user = random.choice(pattern['user_targets'])
        
        return self._create_event(
            event_id=event_id,
            base_time=base_time,
            event_type=EventType.BRUTE_FORCE_ATTEMPT,
            user=target_user,
            severity=SeverityLevel.HIGH,
            risk_score=random.randint(70, 95),
            source_ip=source_ip,
            is_attack=True
        )
    
    def _generate_port_scan_event(self, event_id: str, base_time: datetime, pattern: Dict) -> SecurityEvent:
        """Generate port scan event"""
        ip_prefix = random.choice(pattern['ip_ranges'])
        source_ip = f"{ip_prefix}{random.randint(1, 255)}.{random.randint(1, 255)}"
        
        return self._create_event(
            event_id=event_id,
            base_time=base_time,
            event_type=EventType.PORT_SCAN,
            user='unknown',
            severity=SeverityLevel.MEDIUM,
            risk_score=random.randint(60, 80),
            source_ip=source_ip,
            is_attack=True
        )
    
    def _generate_exfiltration_event(self, event_id: str, base_time: datetime, pattern: Dict) -> SecurityEvent:
        """Generate data exfiltration event"""
        target_country = random.choice(pattern['target_countries'])
        
        return self._create_event(
            event_id=event_id,
            base_time=base_time,
            event_type=EventType.DATA_EXFILTRATION,
            user=random.choice([u['username'] for u in self.users if u['role'] == 'user']),
            severity=SeverityLevel.CRITICAL,
            risk_score=random.randint(80, 100),
            country=target_country,
            bytes_sent=random.randint(1000000, 50000000),  # 1MB - 50MB
            is_attack=True
        )
    
    def _generate_generic_attack_event(self, event_id: str, base_time: datetime) -> SecurityEvent:
        """Generate generic attack event"""
        attack_types = [
            (EventType.MALWARE_DETECTED, SeverityLevel.CRITICAL, 85, 100),
            (EventType.FIREWALL_BLOCK, SeverityLevel.HIGH, 70, 90),
            (EventType.PRIVILEGE_ESCALATION, SeverityLevel.HIGH, 75, 95),
            (EventType.SUSPICIOUS_CONNECTION, SeverityLevel.MEDIUM, 60, 80)
        ]
        
        event_type, severity, min_risk, max_risk = random.choice(attack_types)
        
        return self._create_event(
            event_id=event_id,
            base_time=base_time,
            event_type=event_type,
            user=random.choice([u['username'] for u in self.users]),
            severity=severity,
            risk_score=random.randint(min_risk, max_risk),
            is_attack=True
        )
    
    def _create_event(self, event_id: str, base_time: datetime, event_type: EventType, 
                     user: str, severity: SeverityLevel, risk_score: int,
                     source_ip: str = None, country: str = None, 
                     bytes_sent: int = None, is_attack: bool = False) -> SecurityEvent:
        """Create a security event with realistic data"""
        
        # Generate timestamp with realistic distribution
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        
        timestamp = base_time + timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        # Generate IP addresses
        if not source_ip:
            if is_attack and random.random() < 0.7:  # 70% external IPs for attacks
                source_ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            else:
                source_ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
        destination_ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 254)}"
        
        # Generate country
        if not country:
            if is_attack and random.random() < 0.6:  # 60% foreign countries for attacks
                country = random.choice([c for c in self.countries if c != 'US'])
            else:
                country = random.choice(self.countries)
        
        # Generate message based on event type
        messages = {
            EventType.FAILED_LOGIN: f"Failed authentication attempt for user {user} from {source_ip}",
            EventType.SUCCESSFUL_LOGIN: f"Successful login for user {user} from {source_ip}",
            EventType.MALWARE_DETECTED: f"Potential malware activity detected from {source_ip}",
            EventType.FIREWALL_BLOCK: f"Firewall blocked connection attempt from {source_ip} to port {random.randint(1000, 9999)}",
            EventType.PRIVILEGE_ESCALATION: f"Privilege escalation attempt detected for user {user}",
            EventType.DATA_EXFILTRATION: f"Large data transfer ({bytes_sent} bytes) detected from {source_ip} to {country}",
            EventType.PORT_SCAN: f"Port scanning activity detected from {source_ip}",
            EventType.BRUTE_FORCE_ATTEMPT: f"Multiple failed login attempts from {source_ip} targeting user {user}",
            EventType.SUSPICIOUS_CONNECTION: f"Suspicious network connection from {source_ip} to internal resource"
        }
        
        message = messages.get(event_type, "Security event detected")
        
        # Set bytes if not provided
        if bytes_sent is None:
            bytes_sent = random.randint(0, 100000)
        
        return SecurityEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            source_ip=source_ip,
            destination_ip=destination_ip,
            user=user,
            severity=severity,
            country=country,
            message=message,
            risk_score=risk_score,
            bytes_sent=bytes_sent,
            bytes_received=random.randint(0, 50000)
        )

# Utility function to generate sample dataset
def generate_sample_dataset(size: int = 10000) -> List[Dict]:
    """Generate sample dataset for training and testing"""
    generator = AdvancedDataGenerator()
    return generator.generate_training_data(size)

if __name__ == "__main__":
    # Generate sample dataset
    sample_data = generate_sample_dataset(1000)
    print(f"Generated {len(sample_data)} sample events")
    print("Sample event:", json.dumps(sample_data[0], indent=2))