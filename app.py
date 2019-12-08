from flask import Flask, render_template, request, g, redirect
import finalproj_main as _data_
import sqlite3

app = Flask(__name__)

search_terms_so_far = []

conn = sqlite3.connect(_data_.DBNAME)
cur = conn.cursor()

@app.route('/', methods=['GET', 'POST'])
def top_stories():
    statement = _data_.top_stories_func()
    return render_template("top_stories.html", statement = statement)

@app.route('/phrases', methods=['GET', 'POST'])
def phrases():
    statement2 = _data_.phrases_func()
    return render_template("phrases.html", statement2=statement2)

@app.route('/search')
def search():
    return render_template("search.html")

@app.route('/20words')
def twentywords():
    _data_.countwords_highest()
    return redirect('/')

@app.route('/searchterms')
def searchterms():
    _data_.terms_searched(search_terms_so_far)
    return redirect('/results')

@app.route('/phrasescatter')
def phrase_scatter():
    _data_.linked_phrase_scatter()
    return redirect("/")

@app.route('/process_search', methods=['POST'])
def process_search():
    global search_terms_so_far
    search_term_ = request.form["search"]
    search_terms_so_far.append(search_term_)
    return redirect('/results')

@app.route('/results', methods=["GET", "POST"])
def results():
    global search_terms_so_far
    search_term = search_terms_so_far[-1]
    statement = _data_.top_stories_results_func(search_term)
    return render_template("results.html", statement = statement, search_term=search_term)

@app.route('/phraseresults', methods=["GET", "POST"])
def phrase_results():
    global search_terms_so_far
    search_term = search_terms_so_far[-1]
    statement = _data_.phrases_results_func(search_term)
    return render_template("phraseresults.html", statement = statement, search_term = search_term)

conn.commit()
conn.close()

if __name__ == '__main__':
    app.run(debug=True)
