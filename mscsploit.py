#!/usr/bin/python3

from bs4 import BeautifulSoup
import requests

HEADERS = headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }


download_url = 'https://msc-mu.com/courses/113'
course_page = requests.get(download_url, headers=HEADERS)
soup = BeautifulSoup(course_page.text, 'html.parser')


def create_nav_links_dictionary():
    nav_dict = {}
    nav_links = soup.find_all('li', attrs={"class": "nav-item"})
    for nav_link in nav_links:
        if nav_link.h5:
            nav_name = nav_link.h5.text.strip()
            nav_number = nav_link.a.get('aria-controls')
            nav_dict[nav_number] = nav_name
    return nav_dict


def find_files_paths_and_links(navigation_dict):
    file_tags = soup.find_all('a', string=lambda text: text and '.pdf' in text) + soup.find_all('a', string=lambda text: text and '.pptx' in text)
    files_dictionary = {}
    path = []
    associated_nav_link_id = ''
    for file_tag in file_tags:
        current_tag = file_tag
        if not current_tag:
            print('no pdf files!')
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
        path.append(file_tag.text)
        file_path = "/".join(path)
        path.clear()

        file_link = file_tag.get('href')
        files_dictionary[file_path] = file_link
    return files_dictionary


def download_from_dict(path_link_dict):
    for path in path_link_dict:
        response = requests.get(path_link_dict[path], headers=HEADERS)
        with open(path, 'wb') as file:
            file.write(response.content)
        print('[*] Downloaded ' + path)


if __name__ == '__main__':
    dictionary = create_nav_links_dictionary()
    find_files_paths_and_links(dictionary)
