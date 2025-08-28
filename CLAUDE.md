# Project Information

This is Nikola based setup to manage blog under feeds.code-drill.eu.

this project uses content from http://127.0.0.1:8000/daily-items.csv (data for any day are available under: http://127.0.0.1:8000/daily-items/<YYYY-MM-DD>.csv) 
in script generate_blog_posts.py to create data for hugo static page generator to create simple web page being listing of the articles for a given day, 
having categories selection and sources like here: http://127.0.0.1:8000 (ignore search, page per page and auto refresh), sources should be based on source name from csv data, 
also whole page should have only list view, entries on list pages should be links to original articles

## Management Commands

#### build blog
use `cd feeds.code-drill.eu && nikola build`

