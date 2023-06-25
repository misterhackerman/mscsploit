#!/usr/bin/python3

from bs4 import BeautifulSoup
from art import tprint
from colorama import Fore

import argparse
import html
import os
import re
import requests

parser = argparse.ArgumentParser(description='API to download lectures off msc-mu.com')
parser.add_argument('-b', '--batch', type=int, metavar='', help='to specify batch number')
parser.add_argument('-c', '--course', type=int, metavar='', help='to specify course number')
parser.add_argument('-f', '--folder', type=str, metavar='', help='to specify destination folder')
args = parser.parse_args()

#FOLDER = '\\Documents\\Human Systems\\CVS\\' #Beggining with ~
FOLDER = '/documents/med/' # For linux

HEADERS = headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        }

def choose_batch():
    batches = [
	    [1, '2022', 'https://msc-mu.com/level/17'],
        [2, 'Rou7', 'https://msc-mu.com/level/16'],
        [3, 'Wateen', 'https://msc-mu.com/level/15'],
        [4, 'Nabed', 'https://msc-mu.com/level/14'],
        [5, 'Wareed', 'https://msc-mu.com/level/13']
    ]
    print('\n')
    if args.batch:
        batch_url = batches[args.batch - 1][2]
        print(Fore.GREEN + '\n[*] Searching', batches[args.batch - 1][1] + '\'s batch...\n')
        return batch_url
    for batch in batches:
        print(str(batch[0]) + ') ' + batch[1] )
    selected_batch = input('\n[*] Which batch are you?\n\n>> ')
    try:
        selected_batch = int(selected_batch)
        for batch in batches:
            if selected_batch == batch[0]:
                print('\n[*] Searching', batch[1] + '\'s batch...\n')
        batch_url = batches[selected_batch - 1][2]
        return batch_url
    except:
        print('\n[*]Invalid Input\n')
        return choose_batch()

def find_courses(url):
    page = requests.get(url, headers=HEADERS)
    doc = BeautifulSoup(page.text, 'html.parser')
    subject = doc.find_all('h6')
    courses = []
    for x, i in enumerate(subject):
        parent = i.parent.parent.parent
        course_number = re.findall('href="https://msc-mu.com/courses/(.*)">', parent.decode())[0]
        course_name = i.string.strip()
        courses.append([x + 1, course_name, course_number])
    return courses

def find_subject_folder(name, doc):
    if '&#39;' not in name:
        name = html.unescape(name)
    else:
        name = name.strip('&#39;')
        name = html.unescape(name)
    folder_source = doc.find_all("a", string=name)[0].parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent
    folder = re.findall('''</i>
                    (.*)

                </h6>''', folder_source.decode())
    return folder[0]

def choose_course(courses):
    if args.course:
        course_number = str(courses[args.course - 1][2])
        print('\n[*] Downloading', courses[args.course - 1][1])
        print(Fore.RESET)
        return course_number
    for course in courses:
        print(str(course[0]) + ') ' + course[1])
    selected_course = input('\n[*] Which course would you like to download?\n\n>> ')
    try:
        selected_course = int(selected_course)
        for course in courses:
            if selected_course == course[0]:
                list_index = selected_course - 1
                print('\n[*] Downloading', course[1])
        course_number = str(courses[list_index][2])
        return course_number
    except:
        print('\n[*]Invalid Input\n')
        return choose_course(courses)

def download_lectures(url, folder):
    extension = '.pdf'
    course_page = requests.get(url, headers=HEADERS)
    links = re.findall('<a href="(.*)">.*' + extension + '</a>', course_page.content.decode())
    names = re.findall('<a href=".*">(.*)' + extension + '</a>', course_page.content.decode())
    doc = BeautifulSoup(course_page.text, 'html.parser')
    y = 0
    prev_sub_folder = None
    subject_folders_list =[]
    for x, link in enumerate(links):
        link = link.strip() + extension
        subject_folder = find_subject_folder(names[x] + extension, doc)
        if subject_folder != prev_sub_folder:
            if subject_folder in subject_folders_list:
                subject_folder = subject_folder + '-extras'
            y = 0
        new_name = str(y + 1) + '. ' + names[x] + extension
        y += 1
        subject_folders_list.append(subject_folder)
        prev_sub_folder = subject_folder
        file_path = folder + subject_folder + '/' + new_name
        if os.path.isfile(file_path):
            if new_name.startswith('1.'):
                print('\n################ ' + subject_folder + ' ################\n')
            print( new_name + ' <is already downloaded there XD>')
            continue
        if not os.path.isdir(folder + subject_folder):
            os.makedirs(folder + subject_folder)
            print('\n################ ' + subject_folder + ' ################\n')
        
        response = requests.get(link, headers=HEADERS)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print('[*] Downloaded ' + new_name)

# If not specified, prompt the user to input a folder
         
def choose_folder():
    folder = os.path.expanduser("~") + FOLDER
    if args.folder:
        if '~' in args.folder:
            args.folder = os.path.expanduser(args.folder)
        if os.path.isdir(args.folder):
            folder = args.folder   
            return folder 
        else:
            print('\n[*] Folder Not found! ', end='')
            quit()
    else:
        answer = input('[*] Your default destination is ' + folder +  "\n[*] Do you want to change that (N/y): ")
        if answer == 'y' or answer == 'yes':
            valid_folder = False
            while valid_folder == False:
                selected_folder = input('\n[*] Enter the Folder you want to save material in.\n\n>> ')
                # Adds a seperator at the end if the user didn't
                if not selected_folder.endswith(os.path.sep):
                    selected_folder = selected_folder + os.path.sep
                selected_folder = os.path.expanduser(selected_folder)
                if os.path.isdir(selected_folder):
                    folder = selected_folder
                    valid_folder = True
                else:
                    print('\n[*] Folder Not found! ', end='')
    return folder

# Gets the name of the course from the course number, and makes a folder with that name

def make_course_folder(courses, index, folder):
    for course in courses:
        if course[2] == index:
            course_name = course[1]
            break
    new_folder = folder + os.path.sep + course_name + os.path.sep
    if not os.path.isdir(new_folder):
        os.mkdir(new_folder)
    folder = new_folder
    return folder

def main():
    folder = choose_folder()
    batch_url = choose_batch()
    courses = find_courses(batch_url)
    course_number = choose_course(courses)
    folder = make_course_folder(courses, course_number, folder)
    download_url = 'https://msc-mu.com/courses/' + course_number
    download_lectures(download_url, folder)

if __name__ == '__main__':
    print(Fore.CYAN + '#'*54)
    print(Fore.RED)
    tprint('RBCs')
    print(Fore.CYAN + '#'*54, end='\n')
    
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + '\n[*] KeyboardInterrupt')
        print(Fore.GREEN + '[*] Good bye!')
        quit()

    print(Fore.GREEN + '\n\n[*] Done...')
    print('[*] Goodbye!')
    input('[*] Press anything to' + Fore.RED + ' exit')
