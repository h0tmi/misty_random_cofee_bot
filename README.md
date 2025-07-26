# 🤖 Random Coffee Bot

A Telegram bot that helps people connect and socialize over coffee by automatically matching participants each week.

## ✨ Features

### 👤 Profile Management
- **User Profiles**: Create and manage personal profiles with bio and interests
- **Participation Control**: Set participation preferences (always/never/ask each time)
- **Profile Editing**: Update information anytime through the bot interface

### 🔄 Automated Matching
- **Weekly Schedule**: Automatic matching every Monday at 10:00 AM
- **Smart Algorithm**: Avoids recent matches to ensure variety
- **Two-Phase Process**:
  - Phase 1 (Monday): Collect participants and confirmations
  - Phase 2 (Tuesday): Create and notify about matches

### 💬 Interactive Features
- **Meeting Notifications**: Get matched with someone new each week
- **Feedback System**: Rate meetings and provide feedback
- **Participation Confirmation**: Optional weekly participation requests

### 🔧 Admin Panel
- **User Management**: View and manage all registered users
- **Manual Matching**: Force start matching sessions when needed
- **Statistics**: Monitor bot usage and matching success

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Your Telegram User ID (for admin access)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd misty_random_coffee_bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the bot**

   Set your bot token as an environment variable:
   ```bash
   export BOT_TOKEN="your_bot_token_here"
   ```

   Or edit `config.py` to set your token and admin ID:
   ```python
   def load_config() -> Config:
       return Config(
           bot_token="YOUR_BOT_TOKEN_HERE",
           admin_ids=[YOUR_TELEGRAM_USER_ID]  # Replace with your Telegram ID
       )
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## 📋 How It Works

### For Users

1. **Start** - Send `/start` to the bot
2. **Create Profile** - Fill in your bio and interests
3. **Set Participation** - Choose your participation preference:
   - ✅ **Always participate** - Automatic weekly participation
   - ❓ **Ask each time** - Bot asks before each matching
   - ❌ **Don't participate** - Pause participation

4. **Get Matched** - Receive weekly matches with interesting people
5. **Meet & Feedback** - Meet your match and provide feedback

### Weekly Schedule

- **Monday 10:00 AM**: Matching session starts, participation requests sent
- **Tuesday 10:00 AM**: Pairs created from confirmed participants
- **Throughout the week**: Users meet and provide feedback

### For Admins

Access the admin panel with `/admin` to:
- View all registered users
- Manually start matching sessions
- Force complete matching sessions
- Monitor bot statistics

## 🛠 Development

### Project Structure

```
misty_random_coffee_bot/
├── bot.py                 # Main bot entry point
├── config.py             # Configuration management
├── database.py           # Database operations
├── models.py            # Data models
├── matching.py          # Matching algorithm
├── scheduler.py         # Automated scheduling
├── keyboards.py         # Telegram keyboards
├── handlers/            # Command handlers
│   ├── admin.py        # Admin functionality
│   ├── profile.py      # Profile management
│   ├── participation.py # Participation control
│   ├── matching.py     # Match handling
│   └── feedback.py     # Feedback system
└── tests/              # Test suite
    ├── test_database.py
    ├── test_matching.py
    └── test_integration.py
```

### Running Tests

Install test dependencies:
```bash
pip install -r tests/test_requirements.txt
```

Run all tests:
```bash
cd tests && make test
```

Run specific test suites:
```bash
cd tests && make test-matching      # Matching algorithm tests
cd tests && make test-database      # Database tests
cd tests && make test-integration   # Integration tests
```

Run tests with coverage:
```bash
cd tests && make test-coverage
```

### Key Components

#### Database Schema
- **users**: User profiles and participation settings
- **matches**: Match history and feedback
- **pending_matches**: Participation confirmations
- **matching_sessions**: Session tracking

#### Matching Algorithm
- Prioritizes users who haven't met recently
- Handles odd numbers of participants
- Tracks match history to avoid repeats
- Supports manual admin intervention

#### Scheduler
- Uses APScheduler for automated timing
- Configurable cron-based scheduling
- Graceful error handling and logging

## 🤖 Bot Commands

### User Commands
- `/start` - Start the bot and create profile
- `/help` - Show help information
- `/menu` - Access main menu

### Admin Commands
- `/admin` - Access admin panel (admins only)

### Interactive Menus
- **Profile Menu**: Manage your profile and participation
- **Admin Panel**: User management and manual controls
- **Feedback Buttons**: Rate meetings and provide feedback

## 📊 Participation Options

### ✅ Always Participate
- Automatically included in every weekly matching
- No confirmation required
- Can opt-out anytime through profile settings

### ❓ Ask Each Time
- Receive participation request each Monday
- Must confirm to be included in matching
- Default setting for new users

### ❌ Don't Participate
- Excluded from all matching
- Profile remains but inactive
- Can re-enable anytime

## 🔧 Configuration

### Environment Variables
- `BOT_TOKEN` - Your Telegram bot token

### Config Options (config.py)
- `bot_token` - Telegram bot token
- `database_path` - SQLite database file path (default: "bot.db")
- `admin_ids` - List of admin Telegram user IDs

### Scheduling
Default schedule (configurable in `scheduler.py`):
- **Monday 10:00**: Start weekly matching
- **Tuesday 10:00**: Create confirmed matches

## 🗂 Database

The bot uses SQLite with the following tables:
- `users` - User profiles and settings
- `matches` - Match history and feedback
- `pending_matches` - Participation confirmations
- `matching_sessions` - Session tracking

Database is automatically created on first run.

## 🧪 Testing

Comprehensive test suite covering:
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflows
- **Matching Tests**: Algorithm validation
- **Database Tests**: Data persistence and retrieval

### Test Categories
- `pytest tests/` - Run all tests
- `pytest -m integration` - Integration tests only
- `pytest -m "not stress"` - Skip stress tests
- `pytest tests/test_matching.py` - Matching tests only

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check bot token is correct
   - Verify bot is running with `python bot.py`
   - Check logs for error messages

2. **Database errors**
   - Ensure write permissions in bot directory
   - Database file will be created automatically

3. **Scheduling not working**
   - Verify system timezone
   - Check APScheduler logs
   - Ensure bot process stays running

4. **Admin commands not working**
   - Verify your Telegram user ID in `config.py`
   - Use `/admin` instead of legacy commands

### Logging
The bot logs to console with INFO level. For debugging, modify the logging level in `bot.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is open source. Please check the license file for details.

## 🔗 Related

- [aiogram Documentation](https://docs.aiogram.dev/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)