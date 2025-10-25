"""
Configuration for MCP Parent Services Server - K-12 School Choice
"""
import os

# Server Configuration
SERVER_NAME = "parent-services-server"
SERVER_VERSION = "1.0.0"

# Google Cloud Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "a4i-c1-test")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "education_data")

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model Configuration
VISION_MODEL = "gemini-2.0-flash-exp"
MATCHING_MODEL = "gemini-2.0-flash-exp"

# K-12 School Matching Weights
MATCHING_WEIGHTS = {
    "school_quality": 0.30,        # Academic performance, graduation rates
    "programs_services": 0.25,     # STEM, Special Ed, Gifted programs
    "school_environment": 0.20,    # Class size, school size, culture
    "location": 0.15,              # Distance from home
    "admission_fit": 0.10          # Likelihood of admission (neighborhood vs lottery)
}

# School Level Mapping
SCHOOL_LEVELS = {
    "elementary": 1,    # K-5
    "middle": 2,        # 6-8
    "high": 3,          # 9-12
    "other": 4          # Mixed/Alternative
}

# Grade to School Level Mapping
GRADE_TO_LEVEL = {
    "K": 1, "kindergarten": 1,
    "1": 1, "2": 1, "3": 1, "4": 1, "5": 1, "first": 1, "second": 1, "third": 1, "fourth": 1, "fifth": 1,
    "6": 2, "7": 2, "8": 2, "sixth": 2, "seventh": 2, "eighth": 2,
    "9": 3, "10": 3, "11": 3, "12": 3, "ninth": 3, "tenth": 3, "eleventh": 3, "twelfth": 3
}

# School Categories for Match Quality
MATCH_CATEGORIES = {
    "excellent": {"min_score": 0.85, "label": "Excellent Match", "color": "#10b981", "emoji": "🌟"},
    "good": {"min_score": 0.70, "label": "Good Match", "color": "#3b82f6", "emoji": "✅"},
    "fair": {"min_score": 0.50, "label": "Fair Match", "color": "#f59e0b", "emoji": "⚠️"},
    "consider": {"min_score": 0.00, "label": "Consider", "color": "#6b7280", "emoji": "💭"}
}

# Admission Types
ADMISSION_TYPES = {
    "neighborhood": {"priority": 1, "description": "Guaranteed admission based on residence"},
    "lottery": {"priority": 2, "description": "Application required, lottery selection"},
    "magnet": {"priority": 3, "description": "Competitive application required"},
    "charter": {"priority": 2, "description": "Charter school, may have lottery"}
}

# File Upload Limits
MAX_FILE_SIZE_MB = 20
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/jpg',
    'image/webp',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
]

# Default location (if not specified)
DEFAULT_LOCATION = {"city": "San Jose", "state": "CA", "zip": "95112"}

