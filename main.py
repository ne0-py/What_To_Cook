from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from kivymd.uix.button import MDRectangleFlatIconButton
from kivy.lang import Builder
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from bs4 import BeautifulSoup
import requests
import sqlite3
import webbrowser
from functools import partial
import os


#Intialize sqlite3 database for storage
connect = sqlite3.connect('recipe.db')
c = connect.cursor()

try:
    c.execute('''CREATE TABLE recipes (
                title text,
                url   text
    )''')
except sqlite3.OperationalError:
    pass


#Simple function to apply BeautifulSoup to the provided URL
def soupify(url):

    result = requests.get(url)
    print(result.status_code)

    #Get source code of the website
    src = result.content

    #Soup-ify the source to be utilised for scraping
    soup = BeautifulSoup(src, 'lxml')

    return soup


#Soupify all the links we are going to use
bake = soupify('https://bakerbettie.com/')
veg = soupify('https://www.vegrecipesofindia.com/glossary/')


#Temporary storage, needs to be replaced with sqllite3 database
title_list = []
link_list = []
bakepage_list = []
data_tuple_list = []


def update():

    for z in range(len(title_list)):
        t = (title_list[z], link_list[z])

        if t not in data_tuple_list:
            data_tuple_list.append(t)

    c.executemany('INSERT INTO recipes VALUES (?, ?)', data_tuple_list)

    c.execute('SELECT * FROM recipes')

    #Commit our command
    connect.commit()


#Find the recipes from the veg recipes of india website
def find_veg(soup):

    listboxes = soup.find_all('div', class_ = 'glossary-section')

    for listbox in listboxes:
        titles = listbox.find_all('a')
        for title in titles:
            title_list.append(title.text)
        for link in titles:
            link_list.append(link.attrs['href'])
    
    update()


#Find the recipes from baker bettie website's current page
def baked(soup):

    cards = soup.find_all('h2', class_ = 'post-title')

    for card in cards:
        bs = card.find_all('a')
        for b in bs:
            link = b.attrs['href']
            if link not in link_list:
                link_list.append(link)

            title = b.text
            if title not in title_list:
                title_list.append(title)


#Initialize the baker bettie page list
pages = bake.find_all('a', class_ = 'page-numbers')

for page in pages:
    if page.attrs['href'] not in bakepage_list:
        bakepage_list.append(page.attrs['href'])

maxpage = int(''.join(filter(str.isdigit, bakepage_list[len(bakepage_list) - 1]))) + 1


#Change page function that takes the soup of the current page, finds all the page number links   
def changepage(soup, num):

        pages = soup.find_all('a', class_ = 'page-numbers')

        for page in pages:
            if page.attrs['href'] not in bakepage_list:
                bakepage_list.append(page.attrs['href'])

        souped = soupify(bakepage_list[num])

        return souped


#Main function that calls all the web scraping functions, this will be used to refresh the app
def find_bake():

    for x in range(68):
        current_page = changepage(bake, x)
        changepage(current_page, x)
        baked(current_page)
    
    update()


#Access the database to get all the data when the app first starts
def access():

    if os.path.isfile('D:/Python_Development/Scripts/recipe.db'):
        print('Database exists')
        pass
    else:
        print('Creating database...')
        find_veg(veg)
        find_bake()
        
    c.execute('SELECT * FROM recipes')
    data = c.fetchall()

    connect.commit()

    return data


#KivyMD UI elements and logic
class Main(Screen):
   
    @staticmethod
    def on_text_validate(sid, widget):

        if widget == 1 and sid == 1:
            #Build the external kv file to create UI elements
            root = Builder.load_file('cookapp.kv')
            #Create screeen that will be inserted in the menu
            screen_id = root.get_screen('main').ids.card_list
            data = access()
        else:
            sid.clear_widgets()
            root = None
            screen_id = sid
            search_text = '%' + str(widget.text) + '%'
            c.execute(f'SELECT * FROM recipes WHERE title LIKE "{search_text}"')
            data = c.fetchall()

        for s in data:
        
            card = MDCard(size_hint=(1, None), height='100dp')

            cardlayout = GridLayout(cols = 1, padding = (30, 10, 10, 20), spacing = (10, 10))

            label = MDLabel(text = str(s[0]).title())

            button = MDRectangleFlatIconButton(icon= 'web', text = 'OPEN', on_press= partial(webbrowser.open, s[1]))

            cardlayout.add_widget(label)
            cardlayout.add_widget(button)
            card.add_widget(cardlayout)
            screen_id.add_widget(card)

        return root, screen_id
                

sm = ScreenManager()
sm.add_widget(Main(name='main'))


class RecipeApp(MDApp):
    
    def build(self):

        #Set device main theme and accent color
        self.theme_cls.theme_style = 'Light'
        self.theme_cls.primary_palette = 'DeepPurple'

        root, sid = Main.on_text_validate(1, 1)

        return root     

#Run the app
RecipeApp().run()