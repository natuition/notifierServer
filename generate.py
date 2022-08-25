from selenium import webdriver
from haversine import haversine
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
import datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from time import sleep
import os
import cv2
import re
import requests
import matplotlib.pyplot as plt
import math
from urllib.parse import unquote

from backports.datetime_fromisoformat import MonkeyPatch
MonkeyPatch.patch_fromisoformat()


"""
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
"""


def takeScreenshot(url: str, file_name: str):

    op = webdriver.ChromeOptions()
    op.add_argument("headless")
    op.add_argument("--no-sandbox")

    #driver = webdriver.Chrome(ChromeDriverManager().install())
    #driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    driver = webdriver.Chrome(
        options=op, executable_path="./utils_generate/chromedriver")

    driver.set_window_position(0, 0)
    # driver.set_window_size(720,480)
    driver.set_window_size(740, 500)

    driver.get(url)

    driver.get_screenshot_as_file(file_name.replace("jpeg", "png"))
    driver.quit()

    image = cv2.imread(os.getcwd()+"/"+file_name.replace("jpeg", "png"))
    cv2.imwrite(os.getcwd()+"/"+file_name, image,
                [int(cv2.IMWRITE_JPEG_QUALITY), 50])

    os.remove(os.getcwd()+"/"+file_name.replace("jpeg", "png"))


def makeStats(dict_extract_plant_by_number, total_plant, file_name: str):
    colors = ['#91BD55', '#D4DA54', '#41884B', '#56A973', '#459B90']

    if len(dict_extract_plant_by_number) == 0:
        plt.pie([1], colors=['#E4E4E3'], startangle=90, counterclock=True)
    elif len(dict_extract_plant_by_number) <= 5:
        stats = [
            number/total_plant for number in dict_extract_plant_by_number.values()]
        colors_final = colors[0:len(dict_extract_plant_by_number)]
        plt.pie(stats, colors=colors_final, startangle=90, counterclock=True)
    else:
        stats = [number for number in list(
            dict_extract_plant_by_number.values())[0:4]]
        print(stats)
        last_number = sum([number for number in list(
            dict_extract_plant_by_number.values())[4:]])
        stats.append(last_number)
        print(stats)
        print(colors)
        plt.pie(stats, colors=colors, startangle=90,
                counterclock=True, normalize=True)

    my_circle = plt.Circle((0, 0), 0.6, color='white', alpha=1)
    p = plt.gcf()
    p.gca().add_artist(my_circle)
    plt.savefig(file_name, dpi=200)

    image = cv2.imread(os.getcwd()+"/"+file_name)
    crop_image = image[180:790, 360:960]
    cv2.imwrite(os.getcwd()+"/"+file_name, crop_image,
                [int(cv2.IMWRITE_PNG_COMPRESSION), 9])


