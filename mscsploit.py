#!/usr/bin/python3

from bs4 import BeautifulSoup
from rich.progress import track
import requests

import argparse
import datetime
import os
import re

parser = argparse.ArgumentParser(description='API to download lectures off msc-mu.com')
parser.add_argument('-t', '--category', type=int, metavar='', help='to specify category number')
parser.add_argument('-c', '--course', type=int, metavar='', help='to specify course number')
parser.add_argument('-f', '--folder', type=str, metavar='', help='to specify destination folder')
parser.add_argument('-v', '--verbose', action='store_true', help='Increase Verbosity')
args = parser.parse_args()

DECOR = ' \033[34;1m::\033[0m '
FOLDER = '/dox/med'

HEADERS = headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }


def choose_category():
    categories = [
        [1, 'Sha3\'af', 'https://msc-mu.com/level/18'],
        [2, 'Athar', 'https://msc-mu.com/level/17'],
        [3, 'Rou7', 'https://msc-mu.com/level/16'],
        [4, 'Wateen', 'https://msc-mu.com/level/15'],
        [5, 'Nabed', 'https://msc-mu.com/level/14'],
        [6, 'Wareed', 'https://msc-mu.com/level/13'],
        [7, 'Minors', 'https://msc-mu.com/level/10'],
        [8, 'Majors', 'https://msc-mu.com/level/9']
    ]
    if args.category:
        category_url = categories[args.category - 1][2]
        print(DECOR + 'Searching', categories[args.category - 1][1] + '\'s category...')
        return category_url
    print('\n')
    for category in categories:
        print(str(category[0]) + ') ' + category[1])
    selected_category = input('\n' + DECOR + 'Choose  a category.\n\n>> ')
    try:
        selected_category = int(selected_category)
        for category in categories:
            if selected_category == category[0]:
                print('\n' + DECOR + 'Searching', category[1] + '\'s category...\n')
        category_url = categories[selected_category - 1][2]
        return category_url
    except:
        print('\n' + DECOR + 'Invalid Input\n')
        return choose_category()


def find_courses(url):
    page = s.get(url, headers=HEADERS)
    doc = BeautifulSoup(page.text, 'html.parser')
    subject = doc.find_all('h6')
    courses = []
    for x, i in enumerate(subject):
        parent = i.parent.parent.parent
        course_number = re.findall('href="https://msc-mu.com/courses/(.*)">', parent.decode())[0]
        course_name = i.string.strip()
        courses.append([x + 1, course_name, course_number])
    return courses


def choose_course(courses):
    if args.course:
        course_number = str(courses[args.course - 1][2])
        print(DECOR + 'Alright, ', courses[args.course - 1][1])
        return course_number
    for course in courses:
        print(str(course[0]) + ') ' + course[1])
    selected_course = input('\n' + DECOR + 'Which course would you like to download?\n\n>> ')
    list_index = None
    try:
        selected_course = int(selected_course)
        for course in courses:
            if selected_course == course[0]:
                list_index = selected_course - 1
                print('\n' + DECOR + 'Alright, ', course[1])
        course_number = str(courses[list_index][2])
        return course_number
    except:
        print('\n' + DECOR + 'Invalid Input\n')
        return choose_course(courses)


def choose_folder():
    folder = os.path.expanduser("~") + FOLDER
    if args.folder:
        if '~' in args.folder:
            args.folder = os.path.expanduser(args.folder)
        if os.path.isdir(args.folder):
            folder = args.folder
            if not folder[-1] == os.path.sep:
                folder = folder + os.path.sep
            return folder
        else:
            print('\n' + DECOR + 'Folder Not found! ', end='')
            quit()
    else:
        answer = input(DECOR + 'Your default destination is ' + folder + '\n' + DECOR + ' Do you want to keep that (Y/n): ')
        if answer == 'n' or answer == 'no' or answer == 'N':
            valid_folder = False
            while not valid_folder:
                selected_folder = input('\n' + DECOR + 'Enter the Folder you want to save material in.\n\n>> ')
                # Adds a seperator at the end if the user didn't
                if not selected_folder.endswith(os.path.sep):
                    selected_folder = selected_folder + os.path.sep
                selected_folder = os.path.expanduser(selected_folder)
                if os.path.isdir(selected_folder):
                    folder = selected_folder
                    valid_folder = True
                else:
                    print('\n' + DECOR + 'Folder Not found! ', end='')
    if not folder[-1] == os.path.sep:
        folder = folder + os.path.sep
    return folder


