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

constitutionUrl = "/akn/ke/act/2010/constitution/eng@2010-09-03";
chapters=["ONE","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","TWELVE","Thirteen","Fourteen","Fifteen","Sixteen","Seventeen","Eighteen"] #check exact case incase of case sensitivity

# get the coverpage
def getCoverPage(driver):
    coverpage = driver.find_element(By.CLASS_NAME, "coverpage")
    title = coverpage.find_element(By.TAG_NAME, "h1").text
    publication_info = driver.find_element(By.CLASS_NAME, "publication-info").text
    assent_date = driver.find_element(By.CLASS_NAME, "assent-date").text
    commencement_date = driver.find_element(By.CLASS_NAME, "commencement-date").text
    preamble_container =driver.find_element(By.CLASS_NAME,"akn-akomaNtoso")
    preamble = getPreamble(preamble_container)

    return {
        "title": title,
        "publication_info": publication_info,
        "assent_date": assent_date,
        "commencement_date": commencement_date,
        "preamble": preamble
    }

def getPreamble(preamble_container):
    preamble = []
    for i in range(1, 10):
        try:
            preamble_element = preamble_container.find_element(By.ID, f"hcontainer_1__p_{i}")
            preamble.append(preamble_element.text)
        except:
            break
    return preamble

def getChapter(driver):
    chapters_object={}
    for chapter in chapters:
        try:
            chapter_class =f"chp_{chapter}"
            chp_container=driver.find_element(By.ID,chapter_class)
            title = chp_container.find_element(By.TAG_NAME,'h2').text
            sections = getSec(chapter_container=chp_container, chapter_class=chapter_class)
            chapters_object[f"CHAPTER {chapter}"]={"title":title,"sections":sections}
        except Exception as e:
            print(f"Error Retrieving chapter {chapter}",e)
    return chapters_object

def getSec(chapter_container, chapter_class):
    section_object={}
    index =1
    while True:
        try:
            section_class =chapter_class+"__sec_"+f"{index}"
            sec_container = chapter_container.find_element(By.ID,section_class)
            title = sec_container.find_element(By.TAG_NAME,'h3').text
            subsections = getSubSec(section_container=sec_container, section_class=section_class)
            section_object[f"Section {index}"]={"title":title,"sub_sections":subsections}
            index=index+1
        except:
            break

    return section_object

def getSubSec(section_container,section_class):
    sub_section_object={}
    index =1
    while True:
        try:
            sub_section_class =section_class+"__subsec_"+f"{index}"
            sub_sec_container = section_container.find_element(By.ID,sub_section_class)
            title = sub_sec_container.find_element(By.CLASS_NAME,'akn-num').text
            content = getContent(subSectionContainer=sub_sec_container, section_class=sub_section_class)
            sub_section_object[f"Subsection {index}"]={"number":title,"sub_sections":content}
            index=index+1
        except:
            break

    return sub_section_object

def getContent(subSectionContainer, subSectionClass):
    content ={}
    try:
        point=subSectionContainer.find_element(By.CLASS_NAME,'akn-content')
        content["point"] =point.text
    except:
        content['intro'] =subSectionContainer.find_element(By.CLASS_NAME,'akn-intro').text
        content['paragraphs']= getPara(subSectionContainer,subSectionClass)
    return content

def getPara(subSectionContainer,subSectionClass):
    para_object = {}
    index = 97
    while True:
        try:
            para_class =subSectionClass+"__para_"+chr(index)
            para_container = subSectionContainer.find_element(By.ID,para_class)
            title = para_container.find_element(By.CLASS_NAME,'akn-num').text
            para= para_container.find_element(By.CLASS_NAME,'akn-content').text
            para_object[f"Paragraph {chr(index)}"]= {"letter":title,"content":para}
            index=index+1
        except:
            break
    return para_object



def main():
    # get url, driver and connect
    url = BASE_URL+constitutionUrl
    driver = webdriver.Chrome()
    driver.get(url)
    content = getChapter(driver=driver)
    print(content)


    time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    main()