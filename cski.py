#!/usr/bin/python3

from bs4 import BeautifulSoup
import requests
import re
import os
import customtkinter as ctk
from tkinter import messagebox, filedialog, Listbox, Toplevel
import threading
import json

# Constants
DECOR = ' ::'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
STATE_FILE = "app_state.json"

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

# Load and save application state
def load_state():
    global favorites, dark_mode, download_progress
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as file:
            state = json.load(file)
            favorites = state.get("favorites", [])
            dark_mode = state.get("dark_mode", False)
            download_progress = state.get("download_progress", {})
    else:
        favorites = []
        dark_mode = False
        download_progress = {}

def save_state():
    with open(STATE_FILE, 'w') as file:
        state = {
            "favorites": favorites,
            "dark_mode": dark_mode,
            "download_progress": download_progress
        }
        json.dump(state, file)

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

def make_course_folder(folder, course_name):
    new_folder = os.path.join(folder, course_name)
    if not os.path.isdir(new_folder):
        os.mkdir(new_folder)
    return new_folder

def find_files_paths_and_links(navigation_dict, soup, file_types):
    file_tags = []
    for file_type in file_types:
        file_tags.extend(soup.find_all('a', string=lambda text: text and file_type in text))
    
    files_list = []
    path = []
    associated_nav_link_id = ''
    for file_tag in file_tags:
        current_tag = file_tag
        if not current_tag:
            print('No files found for the selected extensions!')
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

def download_from_dict(path_link_dict, folder, progress_bar):
    counter = 0
    total_files = len(path_link_dict)
    
    for path, link, name in path_link_dict:
        counter += 1
        count = f' ({counter}/{total_files})'
        full_path = os.path.join(folder, path)
        
        if os.path.isfile(os.path.join(full_path, name)):
            print('[ Already there! ] ' + name + count)
            already_downloaded_listbox.insert("end", name)
            continue

        if not os.path.isdir(full_path):
            os.makedirs(full_path)

        response = requests.get(link, headers=HEADERS)
        with open(os.path.join(full_path, name), 'wb') as file:
            file.write(response.content)
        print(DECOR + ' Downloaded ' + name + count)
        downloading_listbox.insert("end", name)
        
        # Update the progress bar
        progress = counter / total_files
        progress_bar.set(progress)

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
    course_menu.configure(values=[course[1] for course in courses])

