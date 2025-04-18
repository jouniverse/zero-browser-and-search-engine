from flask import Flask, request, jsonify
from search import search
from filter import Filter
from storage import DBStorage
import html

app = Flask(__name__)

styles = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300..700&display=swap');

    /* Scrollbar styling */
    ::-webkit-scrollbar {
    width: 12px;
    }

    ::-webkit-scrollbar-track {
    background: #000000;
    }

    ::-webkit-scrollbar-thumb {
    background: #ffff00;
    border: 3px solid #000000;
    border-radius: 6px;
    }

    ::-webkit-scrollbar-thumb:hover {
    background: #000000;
    }

    body {
        font-family: 'Fira Code', monospace;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background-color: #000000;
        color: #FFFFFF;
    }

    .search-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
        gap: 20px;
    }

    .search-form {
        display: flex;
        gap: 10px;
        width: 100%;
        max-width: 600px;
    }

    input[type="text"] {
        flex: 1;
        padding: 12px 20px;
        font-family: 'Fira Code', monospace;
        font-size: 16px;
        border: 2px solid #00FFFF;
        border-radius: 25px;
        background: #000000;
        color: #FFFFFF;
        outline: none;
    }

    input[type="text"]:focus {
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
    }

    input[type="submit"] {
        padding: 12px 30px;
        font-family: 'Fira Code', monospace;
        font-size: 16px;
        background-color: #FFFF00;
        color: #000000;
        border: none;
        border-radius: 25px;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    input[type="submit"]:hover {
        background-color: #00FFFF;
    }

    .site {
        font-size: 14px;
        color: #00FFFF;
        margin-bottom: 5px;
    }
    
    .snippet {
        font-size: 14px;
        color: #CCCCCC;
        margin-bottom: 30px;
        line-height: 1.5;
    }
    
    .rel-button {
        cursor: pointer;
        color: #FFFF00;
        margin-left: 10px;
        transition: color 0.3s ease;
    }

    .rel-button:hover {
        color: #00FFFF;
    }

    a {
        color: #FFFFFF;
        text-decoration: none;
        font-size: 18px;
        font-weight: 500;
        display: block;
        margin: 10px 0;
    }

    a:hover {
        color: #FFFF00;
    }

    .results-container {
        margin-top: 40px;
    }

    .loader-container {
        display: none;
        justify-content: center;
        margin: 40px 0;
        text-align: center;
    }

    .loader {
        color: #FFFF00;
        font-size: 18px;
        display: block;
    }
</style>
<script>
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('.search-form');
    const loaderContainer = document.querySelector('.loader-container');
    const resultsContainer = document.querySelector('.results-container');
    const loader = document.querySelector('.loader');

    // Create the loading text
    if (loader) {
        loader.textContent = 'Fetching search results...';
    }

    if (searchForm) {
        searchForm.addEventListener('submit', function() {
            if (loaderContainer) {
                loaderContainer.style.display = 'flex';
            }
            if (resultsContainer) {
                resultsContainer.style.display = 'none';
            }
        });
    }
});

const relevant = function(query, link){
    fetch("/relevant", {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
           "query": query,
           "link": link
          })
        });
}
</script>
"""

search_template = (
    styles
    + """
    <title>ZERO Search</title>
    <div class="search-container">
        <form action="/" method="post" class="search-form">
            <input type="text" name="query" placeholder="Search...">
            <input type="submit" value="Search">
        </form>
    </div>
    <div class="loader-container">
        <div class="loader"></div>
    </div>
    """
)

result_template = """
<div class="results-container">
    <p class="site">{rank}: {link} <span class="rel-button" onclick='relevant("{query}", "{link}");'>Relevant</span></p>
    <a href="{link}">{title}</a>
    <p class="snippet">{snippet}</p>
</div>
"""


def show_search_form():
    """
    Return the search form HTML.
    """
    return search_template


def run_search(query):
    """
    Run the search and return the results.
    """
    results = search(query)
    fi = Filter(results)
    filtered = fi.filter()
    rendered = search_template
    filtered["snippet"] = filtered["snippet"].apply(lambda x: html.escape(x))
    for index, row in filtered.iterrows():
        rendered += result_template.format(**row)
    return rendered


@app.route("/", methods=["GET", "POST"])
def search_form():
    """
    Handle the root route for the app. If the request is a POST,
    pull the query out of the form and run the search. If the
    request is a GET, show the search form.
    """

    if request.method == "POST":
        query = request.form["query"]
        return run_search(query)
    else:
        return show_search_form()


@app.route("/relevant", methods=["POST"])
def mark_relevant():
    """
    Mark a link as relevant for a given query.

    This endpoint receives a POST request with JSON data containing a
    search query and a link. It updates the relevance score of the link
    for the specified query in the database.

    Request JSON format:
    {
        "query": "<search_query>",
        "link": "<link_url>"
    }

    Returns:
        JSON response indicating success.
    """

    data = request.get_json()
    query = data["query"]
    link = data["link"]
    storage = DBStorage()
    storage.update_relevance(query, link, 10)
    return jsonify(success=True)
