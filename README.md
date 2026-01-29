# GitHub Webhook Receiver

A Flask-based webhook receiver that captures GitHub events (Push, Pull Request, Merge) and displays them in a real-time dashboard.

## 🚀 Features

- **Real-time Event Monitoring**: Captures GitHub webhook events (Push, Pull Request, Merge)
- **MongoDB Storage**: Stores events with proper schema structure
- **Auto-refresh UI**: Dashboard polls MongoDB every 15 seconds for new events
- **Clean UI Design**: Minimal and professional interface with color-coded event types
- **Proper Date Formatting**: Displays dates in required format (e.g., "29th January 2026 - 10:18 PM UTC")

## 📋 Requirements

- Python 3.9+
- MongoDB (local or Atlas)
- ngrok (for local testing with GitHub webhooks)

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Anshul3977/webhook-repo.git
cd webhook-repo
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file:

```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=github_events
```

### 5. Start MongoDB

Make sure MongoDB is running locally:

```bash
# Windows
net start MongoDB

# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongodb
```

## 🏃 Running the Application

### 1. Start the Flask application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### 2. Expose with ngrok (for GitHub webhooks)

In a separate terminal:

```bash
ngrok http 5000
```

Copy the ngrok HTTPS URL (e.g., `https://xxxx.ngrok-free.app`)

### 3. Configure GitHub Webhook

1. Go to your `action-repo` repository settings
2. Navigate to **Settings → Webhooks → Add webhook**
3. Configure:
   - **Payload URL**: `https://xxxx.ngrok-free.app/webhook`
   - **Content type**: `application/json`
   - **Events**: Select "Pushes" and "Pull requests"
4. Click **Add webhook**

## 📊 MongoDB Schema

Events are stored with the following schema:

```json
{
  "author": "string",
  "action": "push | pull_request | merge",
  "to_branch": "string",
  "from_branch": "string | null",
  "timestamp": "ISO 8601 date string",
  "request_id": "unique identifier"
}
```

## 🎯 Event Formats

### Push Event
```
Anshul3977 pushed to main on 29th January 2026 - 10:18 PM UTC
```

### Pull Request Event
```
Anshul3977 submitted a pull request from feature-test to main on 29th January 2026 - 10:19 PM UTC
```

### Merge Event (Brownie Points!)
```
Anshul3977 merged branch feature-test to main on 29th January 2026 - 10:20 PM UTC
```

## 🔗 API Endpoints

- **GET /** - Main dashboard UI
- **POST /webhook** - GitHub webhook receiver endpoint
- **GET /events** - API endpoint that returns formatted events (with optional `last_timestamp` parameter)
- **GET /health** - Health check endpoint

## 🧪 Testing

### Test with curl (local testing)

```bash
# Test push event
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d @test_push_payload.json
```

### Test with actual GitHub events

1. Make a commit to `action-repo`
2. Create a pull request
3. Merge the pull request
4. Check the dashboard at `http://localhost:5000`

## 📁 Project Structure

```
webhook-repo/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .gitignore             # Git ignore file
├── templates/
│   └── index.html         # Dashboard UI
├── Procfile               # For Heroku deployment
└── README.md              # This file
```

## 🎨 UI Features

- **Live Status Indicator**: Shows connection status
- **Auto-refresh**: Polls every 15 seconds
- **Event Badges**: Color-coded (Green for Push, Yellow for Pull Request, Purple for Merge)
- **Responsive Design**: Works on all screen sizes
- **No Duplicate Events**: Smart filtering prevents showing the same event twice

## 🔧 Code Quality Features

- ✅ Proper indentation and comments
- ✅ Clear variable naming
- ✅ Error handling for webhook parsing
- ✅ Date format handling with ordinal suffixes (1st, 2nd, 3rd, etc.)
- ✅ Efficient MongoDB queries with indexing
- ✅ No duplicate event display logic

## 🚀 Deployment Options

### Heroku Deployment

```bash
heroku create your-app-name
heroku addons:create mongolab:sandbox
git push heroku main
```

### Railway/Render

Upload the code and set environment variables in the dashboard.

## 👨‍💻 Author

**Anshul Palarpwar**
- GitHub: [@Anshul3977](https://github.com/Anshul3977)

## 📝 Assignment Details

This project was created as part of the Techstax SDE-1 Python Developer assessment task.

**Repositories:**
- **action-repo**: https://github.com/Anshul3977/action-repo (Dummy repo for triggering webhooks)
- **webhook-repo**: https://github.com/Anshul3977/webhook-repo (This repository)

**Assignment Deadline**: 30 Jan, 2026 23:59:59

## 📄 License

This project is created for educational and assessment purposes.