def start_download():
    category_name = category_var.get()
    course_name = course_var.get()
    folder = folder_var.get()

    selected_file_types = []
    if pdf_var.get():
        selected_file_types.append('.pdf')
    if ppt_var.get():
        selected_file_types.append('.ppt')

    if category_name == "Select a category":
        messagebox.showerror("Error", "Please select a category.")
        return

    if course_name == "Select a course":
        messagebox.showerror("Error", "Please select a course.")
        return

    if not folder:
        messagebox.showerror("Error", "Please select a destination folder.")
        return

    if not selected_file_types:
        messagebox.showerror("Error", "Please select at least one file type to download.")
        return

    category_url = categories[category_name]
    try:
        courses = find_courses(category_url)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch courses: {e}")
        return
    
    course_number = next(course[2] for course in courses if course[1] == course_name)
    download_folder = make_course_folder(folder, course_name)
    download_url = 'https://msc-mu.com/courses/' + course_number

    def download_thread():
        try:
            print(DECOR + ' Requesting page...')
            course_page = requests.get(download_url, headers=HEADERS)
            print(DECOR + ' Parsing page into a soup...')
            soup = BeautifulSoup(course_page.text, 'html.parser')
            nav_dict = create_nav_links_dictionary(soup)
            file_dict = find_files_paths_and_links(nav_dict, soup, selected_file_types)
            
            progress_bar.grid(row=8, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
            download_from_dict(file_dict, download_folder, progress_bar)
            progress_bar.grid_remove()  # Remove progress bar after download completes
            messagebox.showinfo("Success", "Download complete!")
        except Exception as e:
            progress_bar.grid_remove()  # Ensure progress bar is removed on error
            messagebox.showerror("Error", f"An error occurred: {e}")

    # Start download thread
    threading.Thread(target=download_thread).start()

def add_to_favorites():
    category_name = category_var.get()
    course_name = course_var.get()
    folder = folder_var.get()

    if category_name == "Select a category" or course_name == "Select a course" or not folder:
        messagebox.showerror("Error", "Please select a category, course, and folder before adding to favorites.")
        return
    
    favorites.append({
        "category": category_name,
        "course": course_name,
        "folder": folder
    })
    save_state()
    update_favorites_menu()
    messagebox.showinfo("Success", f"Added {course_name} to favorites!")

def remove_from_favorites():
    selected_favorite = favorites_var.get()
    if selected_favorite == "Select a favorite":
        messagebox.showerror("Error", "Please select a favorite to remove.")
        return
    
    favorite_parts = selected_favorite.split(" -> ")
    category_name, course_name, folder = favorite_parts[0], favorite_parts[1], favorite_parts[2]

    for favorite in favorites:
        if favorite["category"] == category_name and favorite["course"] == course_name and favorite["folder"] == folder:
            favorites.remove(favorite)
            save_state()
            update_favorites_menu()
            messagebox.showinfo("Success", f"Removed {course_name} from favorites!")
            return

def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    ctk.set_appearance_mode("Dark" if dark_mode else "Light")
    save_state()

def update_favorites_menu():
    favorites_menu.configure(values=["{} -> {} -> {}".format(fav["category"], fav["course"], fav["folder"]) for fav in favorites])
    favorites_var.set("Select a favorite")

def on_favorite_selected(*args):
    selected_favorite = favorites_var.get()
    if selected_favorite == "Select a favorite":
        return

    favorite_parts = selected_favorite.split(" -> ")
    category_name, course_name, folder = favorite_parts[0], favorite_parts[1], favorite_parts[2]

    category_var.set(category_name)
    update_courses_menu()
    course_var.set(course_name)
    folder_var.set(folder)

def update_download_listboxes():
    downloading_listbox.delete(0, "end")
    already_downloaded_listbox.delete(0, "end")

    for path, files in download_progress.items():
        for file in files:
            if os.path.isfile(os.path.join(path, file)):
                already_downloaded_listbox.insert("end", file)
            else:
                downloading_listbox.insert("end", file)

# GUI Setup
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("MSC-MU Lecture Downloader")

# Configure grid layout
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(10, weight=1)

# Category selection
ctk.CTkLabel(root, text="Select Category:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
category_var = ctk.StringVar(value="Select a category")
category_menu = ctk.CTkOptionMenu(root, variable=category_var, values=list(categories.keys()))
category_menu.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
category_var.trace('w', update_courses_menu)

# Course selection
ctk.CTkLabel(root, text="Select Course:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
course_var = ctk.StringVar(value="Select a course")
course_menu = ctk.CTkOptionMenu(root, variable=course_var, values=["Select a category first"])
course_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

# Folder selection
ctk.CTkLabel(root, text="Select Destination Folder:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
folder_var = ctk.StringVar()
folder_entry = ctk.CTkEntry(root, textvariable=folder_var, width=50)
folder_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
ctk.CTkButton(root, text="Browse...", command=lambda: folder_var.set(filedialog.askdirectory())).grid(row=2, column=2, padx=10, pady=5, sticky="ew")

# File type selection
ctk.CTkLabel(root, text="Select File Types:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
pdf_var = ctk.BooleanVar()
ppt_var = ctk.BooleanVar()
ctk.CTkCheckBox(root, text=".pdf", variable=pdf_var).grid(row=3, column=1, padx=10, pady=5, sticky="w")
ctk.CTkCheckBox(root, text=".ppt", variable=ppt_var).grid(row=3, column=2, padx=10, pady=5, sticky="w")

# Favorites menu
ctk.CTkLabel(root, text="Favorites:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
favorites_var = ctk.StringVar(value="Select a favorite")
favorites_menu = ctk.CTkOptionMenu(root, variable=favorites_var, values=[])
favorites_menu.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
favorites_var.trace('w', on_favorite_selected)

# Add and remove favorites buttons
ctk.CTkButton(root, text="Add to Favorites", command=add_to_favorites).grid(row=5, column=0, padx=10, pady=5, sticky="ew")
ctk.CTkButton(root, text="Remove from Favorites", command=remove_from_favorites).grid(row=5, column=1, padx=10, pady=5, sticky="ew")

# Current downloads
ctk.CTkLabel(root, text="Current Downloads:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
downloading_listbox = Listbox(root)
downloading_listbox.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

# Already downloaded
ctk.CTkLabel(root, text="Already Downloaded:").grid(row=7, column=0, padx=10, pady=5, sticky="w")
already_downloaded_listbox = Listbox(root)
already_downloaded_listbox.grid(row=7, column=1, padx=10, pady=5, sticky="ew")

# Start download button
ctk.CTkButton(root, text="Start Download", command=start_download).grid(row=8, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

# Progress bar
progress_bar = ctk.CTkProgressBar(root)
progress_bar.grid_remove()  # Hide progress bar initially

# Dark mode toggle
ctk.CTkButton(root, text="Toggle Dark Mode", command=toggle_dark_mode).grid(row=9, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

load_state()
update_download_listboxes()
update_favorites_menu()
root.mainloop()
