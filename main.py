#!/usr/bin/python3

import datetime

import requests
from bs4 import BeautifulSoup
from cli import get_args
from config import *
from scraper import Scraper


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
