import logging
import time
import random
import json
import csv
import re
from typing import List, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException, 
    NoSuchElementException, 
    TimeoutException, 
    SessionNotCreatedException
)
from webdriver_manager.chrome import ChromeDriverManager
from getpass import getpass


class AmazonBestSellersScraper:
    def __init__(self):
        # Logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("amazon_scraper.log", encoding="utf-8"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Chrome options for robust WebDriver
        self.chrome_options = Options()
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--remote-debugging-port=9222")
        self.chrome_options.add_argument("--disable-software-rasterizer")
        
        # User agent to reduce detection
        self.chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Scraping configuration
        self.base_url = "https://www.amazon.in"
        self.max_products_per_category = 100  
        #self.min_discount_threshold = 50  
        
        # Data storage
        self.scraped_data = []
        
        # WebDriver and login credentials
        self.driver = None
        self.username = None
        self.password = None

    def create_webdriver(self):
        try:
            self.logger.info("Creating WebDriver")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            driver.maximize_window()
            
            return driver
        
        except Exception as e:
            self.logger.critical(f"WebDriver creation failed: {e}")
            raise

    def login(self):
        """
        Enhanced login method with comprehensive error handling
        """
        max_login_attempts = 3
        for attempt in range(max_login_attempts):
            try:
                # Prompt for credentials
                self.username = input("Enter your Amazon username: ")
                self.password = getpass("Enter your Amazon password: ")
                
                # Create WebDriver
                self.driver = self.create_webdriver()
                
                # Navigate to Amazon homepage
                self.driver.get(f"{self.base_url}/")
                
                # Find and click Sign In button
                signin_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="nav-link-accountList"]/span'))
                )
                signin_button.click()
                
                # Enter username
                username_textbox = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "ap_email"))
                )
                username_textbox.clear()
                username_textbox.send_keys(self.username)
                
                # Click Continue
                continue_button = self.driver.find_element(By.ID, "continue")
                continue_button.click()
                
                # Enter password
                password_textbox = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "ap_password"))
                )
                password_textbox.clear()
                password_textbox.send_keys(self.password)
                
                # Submit Sign In
                signin_button = self.driver.find_element(By.ID, "signInSubmit")
                signin_button.click()
                
                # Wait for login verification
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.ID, "nav-link-accountList"))
                )
                
                self.logger.info("Login successful")
                return True
            
            except Exception as e:
                self.logger.error(f"Login attempt {attempt + 1} failed: {e}")
                
                # Close existing driver
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                
                time.sleep(2)
        
        self.logger.critical("Login failed after multiple attempts")
        return False

    def scrape_category(self, category_url: str, category_name: str):
        """
        Comprehensive category product scraping
        """
        try:
            self.driver.get(category_url)
            
            # Wait for product grid
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'zg-grid-general')]"))
            )
            
            # Find product elements
            products = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'zg-grid-general')]")
            
            # Limit to max products
            products = products[:self.max_products_per_category]
            
            # Extract product details
            for product in products:
                try:
                    # Open product in new tab
                    product_link = product.find_element(By.XPATH, ".//a[contains(@class, 'a-link-normal')]")
                    product_url = product_link.get_attribute('href')
                    
                    # Open new tab and switch
                    self.driver.execute_script(f"window.open('{product_url}', '_blank');")
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    
                    # Wait for product page to load
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.ID, "productTitle"))
                    )
                    
                    # Extract detailed product information
                    details = self.get_product_details(category_name)
                    
                    if details and 'sale_discount' in details:
                        try:
                            discount_value = abs(float(details['sale_discount'].strip('%')))
                            if discount_value > 50:
                                self.scraped_data.append(details)
                        except ValueError:
                            self.logger.warning(f"Could not parse discount: {details['sale_discount']}")
                    
                    # Close tab and switch back
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                
                except Exception as product_error:
                    self.logger.error(f"Error processing product in {category_name}: {product_error}")
                
                # Random delay to avoid detection
                time.sleep(random.uniform(1, 3))
        
        except Exception as e:
            self.logger.error(f"Category Scraping Error for {category_name}: {e}")

    def get_product_details(self, category: str) -> Dict[str, Any]:
        """
        Extract comprehensive product details
        """
        try:
            product_details = {
                "category": category,
                "name": self.safe_extract_text_by_id("productTitle"),
                "price": self.extract_price(),
                "sale_discount": self.extract_discount(),
                "rating": self.safe_extract_text_by_xpath("//*[@id='acrPopover']/span[1]/a/span"),
                "Best_seller_rating": self.safe_extract_text_by_xpath("//*[@id='productDetails_detailBullets_sections1']/tbody/tr[5]/td/span/span[1]"),
                "ship_from": self.safe_extract_text_by_xpath("//*[@id='tabular-buybox']/div[1]/div[4]/div/span"),
                "sold_by": self.safe_extract_text_by_xpath("//a[@id='sellerProfileTriggerId']"),
                "product_description": self.extract_product_description(),
                "number_bought": self.extract_units_sold(),
                "images": self.extract_product_images(),
                #"product_url": self.driver.current_url
            }
            
            return product_details
            
        except Exception as e:
            self.logger.error(f"Product Detail Extraction Error: {e}")
        
        return {}

    def safe_extract_text_by_id(self, element_id: str) -> str:
        """
        Safely extract text by element ID
        """
        try:
            return self.driver.find_element(By.ID, element_id).text.strip()
        except NoSuchElementException:
            return ""

    def safe_extract_text_by_xpath(self, xpath: str) -> str:
        """
        Safely extract text by XPath
        """
        try:
            return self.driver.find_element(By.XPATH, xpath).text.strip()
        except NoSuchElementException:
            return ""

    def extract_price(self) -> str:
        """
        Extract product price
        """
        try:
            # Multiple possible price locators
            price_locators = [
                "//span[@class='a-price-whole']",
                "//span[@class='a-price']",
                "//div[@class='a-section a-spacing-none aok-align-center']//span[@class='a-price-fraction']"
            ]
            
            for locator in price_locators:
                try:
                    price = self.driver.find_element(By.XPATH, locator).text
                    return price
                except:
                    continue
            
            return ""
        
        except Exception as e:
            self.logger.error(f"Price extraction error: {e}")
            return ""

    def extract_discount(self) -> str:
        """
        Extract product discount percentage
        """
        try:
            discount_locators = [
                "//div[@id='corePriceDisplay_desktop_feature_div']//span[@class='a-size-large a-color-price']",
                "//span[contains(@class, 'savingsPercentage')]"
            ]
            
            for locator in discount_locators:
                try:
                    discount = self.driver.find_element(By.XPATH, locator).text
                    return discount
                except:
                    continue
            
            return ""
        
        except Exception as e:
            self.logger.error(f"Discount extraction error: {e}")
            return ""

    def extract_product_description(self) -> str:
        """
        Extract product description
        """
        try:
            description_locators = [
                "//div[@id='productDescription']//p",
                "//div[@id='feature-bullets']//ul",
                "//div[@id='productDescription_feature_div']//div[@class='a-expander-content']"
            ]
            
            for locator in description_locators:
                try:
                    description = self.driver.find_element(By.XPATH, locator).text
                    return description
                except:
                    continue
            
            return ""
        
        except Exception as e:
            self.logger.error(f"Description extraction error: {e}")
            return ""

    def extract_units_sold(self) -> str:
        """
        Extract number of units sold recently
        """
        try:
            units_locators = [
                "//*[@id='social-proofing-faceout-title-tk_bought']/span[1]"
            ]
            
            for locator in units_locators:
                try:
                    units = self.driver.find_element(By.XPATH, locator).text
                    return units
                except:
                    continue
            
            return ""
        
        except Exception as e:
            self.logger.error(f"Units sold extraction error: {e}")
            return ""

    def extract_product_images(self) -> List[str]:
        """
        Extract product image URLs
        """
        try:
            image_locators = [
                "//div[@id='imageBlock']//img",
                "//ul[contains(@class, 'a-unordered-list a-vertical a-spacing-none')]//img",
                "//div[contains(@class, 'image-container')]//img"
            ]
            
            images = []
            for locator in image_locators:
                try:
                    img_elements = self.driver.find_elements(By.XPATH, locator)
                    image_urls = [img.get_attribute('src') for img in img_elements if img.get_attribute('src')]
                    images.extend(image_urls)
                    
                    if images:
                        break
                except:
                    continue
            
            return list(set(images))  # Remove duplicates
        
        except Exception as e:
            self.logger.error(f"Image extraction error: {e}")
            return []

    def run_scraper(self, categories):
        """
        Run scraper across multiple categories
        """
        try:
            # Login first
            if not self.login():
                self.logger.error("Login failed. Exiting.")
                return
            
            # Scrape each category
            for category in categories:
                try:
                    self.scrape_category(category['url'], category['name'])
                except Exception as category_error:
                    self.logger.error(f"Error in category {category['name']}: {category_error}")
                
                # Brief pause between categories
                time.sleep(random.uniform(2, 5))
        
        except Exception as e:
            self.logger.error(f"Overall Scraping Error: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()

    def save_data(self, file_format: str = 'json'):
        """
        Save scraped data
        """
        try:
            timestamp = int(time.time())
            filename = f"amazon_best_sellers_{timestamp}"
            
            if file_format.lower() == 'json':
                with open(f"{filename}.json", 'w', encoding='utf-8') as f:
                    json.dump(self.scraped_data, f, ensure_ascii=False, indent=4)
            else:
                with open(f"{filename}.csv", 'w', newline='', encoding='utf-8') as f:
                    if self.scraped_data:
                        writer = csv.DictWriter(f, fieldnames=list(self.scraped_data[0].keys()))
                        writer.writeheader()
                        writer.writerows(self.scraped_data)
            
            self.logger.info(f"Data saved successfully to {filename}")
        
        except Exception as e:
            self.logger.error(f"Data saving error: {e}")



def main():
    # Categories to scrape
    CATEGORIES = [
        {
            'url': 'https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0',
            'name': 'Kitchen'
        },
        {
            'url': 'https://www.amazon.in/gp/bestsellers/books/ref=zg_bs_nav_books_0',
            'name': 'Books'
        },
        {
            'url': 'https://www.amazon.in/gp/bestsellers/beauty/ref=zg_bs_nav_beauty_0',
            'name': 'Beauty'
        },
        {
            'url': 'https://www.amazon.in/gp/bestsellers/automotive/ref=zg_bs_nav_automotive_0',
            'name': 'Car & Motorbike'
        },
        {
            'url': 'https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0',
            'name': 'Electronics'
        },
        {
            'url': 'https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0',
            'name': 'Computers & Accesories'
        },
        {
            'url': 'https://www.amazon.in/gp/bestsellers/watches/ref=zg_bs_nav_watches_0',
            'name': 'Watches'
        },
        {
            'url': 'https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0',
            'name': 'Shoes & Handbags'
        },
        {
            'url': 'https://www.amazon.in/gp/bestsellers/sports/ref=zg_bs_nav_sports_0',
            'name': 'Sports'
        },
        {
            'url': 'https://www.amazon.in/gp/bestsellers/hpc/ref=zg_bs_nav_hpc_0',
            'name': 'Health & Personal care'
        }
        
    ]

    # Initialize and run scraper
    scraper = AmazonBestSellersScraper()
    scraper.run_scraper(CATEGORIES)
    scraper.save_data(file_format='json')

if __name__ == "__main__":
    main()






