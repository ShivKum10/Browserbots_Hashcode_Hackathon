from playwright.sync_api import sync_playwright
from fsm import BrowserState
import re
from urllib.parse import urlparse, parse_qs
import time
import os

class FlyoExecutor:
    SITE_PRODUCT_SELECTORS = {
        "Amazon": "div[data-component-type='s-search-result']",
        "Flipkart": "div[data-id]",
        "Myntra": "li.product-base"
    }

    def __init__(self, planner, headless=False):
        self.planner = planner
        self.playwright = sync_playwright().start()
        
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--start-maximized'
            ]
        )
        
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = self.context.new_page()
        
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.fsm = BrowserState()

        self.ecommerce_sites = [
            {"name": "Amazon", "search_url": "https://www.amazon.in/s?k={query}"},
            {"name": "Flipkart", "search_url": "https://www.flipkart.com/search?q={query}"}
        ]
        
        self.site_name_map = {site['name'].lower(): site for site in self.ecommerce_sites}
        
        # Load credentials from environment variables
        self.credentials = {
            "Amazon": {
                "email": os.getenv("AMAZON_EMAIL", ""),
                "password": os.getenv("AMAZON_PASSWORD", "")
            },
            "Flipkart": {
                "email": os.getenv("FLIPKART_EMAIL", ""),
                "password": os.getenv("FLIPKART_PASSWORD", "")
            }
        }


    def _clean_price_for_sort(self, item):
        price = item.get("price")
        if isinstance(price, (int, float)):
            return price
        
        if isinstance(price, str):
            cleaned = re.sub(r'[₹$,\s]', '', price)
            try:
                return float(cleaned)
            except ValueError:
                pass
        return float("inf")


    def _correct_item_link(self, item, website):
        link = item.get("link", "").strip()
        if not link:
            return ""

        base_urls = {
            "Amazon": "https://www.amazon.in",
            "Flipkart": "https://www.flipkart.com",
            "Myntra": "https://www.myntra.com"
        }
        base_url = base_urls.get(website, "")
        
        # Flipkart link cleaning
        if website == "Flipkart":
            if 'flipkart.com' in link:
                parsed = urlparse(link)
                path = parsed.path
                match = re.search(r'(/[^/]+/p/[^/?]+)', path)
                if match:
                    clean_path = match.group(1)
                    params = parse_qs(parsed.query)
                    if 'pid' in params:
                        return f"{base_url}{clean_path}?pid={params['pid'][0]}"
                    return f"{base_url}{clean_path}"
            
            if link.startswith('/'):
                match = re.search(r'(/[^/]+/p/[^/?]+)', link)
                if match:
                    return f"{base_url}{match.group(1)}"
        
        # Amazon link cleaning
        if website == "Amazon":
            if link.lower().startswith('http'):
                match = re.search(r'(https?://[^/]+)(/dp/[A-Z0-9]{10}|/gp/product/[A-Z0-9]{10})', link)
                if match:
                    return match.group(1) + match.group(2)
            elif link.startswith('/'):
                match = re.search(r'(/dp/[A-Z0-9]{10}|/gp/product/[A-Z0-9]{10})', link)
                if match:
                    return base_url + match.group(0)
        
        # Generic handling
        if link.lower().startswith('http://') or link.lower().startswith('https://'):
            return link

        if base_url:
            if link.startswith('/'):
                return base_url + link
            else:
                return f"{base_url}/{link}"
        
        return link


    def search_products(self, user_command):
        """Search products without adding to cart - just return the list"""
        sites_to_search = self.ecommerce_sites
        cleaned_command = user_command
        
        # Check for site-specific search
        mentioned_site = None
        for name_lower, site_obj in self.site_name_map.items():
            if name_lower in user_command.lower():
                mentioned_site = site_obj
                cleaned_command = re.sub(name_lower, '', user_command, flags=re.IGNORECASE).strip()
                cleaned_command = re.sub(r'\b(on|from|at)\b', '', cleaned_command, flags=re.IGNORECASE).strip()
                break

        if mentioned_site:
            sites_to_search = [mentioned_site]
            print(f"🎯 Searching only: {mentioned_site['name']}")
        else:
            print(f"🎯 Searching all sites: {', '.join([s['name'] for s in sites_to_search])}")

        query = cleaned_command.replace(" ", "+")
        all_items = []

        try:
            for site in sites_to_search:
                site_name = site["name"]
                url = site["search_url"].format(query=query)
                print(f"\n{'='*60}")
                print(f"🔍 {site_name}: {url}")
                print(f"{'='*60}")
                
                try:
                    self.page.goto(url, wait_until="domcontentloaded", timeout=40000)

                    # Handle popups
                    if site_name == "Flipkart":
                        try:
                            self.page.press("body", "Escape")
                            self.page.wait_for_timeout(1000)
                        except:
                            pass
                    
                    # Wait for products
                    product_selector = self.SITE_PRODUCT_SELECTORS.get(site_name)
                    if product_selector:
                        self.page.wait_for_selector(product_selector, state="attached", timeout=20000)
                        self.page.wait_for_timeout(2000)
                    
                except Exception as e:
                    print(f"❌ {site_name} failed: {e}")
                    continue

                # Extract products
                html_snapshot = self._get_relevant_html(site_name)
                site_plan = self.planner.generate_plan(user_command, html_snapshot, site_name)
                
                for step in site_plan:
                    if step.get("action") == "extract_item":
                        item = step.get("item", {})
                        
                        if not item.get('price') or not item.get('name'):
                            continue
                        
                        raw_link = item.get('link', '').strip()
                        if not raw_link or len(raw_link) < 3:
                            continue
                        
                        item["website"] = site_name
                        corrected_link = self._correct_item_link(item, site_name)
                        
                        if not corrected_link or not corrected_link.startswith('http'):
                            continue
                        
                        item["link"] = corrected_link
                        all_items.append(item)
                        print(f"✓ {item['name']} - ₹{item['price']}")

            # Sort by price
            all_items.sort(key=self._clean_price_for_sort)
            
            print(f"\n{'='*60}")
            print(f"📊 FOUND {len(all_items)} PRODUCTS")
            print(f"{'='*60}\n")
            
            return {"all_items": all_items}

        except Exception as e:
            print(f"❌ Search error: {e}")
            import traceback
            traceback.print_exc()
            return {"all_items": []}


    def proceed_to_checkout(self, item):
        """Add selected item to cart and proceed to checkout page with auto-login"""
        site = item["website"]
        url = item["link"]
        
        print(f"\n{'='*60}")
        print(f"🛒 CHECKOUT AUTOMATION STARTED")
        print(f"{'='*60}")
        print(f"Product: {item['name']}")
        print(f"Price: ₹{item['price']}")
        print(f"Website: {site}")
        print(f"URL: {url}")
        print(f"{'='*60}\n")
        
        try:
            # Step 1: Navigate to product page
            print("Step 1: Opening product page...")
            self.page.goto(url, wait_until="networkidle", timeout=35000)
            self.page.wait_for_timeout(3000)
            print("✓ Product page loaded")
            
            # Step 2: Add to cart and handle login (site-specific)
            if site == "Amazon":
                success = self._amazon_checkout()
            elif site == "Flipkart":
                success = self._flipkart_checkout()
            else:
                return {"success": False, "error": f"Checkout not supported for {site}"}
            
            return success

        except Exception as e:
            print(f"❌ Checkout failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}


    def _amazon_login(self):
        """Handle Amazon login automation"""
        try:
            email = self.credentials["Amazon"]["email"]
            password = self.credentials["Amazon"]["password"]
            
            if not email or not password:
                print("⚠️ Amazon credentials not configured")
                return False
            
            print("\n🔐 Amazon Login Automation")
            print("-" * 40)
            
            current_url = self.page.url.lower()
            
            # Check if we're on a login page
            if 'signin' not in current_url and 'login' not in current_url:
                print("ℹ️ Not on login page, skipping login")
                return True
            
            # Step 1: Enter email/phone
            print("Step 1: Entering email...")
            email_selectors = [
                "#ap_email",
                "input[name='email']",
                "input[type='email']",
                "#ap_email_login"
            ]
            
            email_entered = False
            for selector in email_selectors:
                try:
                    self.page.wait_for_selector(selector, state="visible", timeout=5000)
                    self.page.fill(selector, email)
                    email_entered = True
                    print("✓ Email entered")
                    break
                except:
                    continue
            
            if not email_entered:
                print("❌ Could not find email field")
                return False
            
            # Click Continue
            self.page.wait_for_timeout(1000)
            try:
                continue_selectors = [
                    "#continue",
                    "input[id='continue']",
                    "#ap_email_login_signup_submit"
                ]
                for selector in continue_selectors:
                    try:
                        self.page.click(selector, timeout=3000)
                        print("✓ Clicked Continue")
                        break
                    except:
                        continue
            except:
                pass
            
            self.page.wait_for_timeout(3000)
            
            # Step 2: Enter password
            print("Step 2: Entering password...")
            password_selectors = [
                "#ap_password",
                "input[name='password']",
                "input[type='password']"
            ]
            
            password_entered = False
            for selector in password_selectors:
                try:
                    self.page.wait_for_selector(selector, state="visible", timeout=5000)
                    self.page.fill(selector, password)
                    password_entered = True
                    print("✓ Password entered")
                    break
                except:
                    continue
            
            if not password_entered:
                print("❌ Could not find password field")
                return False
            
            # Click Sign In
            self.page.wait_for_timeout(1000)
            try:
                signin_selectors = [
                    "#signInSubmit",
                    "input[id='signInSubmit']",
                    "#ap_password_login_signup_submit"
                ]
                for selector in signin_selectors:
                    try:
                        self.page.click(selector, timeout=3000)
                        print("✓ Clicked Sign In")
                        break
                    except:
                        continue
            except:
                pass
            
            # Wait for login to complete
            self.page.wait_for_timeout(5000)
            
            # Check if login was successful
            current_url = self.page.url.lower()
            if 'signin' not in current_url and 'login' not in current_url:
                print("✅ Login successful!")
                return True
            
            # Check for OTP requirement
            if self.page.is_visible("#auth-mfa-otpcode") or self.page.is_visible("input[name='otpCode']"):
                print("⚠️ OTP required - Please enter manually in the browser")
                print("⏳ Waiting 60 seconds for manual OTP entry...")
                self.page.wait_for_timeout(60000)
                return True
            
            print("⚠️ Login status unclear, proceeding...")
            return True
            
        except Exception as e:
            print(f"❌ Amazon login error: {e}")
            import traceback
            traceback.print_exc()
            return False


    def _flipkart_login(self):
        """Handle Flipkart login automation - auto-fills phone number, user enters OTP"""
        try:
            phone = self.credentials["Flipkart"]["email"]  # Phone number stored in email field
            
            if not phone:
                print("⚠️ Flipkart phone number not configured")
                print("💡 Add FLIPKART_EMAIL=your_phone_number to .env file")
                return False
            
            print("\n🔐 Flipkart Login Automation")
            print("-" * 40)
            print(f"📱 Phone Number: {phone}")
            
            current_url = self.page.url.lower()
            
            # Check if we're on a login page
            if 'login' not in current_url and 'account' not in current_url:
                print("ℹ️ Not on login page, skipping login")
                return True
            
            # Step 1: Enter phone number
            print("\nStep 1: Auto-filling phone number...")
            phone_selectors = [
                "input[class*='_2IX_2-']",
                "input[type='text']",
                "input.r4vIwl",
                "//input[@class and contains(@class, '_2IX_2-')]",
                "//input[@type='text' and not(@type='password')]"
            ]
            
            phone_entered = False
            for selector in phone_selectors:
                try:
                    if selector.startswith("//"):
                        element = self.page.wait_for_selector(f"xpath={selector}", state="visible", timeout=5000)
                        element.clear()
                        element.fill(phone)
                    else:
                        self.page.wait_for_selector(selector, state="visible", timeout=5000)
                        self.page.fill(selector, "")  # Clear first
                        self.page.fill(selector, phone)
                    
                    phone_entered = True
                    print(f"✅ Phone number entered: {phone}")
                    break
                except Exception as e:
                    continue
            
            if not phone_entered:
                print("❌ Could not find phone number input field")
                print("⚠️  Please enter your phone number manually in the browser")
                self.page.wait_for_timeout(30000)  # Wait 30 seconds for manual entry
                return False
            
            self.page.wait_for_timeout(1500)
            
            # Step 2: Click "Request OTP" button
            print("\nStep 2: Clicking 'Request OTP'...")
            otp_button_clicked = False
            
            otp_button_selectors = [
                "button._2KpZ6l._2HKlqd._3AWRsL",
                "button[class*='_2KpZ6l'][class*='_2HKlqd']",
                "//button[contains(@class, '_2KpZ6l') and contains(@class, '_2HKlqd')]",
                "//button[contains(text(), 'Request OTP')]",
                "//button[contains(text(), 'CONTINUE')]",
                "button._2KpZ6l._2doB4z._3AWRsL"
            ]
            
            for selector in otp_button_selectors:
                try:
                    if selector.startswith("//"):
                        element = self.page.wait_for_selector(f"xpath={selector}", state="visible", timeout=3000)
                        element.click()
                    else:
                        self.page.wait_for_selector(selector, state="visible", timeout=3000)
                        self.page.click(selector)
                    
                    otp_button_clicked = True
                    print("✅ Clicked 'Request OTP' button")
                    break
                except Exception as e:
                    continue
            
            if not otp_button_clicked:
                print("⚠️  Could not find 'Request OTP' button")
                print("💡 Please click it manually in the browser")
            
            # Wait for OTP screen to load
            self.page.wait_for_timeout(3000)
            
            # Step 3: Wait for user to enter OTP manually
            print("\n" + "="*60)
            print("📲 OTP SENT TO YOUR PHONE")
            print("="*60)
            print("⏳ Please enter the OTP in the browser window")
            print("⏱️  Waiting 90 seconds for OTP entry...")
            print("="*60)
            
            # Check for OTP input field
            otp_field_visible = False
            otp_selectors = [
                "input[type='text']",
                "input[type='number']",
                "input[class*='_2IX_2-']",
                "//input[@type='text' or @type='number']"
            ]
            
            for selector in otp_selectors:
                try:
                    if selector.startswith("//"):
                        if self.page.locator(f"xpath={selector}").is_visible():
                            otp_field_visible = True
                            break
                    else:
                        if self.page.is_visible(selector):
                            otp_field_visible = True
                            break
                except:
                    continue
            
            if otp_field_visible:
                print("✅ OTP input field detected")
            
            # Wait 90 seconds for user to enter OTP and complete login
            for i in range(18):  # 18 * 5 seconds = 90 seconds
                self.page.wait_for_timeout(5000)
                current_url = self.page.url.lower()
                
                # Check if login was successful (URL changed from login page)
                if 'login' not in current_url and 'account/login' not in current_url:
                    print(f"\n✅ Login successful! (detected after {(i+1)*5} seconds)")
                    return True
                
                # Show progress every 15 seconds
                if (i + 1) % 3 == 0:
                    remaining = 90 - ((i + 1) * 5)
                    print(f"⏳ Still waiting... ({remaining} seconds remaining)")
            
            # After 90 seconds, check final status
            current_url = self.page.url.lower()
            if 'login' not in current_url and 'account/login' not in current_url:
                print("\n✅ Login appears successful!")
                return True
            else:
                print("\n⚠️  Still on login page - please complete login manually")
                print("⏳ Giving you 30 more seconds...")
                self.page.wait_for_timeout(30000)
                return True
            
        except Exception as e:
            print(f"\n❌ Flipkart login error: {e}")
            import traceback
            traceback.print_exc()
            print("\n⚠️  Please complete login manually in the browser")
            self.page.wait_for_timeout(30000)
            return False


    def _amazon_checkout(self):
        """Amazon-specific checkout automation with login"""
        try:
            print("\n🔵 Amazon Checkout Automation")
            print("-" * 40)
            
            # Step 1: Click Add to Cart
            print("Step 1: Adding to cart...")
            add_to_cart_selectors = [
                "#add-to-cart-button",
                "input[name='submit.add-to-cart']",
                ".a-button-input[name='submit.add-to-cart']"
            ]
            
            clicked = False
            for selector in add_to_cart_selectors:
                try:
                    self.page.wait_for_selector(selector, state="visible", timeout=5000)
                    self.page.click(selector)
                    clicked = True
                    print("✓ Added to cart")
                    break
                except:
                    continue
            
            if not clicked:
                print("❌ Could not find Add to Cart button")
                return {"success": False, "error": "Add to Cart button not found"}
            
            self.page.wait_for_timeout(3000)
            
            # Step 2: Proceed to checkout
            print("Step 2: Proceeding to checkout...")
            checkout_selectors = [
                "#sc-buy-box-ptc-button",
                "input[name='proceedToRetailCheckout']",
                "//span[contains(text(), 'Proceed to Buy')]",
                "#attach-sidesheet-checkout-button"
            ]
            
            reached_checkout = False
            for selector in checkout_selectors:
                try:
                    if selector.startswith("//"):
                        element = self.page.wait_for_selector(f"xpath={selector}", state="visible", timeout=5000)
                        element.click()
                    else:
                        self.page.wait_for_selector(selector, state="visible", timeout=5000)
                        self.page.click(selector)
                    
                    reached_checkout = True
                    print("✓ Navigated to checkout")
                    break
                except:
                    continue
            
            self.page.wait_for_timeout(5000)
            
            # Step 3: Handle login if needed
            current_url = self.page.url.lower()
            if 'signin' in current_url or 'login' in current_url:
                print("\n🔐 Login page detected, attempting auto-login...")
                login_success = self._amazon_login()
                
                if login_success:
                    self.page.wait_for_timeout(5000)
                    current_url = self.page.url.lower()
                    if 'checkout' in current_url or 'buy' in current_url:
                        reached_checkout = True
            
            # Check final status
            if 'checkout' in current_url or 'buy' in current_url:
                reached_checkout = True
            
            print(f"\nCurrent URL: {current_url}")
            print("\n" + "="*60)
            print("✅ AUTOMATION COMPLETE")
            print("="*60)
            print("Status: Item in cart")
            if reached_checkout:
                print("Position: Checkout page")
                print("\n⚠️ Please complete payment manually in the browser")
            else:
                print("Position: Cart/Login page")
                print("\n⚠️ Please complete login and payment manually")
            print("="*60 + "\n")
            
            return {
                "success": True,
                "reached_checkout": reached_checkout,
                "message": "Added to cart successfully"
            }

        except Exception as e:
            print(f"❌ Amazon checkout error: {e}")
            return {"success": False, "error": str(e)}


    def _flipkart_checkout(self):
        """Flipkart-specific checkout automation with login"""
        try:
            print("\n🟢 Flipkart Checkout Automation")
            print("-" * 40)
            
            # Step 1: Check if login popup appears on product page
            self.page.wait_for_timeout(2000)
            
            # Try to close any login popup on product page
            try:
                close_selectors = [
                    "button._2KpZ6l._2doB4z", 
                    "button._2KpZ6l.QXhDTZ",
                    "button[class*='_2KpZ6l'][class*='_2doB4z']"
                ]
                for selector in close_selectors:
                    try:
                        if self.page.is_visible(selector):
                            self.page.click(selector, timeout=2000)
                            print("✓ Closed login popup on product page")
                            break
                    except:
                        continue
            except:
                pass
            
            self.page.wait_for_timeout(1000)
            
            # Step 2: Add to cart
            print("\nStep 1: Adding to cart...")
            add_to_cart_selectors = [
                "button._2KpZ6l._2U9uOA._3v1-ww",
                "//button[contains(text(), 'ADD TO CART')]",
                "button.QqFHMw",
                "button[class*='_2KpZ6l'][class*='_2U9uOA']"
            ]
            
            clicked = False
            for selector in add_to_cart_selectors:
                try:
                    if selector.startswith("//"):
                        element = self.page.wait_for_selector(f"xpath={selector}", state="visible", timeout=5000)
                        element.click()
                    else:
                        self.page.wait_for_selector(selector, state="visible", timeout=5000)
                        self.page.click(selector)
                    
                    clicked = True
                    print("✓ Clicked Add to Cart button")
                    break
                except Exception as e:
                    continue
            
            if not clicked:
                print("❌ Could not find Add to Cart button")
                return {"success": False, "error": "Add to Cart button not found"}
            
            # Wait for cart/login page to load
            print("\n⏳ Waiting for page to load...")
            self.page.wait_for_timeout(4000)
            
            # Check current URL after adding to cart
            current_url = self.page.url.lower()
            print(f"📍 Current page: {current_url}")
            
            # Step 3: CHECK IF LOGIN PAGE APPEARED IMMEDIATELY
            if 'login' in current_url or 'account/login' in current_url:
                print("\n🔐 LOGIN PAGE DETECTED AFTER ADD TO CART!")
                print("=" * 60)
                print("📱 Attempting to auto-fill phone number...")
                print("=" * 60)
                
                # Call login function immediately
                login_success = self._flipkart_login()
                
                if login_success:
                    print("\n✅ Login completed, checking current page...")
                    self.page.wait_for_timeout(3000)
                    current_url = self.page.url.lower()
                    print(f"📍 After login: {current_url}")
            
            # Step 4: Try to navigate to cart if not already there
            if 'cart' not in current_url and 'checkout' not in current_url:
                print("\nStep 2: Navigating to cart...")
                try:
                    cart_selectors = [
                        "a[href='/viewcart']",
                        "//a[contains(@href, 'viewcart')]",
                        "//span[contains(text(), 'GO TO CART')]",
                        "button[class*='_2KpZ6l']"
                    ]
                    
                    for selector in cart_selectors:
                        try:
                            if selector.startswith("//"):
                                element = self.page.wait_for_selector(f"xpath={selector}", state="visible", timeout=3000)
                                element.click()
                            else:
                                self.page.wait_for_selector(selector, state="visible", timeout=3000)
                                self.page.click(selector)
                            print("✓ Navigated to cart")
                            break
                        except:
                            continue
                    
                    self.page.wait_for_timeout(3000)
                except:
                    print("⚠️ Cart navigation not needed or failed")
            
            # Step 5: Click Place Order / Proceed to Checkout
            current_url = self.page.url.lower()
            print(f"\n📍 Before Place Order: {current_url}")
            
            if 'cart' in current_url or 'checkout' not in current_url:
                print("\nStep 3: Looking for 'Place Order' button...")
                
                # Check if login is required (button might show "Login to continue")
                login_button_selectors = [
                    "//span[contains(text(), 'LOGIN')]",
                    "//button[contains(text(), 'LOGIN')]",
                    "a[href*='login']"
                ]
                
                login_button_found = False
                for selector in login_button_selectors:
                    try:
                        if selector.startswith("//"):
                            if self.page.locator(f"xpath={selector}").is_visible():
                                element = self.page.locator(f"xpath={selector}")
                                element.click()
                                login_button_found = True
                                print("✓ Clicked LOGIN button from cart")
                                break
                        else:
                            if self.page.is_visible(selector):
                                self.page.click(selector)
                                login_button_found = True
                                print("✓ Clicked LOGIN button from cart")
                                break
                    except:
                        continue
                
                if not login_button_found:
                    # Try regular Place Order buttons
                    place_order_selectors = [
                        "//span[contains(text(), 'Place Order')]",
                        "//span[contains(text(), 'PLACE ORDER')]",
                        "button._2KpZ6l._2U9uOA._3v1-ww",
                        "//button[contains(@class, '_2KpZ6l') and contains(@class, '_2U9uOA')]",
                        "button[class*='_2KpZ6l _2U9uOA']"
                    ]
                    
                    for selector in place_order_selectors:
                        try:
                            if selector.startswith("//"):
                                element = self.page.wait_for_selector(f"xpath={selector}", state="visible", timeout=5000)
                                element.click()
                            else:
                                self.page.wait_for_selector(selector, state="visible", timeout=5000)
                                self.page.click(selector)
                            
                            print("✓ Clicked Place Order")
                            break
                        except:
                            continue
                
                self.page.wait_for_timeout(5000)
            
            # Step 6: Check if login page appeared AFTER Place Order
            current_url = self.page.url.lower()
            print(f"\n📍 Current URL: {current_url}")
            
            if ('login' in current_url or 'account/login' in current_url) and 'checkout' not in current_url:
                print("\n🔐 LOGIN PAGE DETECTED AFTER PLACE ORDER!")
                print("=" * 60)
                print("📱 Attempting to auto-fill phone number...")
                print("=" * 60)
                
                # Call login function
                login_success = self._flipkart_login()
                
                if login_success:
                    self.page.wait_for_timeout(3000)
                    current_url = self.page.url.lower()
            
            # Final status check
            reached_checkout = 'checkout' in current_url or ('cart' not in current_url and 'login' not in current_url)
            
            print(f"\n📍 Final URL: {current_url}")
            print("\n" + "="*60)
            print("✅ AUTOMATION COMPLETE")
            print("="*60)
            print("Status: Item in cart")
            if reached_checkout:
                print("Position: Checkout page")
                print("\n⚠️ Please complete address selection and payment manually")
            else:
                print("Position: Cart/Login page")
                print("\n⚠️ Please complete remaining steps manually")
            print("="*60 + "\n")
            
            return {
                "success": True,
                "reached_checkout": reached_checkout,
                "message": "Added to cart successfully"
            }

        except Exception as e:
            print(f"❌ Flipkart checkout error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}


    def _get_relevant_html(self, site_name):
        """Get only the relevant product listing section to reduce token usage"""
        try:
            selector = self.SITE_PRODUCT_SELECTORS.get(site_name)
            if selector:
                elements = self.page.query_selector_all(selector)
                html_parts = []
                for i, element in enumerate(elements[:10]):
                    try:
                        html_parts.append(element.inner_html())
                    except:
                        continue
                
                if html_parts:
                    return "\n---PRODUCT---\n".join(html_parts)
        except Exception as e:
            print(f"⚠️ Could not extract focused HTML: {e}")
        
        full_html = self.page.content()
        return full_html[:50000]


    def close(self):
        """Clean up Playwright resources."""
        print("\n🔴 Closing browser and stopping Playwright...")
        try:
            self.context.close()
            self.browser.close()
            self.playwright.stop()
            print("✓ Cleanup complete")
        except Exception as e:
            print(f"⚠️ Error during shutdown: {e}")