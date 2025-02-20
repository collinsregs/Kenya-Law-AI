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
    number="1"
    for chapter in chapters:
        try:

            chapter_class =f"chp_{chapter}"
            print(chapter_class)
            chp_container=driver.find_element(By.ID,chapter_class)
            title = chp_container.find_element(By.TAG_NAME,'h2').text
            try:
                
                if chapter=="TWELVE" :
                    number ="I"
                print(f"TRY: {chapter_class}__part_{number}")
                chp_container.find_element(By.ID,f"{chapter_class}__part_{number}")
                parts = getPart(chp_container, section_class=chapter_class)
                chapters_object[f"CHAPTER {chapter}"]={"title":title,"sections":parts}
                number ="1"
            except:
                sections = getSec(chapter_container=chp_container, chapter_class=chapter_class, starting_index=global_section_index)
                chapters_object[f"CHAPTER {chapter}"]={"title":title,"sections":sections}
        except Exception as e:
            print(f"")
    return chapters_object

def getSec(chapter_container, chapter_class,starting_index):
    global global_section_index
    section_object={}
    index =starting_index
    while True:
        try:
            section_class =chapter_class+"__sec_"+f"{index}"
            print(section_class)
            sec_container = chapter_container.find_element(By.ID,section_class)
            title = sec_container.find_element(By.TAG_NAME,'h3').text
            try:
                sec_container.find_element(By.ID,f"{section_class}__subsec_1")
                subsections = getSubSec(section_container=sec_container, section_class=section_class)
                section_object[f"Section {index}"]={"title":title,"sub_sections":subsections}
            except:
                content = getContent(sec_container,section_class)
                section_object[f"Section {index}"]={"title":title,"Content":content}
            index=index+1
        except Exception as e:
            global_section_index =  index
            print(f"exception in get section")
            break

    return section_object

def getSubSec(section_container,section_class):
    sub_section_object={}
    index =1
    while True:
        try:
            sub_section_class =section_class+"__subsec_"+f"{index}"
            print (sub_section_class)
            sub_sec_container = section_container.find_element(By.ID,sub_section_class)
            title = sub_sec_container.find_element(By.CLASS_NAME,'akn-num').text
            content = getContent(subSectionContainer=sub_sec_container, subSectionClass=sub_section_class)
            sub_section_object[f"Subsection {index}"]={"number":title,"sub_sections":content}
            index=index+1
            
        except Exception as e:
            # print(f"exception in get section")
            break

    return sub_section_object


def getPart(section_container,section_class):
    sub_section_object={}
    index =1
    while True:
        try:
            sub_section_class =section_class+"__part_"+f"{index}"
            if section_class=="chp_TWELVE" and index==1:
                    sub_section_class =section_class+"__part_"+f"I"
            print ("part",sub_section_class)
            sub_sec_container = section_container.find_element(By.ID,sub_section_class)
            title = sub_sec_container.find_element(By.TAG_NAME,'h2').text
            content = getSec(sub_sec_container,sub_section_class,global_section_index)
            sub_section_object[f"Part {index}"]={"title":title,"Sections":content}
            index=index+1

        except Exception as e:
            # print(f"exception in get section")
            break

    return sub_section_object

def getContent(subSectionContainer, subSectionClass):

    # print("getting content for:",subSectionClass)
    content ={}
    try:
        content['intro'] =subSectionContainer.find_element(By.CLASS_NAME,'akn-intro').text
        content['paragraphs']= getPara(subSectionContainer,subSectionClass)

        # print("getting actual content",point.text)
    except:
        point=subSectionContainer.find_element(By.CLASS_NAME,'akn-content')
        content["point"] =point.text
        # print("getting paragraph",point.text)

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
    # print(content)


    time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    main()