from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient, DESCENDING
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['github_events']
collection = db['events']

# Create index on timestamp for efficient querying
collection.create_index([('timestamp', DESCENDING)])


def format_timestamp(iso_timestamp):
    """
    Convert ISO timestamp to required format: "1st April 2021 - 9:30 PM UTC"
    """
    dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
    
    # Get day with ordinal suffix
    day = dt.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    
    # Format the datetime
    formatted = dt.strftime(f"{day}{suffix} %B %Y - %I:%M %p UTC")
    return formatted


def parse_push_event(payload):
    """
    Parse GitHub push event webhook payload
    """
    try:
        # Extract branch name from ref (refs/heads/main -> main)
        ref = payload.get('ref', '')
        to_branch = ref.split('/')[-1] if '/' in ref else ref
        
        # Get author information
        author = payload.get('pusher', {}).get('name', 'Unknown')
        
        # Get timestamp
        timestamp = payload.get('head_commit', {}).get('timestamp', datetime.utcnow().isoformat())
        
        return {
            'author': author,
            'action': 'push',
            'to_branch': to_branch,
            'from_branch': None,
            'timestamp': timestamp,
            'request_id': payload.get('head_commit', {}).get('id', str(datetime.utcnow().timestamp()))
        }
    except Exception as e:
        print(f"Error parsing push event: {e}")
        return None


def parse_pull_request_event(payload):
    """
    Parse GitHub pull request event webhook payload
    """
    try:
        pull_request = payload.get('pull_request', {})
        action = payload.get('action', '')
        
        # Get author
        author = pull_request.get('user', {}).get('login', 'Unknown')
        
        # Get branches
        from_branch = pull_request.get('head', {}).get('ref', 'unknown')
        to_branch = pull_request.get('base', {}).get('ref', 'unknown')
        
        # Get timestamp
        timestamp = pull_request.get('created_at', datetime.utcnow().isoformat())
        
        # Determine if this is a merge or pull request
        event_action = 'pull_request'
        if action == 'closed' and pull_request.get('merged', False):
            event_action = 'merge'
            timestamp = pull_request.get('merged_at', timestamp)
        
        return {
            'author': author,
            'action': event_action,
            'to_branch': to_branch,
            'from_branch': from_branch,
            'timestamp': timestamp,
            'request_id': str(pull_request.get('id', datetime.utcnow().timestamp()))
        }
    except Exception as e:
        print(f"Error parsing pull request event: {e}")
        return None


@app.route('/')
def index():
    """
    Serve the main UI page
    """
    return render_template('index.html')


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    GitHub webhook endpoint
    Receives events from GitHub and stores them in MongoDB
    """
    try:
        # Get the event type from headers
        event_type = request.headers.get('X-GitHub-Event')
        payload = request.json
        
        event_data = None
        
        # Parse based on event type
        if event_type == 'push':
            event_data = parse_push_event(payload)
        elif event_type == 'pull_request':
            event_data = parse_pull_request_event(payload)
        
        # Store in MongoDB if parsing was successful
        if event_data:
            collection.insert_one(event_data)
            print(f"Stored {event_data['action']} event from {event_data['author']}")
            return jsonify({'status': 'success', 'message': 'Event stored'}), 200
        else:
            return jsonify({'status': 'ignored', 'message': 'Event not processed'}), 200
            
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/events', methods=['GET'])
def get_events():
    """
    API endpoint to fetch recent events for UI polling
    Returns events from the last 15 seconds to avoid duplicates
    """
    try:
        # Get timestamp parameter (optional) to fetch only new events
        last_timestamp = request.args.get('last_timestamp')
        
        # Build query
        query = {}
        if last_timestamp:
            query['timestamp'] = {'$gt': last_timestamp}
        
        # Fetch events sorted by timestamp (newest first)
        events = list(collection.find(query, {'_id': 0}).sort('timestamp', DESCENDING).limit(50))
        
        # Format events for display
        formatted_events = []
        for event in events:
            if event['action'] == 'push':
                message = f"{event['author']} pushed to {event['to_branch']} on {format_timestamp(event['timestamp'])}"
            elif event['action'] == 'pull_request':
                message = f"{event['author']} submitted a pull request from {event['from_branch']} to {event['to_branch']} on {format_timestamp(event['timestamp'])}"
            elif event['action'] == 'merge':
                message = f"{event['author']} merged branch {event['from_branch']} to {event['to_branch']} on {format_timestamp(event['timestamp'])}"
            else:
                continue
            
            formatted_events.append({
                'message': message,
                'timestamp': event['timestamp'],
                'action': event['action']
            })
        
        return jsonify({'events': formatted_events}), 200
        
    except Exception as e:
        print(f"Error fetching events: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)