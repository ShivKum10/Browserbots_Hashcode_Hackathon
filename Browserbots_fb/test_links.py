
"""
Test script to verify that extracted product links are valid
Run this after getting results to check which links work
"""

import requests
from playwright.sync_api import sync_playwright

def test_link_with_requests(url):
    """Test if link is accessible using requests"""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code in [200, 301, 302]
    except:
        return False

def test_link_with_browser(url):
    """Test if link opens in browser"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            response = page.goto(url, timeout=10000, wait_until="domcontentloaded")
            success = response.status in [200, 301, 302]
            browser.close()
            return success
    except:
        return False

def extract_links_from_html(html_content):
    """Extract product links from HTML (for Amazon/Flipkart)"""
    import re
    
    # Amazon ASIN pattern
    amazon_links = re.findall(r'href="(/dp/[A-Z0-9]{10}|/gp/product/[A-Z0-9]{10})"', html_content)
    
    # Flipkart product pattern
    flipkart_links = re.findall(r'href="(/[^"]+/p/itm[^"]+)"', html_content)
    
    return {
        'amazon': list(set(amazon_links))[:5],
        'flipkart': list(set(flipkart_links))[:5]
    }

def test_extracted_results(all_items):
    """Test the items returned by your app"""
    print("\n" + "="*60)
    print("TESTING EXTRACTED PRODUCT LINKS")
    print("="*60 + "\n")
    
    if not all_items:
        print("No items to test!")
        return
    
    for i, item in enumerate(all_items, 1):
        print(f"\n[{i}] Testing: {item['name'][:50]}...")
        print(f"    Website: {item['website']}")
        print(f"    Link: {item['link']}")
        
        # Test with requests first (faster)
        requests_ok = test_link_with_requests(item['link'])
        print(f"    Status (requests): {'✅ OK' if requests_ok else '❌ FAILED'}")
        
        # If requests fails, try with browser
        if not requests_ok:
            print(f"    Retrying with browser...")
            browser_ok = test_link_with_browser(item['link'])
            print(f"    Status (browser): {'✅ OK' if browser_ok else '❌ FAILED'}")
            
            if not browser_ok:
                print(f"    ⚠️  BROKEN LINK - This link does not work!")
    
    # Summary
    working = sum(1 for item in all_items if test_link_with_requests(item['link']))
    print(f"\n{'='*60}")
    print(f"SUMMARY: {working}/{len(all_items)} links are working")
    print(f"{'='*60}")

# Example usage - paste your results here
if __name__ == "__main__":
    # PASTE YOUR RESULTS HERE
    # Example format:
    sample_items = [
        {
            "name": "Samsung Galaxy M14 5G",
            "price": 13990,
            "website": "Amazon",
            "link": "https://www.amazon.in/dp/B0BT8KN2BT"
        },
        {
            "name": "Samsung Galaxy F14 5G",
            "price": 12490,
            "website": "Flipkart",
            "link": "https://www.flipkart.com/samsung-galaxy-f14-5g/p/itm123456"
        }
    ]
    
    print("This is a sample test. To test your actual results:")
    print("1. Run your search and get the all_items JSON from backend")
    print("2. Replace 'sample_items' above with your actual data")
    print("3. Run this script again\n")
    
    test_extracted_results(sample_items)