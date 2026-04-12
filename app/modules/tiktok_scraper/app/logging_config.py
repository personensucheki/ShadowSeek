import logging

def setup_logger():
    # Only return a named logger, do not configure handlers or basicConfig
    return logging.getLogger("scraper")
