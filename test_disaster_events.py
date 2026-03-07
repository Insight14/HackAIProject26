"""
Test script for disaster_events.py
"""
from disaster_events import get_active_disaster_events
import json

def main():
    events = get_active_disaster_events()
    print(json.dumps(events, indent=2))

if __name__ == "__main__":
    main()
