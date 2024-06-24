#!/usr/bin/python
import scraper
from scraper import *


def main():
    # main function should use the scraper class
    start = datetime.datetime.now()
    folder = scraper.choose_folder()
    category_url = scraper.choose_category()
    courses = scraper.find_courses(category_url)
    course_number = scraper.choose_course(courses)
    folder = scraper.make_course_folder(courses, course_number, folder)
    download_url = 'https://msc-mu.com/courses/' + course_number
    print(DECOR + 'Requesting page...')
    course_page = s.get(download_url, headers=HEADERS)
    print(DECOR + 'Parsing page into a soup...')
    soup = BeautifulSoup(course_page.text, 'html.parser')

    nav_dict = scraper.create_nav_links_dictionary(soup)
    file_dict = scraper.find_files_paths_and_links(nav_dict, soup)
    downloaded_count = scraper.download_from_dict(file_dict, folder)
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
        scraper = Scraper()
        main()
    except KeyboardInterrupt:
        print('\n' + DECOR + 'KeyboardInterrupt')
        if 'downloaded_count' in globals():
            print(DECOR + 'Downloaded ' + str(downloaded_count) + ' files.')
        print(DECOR + 'Good bye!')
        quit()
