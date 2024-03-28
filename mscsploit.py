#!/usr/bin/python3

from bs4 import BeautifulSoup
from rich.progress import track
import requests
import argparse
import re
import os

parser = argparse.ArgumentParser(description='API to download lectures off msc-mu.com')
parser.add_argument('-b', '--batch', type=int, metavar='', help='to specify batch number')
parser.add_argument('-c', '--course', type=int, metavar='', help='to specify course number')
parser.add_argument('-f', '--folder', type=str, metavar='', help='to specify destination folder')
args = parser.parse_args()

FOLDER = '/dox/med'

HEADERS = headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }


def choose_batch():
    batches = [
        [1, 'Athar', 'https://msc-mu.com/level/17'],
        [2, 'Rou7', 'https://msc-mu.com/level/16'],
        [3, 'Wateen', 'https://msc-mu.com/level/15'],
        [4, 'Nabed', 'https://msc-mu.com/level/14'],
        [5, 'Wareed', 'https://msc-mu.com/level/13'],
        [6, 'Minors', 'https://msc-mu.com/level/10'],
        [7, 'Majors', 'https://msc-mu.com/level/9']
    ]
    print('\n')
    if args.batch:
        batch_url = batches[args.batch - 1][2]
        print('\n[*] Searching', batches[args.batch - 1][1] + '\'s batch...\n')
        return batch_url
    for batch in batches:
        print(str(batch[0]) + ') ' + batch[1])
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


def choose_course(courses):
    if args.course:
        course_number = str(courses[args.course - 1][2])
        print('\n[*] Alright, ', courses[args.course - 1][1])
        return course_number
    for course in courses:
        print(str(course[0]) + ') ' + course[1])
    selected_course = input('\n[*] Which course would you like to download?\n\n>> ')
    list_index = None
    try:
        selected_course = int(selected_course)
        for course in courses:
            if selected_course == course[0]:
                list_index = selected_course - 1
                print('\n[*] Alright, ', course[1])
        course_number = str(courses[list_index][2])
        return course_number
    except:
        print('\n[*]Invalid Input\n')
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
            print('\n[*] Folder Not found! ', end='')
            quit()
    else:
        answer = input('[*] Your default destination is ' + folder + "\n[*] Do you want to keep that (Y/n): ")
        if answer == 'n' or answer == 'no' or answer == 'N':
            valid_folder = False
            while not valid_folder:
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
    new_folder = folder + course_name + os.path.sep
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
    counter = 0
    for path, link, name in track(path_link_dict, description=f'[*] Downloading...'):

        counter = counter + 1
        count = f' ({counter}/{len(path_link_dict)})'
        if os.path.isfile(folder + path + name):
            print('[ Already there! ] ' + name + count)
            continue

        if not os.path.isdir(folder + path):
            os.makedirs(folder + path)

        response = requests.get(link, headers=HEADERS)
        with open(folder + path + name, 'wb') as file:
            file.write(response.content)
        print('[*] Downloaded ' + name + count)


def main():
    folder = choose_folder()
    batch_url = choose_batch()
    courses = find_courses(batch_url)
    course_number = choose_course(courses)
    folder = make_course_folder(courses, course_number, folder)
    download_url = 'https://msc-mu.com/courses/' + course_number
    print('[*] Requesting page...')
    course_page = requests.get(download_url, headers=HEADERS)
    print('[*] Parsing page into a soup')
    soup = BeautifulSoup(course_page.text, 'html.parser')

    nav_dict = create_nav_links_dictionary(soup)
    file_dict = find_files_paths_and_links(nav_dict, soup)
    download_from_dict(file_dict, folder)


if __name__ == '__main__':
    print('#'*54)
    try:
        main()
    except KeyboardInterrupt:
        print('\n[*] KeyboardInterrupt')
        print('[*] Good bye!')
        quit()
    print('\n\n[*] Done...')
    print('[*] Goodbye!')
    input('[*] Press anything to exit')
