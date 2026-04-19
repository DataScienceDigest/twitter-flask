from flask import Flask, render_template, request
from scrapers import run_all_scrapers
from gemini import process_links

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Step 1: Run all scrapers → get links + portal brains content
        links, portal_brains = run_all_scrapers()

        # Step 2: Send links + portal brains to Gemini → get parsed result
        result = process_links(links, portal_brains)
        # Step 3: Render result page
        return render_template("result.html", result=result, links=links, portal_brains=portal_brains)

    # GET → show the home page with Run button
    return render_template("result.html", result=None, links=None, portal_brains=None)


if __name__ == "__main__":
    app.run(debug=True)