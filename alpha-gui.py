#!/usr/bin/python3

from bs4 import BeautifulSoup
from rich.progress import track
import requests
import re
import os

# Imports for the Gui
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk


# Constants
DECOR = ' ::'
FOLDER = '/dox/med'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Categories data
categories = {
    'Athar': 'https://msc-mu.com/level/17',
    'Rou7': 'https://msc-mu.com/level/16',
    'Wateen': 'https://msc-mu.com/level/15',
    'Nabed': 'https://msc-mu.com/level/14',
    'Wareed': 'https://msc-mu.com/level/13',
    'Minors': 'https://msc-mu.com/level/10',
    'Majors': 'https://msc-mu.com/level/9'
}

# Functions
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
    for path, link, name in track(path_link_dict, description=f'{DECOR} Downloading...'):

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
        print(DECOR + ' Downloaded ' + name + count)

def update_courses_menu(*args):
    category_name = category_var.get()
    if category_name == "Select a category":
        return

    category_url = categories[category_name]
    
    try:
        courses = find_courses(category_url)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch courses: {e}")
        return

    course_var.set("Select a course")
    menu = course_menu['menu']
    menu.delete(0, 'end')

    for idx, course in enumerate(courses):
        menu.add_command(label=course[1], command=ctk._setit(course_var, course[1]))

def start_download():
    category_name = category_var.get()
    course_name = course_var.get()
    folder = folder_var.get()

    if category_name == "Select a category":
        messagebox.showerror("Error", "Please select a category.")
        return

    if course_name == "Select a course":
        messagebox.showerror("Error", "Please select a course.")
        return

    if not folder:
        messagebox.showerror("Error", "Please select a destination folder.")
        return

    category_url = categories[category_name]
    try:
        courses = find_courses(category_url)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch courses: {e}")
        return
    
    course_number = next(course[2] for course in courses if course[1] == course_name)
    folder = make_course_folder(courses, course_number, folder)
    download_url = 'https://msc-mu.com/courses/' + course_number

    try:
        print(DECOR + ' Requesting page...')
        course_page = requests.get(download_url, headers=HEADERS)
        print(DECOR + ' Parsing page into a soup...')
        soup = BeautifulSoup(course_page.text, 'html.parser')
        nav_dict = create_nav_links_dictionary(soup)
        file_dict = find_files_paths_and_links(nav_dict, soup)
        download_from_dict(file_dict, folder)
        messagebox.showinfo("Success", "Download complete!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


#theme 
ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
ctk.set_default_color_theme("green")  # Themes: blue (default), dark-blue, green
# GUI Setup
root = ctk.CTk()
root.title("MSC-MU Lecture Downloader")

# Category selection
ctk.CTkLabel(root, text="Select Category:").grid(row=0, column=0, padx=10, pady=10)
category_var = ctk.StringVar(value="Select a category")
category_menu = ctk.CTkOptionMenu(root,values=list(categories.keys()),variable = category_var,command=update_courses_menu)
category_menu.grid(row=0, column=2, padx=10, pady=10)
category_var.trace('w', update_courses_menu)

# Course selection
ctk.CTkLabel(root, text="Select Course:").grid(row=1, column=0, padx=10, pady=10)
course_var = ctk.StringVar(value="Select a course")
course_menu = ctk.CTkOptionMenu(root,variable=course_var,values=["Select a category first"])
course_menu.grid(row=1, column=2, padx=10, pady=10)

# Folder selection
ctk.CTkLabel(root, text="Select Destination Folder:").grid(row=2, column=0, padx=10, pady=10)
folder_var = ctk.StringVar()
folder_entry = ctk.CTkEntry(root, textvariable=folder_var, width=50)
folder_entry.grid(row=2, column=1, padx=10, pady=10)
ctk.CTkButton(root, text="Browse...", command=lambda: folder_var.set(filedialog.askdirectory())).grid(row=2, column=2, padx=10, pady=10)

# Download button
ctk.CTkButton(root, text="Download", command=start_download).grid(row=3, column=2, padx=10, pady=10)

root.mainloop()


