"""
Test script for GitHub webhook endpoint
Run this to test without actual GitHub webhooks
"""

import requests
import json
from datetime import datetime

WEBHOOK_URL = "http://localhost:5000/webhook"

def test_push_event():
    payload = {
        "ref": "refs/heads/main",
        "pusher": {"name": "Anshul3977"},
        "head_commit": {
            "id": "abc123",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    headers = {
        "X-GitHub-Event": "push",
        "Content-Type": "application/json"
    }
    
    print("Testing PUSH event...")
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_pull_request_event():
    payload = {
        "action": "opened",
        "pull_request": {
            "id": 12345,
            "user": {"login": "Anshul3977"},
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "Content-Type": "application/json"
    }
    
    print("Testing PULL REQUEST event...")
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_merge_event():
    payload = {
        "action": "closed",
        "pull_request": {
            "id": 67890,
            "merged": True,
            "user": {"login": "Anshul3977"},
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
            "created_at": datetime.utcnow().isoformat() + "Z",
            "merged_at": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "Content-Type": "application/json"
    }
    
    print("Testing MERGE event...")
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

if __name__ == "__main__":
    print("="*50)
    print("GitHub Webhook Testing")
    print("="*50 + "\n")
    
    try:
        test_push_event()
        test_pull_request_event()
        test_merge_event()
        
        print("="*50)
        print("Tests completed! Check http://localhost:5000")
        print("="*50)
    except requests.exceptions.ConnectionError:
        print("ERROR: Flask app not running!")
        print("Start it with: python app.py")
