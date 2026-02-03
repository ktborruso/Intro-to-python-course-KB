

# Phase 4. Pull all images
import requests
from bs4 import BeautifulSoup
import csv
import urllib.parse
import os
import re

# Base URLs
BASE_SITE_URL = "http://books.toscrape.com/index.html"
CATALOGUE_PREFIX = "http://books.toscrape.com/catalogue/"

def slugify(text):
    """Converts titles into filesystem-safe filenames."""
    return re.sub(r'[^\w\s-]', '', text).strip().lower().replace(' ', '_')

def download_image(img_url, category_name, book_title):
    """Downloads an image and saves it in a category-specific folder."""
    # Create category image directory
    img_dir = f"scraped_data/images/{slugify(category_name)}"
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    # Define file path
    filename = f"{slugify(book_title)}.jpg"
    path = os.path.join(img_dir, filename)

    # Download and save
    try:
        img_data = requests.get(img_url).content
        with open(path, 'wb') as handler:
            handler.write(img_data)
    except Exception as e:
        print(f"Failed to download image for {book_title}: {e}")

def get_categories():
    response = requests.get(BASE_SITE_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    categories = {}
    category_list = soup.find("div", class_="side_categories").ul.find("ul")
    for link in category_list.find_all("a"):
        cat_name = link.text.strip()
        cat_url = urllib.parse.urljoin(BASE_SITE_URL, link['href'])
        categories[cat_name] = cat_url
    return categories

def get_book_data(book_url):
    try:
        response = requests.get(book_url)
        soup = BeautifulSoup(response.content, "html.parser")

        info_table = {row.th.text: row.td.text for row in soup.find_all("tr")}
        desc_tag = soup.find("div", id="product_description")
        description = desc_tag.find_next("p").text if desc_tag else ""
        rating_tag = soup.find("p", class_="star-rating")
        rating = rating_tag['class'][1] if rating_tag else ""

        # Image Handling
        img_tag = soup.find("img")
        img_rel_url = img_tag['src']
        image_url = urllib.parse.urljoin(book_url, img_rel_url)

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
    if not os.path.exists("scraped_data/csv"):
        os.makedirs("scraped_data/csv")

    categories = get_categories()
    print(f"Total categories found: {len(categories)}")

    for cat_name, cat_url in categories.items():
        print(f"\n--- Processing: {cat_name} ---")
        book_urls = get_category_books(cat_url)
        category_data = []

        for url in book_urls:
            data = get_book_data(url)
            if data:
                category_data.append(data)
                # Download the image
                download_image(data['image_url'], cat_name, data['title'])
                print(f"  > Scraped: {data['title'][:30]}...")

        # Save CSV
        csv_filename = f"scraped_data/csv/{slugify(cat_name)}.csv"
        if category_data:
            keys = category_data[0].keys()
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(category_data)

    print("\nSuccess! Data saved to 'scraped_data' folder.")

if __name__ == "__main__":
    main()
