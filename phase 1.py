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


