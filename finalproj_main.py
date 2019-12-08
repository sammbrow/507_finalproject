import json
import requests
from bs4 import BeautifulSoup as bs
import plotly
import csv
import plotly.graph_objs as go
import pandas as pd
from plotly.offline import plot
import random

import sqlite3

import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter

#Crawling the UXDesign Collective website.

#-- cache
CACHE_FNAME = 'finalproj_cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

#grapping top articles page source code
def get_top_page_source(url):
    # Obtained help from: https://michaeljsanders.com/2017/05/12/scrapin-and-scrollin.html to write code using selenium to scroll the page
    use_browser = webdriver.Chrome(ChromeDriverManager().install())
    use_browser.get(url)
    page_len = use_browser.execute_script(
    '''
    window.scrollTo(0, document.body.scrollHeight);
    var page_len=document.body.scrollHeight;
    return page_len;
    ''')
    loop_num = 0
    while(loop_num == 0):
        count = page_len
        time.sleep(3)
        page_len = use_browser.execute_script('''
        window.scrollTo(0, document.body.scrollHeight);
        var page_len=document.body.scrollHeight;
        return page_len;
        ''')
        if count == page_len:
            loop_num = 1
    return use_browser.page_source

# make request to the top articles page using the cache
def top_page_request_using_cache(url):
    if url in CACHE_DICTION:
        # print("Getting cached data...")
        return CACHE_DICTION[url]
    else:
        print("Making a request for new data...")
        resp = get_top_page_source(url)
        CACHE_DICTION[url] = resp
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION[url]

#get article data using cache
def scrape_articles_using_cache(url):
    if url in CACHE_DICTION:
        # print("Getting cached data...")
        return CACHE_DICTION[url]
    else:
        print("Making a request for new data...")
        resp = requests.get(url)
        CACHE_DICTION[url] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION[url]

#Scraping
#scrape the top page using the top page request cache function
def scrape_top_page():
    page_text = top_page_request_using_cache("https://uxdesign.cc/top/home")
    bs_output = bs(page_text, "html.parser")

    article_grouping = bs_output.find_all(class_="col u-xs-marginBottom10 u-paddingLeft0 u-paddingRight0 u-paddingTop15 u-marginBottom30")
    article_data_dict = {}
    article_data_list = []
    for item in article_grouping:
        #title
        title = item.find(class_="u-letterSpacingTight u-lineHeightTighter u-breakWord u-textOverflowEllipsis u-lineClamp3 u-fontSize24").text.replace("\xa0", " ")
        #author
        try:
            author = item.find(class_="ds-link ds-link--styleSubtle link link--darken link--accent u-accentColor--textNormal u-accentColor--textDarken").text
        except:
            article = article_data.append("No author")
        #date
        try:
            date = item.find("time").text
        except:
            date = "No date"
        #description
        try:
            descr = item.find(class_="u-contentSansThin u-lineHeightBaseSans u-fontSize24 u-xs-fontSize18 u-textColorNormal u-baseColor--textNormal").text.replace("\xa0", " ")
        except:
            descr = "No description"
        #url
        url = item.find("a")["href"]
        article_data_dict[title] = [author, date, descr, url]
        article_data_list.append([title, author, date, descr, url])
    return [article_data_dict, article_data_list]

#scrape each page for links usign the scrape article cache function
def scrape_page_for_links(url):
    page_text = scrape_articles_using_cache(url)
    bs_output = bs(page_text, "html.parser")

    article_body = bs_output.find("article")
    list = []

    try:
        for item in article_body:
            article_sections = item.find_all("section")
            for item in article_sections:
                a_s = item.find_all("a")
                for item in a_s:
                    if len((item.text).split()) > 2:
                        if "http" not in item['href']:
                            pass
                        else:
                            list.append([item.text, item['href']])
    except:
        list = ["No linked phrases"]

    return list

