# Amazon-BestSellers-Scraper

## Overview

This Python script is a web scraping tool designed to extract product information from Amazon India's Best Sellers pages across multiple categories. The scraper uses Selenium WebDriver to navigate through Amazon, log in, and collect detailed product information.

## Features

- Scrapes Best Sellers products from multiple Amazon categories
- Extracts comprehensive product details including:
  - Product name
  - Price
  - Discount percentage
  - Rating
  - Seller information
  - Product description
  - Number of units sold
  - Product images
- Supports saving data in JSON or CSV formats
- Configurable maximum number of products per category
- Robust error handling and logging
- Randomized delays to avoid detection

## Prerequisites

### Software Requirements
- Python 3.7+
- Google Chrome browser
- ChromeDriver (automatically managed via webdriver_manager)

### Python Dependencies
- selenium
- webdriver_manager
- logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/akiroh0128/Amazon-BestSellers-Scraper.git
cd Amazon-BestSellers-Scraper
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install required packages:
```bash
pip install selenium webdriver_manager
```

## Configuration

### Categories
You can modify the `CATEGORIES` list in the `main()` function to include or exclude specific Amazon categories. Each category requires:
- `url`: Direct link to the Amazon Best Sellers page
- `name`: Category name for identification

### Scraping Parameters
Adjust these parameters in the `AmazonBestSellersScraper` class:
- `max_products_per_category`: Limit the number of products scraped per category
- `base_url`: Change the Amazon domain if scraping from a different country

## Usage

1. Run the script:
```bash
python AmazonBestSellersScraper.py
```

2. When prompted, enter your Amazon login credentials:
- Username (email)
- Password (will be hidden during input)

3. The script will:
- Log in to Amazon
- Navigate through specified categories
- Scrape product details
- Save results in a timestamped JSON or CSV file

## Output

Scraped data will be saved in the format:
- `amazon_best_sellers_{timestamp}.json`

## Logging

- Detailed logs are saved in `amazon_scraper.log`
- Logs include information about scraping process, errors, and system events

## Troubleshooting

- Ensure Chrome is up-to-date
- Check internet connection
- Verify Amazon login credentials
- Review `amazon_scraper.log` for specific error details
