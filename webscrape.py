import requests
from bs4 import BeautifulSoup
import pandas as pd

# The URL of the main page with the list of temples
main_url = "https://karnatakatourism.org/tour-item/?type%5B%5D=temples"

# --- Step 1: Get all the temple names and their individual links ---
print("Fetching list of temples from the main page...")
response = requests.get(main_url)
soup = BeautifulSoup(response.content, 'html.parser')

# This list will store dictionaries, each with a name and a link
temple_links = []
# We inspect the page and find that each temple is in a 'div' with the class 'tour-item'
temple_cards = soup.find_all('div', class_='tour-item')

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

    # Visit the individual temple page
    page_response = requests.get(temple_url)
    page_soup = BeautifulSoup(page_response.content, 'html.parser')

    # The description is in a 'div' with the class 'tour-item-description'
    description_div = page_soup.find('div', class_='tour-item-description')

    information = "No description found."  # A default value
    if description_div:
        # Find all paragraph tags <p> within the description div and join them
        p_tags = description_div.find_all('p')
        # Join the text from each paragraph with a space in between
        information = ' '.join([p.text for p in p_tags]).strip()

    # Append the final result to our main list
    all_temples_data.append(
        {'Temple Name': temple_name, 'Information': information})

# --- Step 3: Save the collected data to an Excel file ---
print("Scraping complete. Saving data to Excel...")
df = pd.DataFrame(all_temples_data)

# Save the DataFrame to an Excel file
output_filename = 'temples_of_karnataka.xlsx'
df.to_excel(output_filename, index=False)

print(f"Success! Data saved to {output_filename}")
