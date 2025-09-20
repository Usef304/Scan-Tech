# ScanTech - Secure QR Code Scanner

A Flask-based web application for scanning and analyzing QR codes with security features.

## Features

- QR code scanning via camera or file upload
- Security analysis using VirusTotal API
- Dark/light theme support
- Responsive design
- Security threat detection

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure your settings:
   - `SECRET_KEY`: Flask secret key
   - `VT_API_KEY`: VirusTotal API key
   - `REDIS_URL`: Redis connection URL (optional, for caching)
4. Run the application: `python run.py`

## Using Docker

1. Build and run with Docker Compose: `docker-compose up --build`
2. Access the application at http://localhost:5000

## API Key Setup

1. Sign up for a VirusTotal account at https://www.virustotal.com/
2. Get your API key from the account settings
3. Add it to your `.env` file as `VT_API_KEY=your_api_key_here`

## Development

For development with hot reloading:
```bash

FLASK_DEBUG=1 python run.py
