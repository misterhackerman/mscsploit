#!/usr/bin/python3
import argparse
import datetime
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from fake_useragent import FakeUserAgent
from tqdm import tqdm

ua = FakeUserAgent()

FOLDER = os.path.expanduser("~") + '/dox/med'
HEADERS  = {
            "User-Agent": ua.random,
            "Accept-Encoding": "identity"
        }
DECOR = ' \033[34;1m::\033[0m '
EXTENSIONS = ["pdf", "ppt", "doc"]


def get_args():
    parser = argparse.ArgumentParser(
            description='API to download lectures off msc-mu.com')
    parser.add_argument(
            '-t', '--category', type=int, metavar='', help='to specify category number'
            )
    parser.add_argument(
            '-c', '--course', type=int, metavar='', help='to specify course number'
            )
    parser.add_argument(
            '-f', '--folder', type=str, metavar='', help='to specify destination folder'
            )
    parser.add_argument(
            '-d', '--default-folder', action='store_true', help='Use default folder'
            )
    parser.add_argument(
            '-v', '--verbose', action='store_true', help='Increase Verbosity'
            )
    return parser.parse_args()




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
        except Exception:
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
        except Exception:
            print('\n' + DECOR + 'Invalid Input\n')
            return self.choose_course(courses)


    def choose_folder(self):
        folder = FOLDER
        # TODO let the system figure out the directory.
        if self.args.folder or self.args.default_folder:
            if not self.args.default_folder:
                folder = self.args.folder

            if '~' in folder:
                folder = os.path.expanduser(folder)
            if not folder[-1] == os.path.sep:
                folder = folder + os.path.sep
            if os.path.isdir(folder):
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
        # Replace any invalid characters with an underscore ( Sanitize course name )
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
                # TODO fix this print to include all EXTENSIONS
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


    def _download_single_file(self, data):
            path, link, name, folder = data
            safe_name = re.sub(r'[\/:*?"<>|]', '_', name)
            full_path = os.path.join(folder, path)
            file_location = os.path.join(full_path, safe_name)

            if os.path.isfile(file_location):
                return # Skip existing

            if not os.path.isdir(full_path):
                os.makedirs(full_path, exist_ok=True)

            try:
                with self.session.get(link, headers=HEADERS, stream=True) as r:
                    total_size = int(r.headers.get("content-length", 0))
                    with tqdm(total=total_size, unit="B", unit_scale=True,
                             desc=f"{safe_name:14.14}", leave=False, ascii='-#', ncols=86) as file_bar:

                        with open(file_location, 'wb') as file:
                            for chunk in r.iter_content(chunk_size=128 * 1024):
                                file.write(chunk)
                                file_bar.update(len(chunk))

                Scraper.downloaded_count += 1

            except Exception as e:
                # Using tqdm.write prevents breaking the progress bars
                tqdm.write(f"Error on {safe_name}: {e}")



    def download_from_dict(self, path_link_dict, folder):
            print(DECOR + "Starting threaded download...")
            tasks = [(path, link, name, folder) for path, link, name in path_link_dict]

            # 1. Start executor manually (No 'with' statement)
            executor = ThreadPoolExecutor(max_workers=5)
            futures = [executor.submit(self._download_single_file, t) for t in tasks]

            try:
                # 2. Process downloads
                with tqdm(total=len(tasks), desc="Total Progress", position=0, ncols=86, ascii='-#') as overall_bar:
                    for _ in as_completed(futures):
                        overall_bar.update(1)

            except KeyboardInterrupt:
                # 3. Force kill threads immediately on Ctrl+C
                print('\n' + DECOR + 'Stopping threads...')
                executor.shutdown(wait=False)
                raise # Re-raise error so the main block handles the exit

            # 4. Normal cleanup if no error
            executor.shutdown(wait=True)
def main():
    # main function should use the scraper class
    start = datetime.datetime.now()
    folder = scraper.choose_folder()
    print(DECOR + f"Choosen folder: {folder}")
    category_url = scraper.choose_category()
    courses = scraper.find_courses(category_url)
    course_number = scraper.choose_course(courses)
    folder = scraper.make_course_folder(courses, course_number, folder)
    download_url = 'https://msc-mu.com/courses/' + course_number
    print(DECOR + 'Requesting page...')
    course_page = scraper.session.get(download_url, headers=HEADERS)
    print(DECOR + 'Parsing page into a soup...')
    print(DECOR + f"I'll download {EXTENSIONS} files.")
    soup = BeautifulSoup(course_page.text, 'html.parser')

    nav_dict = scraper.create_nav_links_dictionary(soup)
    file_dict = scraper.find_files_paths_and_links(nav_dict, soup)
    scraper.download_from_dict(file_dict, folder)
    print('\n\n' + DECOR + 'Done...')
    print(DECOR + 'Downloaded ' + str(Scraper.downloaded_count) + ' files.')
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
        scraper = Scraper(get_args())
        main()
    except KeyboardInterrupt:
        print('\n' + DECOR + 'KeyboardInterrupt')
        print(DECOR + 'Downloaded ' + str(Scraper.downloaded_count) + ' files.')
        print(DECOR + 'Good bye!')
        quit()
