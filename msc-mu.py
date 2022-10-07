#!python

from bs4 import BeautifulSoup
from art import tprint

import os
import re
import requests

HEADERS = headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        }

def choose_batch():
    batches = [
        [1, 'Wateen', 'https://msc-mu.com/level/15'],
        [2, 'Rou7', 'https://msc-mu.com/level/16'],
        [3, 'Nabed', 'https://msc-mu.com/level/14']
    ]
    for batch in batches:
        print(str(batch[0]) + ') ' + batch[1] )
    ui_batch = input('\n[*] Which batch are you?\n\n>> ')
    try:
        ui_batch = int(ui_batch)
        for batch in batches:
            if ui_batch == batch[0]:
                print('\n[*] Searching', batch[1] + '\'s batch...')
        batch_url = batches[ui_batch - 1][2]
        return batch_url
    except:
        print('\n[*]Invalid Input\n')
        choose_batch()

def find_courses(url):
    page = requests.get(url, headers=HEADERS)
    doc = BeautifulSoup(page.text, 'html.parser')
    subject = doc.find_all('h6')
    courses = []
    x = 0
    for i in subject:
        x += 1
        parent = i.parent.parent.parent
        course_number = re.findall('href="https://msc-mu.com/courses/(.*)">', parent.decode())[0]
        course_name = i.string.strip()
        courses.append([x, course_name, course_number])
    return courses

def choose_course(url):
    global courses
    courses = find_courses(url)
    for course in courses:
        print(str(course[0]) + ') ' + course[1])
    ui_course = input('\n[*] Which course would you like to download?\n\n>> ')
    try:
        ui_course = int(ui_course)
        for course in courses:
            if ui_course == course[0]:
                list_index = ui_course - 1
                print('\n[*] Downloading', course[1])
        course_number = str(courses[list_index][2])
        return course_number
    except:
        print('\n[*]Invalid Input\n')
        choose_course()

def download_lectures(url, course_number):
    course_page = requests.get(url, headers=HEADERS)
    links = re.findall('<a href="(.*)">.*.pdf</a>', course_page.content.decode())
    names = re.findall('<a href=".*">(.*).pdf</a>', course_page.content.decode())
    x=0
    for link in links:
        link = link.strip() + '.pdf'
        new_name = str(x+1) + '. ' + names[x] + '.pdf'
        # os.system('wget ' + link + ' -O \'' + folder + new_name + '\'')
        os.system('powershell -c "Invoke-Webrequest -Uri ' + link+ ' -OutFile \'' + folder + new_name + '\'"') 
        x += 1

def main():
    batch_url = choose_batch()
    course_number = choose_course(batch_url)

    download_url = 'https://msc-mu.com/courses/' + course_number
    download_lectures(download_url, course_number)

if __name__ == '__main__':
    print('#'*54)
    tprint('Welcome!')
    print('#'*54)
    
    ui_folder = input('\n[*] Enter the Folder you want to save material in.\n\n>> ')
    if os.path.isdir(ui_folder):
        folder = ui_folder
    else:
        print('[*] Folder Not found! ')
        exit()
            
    main()
