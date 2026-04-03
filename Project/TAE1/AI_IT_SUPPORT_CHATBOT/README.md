# AI-Based Chatbot for IT Support

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A complete, production-style AI chatbot designed to automatically resolve common IT problems for users. This intelligent system simulates a real IT helpdesk chatbot that assists users with troubleshooting technical issues and reduces the workload of human IT support staff.

![IT Support Chatbot](https://via.placeholder.com/800x400/4f46e5/ffffff?text=IT+Support+Chatbot)

## Features

- **Smart Chatbot Interface** - Modern, responsive chat UI with message bubbles, typing indicators, and timestamps
- **Rule-Based AI Engine** - Pattern matching with keyword detection and confidence scoring
- **IT Knowledge Base** - 30+ comprehensive troubleshooting rules covering common IT issues
- **Support Ticket System** - Create and manage support tickets with SQLite database
- **Chat History Logging** - Store conversation logs for analysis and improvement
- **Dialogflow Integration** - Optional Google Dialogflow integration for advanced NLP
- **Dark/Light Theme** - Toggle between themes for user preference
- **Mobile Responsive** - Works seamlessly on desktop, tablet, and mobile devices

## Supported IT Issues

The chatbot can help with:

- Internet & WiFi connectivity problems
- Password resets and account issues
- Printer troubleshooting
- Slow computer performance
- Software installation issues
- Blue screen (BSOD) errors
- Email synchronization problems
- Keyboard and mouse issues
- VPN connection problems
- Virus and malware concerns
- File recovery
- Monitor/display issues
- Audio problems
- Browser issues
- Microsoft Office problems
- USB device detection
- Video conferencing issues
- Disk space management
- Windows updates
- And more...

## Technology Stack

### Backend
- **Python 3.8+**
- **Flask Web Framework** - RESTful API endpoints
- **SQLite** - Database for tickets and chat history

### AI / NLP
- **Pattern Matching** - Keyword and regex-based matching
- **SequenceMatcher** - Similarity scoring for fuzzy matching
- **NLTK** (optional) - Advanced text processing
- **Google Dialogflow** (optional) - Cloud-based NLP

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with CSS variables
- **JavaScript (ES6+)** - Interactive functionality
- **Font Awesome** - Icons
- **Google Fonts** - Inter font family

## Project Structure

```
AI_IT_SUPPORT_CHATBOT/
│
├── app.py                      # Main Flask application
├── chatbot_engine.py           # Rule-based AI engine
├── database.py                 # SQLite database manager
├── rules.json                  # IT knowledge base (30+ rules)
├── requirements.txt            # Python dependencies
│
├── templates/
│   └── index.html              # Main chat interface
│
├── static/
│   ├── css/
│   │   └── style.css           # Stylesheet with themes
│   └── js/
│       └── script.js           # Frontend JavaScript
│
├── logs/
│   └── chatbot.log             # Application logs
│
├── database/
│   └── tickets.db              # SQLite database
│
├── dialogflow/
│   ├── intents.json            # Dialogflow intent definitions
│   └── webhook_handler.py      # Dialogflow webhook handler
│
└── README.md                   # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (optional)

### Step 1: Clone or Download

```bash
# Clone the repository (if using git)
git clone <repository-url>
cd AI_IT_SUPPORT_CHATBOT

# Or download and extract the ZIP file
cd AI_IT_SUPPORT_CHATBOT
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

Open your browser and navigate to: http://localhost:5000

## Usage

### Starting the Chatbot

1. Open your web browser and go to `http://localhost:5000`
2. The chatbot will greet you with a welcome message
3. Type your IT issue in the input box and press Enter
4. The chatbot will analyze your query and provide troubleshooting steps

### Example Conversations

**Internet Issue:**
```
User: My WiFi is not working
Bot: Let's troubleshoot your internet connection:

1. Check if your WiFi is enabled on your device
2. Restart your router/modem (unplug for 30 seconds)
3. Check network cables are securely connected
...
```

**Password Reset:**
```
User: I forgot my password
Bot: For password reset assistance:

1. Visit the self-service password portal: password.company.com
2. Click 'Forgot Password' and enter your email
3. Check your email for reset instructions
...
```

### Creating a Support Ticket

If the chatbot cannot resolve your issue:

1. Click the **ticket icon** in the header
2. Fill in your name, email, and issue description
3. Select the appropriate category and priority
4. Click **Submit Ticket**
5. You will receive a ticket number for reference

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Focus message input |
| `Ctrl/Cmd + N` | Start new chat |
| `Ctrl/Cmd + T` | Open ticket form |
| `Esc` | Close modal |
| `Enter` | Send message |
| `Shift + Enter` | New line in message |

## API Endpoints

### Chat Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message to chatbot |
| `/api/chat/suggestions` | GET | Get chat suggestions |
| `/api/chat/categories` | GET | Get all issue categories |

### Ticket Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tickets` | POST | Create new ticket |
| `/api/tickets` | GET | List all tickets |
| `/api/tickets/<ticket_number>` | GET | Get ticket details |
| `/api/tickets/<ticket_number>/status` | PUT | Update ticket status |
| `/api/tickets/search` | GET | Search tickets |
| `/api/tickets/user/<email>` | GET | Get user's tickets |

### Session Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | POST | Start new session |
| `/api/sessions/<session_id>/end` | POST | End session |
| `/api/sessions/<session_id>/history` | GET | Get chat history |

### Statistics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/statistics` | GET | Get system statistics |

### Dialogflow

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dialogflow/webhook` | POST | Dialogflow webhook |

## Rule-Based AI Engine

The chatbot uses a sophisticated rule-based engine with:

### Pattern Matching Techniques

1. **Exact Match** - Direct string comparison
2. **Substring Match** - Pattern contained in input
3. **Word Boundary Match** - All pattern words present
4. **Similarity Scoring** - SequenceMatcher for fuzzy matching
5. **Keyword Matching** - Keyword presence scoring

### Confidence Scoring

The engine calculates confidence scores (0.0 to 1.0) based on:
- Pattern match quality
- Keyword presence
- Combined scoring algorithm

Threshold: 0.6 (responses below this show fallback message)

### Adding New Rules

Edit `rules.json` to add new troubleshooting rules:

```json
{
  "id": 31,
  "category": "Your Category",
  "patterns": [
    "pattern one",
    "pattern two"
  ],
  "keywords": ["keyword1", "keyword2"],
  "response": "Your troubleshooting response here",
  "escalation_required": false
}
```

## Dialogflow Integration

### Setup

1. Create a Google Cloud project
2. Enable Dialogflow API
3. Create a service account and download credentials
4. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
   ```

### Import Intents

1. Go to Dialogflow Console
2. Select your agent
3. Go to **Settings** > **Export and Import**
4. Import `dialogflow/intents.json`

### Webhook Configuration

1. In Dialogflow Console, go to **Fulfillment**
2. Enable **Webhook**
3. Set URL to: `https://your-domain.com/api/dialogflow/webhook`
4. Save

## Database Schema

### support_tickets Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| ticket_number | TEXT | Unique ticket ID (IT-YYYYMMDD-XXXX) |
| name | TEXT | User's name |
| email | TEXT | User's email |
| issue_description | TEXT | Problem description |
| category | TEXT | Issue category |
| priority | TEXT | Low/Medium/High/Critical |
| status | TEXT | Open/In Progress/Resolved/Closed |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |
| resolved_at | TIMESTAMP | Resolution time |
| assigned_to | TEXT | Assigned technician |
| resolution_notes | TEXT | Resolution details |
| chat_session_id | TEXT | Associated chat session |

### chat_history Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| session_id | TEXT | Chat session ID |
| timestamp | TIMESTAMP | Message time |
| user_message | TEXT | User's message |
| bot_response | TEXT | Bot's response |
| confidence | REAL | Match confidence |
| category | TEXT | Issue category |
| escalation_triggered | BOOLEAN | Escalation flag |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Dialogflow credentials | None |
| `DIALOGFLOW_PROJECT_ID` | Dialogflow project ID | None |
| `FLASK_ENV` | Environment (development/production) | `development` |
| `FLASK_PORT` | Server port | `5000` |

### Creating .env File

```bash
# Create .env file
touch .env

# Add configuration
echo "SECRET_KEY=your-secret-key-here" >> .env
echo "FLASK_ENV=development" >> .env
```

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest
```

### Manual Testing

Test the chatbot with these sample queries:

```
- "Hello"
- "My internet is not working"
- "I forgot my password"
- "Printer is offline"
- "Computer is slow"
- "Blue screen error"
- "Cannot connect to VPN"
- "Email not syncing"
- "Thanks, bye!"
```

## Deployment

### Local Deployment

```bash
python app.py
```

### Production Deployment with Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t it-support-chatbot .
docker run -p 5000:5000 it-support-chatbot
```

## Screenshots

### Chat Interface
![Chat Interface](https://via.placeholder.com/600x400/4f46e5/ffffff?text=Chat+Interface)

### Ticket Form
![Ticket Form](https://via.placeholder.com/600x400/10b981/ffffff?text=Ticket+Form)

### Mobile View
![Mobile View](https://via.placeholder.com/300x600/6366f1/ffffff?text=Mobile+View)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask framework and community
- Font Awesome for icons
- Google Fonts for typography
- Dialogflow for NLP capabilities

## Support

For support, please:
1. Check the troubleshooting section in this README
2. Create an issue in the repository
3. Contact the development team

## Roadmap

- [ ] Machine learning integration for intent classification
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Integration with ticketing systems (Jira, ServiceNow)
- [ ] Admin dashboard with analytics
- [ ] User authentication and profiles
- [ ] File attachment support
- [ ] Real-time notifications

---

**Built with ❤️ for IT Support Teams**

For questions or feedback, please reach out to the development team.
