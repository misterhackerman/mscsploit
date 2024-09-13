from bs4 import BeautifulSoup
from rich.progress import track
import requests

import os
import re

from config import *


class Scraper:
    downloaded_count = 0

    def __init__(self, args):
        self.args = args
        self.session = requests.session()

    def choose_category(self):
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
        if self.args.category:
            category_url = categories[self.args.category - 1][2]
            print(DECOR + 'Searching', categories[self.args.category - 1][1] + '\'s category...')
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
                    break
            raise Exception
        except:
            print('\n' + DECOR + 'Invalid Input\n')
            return self.choose_category()


    def find_courses(self, url):
        page = self.session.get(url, headers=HEADERS)
        doc = BeautifulSoup(page.text, 'html.parser')
        subject = doc.find_all('h6')
        courses = []
        for x, i in enumerate(subject):
            parent = i.parent.parent.parent
            course_number = re.findall('href="https://msc-mu.com/courses/(.*)">', parent.decode())[0]
            course_name = i.string.strip()
            courses.append([x + 1, course_name, course_number])
        return courses


    def choose_course(self, courses):
        if self.args.course:
            course_number = str(courses[self.args.course - 1][2])
            print(DECOR + 'Alright, ', courses[self.args.course - 1][1])
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
            return self.choose_course(courses)


    def choose_folder(self):
        folder = os.path.expanduser("~") + FOLDER
        if self.args.folder:
            if '~' in self.args.folder:
                self.args.folder = os.path.expanduser(args.folder)
            if os.path.isdir(self.args.folder):
                folder = self.args.folder
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


    def create_nav_links_dictionary(self, soup):
        navigate_dict = {}
        nav_links = soup.find_all('li', attrs={"class": "nav-item"})
        for navigate_link in nav_links:
            if navigate_link.h5:
                nav_name = navigate_link.h5.text.strip()
                nav_number = navigate_link.a.get('aria-controls')
                navigate_dict[nav_number] = nav_name
        return navigate_dict


    def make_course_folder(self, courses, index, folder):
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


    def find_files_paths_and_links(self, navigation_dict, soup):
        file_tags = []
        for extension in EXTENSIONS:
            file_tags += soup.find_all('a', string=lambda text: text and f'.{extension}' in text)
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


    def download_from_dict(self, path_link_dict, folder):
        counter = 0
        for path, link, name in track(path_link_dict, description=f'{DECOR}Downloading...'):

            counter += 1
            count = f' ({counter}/{len(path_link_dict)})'

            # Sanitize the lecture name
            safe_name = re.sub(r'[\/:*?"<>|]', '_', name)

            if os.path.isfile(folder + path + safe_name):
                if self.args.verbose:
                    print('[ Already there! ] ' + safe_name + count)
                continue

            if not os.path.isdir(folder + path):
                os.makedirs(folder + path)

            response = self.session.get(link, headers=HEADERS, stream=True)
            with open(folder + path + safe_name, 'wb') as file:
                        file.write(response.content)
            print(DECOR + 'Downloaded ' + safe_name + count)
            Scraper.downloaded_count += 1