def generatePdf(template_name: str, generate_name: str, map_url: str):

    url_screen = map_url.replace("map", "map_static")

    takeScreenshot(url_screen, "utils_generate/map.jpeg")

    html = requests.get(url=map_url).text

    start = re.findall("Start time : (.*)", html)[0]
    end = re.findall("End time : ([^<]*)", html)[0]
    extracted_plant = re.findall("Extraction number : (.*)", html)[0]
    treated_plant = re.findall("Treated plant : (.*)", html)[0]
    travel_distance = re.findall("Traveled distance \(m\) : ([^<]*)", html)[0]
    language = re.findall("Language : ([^<]*)", html)[0]
    field_name = re.findall("Field name : &#39;(.*)&#39;", html)
    if len(field_name) > 0:
        field_name = field_name[0]
        field_name = unquote(field_name).encode("latin1").decode("utf-8")
        if len(field_name) > 20:
            field_name = field_name[0:17]+"..."
        elif len(field_name) < 20:
            space = "  " * math.ceil((20-len(field_name))/2)
            field_name = space+field_name
    field = eval(re.findall("var coords_field = (.*);", html)[0])
    field[0].reverse()
    field[1].reverse()
    field[2].reverse()
    field[3].reverse()
    field_surface = round(
        (haversine(field[0], field[1])*1000) * (haversine(field[1], field[2])*1000))

    surface_covered = round(float(travel_distance)*0.33)

    treated_plant = eval(treated_plant.replace(
        "&#39;", '"').replace(" ", '').lower())
    dict_extract_plant_by_number = eval(
        extracted_plant.replace("&#39;", '"').replace(" ", '').lower())
    dict_extract_plant_by_number = {k: v for k, v in sorted(
        dict_extract_plant_by_number.items(), key=lambda item: item[1], reverse=True)}
    plant_not_extract = list()
    for plant in treated_plant:
        if plant not in dict_extract_plant_by_number.keys():
            plant_not_extract.append(plant)

    total_plant = 0

    for plant, number in dict_extract_plant_by_number.items():
        total_plant += number

    makeStats(dict_extract_plant_by_number,
              total_plant, "utils_generate/stats.png")

    output = PdfFileWriter()

    start = start.split(" ")
    start_format = start[0].split("-")[2].replace(" ", "")+"-" +\
        start[0].split("-")[1].replace(" ", "")+"-" +\
        start[0].split("-")[0].replace(" ", "")+"T" +\
        start[1].split("-")[0].replace(" ", "")+":" +\
        start[1].split("-")[1].replace(" ", "")+":" +\
        start[1].split("-")[2].replace(" ", "")+"." +\
        start[2]
    end = end.split(" ")
    end_format = end[0].split("-")[2].replace(" ", "")+"-" +\
        end[0].split("-")[1].replace(" ", "")+"-" +\
        end[0].split("-")[0].replace(" ", "")+"T" +\
        end[1].split("-")[0].replace(" ", "")+":" +\
        end[1].split("-")[1].replace(" ", "")+":" +\
        end[1].split("-")[2].replace(" ", "")+"." +\
        end[2]

    session_times = {"start": datetime.datetime.fromisoformat(
        start_format), "end": datetime.datetime.fromisoformat(end_format)}

    s = int((session_times["end"]-session_times["start"]).total_seconds())
    hours = s // 3600
    s = s - (hours * 3600)
    minutes = s // 60
    seconds = s - (minutes * 60)
    session_times["duration"] = {"hours": int(
        hours), "minutes": int(minutes), "seconds": int(seconds)}

    fields = {"start_time": session_times["start"].strftime("%H:%M:%S"),
              "end_time": session_times["end"].strftime("%H:%M:%S"),
              "date": session_times["start"].strftime("%d/%m/%Y"),
              "time": "{:02}:{:02}:{:02}".format(session_times["duration"]["hours"], session_times["duration"]["minutes"], session_times["duration"]["seconds"])
              }

    packet = io.BytesIO()
    can = canvas.Canvas(packet)
    can.drawImage("utils_generate/map.jpeg", 55, 390, 500, 290)
    can.drawImage("utils_generate/stats.png", 70, 171, 180, 180)
    can.drawImage("utils_generate/cible.png", 115, 215, 90,
                  90, mask=[250, 255, 250, 255, 250, 255])
    can.drawString(465, 787, fields["start_time"])
    can.drawString(465, 762, fields["end_time"])
    can.drawString(174, 786, fields["date"])
    if isinstance(field_name, str):
        can.drawString(145, 762, field_name)
    can.drawString(184, 362, fields["time"])
    can.drawString(235, 699, str(field_surface).rjust(6))
    can.drawString(499, 699, str(surface_covered).rjust(6))

    print(
        f"treated_plant: {len(treated_plant)} dict_extract_plant_by_number: {len(dict_extract_plant_by_number)}")

    if len(treated_plant) <= 5:
        for index in range(len(dict_extract_plant_by_number)):
            can.drawString(
                498, 358-index*27, str(list(dict_extract_plant_by_number.values())[index]).rjust(6))
            can.drawString(
                358, 358-index*27, str(list(dict_extract_plant_by_number.keys())[index]).capitalize())
        if plant_not_extract:
            for index in range(len(plant_not_extract)):
                can.drawString(
                    498, 358-(index+len(dict_extract_plant_by_number))*27, str(0).rjust(6))
                can.drawString(358, 358-(index+len(dict_extract_plant_by_number))
                               * 27, str(plant_not_extract[index]).capitalize())

    elif len(dict_extract_plant_by_number) <= 5:
        for index in range(len(dict_extract_plant_by_number)):
            can.drawString(
                498, 358-index*27, str(list(dict_extract_plant_by_number.values())[index]).rjust(6))
            can.drawString(
                358, 358-index*27, str(list(dict_extract_plant_by_number.keys())[index]).capitalize())
        for index in range(5-len(dict_extract_plant_by_number)):
            if index < len(plant_not_extract):
                can.drawString(
                    498, 358-(index+len(dict_extract_plant_by_number))*27, str(0).rjust(6))
                can.drawString(358, 358-(index+len(dict_extract_plant_by_number))
                               * 27, str(plant_not_extract[index]).capitalize())
    else:
        for index in range(4):
            can.drawString(
                498, 358-index*27, str(list(dict_extract_plant_by_number.values())[index]).rjust(6))
            can.drawString(
                358, 358-index*27, str(list(dict_extract_plant_by_number.keys())[index]).capitalize())
        can.drawString(498, 247, str(sum([number for number in list(
            dict_extract_plant_by_number.values())[4:]])).rjust(6))
        can.drawString(358, 247, str("other").capitalize())

    can.drawString(498, 210, str(total_plant).rjust(6))
    can.save()

    packet.seek(0)
    new_pdf = PdfFileReader(packet)

    # for language in ["fr","nl","en"]:
    for language in [language]:
        template = PdfFileReader(
            open(f"{template_name}_{language}.pdf", "rb"), strict=False)
        template_page = template.getPage(0)
        template_page.mergePage(new_pdf.getPage(0))
        output.addPage(template_page)

    outputStream = open(f"{generate_name}.pdf", "wb")
    output.write(outputStream)


if __name__ == "__main__":
    robot = "SN011"
    """
    ["24-08-2022 10-09-19 688347", "24-08-2022 11-44-20 848486", "24-08-2022 11-51-34 952924", "25-04-2022 08-05-51 607659",
                 "25-04-2022 08-27-32 476651", "25-04-2022 11-00-26 663230", "25-08-2022 07-48-06 704476", "25-08-2022 08-05-53 910929",
                 "25-08-2022 09-32-12 075669", "25-08-2022 09-53-17 275181", "25-08-2022 10-03-17 486582", "25-08-2022 10-13-15 769097",
                 "25-08-2022 10-37-17 177303", "24-08-2022 08-18-08 958886", "24-08-2022 10-00-05 274358"]
    """
    for date in ["24-08-2022 08-18-08 958886", "24-08-2022 10-00-05 274358"]:
        date_url = date.replace(" ", "%20")
        url = f"http://172.16.0.9/map/{robot}/{date_url}"
        print(f"Pdf généré de : {url}.")
        res_name = "resume"
        generatePdf("utils_generate/template",
                    f"/root/notifierServer/{robot}/{date}/{res_name}", url)
