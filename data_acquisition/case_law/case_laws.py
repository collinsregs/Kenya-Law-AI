import logging
import os
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kenya_law_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
BASE_URL = os.getenv("BASE_URL")

def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)

def get_court_classifications(driver):
    """Get top-level court classifications using the main browser tab"""
    driver.get(BASE_URL)
    classifications = []
    
    try:
        dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dropdown-menu'))
        )
        
        items = dropdown.find_elements(By.CLASS_NAME, 'dropdown-item')
        for item in items:
            link = item.find_element(By.TAG_NAME, 'a')
            classifications.append({
                'classification': link.get_attribute('innerText').strip(),
                'link': link.get_attribute('href')
            })
            
        return classifications
    except Exception as e:
        logger.error(f"Error getting classifications: {str(e)}")
        return []

def scrape_in_new_tab(driver, url, scrape_function):
    """Open URL in new tab, scrape using provided function, then close tab"""
    # Open new tab
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)
    
    try:
        result = scrape_function(driver)
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        result = None
    finally:
        # Close tab and return to main window
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    
    return result

def get_courts(driver):
    """Scrape courts from current page in new tab"""
    courts = []
    
    try:
        unordered_lists = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.list-unstyled"))
        )
        
        for ul in unordered_lists:
            list_items = ul.find_elements(By.TAG_NAME, 'li')
            for li in list_items:
                anchors = li.find_elements(By.TAG_NAME, 'a')
                for anchor in anchors:
                    court_name = anchor.text.strip()
                    court_link = anchor.get_attribute('href')
                    if court_name and court_link:
                        courts.append({
                            'name': court_name,
                            'link': court_link,
                            'Court Stations': scrape_in_new_tab(driver, court_link, get_court_stations)
                        })
        
        logger.info(f"Found {len(courts)} courts")
        return courts
    except Exception as e:
        logger.error(f"Error getting courts: {str(e)}",)
        return []

def get_court_stations(driver):
    """Scrape court stations from current page in new tab"""
    court_stations = []
    
    try:
        unordered_lists = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.list-unstyled"))
        )
        
        for ul in unordered_lists:
            list_items = ul.find_elements(By.TAG_NAME, 'li')
            for li in list_items:
                anchors = li.find_elements(By.TAG_NAME, 'a')
                for anchor in anchors:
                    station_name = anchor.text.strip()
                    station_link = anchor.get_attribute('href')
                    if station_name:
                        court_stations.append({
                            'name': station_name,
                            'link': station_link
                        })
        
        logger.info(f"Found {len(court_stations)} court stations")
        return court_stations
    except Exception as e:
        logger.error(f"Error getting court stations: {str(e)}")
        return []

def main():
    driver = initialize_driver()
    try:
        # Get top-level classifications in main tab
        classifications = get_court_classifications(driver)
        
        # Process each classification in new tabs
        for classification in classifications:
            classification['stations'] = scrape_in_new_tab(
                driver, 
                classification['link'], 
                get_courts
            )
        
        # Print results
        for item in classifications:
            print(f"Classification: {item['classification']}")
            for court in item.get('stations', []):
                print(f"  Court: {court['name']}")
                for station in court.get('Court Stations', []):
                    print(f"    Station: {station['name']}")
                    
    except Exception as e:
        logger.error(f"Main execution error: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()