def create_nav_links_dictionary(soup):
    navigate_dict = {}
    nav_links = soup.find_all('li', attrs={"class": "nav-item"})
    for navigate_link in nav_links:
        if navigate_link.h5:
            nav_name = navigate_link.h5.text.strip()
            nav_number = navigate_link.a.get('aria-controls')
            navigate_dict[nav_number] = nav_name
    return navigate_dict


def make_course_folder(courses, index, folder):
    course_name = None
    for course in courses:
        if course[2] == index:
            course_name = course[1]
            break
    # Replace any invalid characters with an underscore
    safe_course_name = re.sub(r'[\/:*?"<>|]', '_', course_name)
    new_folder = folder + safe_course_name + os.path.sep

    if not os.path.isdir(new_folder):
        os.mkdir(new_folder)
    folder = new_folder
    return folder


def find_files_paths_and_links(navigation_dict, soup):
    file_tags = soup.find_all('a', string=lambda text: text and '.pdf' in text) + soup.find_all('a', string=lambda text: text and '.ppt' in text)
    files_list = []
    path = []
    associated_nav_link_id = ''
    for file_tag in file_tags:
        current_tag = file_tag
        if not current_tag:
            print('no pdf or pptx files!')
            quit()
        while True:
            current_tag = current_tag.parent
            if current_tag.name == 'div' and 'mb-3' in current_tag.get('class', []):
                path.append(current_tag.h6.text.strip())
            if current_tag.name == 'div' and 'tab-pane' in current_tag.get('class', []):
                associated_nav_link_id = current_tag.get('id')
            if not current_tag.parent:
                break
        path.append(navigation_dict[associated_nav_link_id])
        path.reverse()
        basename = file_tag.text
        file_path = "/".join(path) + os.path.sep
        path.clear()

        file_link = file_tag.get('href')
        files_list.append([file_path, file_link, basename])
    return files_list


def download_from_dict(path_link_dict, folder):
    global downloaded_count
    downloaded_count = 0
    counter = 0
    for path, link, name in track(path_link_dict, description=f'{DECOR}Downloading...'):

        counter = counter + 1
        count = f' ({counter}/{len(path_link_dict)})'
        if os.path.isfile(folder + path + name):
            if args.verbose:
                print('[ Already there! ] ' + name + count)
            continue

        if not os.path.isdir(folder + path):
            os.makedirs(folder + path)

        # TODO delete incomplete downloads
        response = s.get(link, headers=HEADERS, stream=True)
        with open(folder + path + name, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        print(DECOR + 'Downloaded ' + name + count)
        downloaded_count += 1


def main():
    start = datetime.datetime.now()
    folder = choose_folder()
    category_url = choose_category()
    courses = find_courses(category_url)
    course_number = choose_course(courses)
    folder = make_course_folder(courses, course_number, folder)
    download_url = 'https://msc-mu.com/courses/' + course_number
    print(DECOR + 'Requesting page...')
    course_page = s.get(download_url, headers=HEADERS)
    print(DECOR + 'Parsing page into a soup...')
    soup = BeautifulSoup(course_page.text, 'html.parser')

    nav_dict = create_nav_links_dictionary(soup)
    file_dict = find_files_paths_and_links(nav_dict, soup)
    download_from_dict(file_dict, folder)
    print('\n\n' + DECOR + 'Done...')
    print(DECOR + 'Downloaded ' + str(downloaded_count) + ' files.')
    print(DECOR + 'Goodbye!')
    finish = datetime.datetime.now() - start
    print(DECOR + 'Time it took: ' + str(finish))
    input(DECOR + 'Press enter to \033[31;1mexit')


if __name__ == '__main__':
    print(''' ███╗   ███╗███████╗ ██████╗███████╗██████╗ ██╗      ██████╗ ██╗████████╗
 ████╗ ████║██╔════╝██╔════╝██╔════╝██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝
 ██╔████╔██║███████╗██║     ███████╗██████╔╝██║     ██║   ██║██║   ██║
 ██║╚██╔╝██║╚════██║██║     ╚════██║██╔═══╝ ██║     ██║   ██║██║   ██║
 ██║ ╚═╝ ██║███████║╚██████╗███████║██║     ███████╗╚██████╔╝██║   ██║
 ╚═╝     ╚═╝╚══════╝ ╚═════╝╚══════╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝   ╚═╝''')
    try:
        s = requests.Session()
        main()
    except KeyboardInterrupt:
        print('\n' + DECOR + 'KeyboardInterrupt')
        if 'downloaded_count' in globals():
            print(DECOR + 'Downloaded ' + str(downloaded_count) + ' files.')
        print(DECOR + 'Good bye!')
        quit()
