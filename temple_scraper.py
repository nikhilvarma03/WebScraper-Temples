import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from time import sleep
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TempleWebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.temples_data = []

    def fetch_webpage(self, url):
        """Fetch the webpage content"""
        try:
            logger.info(f"Fetching webpage: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching webpage: {e}")
            return None

    def parse_temple_data(self, html_content):
        """Parse temple data from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Strategy 1: Look for temple information in structured sections
        # This targets the main content area
        content_sections = soup.find_all(
            ['div', 'section', 'article'], class_=re.compile(r'content|main|body|post'))

        if not content_sections:
            # Fallback: Look for any div that might contain the content
            content_sections = [soup.find('body')] if soup.find(
                'body') else [soup]

        for section in content_sections:
            self._extract_temples_from_section(section)

        # Strategy 2: Look for specific patterns in headings and paragraphs
        self._extract_temples_by_headings(soup)

        return self.temples_data

    def _extract_temples_from_section(self, section):
        """Extract temple information from a specific section"""
        if not section:
            return

        # Look for temple headings (h1, h2, h3, h4 tags)
        headings = section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        for heading in headings:
            temple_name = self._clean_text(heading.get_text())

            # Skip if it's not likely a temple name
            if not self._is_likely_temple_name(temple_name):
                continue

            # Extract description from following siblings
            description = self._extract_description_after_heading(heading)

            if temple_name and description:
                self.temples_data.append({
                    'Temple Name': temple_name,
                    'Description': description
                })
                logger.info(f"Found temple: {temple_name}")

    def _extract_temples_by_headings(self, soup):
        """Alternative method to extract temples by analyzing text patterns"""
        # Look for text patterns that indicate temple information
        text_content = soup.get_text()

        # Split by common patterns that indicate new temple sections
        sections = re.split(
            r'\n(?=About [A-Z]|\d+\.\s*[A-Z]|[A-Z][a-z]+\s+Temple)', text_content)

        for section in sections:
            lines = section.strip().split('\n')
            if len(lines) < 2:
                continue

            potential_name = lines[0].strip()

            if self._is_likely_temple_name(potential_name):
                # Clean the temple name
                temple_name = re.sub(
                    r'^(About\s+|\d+\.\s*)', '', potential_name)

                # Get description from remaining lines
                description = '\n'.join([line.strip()
                                        for line in lines[1:] if line.strip()])
                description = self._clean_description(description)

                if temple_name and description and len(description) > 50:
                    # Check if we already have this temple
                    if not any(temple['Temple Name'] == temple_name for temple in self.temples_data):
                        self.temples_data.append({
                            'Temple Name': temple_name,
                            'Description': description
                        })
                        logger.info(
                            f"Found temple (pattern method): {temple_name}")

    def _extract_description_after_heading(self, heading):
        """Extract description that follows a heading"""
        description_parts = []
        current_element = heading.next_sibling

        # Traverse siblings to collect description
        while current_element:
            if hasattr(current_element, 'name'):
                # If we hit another heading, stop
                if current_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break

                # Collect text from paragraphs and divs
                if current_element.name in ['p', 'div', 'span']:
                    text = self._clean_text(current_element.get_text())
                    if text and len(text) > 20:  # Only meaningful text
                        description_parts.append(text)

            current_element = current_element.next_sibling

            # Limit to prevent infinite loops
            if len(description_parts) > 10:
                break

        return ' '.join(description_parts)

    def _is_likely_temple_name(self, text):
        """Check if text is likely a temple name"""
        if not text or len(text) < 3:
            return False

        # Common temple keywords
        temple_keywords = [
            'temple', 'kovil', 'mandir', 'shrine', 'mutt', 'ashram',
            'swamy', 'swami', 'eswarar', 'amman', 'perumal', 'vishnu',
            'shiva', 'devi', 'lakshmi', 'saraswati', 'durga', 'kali',
            'hanuman', 'ganesha', 'murugan', 'ayyappa'
        ]

        text_lower = text.lower()

        # Check for temple keywords
        has_temple_keyword = any(
            keyword in text_lower for keyword in temple_keywords)

        # Check for proper nouns (starts with capital letters)
        has_proper_noun = bool(re.search(r'\b[A-Z][a-z]+', text))

        # Exclude common non-temple headings
        exclude_keywords = [
            'about', 'history', 'architecture', 'festival', 'how to reach',
            'timings', 'entry fee', 'best time', 'nearby', 'facilities'
        ]

        is_excluded = any(
            keyword in text_lower for keyword in exclude_keywords)

        return (has_temple_keyword or has_proper_noun) and not is_excluded and len(text) < 100

    def _clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters at the beginning
        text = re.sub(r'^[^\w\s]+', '', text)

        return text

    def _clean_description(self, description):
        """Clean description text"""
        # Remove excessive newlines and spaces
        description = re.sub(r'\n+', '\n', description)
        description = re.sub(r'\s+', ' ', description)

        # Remove URLs and email addresses
        description = re.sub(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', description)
        description = re.sub(r'\S+@\S+', '', description)

        # Remove common navigation text
        description = re.sub(
            r'(read more|click here|see more|learn more)', '', description, flags=re.IGNORECASE)

        return description.strip()

    def save_to_excel(self, filename='tamil_nadu_temples.xlsx'):
        """Save temple data to Excel file"""
        if not self.temples_data:
            logger.warning("No temple data found to save")
            return

        try:
            # Create DataFrame
            df = pd.DataFrame(self.temples_data)

            # Remove duplicates based on temple name
            df = df.drop_duplicates(subset=['Temple Name'], keep='first')

            # Save to Excel with formatting
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(
                    writer, sheet_name='Tamil Nadu Temples', index=False)

                # Get the worksheet to apply formatting
                worksheet = writer.sheets['Tamil Nadu Temples']

                # Adjust column widths
                worksheet.column_dimensions['A'].width = 30  # Temple Name
                worksheet.column_dimensions['B'].width = 80  # Description

                # Wrap text for description column
                from openpyxl.styles import Alignment
                for row in worksheet.iter_rows(min_row=2, max_col=2):
                    for cell in row:
                        cell.alignment = Alignment(
                            wrap_text=True, vertical='top')

            logger.info(f"Successfully saved {len(df)} temples to {filename}")
            print(
                f"✅ Excel file '{filename}' created successfully with {len(df)} temples!")

        except Exception as e:
            logger.error(f"Error saving to Excel: {e}")
            print(f"❌ Error saving to Excel: {e}")


def main():
    """Main function to run the scraper"""
    url = "https://www.trawell.in/tamilnadu/pilgrimages"

    # Initialize scraper
    scraper = TempleWebScraper()

    # Fetch and parse the webpage
    html_content = scraper.fetch_webpage(url)
    if not html_content:
        print("❌ Failed to fetch webpage")
        return

    # Parse temple data
    temples = scraper.parse_temple_data(html_content)

    if not temples:
        print("❌ No temple data found")
        return

    print(f"📊 Found {len(temples)} temples")

    # Display first few temples for verification
    print("\n📋 First few temples found:")
    for i, temple in enumerate(temples[:3]):
        print(f"{i+1}. {temple['Temple Name']}")
        print(f"   Description: {temple['Description'][:100]}...")
        print()

    # Save to Excel
    scraper.save_to_excel()

    # Display summary
    print(f"\n📈 Summary:")
    print(f"   • Total temples extracted: {len(temples)}")
    print(f"   • Excel file: tamil_nadu_temples.xlsx")
    print(f"   • Columns: Temple Name, Description")


if __name__ == "__main__":
    main()
