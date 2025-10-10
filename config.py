# SIEM Connection Settings
ELASTICSEARCH_HOSTS = ['http://localhost:9200']
ELASTICSEARCH_TIMEOUT = 30
WAZUH_API_URL = 'https://wazuh-server:55000'

# NLP Settings
SPACY_MODEL = 'en_core_web_sm'
QUERY_CONFIDENCE_THRESHOLD = 0.7

# UI Settings
MAX_RESULTS_DISPLAY = 100
DEFAULT_TIME_RANGE = '24h'