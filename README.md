# GitHub Webhook Receiver - webhook-repo

Flask application that receives GitHub webhook events and displays them in real-time.

## Features

✅ Receives Push, Pull Request, and Merge events from GitHub  
✅ Stores events in MongoDB  
✅ Real-time UI with 15-second auto-refresh  
✅ Clean, minimal design  
✅ Prevents duplicate event display  

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure MongoDB

Create a `.env` file:
```
MONGO_URI=mongodb://localhost:27017/
```

### 3. Run the Application

```bash
python app.py
```

Visit: http://localhost:5000

## GitHub Webhook Configuration

1. Go to your `action-repo` → Settings → Webhooks
2. Click "Add webhook"
3. Payload URL: `https://your-ngrok-url.ngrok.io/webhook`
4. Content type: `application/json`
5. Select events: **Pushes** and **Pull requests**
6. Save

## Event Formats

- **Push**: `{author} pushed to {branch} on {timestamp}`
- **Pull Request**: `{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp}`
- **Merge**: `{author} merged branch {from_branch} to {to_branch} on {timestamp}`

## API Endpoints

- `POST /webhook` - Receives GitHub events
- `GET /events` - Returns events for UI
- `GET /` - Main dashboard
- `GET /health` - Health check

## Tech Stack

- Python 3.9+
- Flask 3.0.0
- MongoDB
- HTML/CSS/JavaScript

## Author

Created for Techstax SDE-1 Assignment

## Repository

https://github.com/Anshul3977/webhook-repo
