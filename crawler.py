import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import time

# Configuration
CONFIG = {
    "base_url": "https://www.khanacademy.org",  # Change this to crawl a different site
    "max_pages": 1,  # Maximum number of pages to crawl
    "delay": 1,  # Delay between requests in seconds
    "output_dir": "."  # Directory to save output files
}

def get_robots_txt():
    """Fetch and analyze robots.txt"""
    robots_url = urljoin(CONFIG["base_url"], "/robots.txt")
    try:
        response = requests.get(robots_url)
        return {
            "status": "success",
            "content": response.text
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def extract_titles(url):
    """Extract titles from a page"""
    try:
        print(f"Fetching content from {url}")
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple approaches to find titles
        titles = []
        
        # Look for main navigation items
        nav_items = soup.select('a[data-test-id="nav-item"]')
        if nav_items:
            titles.extend([item.text.strip() for item in nav_items if item.text.strip()])
        
        # Look for subject titles
        subject_titles = soup.select('.subject-title, .domain-title')
        if subject_titles:
            titles.extend([title.text.strip() for title in subject_titles if title.text.strip()])
        
        # Look for course titles
        course_titles = soup.select('.course-title')
        if course_titles:
            titles.extend([title.text.strip() for title in course_titles if title.text.strip()])
        
        # If still no titles found, try generic heading tags with specific classes
        if not titles:
            headings = soup.select('h1._1lrvdlvj, h2._14hvi6g8, h3.title')
            titles.extend([h.text.strip() for h in headings if h.text.strip()])
        
        # If still nothing, try all headings
        if not titles:
            headings = soup.find_all(['h1', 'h2', 'h3'])
            titles.extend([h.text.strip() for h in headings if h.text.strip()])
        
        print(f"Found {len(titles)} titles")
        if not titles:
            print("Warning: No titles found in the page")
            print("Page URL:", url)
            print("Response status:", response.status_code)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_titles = [x for x in titles if not (x in seen or seen.add(x))]
        
        return unique_titles
    except Exception as e:
        print(f"Error extracting titles from {url}: {e}")
        print("Response status code:", getattr(response, 'status_code', 'N/A'))
        return []

def test_api():
    """Test API accessibility"""
    api_url = urljoin(CONFIG["base_url"], "/api/internal/_bb")
    try:
        response = requests.get(api_url)
        return f"[OK] Attempted API Access to: {api_url}\nStatus Code: {response.status_code}\n"
    except Exception as e:
        return f"[ERROR] API Test Failed: {e}"

def main():
    # Create crawlability summary
    robots_info = get_robots_txt()
    crawl_summary = {
        "Base URL": CONFIG["base_url"],
        "Robots.txt Status": robots_info["status"],
        "Crawl Delay": "Not specified",  # You can parse this from robots.txt if needed
        "Sitemaps": ["https://www.khanacademy.org/sitemap.xml"],  # Add sitemap parsing if needed
        "Rules": {
            "*": {
                "/": "Allowed",
                "/api/internal/_bb/": "Disallowed",
                "/math/algebra": "Allowed"
            }
        }
    }

    # Extract titles from multiple important pages
    all_titles = []
    pages_to_crawl = [
        CONFIG["base_url"],
        urljoin(CONFIG["base_url"], "/math"),
        urljoin(CONFIG["base_url"], "/science"),
        urljoin(CONFIG["base_url"], "/computing"),
        urljoin(CONFIG["base_url"], "/humanities")
    ]

    print("\nStarting title extraction...")
    for page in pages_to_crawl:
        print(f"\nProcessing page: {page}")
        page_titles = extract_titles(page)
        all_titles.extend(page_titles)
        time.sleep(CONFIG["delay"])  # Respect the delay between requests

    # Remove duplicates while preserving order
    seen = set()
    unique_titles = [x for x in all_titles if not (x in seen or seen.add(x))]

    print(f"\nTotal unique titles found: {len(unique_titles)}")

    # Save results
    with open("crawlability_summary.json", "w", encoding="utf-8") as f:
        json.dump(crawl_summary, f, indent=2)

    with open("extracted_titles.json", "w", encoding="utf-8") as f:
        json.dump(unique_titles, f, indent=2)

    with open("api_test_output.txt", "w", encoding="utf-8") as f:
        f.write(test_api())

if __name__ == "__main__":
    main() 