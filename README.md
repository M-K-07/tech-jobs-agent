# AI-Powered Tech Job Fetcher Telegram Bot

## Overview

This project is an automated Telegram notification system that fetches tech job postings from a single specified YouTube channel. It analyzes newly uploaded videos, extracts job-related information using language models, and sends structured job alerts to Telegram users.

The system uses the Supadata API to reliably fetch YouTube video transcripts and is designed to run both locally and via scheduled GitHub Actions for continuous monitoring.

## Key Features

- Monitors one YouTube channel for newly uploaded job-related videos
- Fetches video transcripts using Supadata API
- Extracts job details such as company name, role, location, package, and application link using LLMs
- Sends formatted job notifications to Telegram
- Stores job data in a database to prevent duplicate processing

## Tech Stack

- Python
- YouTube Data API
- Supadata API (for transcript extraction)
- Telegram Bot API (python-telegram-bot)
- LangChain / LLMs for job and link extraction
- PostgreSQL for persistent storage
- GitHub Actions for scheduled execution

## How the Application Works

1. Fetches the latest videos from a configured YouTube channel.
2. Filters videos related to hiring or job postings.
3. Retrieves video transcripts using the Supadata API.
4. Extracts job application links from video descriptions.
5. Uses language models to extract structured job information.
6. Sends formatted job alerts to Telegram.
7. Stores job data only after successful message delivery to avoid duplicates.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/M-K-07/tech-jobs-agent
cd tech-jobs-agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
YOUTUBE_API_KEY=your_youtube_api_key
CHANNEL_ID=target_youtube_channel_id
BOT_TOKEN=your_telegram_bot_token
POSTGRES_URL=your_postgres_connection_url
OPENAI_API_KEY=your_openai_api_key
SUPADATA_API_KEY=your_supadata_api_key
```

### 4. Run the Application Locally

```bash
python main.py
```

### 5. Run Automatically Using GitHub Actions

1. Configure a GitHub Actions workflow to run on a schedule.
2. Add all environment variables as GitHub repository secrets.
3. The workflow will periodically fetch new videos and send updates automatically.