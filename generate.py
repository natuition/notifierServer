from PyPDF2 import PdfFileWriter, PdfFileReader
import datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from time import sleep
import os
import cv2 
import re
import requests
import matplotlib.pyplot as plt
from backports.datetime_fromisoformat import MonkeyPatch
MonkeyPatch.patch_fromisoformat()
from haversine import haversine

def takeScreenshot(url: str, file_name: str):

    op = webdriver.ChromeOptions()
    op.add_argument("headless")
    op.add_argument("--no-sandbox");
    service = Service("./utils_generate/chrome_driver")
    driver = webdriver.Chrome(options=op, executable_path="./utils_generate/chromedriver")
    driver.set_window_position(0, 0)
    driver.set_window_size(2450,1140)
    
    driver.get(url)

    sleep(45)

    driver.get_screenshot_as_file(file_name)
    driver.quit()

    image = cv2.imread(os.getcwd()+"/"+file_name)
    crop_image = image[0:1080, 0:1920]
    cv2.imwrite(os.getcwd()+"/"+file_name, crop_image)

def makeStats(size_of_groups, file_name: str):
    colors = ['#91BD55', '#D3DA54', '#3E894A']
    if size_of_groups == [0,0,0]:
        plt.pie([1], colors=['#E4E4E3'], startangle=90, counterclock=False)
    else:
        plt.pie(size_of_groups, colors=colors, startangle=90, counterclock=False)
    my_circle=plt.Circle( (0,0), 0.6, color='white', alpha=1)
    p=plt.gcf()
    p.gca().add_artist(my_circle)
    plt.savefig(file_name, dpi=200)

    image = cv2.imread(os.getcwd()+"/"+file_name)
    crop_image = image[180:790, 360:960]
    cv2.imwrite(os.getcwd()+"/"+file_name, crop_image)

def generatePdf(template_name: str, generate_name: str, map_url: str):

    takeScreenshot(map_url, "utils_generate/map.png")

    html = requests.get(url = map_url).text

    start = re.findall("Start time : (.*)", html)[0]
    end = re.findall("End time : ([^<]*)", html)[0]
    extracted_plant = re.findall("Extraction number : (.*)", html)[0]
    travel_distance = re.findall("Traveled distance \(m\) : ([^<]*)", html)[0]
    field = eval(re.findall("var coords_field = (.*);", html)[0])
    field[0].reverse()
    field[1].reverse()
    field[2].reverse()
    field[3].reverse()
    field_surface = round((haversine(field[0],field[1])*1000) * (haversine(field[1],field[2])*1000))

    surface_covered = round(float(travel_distance)*0.33)

    dict_extract_plant = eval(extracted_plant.replace("&#39;",'"'))

    index_name_extracted_plant = {"Plantain_great": 0,"Plantain_narrowleaf": 0, "Porcelle" : 1 ,"Dandellion" : 2, "Dandelion" : 2}
    formated_extracted_plant = [0,0,0]

    total_plant = 0

    for plant, number in dict_extract_plant.items():
        if plant in index_name_extracted_plant.keys():
            formated_extracted_plant[index_name_extracted_plant[plant]] += number
        total_plant+=number

    makeStats(formated_extracted_plant, "utils_generate/stats.png")

    output = PdfFileWriter()
    input = PdfFileReader(open(template_name+".pdf", "rb"),strict=False)

    start = start.split(" ")
    start_format =  start[0].split("-")[2].replace(" ","")+"-"+\
                    start[0].split("-")[1].replace(" ","")+"-"+\
                    start[0].split("-")[0].replace(" ","")+"T"+\
                    start[1].split("-")[0].replace(" ","")+":"+\
                    start[1].split("-")[1].replace(" ","")+":"+\
                    start[1].split("-")[2].replace(" ","")+"."+\
                    start[2]
    end = end.split(" ")
    end_format =    end[0].split("-")[2].replace(" ","")+"-"+\
                    end[0].split("-")[1].replace(" ","")+"-"+\
                    end[0].split("-")[0].replace(" ","")+"T"+\
                    end[1].split("-")[0].replace(" ","")+":"+\
                    end[1].split("-")[1].replace(" ","")+":"+\
                    end[1].split("-")[2].replace(" ","")+"."+\
                    end[2]

    session_times = {"start":datetime.datetime.fromisoformat(start_format),"end":datetime.datetime.fromisoformat(end_format)}

    s = int((session_times["end"]-session_times["start"]).total_seconds())
    hours = s // 3600 
    s = s - (hours * 3600)
    minutes = s // 60
    seconds = s - (minutes * 60)
    session_times["duration"] = {"hours":int(hours),"minutes":int(minutes),"seconds":int(seconds)}

    fields = {  "start_time": session_times["start"].strftime("%H:%M:%S"),
                "end_time": session_times["end"].strftime("%H:%M:%S"),
                "date": session_times["start"].strftime("%m/%d/%Y"), 
                "time": "{:02}:{:02}:{:02}".format(session_times["duration"]["hours"], session_times["duration"]["minutes"], session_times["duration"]["seconds"])
    }

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawImage("utils_generate/map.png", 45, 390, 500, 290)
    can.drawImage("utils_generate/stats.png", 80, 167, 180, 180)
    can.drawImage("utils_generate/cible.png", 125, 211, 90, 90, mask=[250,255,250,255,250,255])
    can.drawString(485, 787, fields["start_time"])
    can.drawString(485, 762, fields["end_time"])
    can.drawString(156, 786, fields["date"])
    can.drawString(190, 358, fields["time"])
    can.drawString(186, 700, str(field_surface).rjust(6))
    can.drawString(509, 700, str(surface_covered).rjust(6))
    can.drawString(195, 143, str(formated_extracted_plant[0]).rjust(6))
    can.drawString(195, 115, str(formated_extracted_plant[1]).rjust(6))
    can.drawString(195, 87, str(formated_extracted_plant[2]).rjust(6))
    can.drawString(195, 52, str(total_plant).rjust(6))
    can.save()

    packet.seek(0)
    new_pdf = PdfFileReader(packet)

    page1 = input.getPage(0)
    page1.mergePage(new_pdf.getPage(0))
    output.addPage(page1)

    outputStream = open(generate_name+".pdf", "wb")
    output.write(outputStream)

if __name__ == "__main__":
    url = "http://127.0.0.1/map/SN000/18-11-2021%2023-03-04%20157124"
    res_name =  "output"
    generatePdf("utils_generate/template", res_name, url)