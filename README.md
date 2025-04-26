# NJMVC Appointment Notifier Discord Bot

A Python-based Discord bot that monitors the New Jersey Motor Vehicle Commission (NJMVC) appointment portal and notifies users via Discord when new appointment slots become available.

This tool is particularly useful for individuals seeking timely updates on appointment availability.

---

## Features

- **Automated Monitoring**: Periodically checks the NJMVC appointment portal for new openings.
- **Real-Time Notifications**: Sends alerts to a specified Discord channel when new appointments are detected.
- **Configurable Settings**: Easily adjust monitoring intervals and Discord channel configurations.

---

## Prerequisites

- Python 3.7 or higher
- Discord account and bot token
- Access to the NJMVC appointment portal

---

## Installation

1. **Clone the Repository**

```bash
git clone https://github.com/dej0e/NJMVC-Appointment-Notifier-Discord-Bot.git
cd NJMVC-Appointment-Notifier-Discord-Bot
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure the Bot**

Create a `config.py` file in the root directory with the following content:

```python
DISCORD_TOKEN = 'your_discord_bot_token'
CHANNEL_ID = your_discord_channel_id  # Replace with your channel ID
CHECK_INTERVAL = 300  # Time in seconds between checks (e.g., 300 seconds = 5 minutes)
```

- Replace `'your_discord_bot_token'` with your actual Discord bot token.
- Replace `your_discord_channel_id` with the ID of the Discord channel where you want to receive notifications.
- Adjust `CHECK_INTERVAL` as needed to set how frequently the bot checks for new appointments.

4. **Run the Bot**

```bash
python bot.py
```

---

## Usage

Once the bot is running, it will periodically check the NJMVC appointment portal for new openings. When a new appointment slot becomes available, the bot will send a notification message to the specified Discord channel.

---

## Files Overview

- `bot.py`: Main script that initializes the Discord bot and handles event loops.
- `mvc_checker.py`: Contains the logic for checking the NJMVC appointment portal.
- `config.py`: Holds configuration variables such as the Discord token, channel ID, and check interval.
- `requirements.txt`: Lists all Python dependencies required to run the bot.

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This bot is intended for personal use to monitor NJMVC appointment availability. It is not affiliated with or endorsed by the New Jersey Motor Vehicle Commission. Please use responsibly and ensure compliance with NJMVC's terms of service.

