# Configuration module
import json
import os

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load config at import time
config = load_config()

# Export commonly used values
MODEL_ID = config['model']['model_id']
TIMEOUT = config['model']['timeout']
MAX_RETRIES = config['model']['max_retries']
RETRY_DELAY = config['model']['retry_delay']

OUTPUT_FILE = config['output']['output_file']

TEXT_SPLITTER_CHUNK_SIZE = config['text_splitter']['chunk_size']
TEXT_SPLITTER_CHUNK_OVERLAP = config['text_splitter']['chunk_overlap']

VERBOSE = config['settings']['verbose']
USE_FALLBACK_REGEX = config['settings']['use_fallback_regex']
MAX_HEADING_LENGTH = config['settings']['max_heading_length']

LEVEL_1_KEYWORDS = config['heading_detection']['level_1_keywords']
FALSE_HEADING_PATTERNS = config['heading_detection']['false_heading_patterns']
