"""
Enhanced browser executor with deep UI analysis.
Captures HTML structure, interactive elements, and page state.
"""

import asyncio
import logging
import os
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page, Browser, Error as PlaywrightError
except ImportError:
    class PlaywrightError(Exception): pass
    class Page: pass
    class Browser: pass
    async_playwright = None

logger = logging.getLogger(__name__)


class UICache:
    """Smart UI cache with validation"""
    
    def __init__(self, cache_file: str = "ui_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.load()
    
    def load(self) -> None:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded UI cache with {len(self.cache)} entries")
            except Exception as e:
                logger.warning(f"Failed to load UI cache: {e}")
                self.cache = {}
    
    def save(self) -> None:
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save UI cache: {e}")
    
    def get(self, url: str, ui_hash: str) -> Optional[Dict[str, Any]]:
        base_url = self._normalize_url(url)
        cached = self.cache.get(base_url)
        
        if cached and cached.get('hash') == ui_hash:
            cached['hit_count'] = cached.get('hit_count', 0) + 1
            cached['last_hit'] = datetime.now().isoformat()
            logger.debug(f"Cache HIT: {base_url}")
            return cached
        
        logger.debug(f"Cache MISS: {base_url}")
        return None
    
    def set(self, url: str, ui_hash: str, ui_analysis: Dict[str, Any]) -> None:
        base_url = self._normalize_url(url)
        
        self.cache[base_url] = {
            'hash': ui_hash,
            'analysis': ui_analysis,
            'timestamp': datetime.now().isoformat(),
            'hit_count': 0,
            'last_hit': None
        }
        
        self.save()
        logger.debug(f"Cached UI for: {base_url}")
    
    def invalidate(self, url: str) -> None:
        base_url = self._normalize_url(url)
        if base_url in self.cache:
            del self.cache[base_url]
            self.save()
            logger.info(f"Invalidated cache for: {base_url}")
    
    def _normalize_url(self, url: str) -> str:
        return url.split('?')[0].split('#')[0].rstrip('/')


class CredentialManager:
    """Credential storage"""
    
    def __init__(self, cred_file: str = "credentials.json"):
        self.cred_file = Path(cred_file)
        self.credentials: Dict[str, Dict[str, str]] = {}
        self.load()
    
    def load(self) -> None:
        if self.cred_file.exists():
            try:
                with open(self.cred_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                logger.info(f"Loaded credentials for {len(self.credentials)} sites")
            except Exception as e:
                logger.warning(f"Failed to load credentials: {e}")
                self.credentials = {}
    
    def save(self) -> None:
        try:
            with open(self.cred_file, 'w', encoding='utf-8') as f:
                json.dump(self.credentials, f, indent=2)
            logger.info("Saved credentials")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
    def get(self, domain: str) -> Optional[Dict[str, str]]:
        return self.credentials.get(domain)
    
    def set(self, domain: str, username: str, password: str) -> None:
        self.credentials[domain] = {
            'username': username,
            'password': password,
            'saved_at': datetime.now().isoformat()
        }
        self.save()
        logger.info(f"Saved credentials for {domain}")
    
    def get_domain_from_url(self, url: str) -> str:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc


class BrowserExecutor:
    """Enhanced browser executor with deep UI analysis"""
    
    DEFAULT_TIMEOUT = 30000
    
    def __init__(self, headless: bool = False, timeout: int = DEFAULT_TIMEOUT):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.headless = headless
        self.timeout = timeout
        
        self.ui_cache = UICache()
        self.credentials = CredentialManager()
        
        logger.info(f"Executor initialized (headless={headless}, timeout={timeout}ms)")
    
    async def start(self) -> None:
        """Initialize browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await context.new_page()
            self.page.set_default_navigation_timeout(self.timeout)
            self.page.set_default_timeout(self.timeout)
            
            logger.info("✓ Browser started")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
    
    async def stop(self) -> None:
        """Cleanup browser"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("✓ Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def get_page_context(self, force_fresh: bool = False) -> Dict[str, Any]:
        """
        ENHANCED: Capture comprehensive page context with HTML analysis.
        Returns detailed UI analysis for LLM.
        """
        if not self.page:
            return {'ui_text': '', 'html_structure': '', 'selectors': {}, 'url': '', 'cached': False}
        
        current_url = self.page.url
        
        try:
            # Wait for page to stabilize
            await asyncio.sleep(2)
            
            # 1. Capture comprehensive UI data
            ui_data = await self.page.evaluate('''() => {
                // Helper to get element description
                function describeElement(el) {
                    const tag = el.tagName.toLowerCase();
                    const id = el.id ? `#${el.id}` : '';
                    const classes = el.className ? `.${el.className.split(' ').join('.')}` : '';
                    const text = el.innerText?.trim().substring(0, 50) || '';
                    const type = el.type || '';
                    const name = el.name || '';
                    const placeholder = el.placeholder || '';
                    
                    return {
                        tag,
                        id,
                        classes,
                        text,
                        type,
                        name,
                        placeholder,
                        selector: id || (name ? `[name="${name}"]` : classes || tag)
                    };
                }
                
                return {
                    title: document.title,
                    url: window.location.href,
                    bodyText: document.body.innerText,
                    
                    // Interactive elements
                    inputs: Array.from(document.querySelectorAll('input')).slice(0, 20).map(describeElement),
                    buttons: Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"]')).slice(0, 20).map(describeElement),
                    links: Array.from(document.querySelectorAll('a[href]')).slice(0, 20).map(el => ({
                        text: el.innerText?.trim().substring(0, 50) || '',
                        href: el.href,
                        selector: el.id ? `#${el.id}` : `a:has-text("${el.innerText?.trim().substring(0, 20)}")`
                    })),
                    
                    // Forms
                    forms: Array.from(document.querySelectorAll('form')).map((form, i) => ({
                        id: form.id || `form-${i}`,
                        action: form.action,
                        fields: Array.from(form.querySelectorAll('input, select, textarea')).slice(0, 10).map(describeElement)
                    })),
                    
                    // Key containers (for results, products, etc.)
                    containers: Array.from(document.querySelectorAll('[data-component-type], [class*="result"], [class*="product"], [class*="item"]')).slice(0, 10).map(el => ({
                        className: el.className,
                        dataAttrs: Object.fromEntries(
                            Array.from(el.attributes)
                                .filter(attr => attr.name.startsWith('data-'))
                                .map(attr => [attr.name, attr.value])
                        ),
                        text: el.innerText?.trim().substring(0, 100) || ''
                    })),
                    
                    // Page state indicators
                    hasResults: !!document.querySelector('[class*="result"], [class*="product"], article, [data-component-type]'),
                    hasCart: !!document.querySelector('[href*="cart"], [id*="cart"], [class*="cart"]'),
                    hasLogin: !!document.querySelector('input[type="password"], [href*="login"], [href*="signin"]'),
                    hasCheckout: !!document.querySelector('[href*="checkout"], [class*="checkout"], button:has-text("checkout")'),
                    
                    // Visible text headings
                    headings: Array.from(document.querySelectorAll('h1, h2, h3')).slice(0, 10).map(h => h.innerText?.trim()).filter(Boolean)
                };
            }''')
            
            # 2. Generate hash for cache validation
            body_text = ui_data.get('bodyText', '')
            ui_hash = hashlib.sha256(body_text.encode('utf-8')).hexdigest()
            
            # 3. Check cache (unless force_fresh)
            if not force_fresh:
                cached_data = self.ui_cache.get(current_url, ui_hash)
                if cached_data:
                    analysis = cached_data['analysis']
                    analysis['cached'] = True
                    return analysis
            
            # 4. Build comprehensive UI analysis
            analysis = self._build_ui_analysis(ui_data)
            
            # 5. Cache it
            self.ui_cache.set(current_url, ui_hash, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to capture page context: {e}")
            return {'ui_text': f"Error: {e}", 'html_structure': '', 'selectors': {}, 'url': current_url, 'cached': False}
    
    def _build_ui_analysis(self, ui_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive UI analysis for LLM"""
        
        # Format inputs
        inputs_desc = "\n".join([
            f"  - {inp['tag']} (type={inp['type']}, name={inp['name']}, placeholder={inp['placeholder']}) → {inp['selector']}"
            for inp in ui_data.get('inputs', [])[:10]
        ]) or "  (none)"
        
        # Format buttons
        buttons_desc = "\n".join([
            f"  - {btn['text'][:30] or btn['type']} → {btn['selector']}"
            for btn in ui_data.get('buttons', [])[:10]
        ]) or "  (none)"
        
        # Format links
        links_desc = "\n".join([
            f"  - {link['text'][:40]} → {link['selector']}"
            for link in ui_data.get('links', [])[:10]
        ]) or "  (none)"
        
        # Format containers
        containers_desc = "\n".join([
            f"  - .{cont['className'][:50]} (data: {list(cont['dataAttrs'].keys())})"
            for cont in ui_data.get('containers', [])[:5]
        ]) or "  (none)"
        
        # Build structured analysis
        ui_text = f"""
=== PAGE ANALYSIS ===
Title: {ui_data.get('title', 'Unknown')}
URL: {ui_data.get('url', 'Unknown')}

=== PAGE STATE ===
Has Results/Products: {ui_data.get('hasResults', False)}
Has Cart: {ui_data.get('hasCart', False)}
Has Login Form: {ui_data.get('hasLogin', False)}
Has Checkout: {ui_data.get('hasCheckout', False)}

=== HEADINGS ===
{chr(10).join(['  - ' + h for h in ui_data.get('headings', [])[:5]]) or '  (none)'}

=== INPUT FIELDS ===
{inputs_desc}

=== BUTTONS ===
{buttons_desc}

=== LINKS ===
{links_desc}

=== RESULT CONTAINERS ===
{containers_desc}

=== VISIBLE TEXT (excerpt) ===
{ui_data.get('bodyText', '')[:1000]}

=== SELECTOR RECOMMENDATIONS ===
For search input: {self._recommend_search_selector(ui_data)}
For submit button: {self._recommend_submit_selector(ui_data)}
For results: {self._recommend_results_selector(ui_data)}
"""
        
        return {
            'ui_text': ui_text,
            'selectors': {
                'inputs': [inp['selector'] for inp in ui_data.get('inputs', [])],
                'buttons': [btn['selector'] for btn in ui_data.get('buttons', [])],
                'links': [link['selector'] for link in ui_data.get('links', [])],
                'containers': [cont['className'] for cont in ui_data.get('containers', [])]
            },
            'page_state': {
                'has_results': ui_data.get('hasResults', False),
                'has_cart': ui_data.get('hasCart', False),
                'has_login': ui_data.get('hasLogin', False),
                'has_checkout': ui_data.get('hasCheckout', False)
            },
            'url': ui_data.get('url', ''),
            'title': ui_data.get('title', ''),
            'cached': False
        }
    
    def _recommend_search_selector(self, ui_data: Dict) -> str:
        """Recommend best selector for search input"""
        inputs = ui_data.get('inputs', [])
        for inp in inputs:
            if 'search' in inp.get('name', '').lower() or 'search' in inp.get('id', '').lower():
                return inp['selector']
            if inp.get('type') == 'search':
                return inp['selector']
        return "input[type='search'], input[name*='search'], input[name='q']"
    
    def _recommend_submit_selector(self, ui_data: Dict) -> str:
        """Recommend best selector for submit button"""
        buttons = ui_data.get('buttons', [])
        for btn in buttons:
            text = btn.get('text', '').lower()
            if any(word in text for word in ['search', 'go', 'submit']):
                return btn['selector']
        return "button[type='submit'], input[type='submit']"
    
    def _recommend_results_selector(self, ui_data: Dict) -> str:
        """Recommend best selector for results"""
        containers = ui_data.get('containers', [])
        for cont in containers:
            className = cont.get('className', '')
            if any(word in className.lower() for word in ['result', 'product', 'item']):
                return f".{className.split()[0]}"
        return "[class*='result'], [class*='product'], article"
    
    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action"""
        if not self.page:
            return {"status": "failed", "error": "Browser not started"}
        
        action_type = action.get("action")
        
        try:
            logger.info(f"→ Executing: {action_type}")
            
            # Route to appropriate handler
            handler_name = f'_action_{action_type}'
            handler = getattr(self, handler_name, self._action_generic)
            
            result = await handler(action)
            
            logger.info(f"✓ {action_type} completed")
            return result
            
        except PlaywrightError as e:
            error_msg = f"Playwright error in '{action_type}': {str(e)[:200]}"
            logger.error(error_msg)
            self.ui_cache.invalidate(self.page.url)
            return {"status": "failed", "error": error_msg, "action": action}
            
        except Exception as e:
            error_msg = f"Action '{action_type}' failed: {str(e)[:200]}"
            logger.error(error_msg)
            return {"status": "failed", "error": error_msg, "action": action}
    
    async def _action_navigate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        url = action.get("url")
        if not url:
            return {"status": "failed", "error": "Missing URL"}
        
        await self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
        await asyncio.sleep(3)  # Wait for JS
        
        return {"status": "success", "url": url}
    
    async def _action_type(self, action: Dict[str, Any]) -> Dict[str, Any]:
        selector = action.get("selector")
        text = action.get("text")
        press_enter = action.get("press_enter", False)
        
        if not selector or text is None:
            return {"status": "failed", "error": "Missing selector or text"}
        
        try:
            await self.page.wait_for_selector(selector, state="visible", timeout=15000)
            await self.page.fill(selector, str(text))
            await asyncio.sleep(0.5)
            
            if press_enter:
                await self.page.press(selector, "Enter")
                await asyncio.sleep(5)  # Wait for results
            
            return {"status": "success", "selector": selector}
        except:
            # Try fallback selectors
            fallbacks = [
                "input[type='search']",
                "input[name='q']",
                "input[name*='search']",
                "#search",
                "input[type='text']"
            ]
            
            for fb in fallbacks:
                try:
                    await self.page.wait_for_selector(fb, timeout=3000)
                    await self.page.fill(fb, str(text))
                    if press_enter:
                        await self.page.press(fb, "Enter")
                        await asyncio.sleep(5)
                    logger.info(f"Used fallback: {fb}")
                    return {"status": "success", "selector": fb}
                except:
                    continue
            
            return {"status": "failed", "error": f"Could not find input: {selector}"}
    
    async def _action_click(self, action: Dict[str, Any]) -> Dict[str, Any]:
        selector = action.get("selector")
        if not selector:
            return {"status": "failed", "error": "Missing selector"}
        
        await self.page.wait_for_selector(selector, state="visible", timeout=15000)
        await self.page.click(selector)
        await asyncio.sleep(3)
        
        return {"status": "success", "selector": selector}
    
    async def _action_wait(self, action: Dict[str, Any]) -> Dict[str, Any]:
        selector = action.get("selector")
        timeout = action.get("timeout", 15) * 1000  # Increased default
        
        if not selector:
            return {"status": "failed", "error": "Missing selector"}
        
        try:
            await self.page.wait_for_selector(selector, state="attached", timeout=timeout)
            await asyncio.sleep(2)  # Extra stabilization
            return {"status": "success", "selector": selector}
        except:
            # If selector not found, check if page has content anyway
            has_content = await self.page.evaluate('document.body.innerText.length > 100')
            if has_content:
                logger.warning(f"Selector {selector} not found but page has content, continuing...")
                return {"status": "success", "selector": selector, "note": "Selector not found but page loaded"}
            raise
    
    async def _action_extract(self, action: Dict[str, Any]) -> Dict[str, Any]:
        strategy = action.get("strategy", "auto")
        top_n = action.get("top_n", 5)
        
        # Wait for page to stabilize
        await asyncio.sleep(3)
        
        results = await self._extract_with_strategy(strategy, top_n)
        
        # Print results
        if results:
            print("\n" + "="*70)
            print("📊 EXTRACTED RESULTS")
            print("="*70)
            for i, item in enumerate(results, 1):
                print(f"\n{i}. {item.get('title', 'N/A')[:80]}")
                if item.get('price'):
                    print(f"   💰 Price: {item['price']}")
                if item.get('link'):
                    print(f"   🔗 {item['link'][:80]}...")
            print("="*70 + "\n")
        
        return {
            "status": "success" if results else "failed",
            "results": results,
            "count": len(results)
        }
    
    async def _extract_with_strategy(self, strategy: str, top_n: int) -> List[Dict[str, Any]]:
        """Extract data from page"""
        
        # Get current page analysis
        context = await self.get_page_context()
        
        # Use discovered containers
        container_classes = context.get('selectors', {}).get('containers', [])
        
        # Try discovered selectors first
        for cont_class in container_classes[:3]:
            try:
                selector = f".{cont_class.split()[0]}" if cont_class else None
                if not selector:
                    continue
                    
                items = await self.page.query_selector_all(selector)
                if len(items) >= 2:
                    logger.info(f"Using discovered selector: {selector} ({len(items)} items)")
                    return await self._extract_items(items, top_n)
            except:
                continue
        
        # Fallback to common selectors
        fallback_selectors = [
            "div[data-component-type='s-search-result']",
            "[data-asin]:not([data-asin=''])",
            "[class*='result']",
            "[class*='product']",
            "article",
            "li"
        ]
        
        for selector in fallback_selectors:
            try:
                items = await self.page.query_selector_all(selector)
                if len(items) >= 2:
                    logger.info(f"Using fallback selector: {selector}")
                    return await self._extract_items(items, top_n)
            except:
                continue
        
        return []
    
    async def _extract_items(self, items, top_n: int) -> List[Dict[str, Any]]:
        """Extract data from item elements"""
        results = []
        
        for item in items[:top_n]:
            try:
                # Title
                title = None
                for sel in ["h2", "h3", "[class*='title']", "a"]:
                    try:
                        el = await item.query_selector(sel)
                        if el:
                            title = (await el.inner_text()).strip()
                            if title:
                                break
                    except:
                        continue
                
                # Price
                price = None
                for sel in [".a-price-whole", "[class*='price']"]:
                    try:
                        el = await item.query_selector(sel)
                        if el:
                            price = (await el.inner_text()).strip()
                            if price:
                                break
                    except:
                        continue
                
                # Link
                link = None
                try:
                    el = await item.query_selector("a")
                    if el:
                        link = await el.get_attribute("href")
                        if link and not link.startswith("http"):
                            base = f"{self.page.url.split('/')[0]}//{self.page.url.split('/')[2]}"
                            link = base + link
                except:
                    pass
                
                if title:
                    results.append({
                        'title': title[:200],
                        'price': price,
                        'link': link
                    })
            except:
                continue
        
        return results
    
    async def _action_find_best(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Find best item and navigate to it"""
        criteria = action.get("criteria", "cheapest")
        
        # Extract items
        items = await self._extract_with_strategy("auto", 20)
        
        if not items:
            return {"status": "failed", "error": "No items found"}
        
        # Find best
        best = None
        if criteria == "cheapest":
            items_with_price = [i for i in items if i.get('price')]
            if items_with_price:
                best = min(items_with_price, key=lambda x: self._parse_price(x['price']))
        
        if not best or not best.get('link'):
            return {"status": "failed", "error": "Could not find suitable item"}
        
        # Navigate to best item
        await self.page.goto(best['link'])
        await asyncio.sleep(4)
        
        print(f"\n🎯 Selected: {best['title'][:60]} (Price: {best.get('price', 'N/A')})\n")
        
        return {"status": "success", "item": best}
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to float"""
        import re
        match = re.search(r'[\d,]+\.?\d*', price_str.replace(',', ''))
        return float(match.group()) if match else float('inf')
    
    async def _action_add_to_cart(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Add to cart"""
        selectors = [
            "#add-to-cart-button",
            "button[name='submit.add-to-cart']",
            "[id*='add-to-cart']",
            "button:has-text('Add to Cart')"
        ]
        
        for sel in selectors:
            try:
                await self.page.wait_for_selector(sel, timeout=5000)
                await self.page.click(sel)
                await asyncio.sleep(4)
                print("\n✅ Added to cart!\n")
                return {"status": "success"}
            except:
                continue
        
        return {"status": "failed", "error": "Add to cart button not found"}
    
    async def _action_auto_login(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Auto login"""
        domain = self.credentials.get_domain_from_url(self.page.url)
        creds = self.credentials.get(domain)
        
        if not creds:
            return {"status": "failed", "error": f"No credentials for {domain}"}
        
        u_sel = action.get("username_selector", "input[type='email'], input[type='text']")
        p_sel = action.get("password_selector", "input[type='password']")
        s_sel = action.get("submit_selector", "button[type='submit']")
        
        try:
            await self.page.fill(u_sel, creds['username'])
            await asyncio.sleep(0.5)
            await self.page.fill(p_sel, creds['password'])
            await asyncio.sleep(0.5)
            await self.page.click(s_sel)
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            return {"status": "success"}
        except Exception as e:
            return {"status": "failed", "error": str(e)[:100]}
    
    async def _action_human_pause(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Pause for human"""
        message = action.get("message", "Complete manual steps")
        
        print("\n" + "="*70)
        print("⏸️  HUMAN INPUT REQUIRED")
        print("="*70)
        print(f"\n{message}")
        print("\nPress ENTER when done...")
        print("="*70 + "\n")
        
        await asyncio.to_thread(input)
        print("\n✅ Resuming...\n")
        return {"status": "success"}
    
    async def _action_scroll(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Scroll page"""
        direction = action.get("direction", "down")
        amount = action.get("amount", 3) * 400
        
        if direction == "down":
            await self.page.evaluate(f"window.scrollBy(0, {amount})")
        else:
            await self.page.evaluate(f"window.scrollBy(0, -{amount})")
        
        await asyncio.sleep(1)
        return {"status": "success"}
    
    async def _action_screenshot(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot"""
        path = action.get("path", f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        await self.page.screenshot(path=path, full_page=True)
        return {"status": "success", "path": path}
    
    async def _action_generic(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown actions"""
        action_type = action.get("action", "unknown")
        logger.warning(f"Unknown action: {action_type}")
        return {"status": "failed", "error": f"Unknown action: {action_type}"}