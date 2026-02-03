import requests
from bs4 import BeautifulSoup
import csv
import re # For regular expressions, helpful for clean-up

# Phase 1. Define the URL for the single book product page
# use "Layered Baking Building and Styling Spectacular Cakes"
URL = "http://books.toscrape.com/catalogue/layered-baking-building-and-styling-spectacular-cakes_904/index.html"

# 2. Function to extract all the required data
def scrape_book_page(url):
    """Fetches a book page and extracts the specified data points."""
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        response.raise_for_status() 

        # Parse the content of the page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Dictionary to store the extracted data
        book_data = {}

        # Direct URL Field 
        book_data['product_page_url'] = url

        # Data from the Product Information Table (UPC, Prices, Availability) 
        product_info_table = soup.find('table', class_='table table-striped')

        # Find all rows in the table
        rows = product_info_table.find_all('tr')

        # Helper function to get text from a cell
        def get_cell_text(row):
            return row.find('td').text.strip()

        # Extract data based on row order 
        book_data['universal_product_code (upc)'] = get_cell_text(rows[0])

        # Remove '£' symbol
        price_inc_tax_raw = get_cell_text(rows[3])
        book_data['price_including_tax'] = price_inc_tax_raw.replace('£', '')

        price_exc_tax_raw = get_cell_text(rows[2])
        book_data['price_excluding_tax'] = price_exc_tax_raw.replace('£', '')

        # Clean quantity
        qty_available_raw = get_cell_text(rows[5])
        # Use regex to find the numbers
        match = re.search(r'\((\d+) available\)', qty_available_raw)
        book_data['quantity_available'] = match.group(1) if match else qty_available_raw # Fallback if regex fails

        # Pull data from other HTML elements (Title, Category, Rating, Description, Image)

        # Book Title 
        book_data['book_title'] = soup.find('h1').text.strip()

        # Category 
        breadcrumb = soup.find('ul', class_='breadcrumb')
        # The category is in the third <li>, second <a> tag (index 2)
        book_data['category'] = breadcrumb.find_all('a')[2].text.strip()

        # Review Rating
        star_rating_element = soup.find('p', class_=re.compile(r'star-rating'))
        # Get the second class name (the rating word)
        book_data['review_rating'] = star_rating_element['class'][1] if star_rating_element else 'N/A'

        # Product Description
        description_header = soup.find('h2', string='Product Description')
        if description_header:
            description_element = soup.find('div', id='product_description').find_next_sibling('p')
            book_data['product_description'] = description_element.text.strip()
        else:
            book_data['product_description'] = soup.find('article', class_='product_page').find_all('p', recursive=False)[-1].text.strip()


        # Image URL
        image_tag = soup.find('div', class_='item active').find('img')
        relative_image_url = image_tag['src']
        base_url = "http://books.toscrape.com/"
        # Clean up the relative path
        clean_relative_url = relative_image_url.replace('../../../', '')
        book_data['image_url'] = base_url + clean_relative_url

        return book_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return None
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return None

# 3. Write the data to a CSV file
def write_to_csv(data):
    """Writes a dictionary of data to a CSV file."""
    # Define the fields/column headers in the exact required order
    fieldnames = [
        'product_page_url',
        'universal_product_code (upc)',
        'book_title',
        'price_including_tax',
        'price_excluding_tax',
        'quantity_available',
        'product_description',
        'category',
        'review_rating',
        'image_url'
    ]

    with open('book_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        # Create a CSV DictWriter object
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row
        writer.writeheader()

        # Write the data row
        if data:
            writer.writerow(data)
            print("\nSuccess! Data saved to 'food_and_drink_books.csv'.")
        else:
            print("\nFailed to write data: No data was scraped.")


# 4. Main execution block
if __name__ == "__main__":
    print(f"Scraping data from: {URL}")
    extracted_data = scrape_book_page(URL)
    write_to_csv(extracted_data)


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
