import requests
from bs4 import BeautifulSoup
import re
from os import listdir, path, makedirs
import shutil

BASE_URL = "https://satisfactory.fandom.com"
BASE_CAT = "/wiki/Category:Icons"
BASE_DIR = "./icons"


def scrape():
    scrape_category(BASE_CAT, BASE_DIR)


def download_file(url, path):
    with requests.get(url, stream=True) as r:
        with open(path, "wb") as f:
            shutil.copyfileobj(r.raw, f)


def get_subcategory(soup):
    return {
        anchor.text.split(" ", 1)[0]: anchor.get("href")
        for anchor in soup.find_all("a", attrs={"class": "CategoryTreeLabel"})
    }


def get_icons(soup):
    urls = [
        li.findChildren("img")[0].get("src").partition("/revision")[0]
        for li in soup.find_all("li", attrs={"class": "gallerybox"})
    ]

    return {url.rsplit("/")[-1]: url for url in urls}


def scrape_category(cat, dir):
    print(f"Scraping {cat}")
    makedirs(dir, exist_ok=True)
    r = requests.get(BASE_URL + cat)
    if r.status_code != 200:
        raise RuntimeError(
            f"Scrape: {cat} returned non-zero error code {r.status_code}"
        )
    soup = BeautifulSoup(r.text, "html.parser")
    files = set(f for f in listdir(dir) if path.isfile(path.join(dir, f)))
    icons = get_icons(soup)
    for icon, url in icons.items():
        if icon in files:
            print(f" -- Skip {icon}")
        else:
            print(f" -- Get  {icon}")
            download_file(url, path.join(dir, icon))

    subcats = get_subcategory(soup)
    for name, subcat in subcats.items():
        scrape_category(subcat, path.join(dir, name))


scrape()
