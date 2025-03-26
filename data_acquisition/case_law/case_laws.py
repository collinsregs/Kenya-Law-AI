import logging
import os
import json
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from neo4j import GraphDatabase
from courts_and_tribunals.court_cases import scrape_court_data

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
BASE_URL = os.getenv("BASE_URL")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def initialize_driver():
    """Initialize Chrome WebDriver with stability options"""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def get_court_classifications(driver):
    """Get top-level court classifications"""
    driver.get(BASE_URL)
    classifications = []
    
    try:
        # Wait for dropdown to be present and interactable
        dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dropdown-menu'))
        )
        
        # Find all dropdown items
        items = dropdown.find_elements(By.CLASS_NAME, 'dropdown-item')
        print('Found menu items:', len(items))
        
        for item in items:
            try:
                link = item.find_element(By.TAG_NAME, 'a')
                classification = link.get_attribute('innerText').strip()
                href = link.get_attribute('href')
                
                if classification and href:
                    classifications.append({
                        'classification': classification,
                        'link': href
                    })
            except Exception as item_error:
                logger.warning(f"Error processing classification item: {item_error}")
        
        logger.info(f"Found {len(classifications)} classifications")
        return classifications
    except Exception as e:
        logger.error(f"Error getting classifications: {str(e)}")
        return []

def get_courts(driver):
    """Scrape courts from current page"""
    courts = []
    
    try:
        # Wait for unordered lists
        unordered_lists = WebDriverWait(driver, 20).until(
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
                            'link': court_link
                        })
        
        logger.info(f"Found {len(courts)} courts")
        return courts
    except Exception as e:
        logger.error(f"Error getting courts: {str(e)}")
        return []

def get_court_stations(driver, court_link):
    """Scrape court stations by navigating to the court's specific page"""
    court_stations = []
    
    try:
        # Navigate to the court's specific page
        driver.get(court_link)
        
        # Wait for page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # Look for unordered lists with stations
        unordered_lists = driver.find_elements(By.CSS_SELECTOR, "ul.list-unstyled")
        
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
                            'link': station_link or ''
                        })
        
        logger.info(f"Found {len(court_stations)} court stations for {driver.title}")
        return court_stations
    except Exception as e:
        logger.error(f"Error getting court stations for {court_link}: {str(e)}")
        return []

def getElections(driver):
    Elections =[]
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".pt-4.pb-5"))
        )
        items = element.find_elements(By.TAG_NAME,'li')
        for item in items:
            anchor = item.find_elements(By.TAG_NAME, 'a')
            election_year=anchor.text.strip()
            link= anchor.get_attribute('href')
            if election_year:
                Elections.append({
                    'name':election_year,
                    'link':link
                })
        return Elections
    except Exception as e:
        logger.error(f"Error getting court stations elections: {str(e)}")

    


def insert_data(data):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        case_law_query="""
        CREATE (c:Segment {name: $name})
        RETURN elementId(c) as node_id
        """
        law_result = session.run(
                case_law_query,
                name='Case Law'
            )
        law_id = law_result.single()['node_id']
        length = len(data)
        
        for index, classification in enumerate(data, start=1):
            
            # Create Classification node
            classification_query = """
            MATCH (S:Segment) WHERE elementId(S) = $law_id
            CREATE (c:Classification {name: $name})
            CREATE (c)-[:BELONGS_TO]->(S)
            RETURN elementId(c) as classification_id
            """
            classification_result = session.run(
                classification_query,
                name=classification['classification'],
                law_id=law_id
            )
            classification_id = classification_result.single()['classification_id']
            
            for court in classification['courts']:
                # Create Court node and relationship to Classification
                court_query = """
                MATCH (cl:Classification) WHERE elementId(cl) = $classification_id
                CREATE (co:Court {name: $name})
                CREATE (co)-[:BELONGS_TO]->(cl)
                RETURN elementId(co) as court_id
                """
                court_result = session.run(
                    court_query,
                    classification_id=classification_id,
                    name=court['name']
                )
                court_id = court_result.single()['court_id']
                if(len(court['stations']==0)):
                    scrape_court_data(court_id,court['link'])
                else:
                
                    for station in court['stations']:
                        station_query = """
                        MATCH (co:Court) WHERE elementId(co) = $court_id
                        CREATE (s:Station {name: $name, link: $link})
                        CREATE (s)-[:PART_OF]->(co)
                        RETURN elementId(s) as station_id
                        """
                        station_result =session.run(
                            station_query,
                            court_id=court_id,
                            name=station['name'],
                            link=station.get('link', '')  # Using get() in case link is missing
                        )
                        station_id=station_result.single()['station_id']
                        scrape_court_data(station_id,station['link'])
    
    driver.close()
def main():
    driver = initialize_driver()
    full_results = []
    
    try:
        # Get top-level classifications
        classifications = get_court_classifications(driver)
        total_classifications = len(classifications)
        
        # Process each classification
        for index, classification in enumerate(classifications, start=1):
            try:
                # Open classification link
                driver.get(classification['link'])
                is_last_classification = (index == total_classifications)
                
                if(not is_last_classification):
                # Get courts for this classification
                    courts = get_courts(driver)
                
                # Process each court to get its stations
                    processed_courts = []
                    for court in courts:
                        try:
                        # Get court stations by navigating to court's link
                            court_stations = get_court_stations(driver, court['link'])
                        
                        # Add stations to court details
                            court_details = court.copy()
                            court_details['stations'] = court_stations
                            processed_courts.append(court_details)
                        except Exception as court_error:
                            logger.error(f"Error processing court {court['name']}: {court_error}")
                
                # Prepare classification result
                    classification_result = {
                        'classification': classification['classification'],
                        'courts': processed_courts
                    }
                
                    full_results.append(classification_result)
                
                else:
                    elections = getElections(driver)
                    classification_result = {
                        'classification': classification['classification'],
                        'courts': elections
                    }
                    print('handling elections')
                
                # Detailed logging
                logger.info(f"Processed Classification: {classification['classification']}")
                
            except Exception as classification_error:
                logger.error(f"Error processing classification {classification['classification']}: {classification_error}")
       
       
    except Exception as e:
        logger.error(f"Main execution error: {str(e)}")
    finally:
        driver.quit()
        insert_data(full_results) 

if __name__ == "__main__":
    main()