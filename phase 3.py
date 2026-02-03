
# Phase 3. Extract all categories
import requests
from bs4 import BeautifulSoup
import csv
import urllib.parse
import os

# Base URL for the entire site
BASE_SITE_URL = "http://books.toscrape.com/index.html"
CATALOGUE_PREFIX = "http://books.toscrape.com/catalogue/"

def get_categories():
    """Extracts all category names and their URLs from the homepage sidebar."""
    response = requests.get(BASE_SITE_URL)
    soup = BeautifulSoup(response.content, "html.parser")

    categories = {}
    # The sidebar is usually in a div with class 'side_categories'
    category_list = soup.find("div", class_="side_categories").ul.find("ul")
    links = category_list.find_all("a")

    for link in links:
        cat_name = link.text.strip()
        # Resolve the relative URL
        cat_url = urllib.parse.urljoin(BASE_SITE_URL, link['href'])
        categories[cat_name] = cat_url

    return categories

def get_book_data(book_url):
    """Phase 1: Extracts details from a single product page."""
    try:
        response = requests.get(book_url)
        soup = BeautifulSoup(response.content, "html.parser")

        info_table = {row.th.text: row.td.text for row in soup.find_all("tr")}
        desc_tag = soup.find("div", id="product_description")
        description = desc_tag.find_next("p").text if desc_tag else ""
        rating_tag = soup.find("p", class_="star-rating")
        rating = rating_tag['class'][1] if rating_tag else ""
        img_tag = soup.find("img")
        image_url = urllib.parse.urljoin(book_url, img_tag['src'])

        return {
            "product_page_url": book_url,
            "universal_product_code": info_table.get("UPC"),
            "title": soup.find("h1").text,
            "price_including_tax": info_table.get("Price (incl. tax)"),
            "price_excluding_tax": info_table.get("Price (excl. tax)"),
            "number_available": info_table.get("Availability"),
            "product_description": description,
            "category": soup.find("ul", class_="breadcrumb").find_all("li")[2].text.strip(),
            "review_rating": rating,
            "image_url": image_url
        }
    except Exception as e:
        print(f"Error scraping {book_url}: {e}")
        return None

def get_category_books(category_url):
    """Phase 2: Navigates pagination within a single category."""
    book_urls = []
    current_url = category_url

    while True:
        response = requests.get(current_url)
        soup = BeautifulSoup(response.content, "html.parser")

        articles = soup.find_all("article", class_="product_pod")
        for article in articles:
            rel_link = article.find("h3").a["href"].replace("../../../", "")
            book_urls.append(CATALOGUE_PREFIX + rel_link)

        next_button = soup.find("li", class_="next")
        if next_button:
            next_page_rel = next_button.a["href"]
            current_url = urllib.parse.urljoin(current_url, next_page_rel)
        else:
            break
    return book_urls

def main():
    # 1. Setup storage
    if not os.path.exists("scraped_data"):
        os.makedirs("scraped_data")

    # 2. Get all categories
    print("Fetching categories...")
    categories = get_categories()
    print(f"Found {len(categories)} categories.")

    # 3. Iterate through each category
    for cat_name, cat_url in categories.items():
        print(f"\nProcessing Category: {cat_name}")

        # Get all book URLs for this specific category
        book_urls = get_category_books(cat_url)
        category_data = []

        for url in book_urls:
            data = get_book_data(url)
            if data:
                category_data.append(data)

        # 4. Save to a CSV named after the category
        filename = f"scraped_data/{cat_name.replace(' ', '_').lower()}.csv"

        if category_data:
            keys = category_data[0].keys()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(category_data)
            print(f"Saved {len(category_data)} books to {filename}")

if __name__ == "__main__":
    main()
