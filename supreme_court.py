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

# Load environment variables from .env file
load_dotenv()

# Get the BASE_URL from the environment variables
BASE_URL = os.getenv("BASE_URL")

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
    content = driver.find_element(By.CLASS_NAME,"akn-judgment")
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

def main():
    # get url, driver and connect
    url = BASE_URL+supremeCourtUrl
    driver = webdriver.Chrome()
    links=getCaseLinks(driver,url)
    for link in links:
        getCaseContent(driver,link)

    


    time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    main()