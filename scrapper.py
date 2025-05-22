from urllib import robotparser
import requests
import json
from bs4 import BeautifulSoup
import gzip
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from urllib.parse import urljoin, urlparse

# Configuration
MAX_DEPTH = 2  # How deep to crawl (0 = just main page, 1 = main + sub-pages, 2 = main + sub + sub-sub)
MAX_PAGES_PER_SECTION = 1  # Maximum pages to crawl per section
CRAWL_DELAY = 2  # Default delay between requests

def setup_selenium():
    """Setup Selenium WebDriver with Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

def extract_headings(url, driver=None):
    """Extract all heading tags using Selenium"""
    should_quit = False
    if driver is None:
        driver = setup_selenium()
        should_quit = True
        
    headings_data = {
        'h1': [],
        'h2': [],
        'h3': [],
        'h4': [],
        'h5': [],
        'h6': []
    }
    
    try:
        print(f"\n🔍 Extracting headings from {url}")
        driver.get(url)
        
        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Give extra time for dynamic content
        time.sleep(2)
        
        # Extract all heading levels
        for level in range(1, 7):
            tag = f"h{level}"
            elements = driver.find_elements(By.TAG_NAME, tag)
            
            for element in elements:
                heading_text = element.text.strip()
                if heading_text:  # Only add non-empty headings
                    headings_data[tag].append({
                        'text': heading_text,
                        'level': level
                    })
            
            count = len(headings_data[tag])
            print(f"Found {count} {tag} headings")
    
    except Exception as e:
        print(f"Error extracting headings: {e}")
    
    finally:
        if should_quit:
            driver.quit()
    
    return headings_data

def get_page_links(driver, base_url):
    """Extract links from the current page"""
    links = set()
    try:
        elements = driver.find_elements(By.TAG_NAME, "a")
        for element in elements:
            try:
                href = element.get_attribute("href")
                if href and href.startswith(base_url):
                    links.add(href)
            except:
                continue
    except Exception as e:
        print(f"Error extracting links: {e}")
    return links

def crawl_section(base_url, section_path, max_depth=MAX_DEPTH):
    """Crawl a section of the website with specified depth"""
    driver = setup_selenium()
    visited = set()
    section_data = {}
    pages_crawled = 0
    
    try:
        def crawl_recursive(url, depth=0):
            nonlocal pages_crawled
            
            if pages_crawled >= MAX_PAGES_PER_SECTION:
                return
            
            if url in visited:
                return
                
            visited.add(url)
            pages_crawled += 1
            
            print(f"\nCrawling page {pages_crawled} (depth {depth}): {url}")
            
            # Extract headings from current page
            section_data[url] = extract_headings(url, driver)
            
            # If we haven't reached max depth, get links and continue crawling
            if depth < max_depth:
                links = get_page_links(driver, base_url)
                # Filter links to stay within the current section
                section_links = {link for link in links if section_path in link}
                
                for link in section_links:
                    if pages_crawled < MAX_PAGES_PER_SECTION:
                        time.sleep(CRAWL_DELAY)
                        crawl_recursive(link, depth + 1)
        
        # Start crawling from the section URL
        start_url = urljoin(base_url, section_path)
        crawl_recursive(start_url)
        
    except Exception as e:
        print(f"Error during crawling: {e}")
    
    finally:
        driver.quit()
    
    return section_data

def analyze_sitemap(sitemap_url):
    """Analyze a sitemap and return its contents"""
    try:
        response = requests.get(sitemap_url)
        
        # Handle gzipped sitemaps
        if sitemap_url.endswith('.gz'):
            content = gzip.decompress(response.content)
        else:
            content = response.content
            
        soup = BeautifulSoup(content, 'xml')
        
        # Check if this is a sitemap index
        sitemaps = soup.find_all('sitemap')
        if sitemaps:
            return {
                "type": "sitemap_index",
                "count": len(sitemaps),
                "sitemaps": [loc.text for loc in soup.find_all('loc')]
            }
        
        # Regular sitemap
        urls = soup.find_all('url')
        return {
            "type": "sitemap",
            "count": len(urls),
            "sample_urls": [url.loc.text for url in urls[:5]] if urls else []
        }
    except Exception as e:
        return {
            "type": "error",
            "error": str(e)
        }

# Main execution
if __name__ == "__main__":
    base_url = "https://www.khanacademy.org"
    robots_url = f"{base_url}/robots.txt"

    # Initialize robotparser
    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.read()

    # Download raw robots.txt
    robots_txt = requests.get(robots_url).text
    lines = robots_txt.splitlines()

    # Extract sitemap(s)
    sitemaps = [line.split(": ", 1)[1] for line in lines if line.lower().startswith("sitemap:")]

    # Analyze sitemaps
    sitemap_analysis = {}
    if sitemaps:
        print("\n📋 Analyzing sitemaps...")
        for sitemap in sitemaps:
            print(f"Analyzing {sitemap}...")
            sitemap_analysis[sitemap] = analyze_sitemap(sitemap)

    # Extract crawl-delay
    crawl_delay_manual = None
    recording = False
    for line in lines:
        if line.lower().startswith("user-agent: *"):
            recording = True
        elif line.lower().startswith("user-agent:") and not line.lower().startswith("user-agent: *"):
            recording = False
        if recording and line.lower().startswith("crawl-delay:"):
            crawl_delay_manual = line.split(":")[1].strip()
            break

    crawl_delay = crawl_delay_manual or rp.crawl_delay("*") or "Not specified"
    if crawl_delay != "Not specified":
        CRAWL_DELAY = float(crawl_delay)

    # Test paths and extract headings from allowed paths
    test_paths = [
        "/math",
        "/science",
        "/computing",
        "/humanities"
    ]
    
    results = {}
    extracted_headings = {}
    
    print(f"\n🌐 Crawling with depth {MAX_DEPTH} (max {MAX_PAGES_PER_SECTION} pages per section)")
    
    for path in test_paths:
        full_url = f"{base_url}{path}"
        allowed = rp.can_fetch("*", full_url)
        results[path] = "Allowed" if allowed else "Disallowed"
        
        if allowed:
            print(f"\n📚 Starting section: {path}")
            extracted_headings[path] = crawl_section(base_url, path)

    # Print summary
    print("\n📊 Crawl Summary")
    print(f"Depth: {MAX_DEPTH}")
    print(f"Max pages per section: {MAX_PAGES_PER_SECTION}")
    print("Crawl delay:", CRAWL_DELAY)
    
    print("\nSection Analysis:")
    total_pages = 0
    for path in test_paths:
        if path in extracted_headings:
            pages = len(extracted_headings[path])
            total_pages += pages
            print(f"  {path:30} → {pages} pages crawled")
    
    print(f"\nTotal pages crawled: {total_pages}")

    # Save results
    summary = {
        "crawl_config": {
            "max_depth": MAX_DEPTH,
            "max_pages_per_section": MAX_PAGES_PER_SECTION,
            "crawl_delay": CRAWL_DELAY
        },
        "crawl_stats": {
            "total_pages": total_pages,
            "sections_crawled": len(extracted_headings)
        },
        "sitemaps": {
            "urls": sitemaps,
            "analysis": sitemap_analysis
        },
        "tested_paths": results,
        "extracted_headings": extracted_headings
    }

    with open("crawl_results.json", "w", encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print("\n✅ Results saved to 'crawl_results.json'")
