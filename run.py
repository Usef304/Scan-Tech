from app import create_app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    logger.info("Starting ScanTech application")
    app.run(debug=True, host='0.0.0.0')