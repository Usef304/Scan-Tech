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
2. Create virtual environment `python -m venv venv`
3. Activate it `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure your settings:
   - `VT_API_KEY`: VirusTotal API key
6. Run the application: `python run.py`

## API Key Setup

1. Sign up for a VirusTotal account at https://www.virustotal.com/
2. Get your API key from the account settings
3. Add it to your `.env` file as `VT_API_KEY=your_api_key_here`

## Development

For development with hot reloading:
```bash

FLASK_DEBUG=1 python run.py


