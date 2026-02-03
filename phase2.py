

# PHASE 2. Pull data for whole food and drink category
import requests
from bs4 import BeautifulSoup
import csv
import urllib.parse
import re

# Base URL for resolving relative links
BASE_URL = "http://books.toscrape.com/catalogue/"
CATEGORY_URL = "http://books.toscrape.com/catalogue/category/books/food-and-drink_33/index.html"

def get_book_data(book_url):
    """Phase 1 logic: Extracts details from a single product page."""
    response = requests.get(book_url)
    soup = BeautifulSoup(content := response.content, "html.parser")

    # Scrape Table Data (UPC, Price, Availability)
    info_table = {row.th.text: row.td.text for row in soup.find_all("tr")}

    # Scrape Description
    desc_tag = soup.find("div", id="product_description")
    description = desc_tag.find_next("p").text if desc_tag else ""

    # Scrape Rating 
    rating_tag = soup.find("p", class_="star-rating")
    rating = rating_tag['class'][1] if rating_tag else ""

    # Image URL
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
##get all the books in the page
def get_all_book_urls(category_url):
    """Navigates through pagination to find every book link in the category."""
    book_urls = []
    current_url = category_url

    while True:
        response = requests.get(current_url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all book links on the current page
        articles = soup.find_all("article", class_="product_pod")
        for article in articles:
            # Join relative link with the catalogue base
            relative_link = article.find("h3").a["href"].replace("../../../", "")
            full_link = BASE_URL + relative_link
            book_urls.append(full_link)

        # Look for the 'next' button
        next_button = soup.find("li", class_="next")
        if next_button:
            next_page_rel = next_button.a["href"]
            current_url = urllib.parse.urljoin(current_url, next_page_rel)
        else:
            break  # No more pages

    return book_urls

def main():
    print(f"Starting extraction for category: {CATEGORY_URL}")

    # 1. Get all URLs
    all_urls = get_all_book_urls(CATEGORY_URL)
    print(f"Found {len(all_urls)} books. Starting data extraction...")

    # 2. Extract data for each URL
    all_data = []
    for url in all_urls:
        print(f"Scraping: {url}")
        all_data.append(get_book_data(url))

    # 3. Write to CSV
    keys = all_data[0].keys()
    with open('food_and_drink_books.csv', 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_data)

    print("\nSuccess! Data saved to 'food_and_drink_books.csv'.")

if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()