#collect the phrases using the scrape top pages function
def collect_for_phrases():
    scrape_top_page_ = scrape_top_page()
    articles_dict = scrape_top_page_[0]
    phrase_list = []
    phrase_dict = {}
    for item in articles_dict.values():
        linked_phrases_and_urls = scrape_page_for_links(item[3])
        title_ = ""
        for itm in linked_phrases_and_urls:
            for key, value in articles_dict.items():
                if value == item:
                    title_ = key
            phrase_dict[itm[0]] = [itm[1], title_, item[0], item[3]]
            phrase_list.append([itm[0], itm[1], title_, item[0], item[3]])

    return [phrase_dict, phrase_list]

#collect crawling results into variables
scrape_top_page_ = scrape_top_page()
collect_phrases = collect_for_phrases()

top_page_db_list = scrape_top_page_[1]
phrases_db_list = collect_phrases[1]

#build the DB

DBNAME = 'designcol_toparticles_phrases.db'

#initialize the database
def initialize_db():
    conn = sqlite3.connect(DBNAME)
    conn.execute("PRAGMA foreign_keys = 1")
    cur = conn.cursor()

    statement = '''
        DROP TABLE IF EXISTS 'Articles';
    '''
    cur.execute(statement)
    statement = '''
        DROP TABLE IF EXISTS 'Phrases';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        CREATE TABLE 'Articles' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Title' TEXT,
            'Author' TEXT,
            'Date' TEXT,
            'Description' TEXT,
            'URL' TEXT
        );
    '''
    cur.execute(statement)

    statement = '''
        CREATE TABLE 'Phrases' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Phrase' TEXT,
            'Phrase_URL' TEXT,
            'Source_Title' TEXT,
            'Source_Author' TEXT,
            'Source_URL' TEXT,
            FOREIGN KEY(Source_title, Source_Author, Source_URL) REFERENCES Articles(Title, Author, URL)
        );
    '''
    cur.execute(statement)

    conn.commit()
    conn.close()

#write data into database
def fill_db():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    global top_page_db_list
    global phrases_db_list

    for i in top_page_db_list:

        date_ = ""
        if len(i[2]) < 7:
            date_ = str(i[2]) + ", 2019"
        else:
            date_ = i[2]

        insertion = (None, i[0], i[1], date_, i[3], i[4])
        statement = 'INSERT INTO "Articles"'
        statement += 'VALUES (?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)
    conn.commit()

    for i in phrases_db_list:
        insertion = (None, i[0], i[1], i[2], i[3], i[4])
        statement = 'INSERT INTO "Phrases"'
        statement += 'VALUES (?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)
    conn.commit()

    conn.close()


#queries to fill flask pages with DB data

#pull top stories to display on first flask page
def top_stories_func():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement = []

    for item in cur.execute('''
    SELECT Title, Author, Date, Description, URL
    FROM Articles
    '''):
        statement.append(item)
    return statement

#pull phrases from top stories to display on phrases flask page
def phrases_func():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement2 = []

    for item in cur.execute('''
    SELECT Phrase, Phrase_URL, Source_Title, Source_Author, Source_URL
    FROM Phrases
    '''):
        statement2.append(item)

    return statement2

#top stories search results function

def top_stories_results_func(search_term):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement = []

    for item in cur.execute('''
    SELECT Title, Author, Date, Description, URL
    FROM Articles
    WHERE Title LIKE ''' + "'%" + search_term + "%'"
    '''
    OR Author LIKE ''' + "'%" + search_term + "%'" ):
        statement.append(item)

    if len(statement) == 0:
        statement.append("No Results")

    return statement

#phrases search results function

