from openai import OpenAI
import json
import re
import os

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class LLMPlanner:
    def __init__(self):
        self.client = client

    def _clean_price(self, price_str):
        """Cleans a price string to ensure it's a float for sorting."""
        if isinstance(price_str, (int, float)):
            return float(price_str)
        
        if not isinstance(price_str, str):
            return float('inf')
        
        # Remove currency symbols, commas, and spaces
        cleaned = re.sub(r'[₹$,\s]', '', price_str)
        try:
            return float(cleaned)
        except ValueError:
            return float('inf')

    def generate_plan(self, user_command, html_snapshot, site_name):
        """Generate extraction plan with site-specific prompting"""
        
        # Site-specific extraction hints
        site_hints = {
            "Amazon": """
For Amazon:
- Product names are usually in h2 tags with class containing "s-line-clamp"
- Prices are in span tags with class "a-price-whole"
- Ratings are in span tags with "a-icon-alt"
- Links: Look for 'a' tags with href containing '/dp/' followed by 10 characters (ASIN code)
  Example: /dp/B08XYZ1234 or https://www.amazon.in/dp/B08XYZ1234
- CRITICAL: Every product MUST have a link with '/dp/' in it
Look for data-asin attributes for product identification.
""",
            "Flipkart": """
For Flipkart:
- Product names are in "a" tags or div with class "_4rR01T" or "IRMWrR"
- Prices are in div with class "_30jeq3" or "_1_WHN1"
- Ratings are in div with class "_3LWZlK"
- Links: Look for 'a' tags with href, usually containing '/p/itm' or starting with '/'
  Example: /product-name/p/itm123456 or full URL
- CRITICAL: Every product MUST have a valid link
""",
            "Myntra": """
For Myntra:
- Product names are in h3 or h4 tags with class "product-product"
- Prices are in span or div with class "product-price" or "product-discountedPrice"
- Ratings are in div with class "product-rating" or "product-ratingsContainer"
- Links: CRITICAL - Links are in 'a' tags wrapping the product. Look for hrefs like:
  * Relative: /12345678/brand-name-product-name
  * Absolute: https://www.myntra.com/12345678/product-name
  * Pattern: Usually starts with a product ID (6-8 digits) followed by product slug
- IMPORTANT: The entire product card is usually wrapped in an 'a' tag - extract that href
- Links often have class "product-base" or are parent anchor tags of product elements
"""
        }

        site_hint = site_hints.get(site_name, "")
        
        # Simplified query for better LLM understanding
        search_query = user_command.lower()
        search_query = re.sub(r'\b(find|search|show|get|the|cheapest|best)\b', '', search_query).strip()
        
        prompt = f"""You are extracting product data from {site_name} search results.

USER SEARCH: "{search_query}"

{site_hint}

HTML CONTENT:
{html_snapshot[:15000]}

TASK: Extract EXACTLY 5 products that match the search query (or as many as available, minimum 3). For each product, extract:
1. name: Full product title/name (string)
2. price: Price as a NUMBER ONLY (no currency symbols, no commas). Example: 1999 or 1999.50
3. rating: Rating as string (e.g., "4.5") or "N/A" if not found
4. link: Product URL - MUST be either:
   - Absolute URL starting with https://
   - Relative path starting with / (like /12345/product-name or /dp/ASIN123)

CRITICAL RULES FOR LINKS:
- For Myntra: Look for 'a' tags that wrap the entire product card. The href will look like "/12345678/product-name"
- For Amazon: Must contain '/dp/' followed by 10-character ASIN
- For Flipkart: Usually contains '/p/' or '/itm'
- If you see an 'a' tag with href attribute near the product, that's likely the link
- NEVER return empty links or links without '/' or 'http'
- When in doubt, look for the parent 'a' tag that wraps product elements

VALIDATION:
- Price MUST be numeric only (integer or float)
- Link MUST be present and valid (either absolute URL or relative path starting with /)
- If you cannot find a clear price OR valid link, skip that product
- Only return products relevant to "{search_query}"
- EVERY product must have: name, price, AND link

OUTPUT FORMAT (JSON only, no explanation):
[
  {{
    "action": "extract_item",
    "item": {{
      "name": "Nike Air Zoom Running Shoes",
      "price": 3499,
      "rating": "4.2",
      "link": "/dp/B08XYZ123"
    }}
  }}
]

Return ONLY the JSON array, no markdown, no explanatory text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise product data extractor. Return only valid JSON arrays. ALWAYS include valid links for every product."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )

            text = response.choices[0].message.content.strip()

            print("\n--- RAW LLM RESPONSE START ---")
            print(text[:500])  # Print first 500 chars
            print("--- RAW LLM RESPONSE END ---\n")

            # Clean up markdown code blocks
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            text = text.strip()

            # Try to parse JSON
            plan = []
            try:
                plan = json.loads(text)
            except json.JSONDecodeError:
                # Try to extract JSON array
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    try:
                        plan = json.loads(match.group(0))
                    except:
                        print("[LLM Error] Could not parse JSON even after extraction")
                        return []
                else:
                    print("[LLM Error] No JSON array found in response")
                    return []
            
            # Validate and clean prices
            valid_plan = []
            for step in plan:
                if step.get("action") == "extract_item" and "item" in step:
                    item = step["item"]
                    
                    # Clean and validate price
                    raw_price = item.get("price")
                    cleaned_price = self._clean_price(raw_price)
                    
                    # Skip items without valid prices
                    if cleaned_price == float('inf'):
                        print(f"[Skipped] Item without valid price: {item.get('name')} (price: {raw_price})")
                        continue
                    
                    item["price"] = cleaned_price
                    
                    # Validate name
                    if not item.get("name") or len(item["name"]) < 3:
                        print(f"[Skipped] Item without valid name")
                        continue
                    
                    # Validate link (critical!)
                    link = item.get("link", "").strip()
                    if not link or (not link.startswith('/') and not link.startswith('http')):
                        print(f"[Skipped] Item without valid link: {item.get('name')} (link: {link})")
                        continue
                    
                    valid_plan.append(step)
            
            print(f"[LLM Success] Extracted {len(valid_plan)} valid items")
            return valid_plan

        except Exception as e:
            print(f"[LLM Error] Exception during plan generation: {e}")
            import traceback
            traceback.print_exc()
            return []