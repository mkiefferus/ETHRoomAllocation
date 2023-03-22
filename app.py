from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler

from scraper import scrape

app = Flask(__name__)

scraper_scheduler = BackgroundScheduler()


def do_scrape():
    scrape()

@app.route('/')
def home():
    return render_template('./templates/home.html')



if __name__ == '__main__':
    scraper_scheduler.start()
    scraper_scheduler.add_job(do_scrape, 'interval', weeks=1)
    app.run(debug=True)