def phrases_results_func(search_term):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement = []

    for item in cur.execute('''
    SELECT Phrase, Phrase_URL, Source_Title, Source_Author, Source_URL
    FROM Phrases
    WHERE Phrase LIKE ''' + "'%" + search_term + "%'"
    '''
    OR Source_Title LIKE ''' + "'%" + search_term + "%'"
    '''
    OR Source_Author LIKE ''' + "'%" + search_term + "%'" ):
        statement.append(item)

    if len(statement) == 0:
        statement.append("No Results")

    return statement



#plot.ly - used plot.ly code samples to build visualizations

# 20 most common words used in all top article text in a word cloud - another crawl through text grabbing words, then filtering into a list/dictionary

def pull_text_from_articles():
    get_top_pages = scrape_top_page()
    articles_dict = get_top_pages[0]
    full_text = ""
    for item in articles_dict.values():
        page_text = scrape_articles_using_cache(item[3])
        bs_output = bs(page_text, "html.parser")
        article_body = bs_output.find("article")
        i = article_body.text
        full_text = full_text + i
    return full_text

#class to create instances of cleaned text
class text():
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return str(self.cleantext)

    def cleantext(self):
        #something to clean text of common words and nonsense
        top_article_pull = self.text
        top_article_text = ""
        for char in top_article_pull:
            if char not in string.punctuation:
                top_article_text += char
        common_words = set(stopwords.words('english'))
        tokenize = word_tokenize(top_article_text)
        cleaned_ = [word for word in tokenize if not word in common_words]
        cleaned_ = ""
        for word in tokenize:
            if word not in common_words and string.punctuation:
                cleaned_ += word + " "
        return cleaned_

#function to count most words in top articles text, returns 20 most used words
def countwords_highest():
    cleaned_text = (text(pull_text_from_articles()).cleantext().split())
    common_words = set(stopwords.words('english'))
    cleaned_char = []
    for item in cleaned_text:
        if len(item) > 4:
            cleaned_char.append(item)
        else:
            pass
    cleantext_dict = Counter(cleaned_char)
    twenty_ = cleantext_dict.most_common(20)

    words = []
    weights = []

    for tuple in twenty_:
        words.append(tuple[0])
        weights.append(tuple[1]/8)

    colors = [plotly.colors.DEFAULT_PLOTLY_COLORS[random.randrange(1, 10)] for i in range(30)]

    data = go.Scatter(x=[random.random() for i in range(20)],
                     y=[random.random() for i in range(20)],
                     mode='text',
                     text=words,
                     marker={'opacity': 0.3},
                     textfont={'size': weights,
                               'color': colors})
    layout = go.Layout({'xaxis': {'showgrid': False, 'showticklabels': False, 'zeroline': False},
                        'yaxis': {'showgrid': False, 'showticklabels': False, 'zeroline': False}})
    fig = go.Figure(data=[data], layout=layout)
    fig.show()
    return None

# see searched terms and number of times searched in pie chart
def terms_searched(terms_searched):
    highest = {}
    terms = terms_searched
    count_terms = Counter(terms)
    highest = count_terms.most_common()
    labels = []
    values = []
    for tuple in highest:
        labels.append(tuple[0])
        values.append(tuple[1])
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.show()
    return None

# number of linked phrases in each article in scatter plot
def linked_phrase_scatter():

    statement = []
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    for item in cur.execute('''
    SELECT COUNT(Phrase), Articles.Title
    FROM Articles
    JOIN Phrases
    ON Articles.Title = Phrases.Source_Title
    WHERE Articles.Title = Phrases.Source_Title
    GROUP BY Title
    '''):
        statement.append(item)
    conn.commit()
    conn.close()

    titles = []
    counts = []

    for tuple in statement:
        titles.append(tuple[1])
        counts.append(tuple[0])

    fig = go.Figure(data=go.Scatter(x=titles, y=counts, mode='markers', marker_color=counts, text=titles)) # hover text goes here

    fig.update_layout(title='Top Articles and The Number of Linked Phrases Within Them')
    fig.show()

    return None


#print module check
if __name__=="__main__":
    initialize_db()
    fill_db()
