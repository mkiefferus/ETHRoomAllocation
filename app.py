from flask import Flask, render_template
import schedule
import time

from scraper import scrape

app = Flask(__name__)


def do_scrape():
    scrape()

@app.route('/')
def home():
    return render_template('home.html')



if __name__ == '__main__':
    schedule.every(1).week.do(do_scrape)
    app.run(debug=True)