from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging

# Load environment variables from .env file
load_dotenv()
logger = logging.getLogger(__name__)

# Get the BASE_URL from the environment variables
BASE_URL = os.getenv("BASE_URL")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

global_section_index = 1
supremeCourtUrl = "/judgments/KESC/SCK/?page=";

def getCaseLinks(driver,url):
    index = 1
    links =[]
    while True:
        driver.get(f"{url}{index}")
        # print(f"{url}{index}")
        try:
            error404 = driver.find_element(By.CLASS_NAME, "mb-4").text 
            
            if error404 !=  "Not found (Error 404)":
                index += 1
                rows =driver.find_elements(By.CLASS_NAME, "cell-title")
                
                for row in rows:
                    try:
                        a=row.find_element(By.TAG_NAME,"a")
                        link=a.get_attribute("href")
                        links.append(link)
                    except:
                        pass
            else:
                print("error",error404)
                break
        except Exception as e:
            print("exception", e)
    return links

def getCaseContent(driver,link):
    cases={}
    driver.get(link)
    title = driver.find_element(By.TAG_NAME,"h1").text
    dl=driver.find_elements(By.TAG_NAME,"dl")
    # content = driver.find_element(By.CLASS_NAME,"akn-judgment")
    for dl_item in dl:
        pairs=get_dl_key_value_pairs(dl_item)
        # print("content",pairs)
    return

def get_dl_key_value_pairs(dl_element):
    pairs = {}
    dt_elements = dl_element.find_elements(By.TAG_NAME, "dt")
    for dt in dt_elements:
        try:
            dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
            key = dt.text.strip()
            value = dd.text.strip()
            pairs[key] = value
        except Exception as e:
            print(f"Could not find a subsequent dt for dd with text '{dd.text}': {e}")
    return pairs

def getCase(content):
    case={}
    header=content.find_element(By.ID,"header")
    headerContent=getHeader(header)
    body = content.find_element(By.ID,"judgmentBody")
    bodyContent =getBody(body)
    conclusion = content.find_element(By.ID,"conclusions")
    case ={"Header":headerContent,"Body":bodyContent}
    return case

def getBody(body):
    paras =body.find_elements(By.CLASS_NAME,"akn-paragraph")
    for para in paras:
        body=getPara(para)
    return body

def getPara(para):
    paragraph={}
    text = para.find_element(By.ID,"akn-content").text
    number = para.find_element(By.ID,"akn-num").text
    paragraph[f"{number}"] = text
    return paragraph

def getHeader(header):
    header ={}
    title = header.find_element(By.CLASS_NAME,"doc-title").text
    neutral_citation =header.find_element(By.CLASS_NAME,"neutral-citation").text
    authority =header.find_element(By.CLASS_NAME,"doc-authority").text
    docket =header.find_element(By.CLASS_NAME,"docket-number").text
    date =header.find_element(By.CLASS_NAME,"doc-date").text
    note =header.find_element(By.CLASS_NAME,"header-note").text
    header= {"title":title,"neutral-citation":neutral_citation,"authority":authority,"docket":docket,"date":date,"note":note}

    parties =header.find_element(By.CLASS_NAME,"parties-listing")
    listings =parties.find_elements(By.CLASS_NAME,"parties-listing")
    for listing in listings:
        items=listing.find_elements(By.CLASS_NAME,"akn-div")
        name = items[0].text
        role = items[len(items)-1].text
        header ={f"{role}":name}
    return header

def create_nodes_recursively(tx, data, parent_id=None, node_label="Node", node_name=None):
    if parent_id is None:
        primitive_props = {k: v for k, v in data.items()
                           if isinstance(v, (str, int, float, bool)) or 
                              (isinstance(v, list) and all(isinstance(item, (str, int, float, bool)) for item in v))}
        result = tx.run(
            "CREATE (n:Constitution) SET n += $props RETURN elementId(n) AS node_id", 
            props=primitive_props
        )
        parent_id = result.single()["node_id"]
    
    for key, value in data.items():
        if isinstance(value, dict):
            child_props = {k: v for k, v in value.items()
                           if isinstance(v, (str, int, float, bool)) or 
                              (isinstance(v, list) and all(isinstance(x, (str, int, float, bool)) for x in v))}
            # Inject the label into the query string.
            query = "CREATE (n:" + node_label + " {name: $name}) SET n += $props RETURN elementId(n) AS node_id"
            result = tx.run(query, name=key, props=child_props)
            child_id = result.single()["node_id"]
            tx.run(
                "MATCH (p), (c) WHERE elementId(p) = $parent_id AND elementId(c) = $child_id "
                "CREATE (p)-[:HAS_CHILD]->(c)",
                parent_id=parent_id, child_id=child_id
            )
            create_nodes_recursively(tx, value, parent_id=child_id, node_label=node_label, node_name=key)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    child_props = {k: v for k, v in item.items()
                                   if isinstance(v, (str, int, float, bool)) or 
                                      (isinstance(v, list) and all(isinstance(x, (str, int, float, bool)) for x in v))}
                    query = "CREATE (n:" + node_label + " {name: $name}) SET n += $props RETURN elementId(n) AS node_id"
                    result = tx.run(query, name=key, props=child_props)
                    child_id = result.single()["node_id"]
                    tx.run(
                        "MATCH (p), (c) WHERE elementId(p) = $parent_id AND elementId(c) = $child_id "
                        "CREATE (p)-[:HAS_CHILD]->(c)",
                        parent_id=parent_id, child_id=child_id
                    )
                    create_nodes_recursively(tx, item, parent_id=child_id, node_label=node_label, node_name=key)
                else:
                    tx.run(
                        "MATCH (n) WHERE elementId(n) = $parent_id "
                        "SET n[$key] = coalesce(n[$key], []) + $value",
                        parent_id=parent_id, key=key, value=item
                    )
        else:
            tx.run(
                "MATCH (n) WHERE elementId(n) = $parent_id SET n[$key] = $value",
                parent_id=parent_id, key=key, value=value
            )
    return parent_id

def insert_hierarchy(data):

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.execute_write(create_nodes_recursively, data)
    driver.close()

def insert_with_parent(parent_id, data):

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.execute_write(create_nodes_recursively, data, parent_id=parent_id)
    driver.close()



def scrape_court_data(parent_id=None, url=None):

    url = BASE_URL + url
    driver = webdriver.Chrome()
    try:
        links = getCaseLinks(driver, url)
        cases_data = []
        
        for link in links:
            case_data = getCaseContent(driver, link)
            if case_data:
                cases_data.append(case_data)
        
        # Structure the data for Neo4j insertion
       
        
        # Insert with parent connection if specified
        if parent_id:
            insert_with_parent(parent_id, cases_data)
        else:
            insert_hierarchy(cases_data)
            
        return cases_data
    finally:
        driver.quit()



def main():
    logging.basicConfig(filename='Kenya-Law-AI.log', level=logging.INFO)
    logger.info('Getting contitutional data')
    court_data = scrape_court_data()
    logger.info('Storing constitutional data')
    insert_hierarchy(court_data)

    

    

__all__ = ['scrape_constitution_data', 'insert_hierarchy']
    

if __name__ == "__main__":
    main()