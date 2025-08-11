import requests
from bs4 import BeautifulSoup
import pandas as pd

# The URL of the main page with the list of temples
main_url = "https://karnatakatourism.org/tour-item/?type%5B%5D=temples"

# Add a User-Agent header to mimic a browser, which is a good practice
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Step 1: Get all the temple names and their individual links ---
print("Fetching list of temples from the main page...")
try:
    # Pass the headers with the request
    response = requests.get(main_url, headers=headers, timeout=10)
    response.raise_for_status()  # This will raise an error for bad responses (4xx or 5xx)
except requests.exceptions.RequestException as e:
    print(f"Error fetching main URL: {e}")
    exit()

soup = BeautifulSoup(response.content, 'html.parser')

temple_links = []
# The website uses <article> with the class 'tour-item-new' for each temple
temple_cards = soup.find_all('article', class_='tour-item-new')

for card in temple_cards:
    # The name and link are inside an <a> tag within an <h3> tag
    h3_tag = card.find('h3')
    if h3_tag and h3_tag.find('a'):
        a_tag = h3_tag.find('a')
        temple_name = a_tag.text.strip()
        temple_url = a_tag['href']
        temple_links.append({'name': temple_name, 'url': temple_url})

print(f"Found {len(temple_links)} temples. Now scraping individual pages...")

# --- Step 2: Visit each link and scrape the detailed information ---
all_temples_data = []

# Loop through the list of links we just created
for item in temple_links:
    temple_name = item['name']
    temple_url = item['url']

    print(f"Scraping details for: {temple_name}")

    try:
        # Visit the individual temple page using headers
        page_response = requests.get(temple_url, headers=headers, timeout=10)
        page_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Could not scrape {temple_name}. Error: {e}")
        continue  # Skip to the next temple if this one fails

    page_soup = BeautifulSoup(page_response.content, 'html.parser')

    # The description is in a 'div' with the class 'tour-item-description'
    description_div = page_soup.find('div', class_='tour-item-description')

    information = "No description found."  # A default value
    if description_div:
        # Find all paragraph tags <p> within the description div and join their text
        p_tags = description_div.find_all('p')
        # Join the text from each paragraph with a space in between
        information = ' '.join([p.text for p in p_tags]).strip()

    # Append the final result to our main list
    all_temples_data.append(
        {'Temple Name': temple_name, 'Information': information})

# --- Step 3: Save the collected data to an Excel file ---
print("Scraping complete. Saving data to Excel...")
if not all_temples_data:
    print("No data was scraped. The Excel file will be empty.")
else:
    # Create a pandas DataFrame from our list of dictionaries
    df = pd.DataFrame(all_temples_data)

    # Save the DataFrame to an Excel file
    output_filename = 'temples_of_karnataka.xlsx'
    df.to_excel(output_filename, index=False)

    print(f"Success! Data saved to {output_filename}")
