"""
LinkedIn page scraper service
"""
import logging
import asyncio
import aiohttp
from typing import Optional, Dict, List
from datetime import datetime
from urllib.parse import urljoin
import json
import time
import os
import re

from bs4 import BeautifulSoup

# Optional Selenium imports - only needed for browser-based scraping
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.debug("Selenium not installed - browser-based scraping disabled")

from app.utils import retry, async_retry
from app.utils.helpers import truncate_text

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """
    LinkedIn page scraper
    
    Scrapes company page details, posts, and employees
    """
    
    LINKEDIN_BASE_URL = "https://www.linkedin.com"
    SCRAPERAPI_URL = "http://api.scraperapi.com"
    
    def __init__(self, use_browser: bool = False):
        """
        Args:
            use_browser: Use Selenium for JavaScript rendering
        """
        self.use_browser = use_browser
        self.driver = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.scraperapi_key = os.getenv('SCRAPERAPI_KEY', '')
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
    
    def init_browser(self):
        """Initialize Selenium WebDriver with automatic driver management"""
        if not SELENIUM_AVAILABLE:
            logger.error("❌ Selenium not installed. Install with: pip install selenium webdriver-manager")
            self.use_browser = False
            return
        
        try:
            logger.info("🔴 Initializing Chrome browser for LIVE LinkedIn scraping...")
            
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(f"user-agent={self.user_agent}")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            # Headless mode for production (no GUI window)
            if logging.getLogger().level != logging.DEBUG:
                options.add_argument("--headless")
            
            # Use webdriver-manager to auto-download chromedriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            logger.info("✅ Browser initialized successfully for LIVE scraping")
        except Exception as e:
            logger.error(f"❌ Error initializing browser: {str(e)}")
            logger.error("Install webdriver-manager: pip install webdriver-manager")
            self.use_browser = False
    
    async def init_session(self):
        """Initialize async HTTP session"""
        if not self.session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(headers=headers, connector=connector)
    
    async def close_session(self):
        """Close async HTTP session"""
        if self.session:
            await self.session.close()
    
    def close(self):
        """Close browser and session"""
        if self.driver:
            self.driver.quit()
    
    async def fetch_page_details(self, page_id: str) -> Optional[Dict]:
        """
        Fetch company page details using ACTUAL LinkedIn scraping
        
        Priority (UPDATED - Selenium first since ScraperAPI free tier doesn't support LinkedIn):
        1. Selenium Browser (REAL LinkedIn with JS rendering - FREE, no API limits)
        2. Direct HTTP (fallback, might work)
        3. ScraperAPI (only if PAID plan available)
        
        NO DEMO DATA - Only real or error!
        
        Args:
            page_id: LinkedIn page ID (from URL)
        
        Returns:
            Dictionary with REAL page details or None if failed
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔴 SCRAPING REAL DATA: {page_id}")
            logger.info(f"{'='*60}")
            
            # PRIORITY 1: Selenium Browser (REAL data with JS rendering - FREE!)
            if SELENIUM_AVAILABLE:
                logger.info(f"🌐 Trying Selenium Browser (JS rendering, free)...")
                url = f"{self.LINKEDIN_BASE_URL}/company/{page_id}"
                if not self.driver:
                    self.init_browser()
                
                if self.driver:
                    try:
                        page_data = await self._fetch_with_browser(url)
                        if page_data:
                            parsed = self._parse_page_details(page_data, page_id, url)
                            if parsed and parsed.get('followers_count', 0) > 0:
                                logger.info(f"✅ SUCCESS: Got REAL data from Browser")
                                logger.info(f"   Followers: {parsed.get('followers_count', 0)}")
                                logger.info(f"   Employees: {parsed.get('employees_count', 0)}")
                                return parsed
                    except Exception as e:
                        logger.warning(f"⚠️  Browser scraping failed: {str(e)}")
            else:
                logger.warning(f"⚠️  Selenium not available, browser scraping disabled")
            
            # PRIORITY 2: Direct HTTP (fallback, usually blocked)
            logger.info(f"🔗 Trying direct HTTP (may be blocked)...")
            url = f"{self.LINKEDIN_BASE_URL}/company/{page_id}/about"
            page_data = await self._fetch_with_requests(url)
            if page_data:
                parsed = self._parse_page_details(page_data, page_id, url)
                if parsed:
                    logger.info(f"✅ SUCCESS: Got REAL data from direct HTTP")
                    return parsed
            
            # PRIORITY 3: ScraperAPI (only if key configured and user has PAID plan)
            if self.scraperapi_key:
                logger.info(f"📡 Trying ScraperAPI (requires PAID plan for LinkedIn)...")
                page_data = await self._fetch_with_scraperapi(page_id)
                if page_data:
                    logger.info(f"✅ SUCCESS: Got REAL data from ScraperAPI")
                    logger.info(f"   Followers: {page_data.get('followers_count', 0)}")
                    logger.info(f"   Employees: {page_data.get('employees_count', 0)}")
                    return page_data
                else:
                    logger.warning(f"⚠️  ScraperAPI failed (may need PAID plan)")
            
            # NO DEMO DATA - FAIL
            logger.error(f"❌ FAILED: Could not scrape REAL data from LinkedIn for {page_id}")
            logger.error(f"   - Browser: {'Not available' if not SELENIUM_AVAILABLE else 'Failed to scrape'}")
            logger.error(f"   - Direct HTTP: Blocked by LinkedIn")
            logger.error(f"   - ScraperAPI: Not configured or needs PAID plan")
            logger.info(f"{'='*60}")
            logger.error(f"\n💡 SOLUTION: Install Chrome and make sure Selenium can access LinkedIn")
            return None
        
        except Exception as e:
            logger.error(f"❌ Error scraping {page_id}: {str(e)}")
            return None
    
    async def _fetch_with_requests(self, url: str) -> Optional[str]:
        """Fetch page with aiohttp"""
        try:
            if not self.session:
                await self.init_session()
            
            # Try different URL formats
            urls_to_try = [
                url,  # /about page
                url.replace('/about', ''),  # main page
                url.replace('/company/', '/companies/'),  # alternative format
            ]
            
            for attempt_url in urls_to_try:
                try:
                    async with self.session.get(
                        attempt_url, 
                        timeout=aiohttp.ClientTimeout(total=30),
                        allow_redirects=True,
                        ssl=False
                    ) as response:
                        # Check if we got the actual page or login page
                        html = await response.text()
                        
                        # Check if we got redirected to login
                        if 'Sign in' in html and 'login' in response.url.path.lower():
                            logger.debug(f"Got redirected to login page: {response.url}")
                            continue
                        
                        # Check if response is valid
                        if response.status == 200 and len(html) > 1000:
                            logger.debug(f"Successfully fetched from: {attempt_url}")
                            return html
                except asyncio.TimeoutError:
                    logger.debug(f"Timeout for {attempt_url}")
                    continue
                except Exception as e:
                    logger.debug(f"Error fetching {attempt_url}: {str(e)}")
                    continue
            
            return None
        except Exception as e:
            logger.debug(f"Failed to fetch with requests: {str(e)}")
            return None
    
    async def _fetch_with_scraperapi(self, page_id: str) -> Optional[Dict]:
        """
        Fetch REAL LinkedIn company data using ScraperAPI
        
        ScraperAPI:
        - Handles anti-scraping (IP rotation, headers)
        - Renders JavaScript for dynamic content
        - Returns ACTUAL LinkedIn data
        
        Args:
            page_id: LinkedIn company ID (e.g., "eightfoldai")
            
        Returns:
            Dictionary with REAL company data or None if failed
        """
        try:
            if not self.scraperapi_key:
                logger.warning("ScraperAPI key not configured")
                return None
            
            url = f"{self.LINKEDIN_BASE_URL}/company/{page_id}/"
            
            logger.info(f"   Calling ScraperAPI for: {url}")
            
            # ScraperAPI parameters for LinkedIn
            params = {
                'api_key': self.scraperapi_key,
                'url': url,
                'render': 'true',  # CRITICAL: Render JavaScript to get dynamic content
                'country_code': 'us',
                'premium': 'true',  # Use premium rendering for better results
            }
            
            if not self.session:
                await self.init_session()
            
            # Call ScraperAPI
            logger.info(f"   Sending request to ScraperAPI...")
            async with self.session.get(
                self.SCRAPERAPI_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=120),  # Increased timeout for rendering
                ssl=False
            ) as response:
                if response.status != 200:
                    logger.warning(f"   ScraperAPI returned status {response.status}")
                    return None
                
                html = await response.text()
                logger.info(f"   ✓ Received {len(html)} bytes from ScraperAPI")
                
                # Parse the returned HTML to extract REAL data
                if len(html) < 5000:
                    logger.warning(f"   ⚠️  Response too small ({len(html)} bytes), might be error page")
                    return None
                
                # Parse and return REAL LinkedIn data
                parsed = self._parse_page_details(html, page_id, url)
                
                # Validate we got real data (not demo)
                if parsed and parsed.get('followers_count', 0) > 100:
                    logger.info(f"   ✓ Extracted REAL data: {parsed.get('followers_count')} followers")
                    return parsed
                else:
                    logger.warning(f"   ⚠️  No valid data extracted from ScraperAPI response")
                    return None
        
        except asyncio.TimeoutError:
            logger.warning(f"   ⏱️  ScraperAPI timeout - LinkedIn took too long to respond")
            return None
        except Exception as e:
            logger.error(f"   ❌ ScraperAPI error: {str(e)}")
            return None
    
    async def _fetch_with_browser(self, url: str) -> Optional[str]:
        """
        Fetch page with Selenium browser for LIVE LinkedIn data
        
        This is slower (10-20 seconds) but more reliable than HTTP
        because it:
        - Renders JavaScript content
        - Handles dynamic loading
        - Bypasses basic anti-bot measures
        """
        try:
            if not self.driver:
                logger.info("Browser not initialized, initializing now...")
                self.init_browser()
            
            if not self.driver:
                logger.error("Failed to initialize browser")
                return None
            
            logger.info(f"🔴 Browser: Loading {url}")
            self.driver.get(url)
            
            # Wait for main content to load
            logger.info("Waiting for page to render...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for JavaScript and dynamic content
            await asyncio.sleep(3)
            
            # Get the fully rendered page
            html = self.driver.page_source
            logger.info(f"✅ Browser: Successfully fetched {len(html)} bytes from {url}")
            
            return html if len(html) > 2000 else None
        
        except TimeoutException:
            logger.warning(f"⏱️ Browser timeout waiting for {url}")
            return None
        except Exception as e:
            logger.error(f"❌ Browser error: {str(e)}")
            return None
    
    def _parse_page_details(self, html: str, page_id: str, url: str) -> Dict:
        """
        Parse page HTML and extract REAL LinkedIn details
        
        Looks for:
        - Company name (h1, title tag, og:title)
        - Followers count (meta tags, JSON data, visible text)
        - Employees count (company info section)
        - Industry, location, website
        - Description from og:description
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check if we actually got a company page (not login page)
            page_name = self._extract_text(soup, 'h1')
            
            logger.debug(f"   Parsing HTML ({len(html)} bytes)...")
            logger.debug(f"   Found company name: {page_name}")
            
            # If got login page, we failed
            if page_name == 'Sign in' or not page_name or len(html) < 2000:
                logger.warning(f"   ❌ Got login page or invalid HTML (not a company page)")
                return None
            
            # Try to extract structured data from script tags (JSON-LD)
            followers_from_json = self._extract_followers_from_json(html)
            employees_from_json = self._extract_employees_from_json(html)
            
            details = {
                'page_id': page_id,
                'url': f"{self.LINKEDIN_BASE_URL}/company/{page_id}",
                'name': page_name,
                'description': self._extract_meta(soup, 'og:description'),
                'profile_picture_url': self._extract_meta(soup, 'og:image'),
                'industry': self._extract_from_list(soup, 'Industry'),
                'company_size': self._extract_from_list(soup, 'Company size'),
                'headquarters': self._extract_from_list(soup, 'Headquarters'),
                'founded_year': self._extract_year_from_list(soup),
                'website': self._extract_from_list(soup, 'Website'),
                'specialties': [],
                'followers_count': followers_from_json or self._extract_follower_count(soup),
                'employees_count': employees_from_json or self._extract_employee_count(soup),
            }
            
            # Extract specialties
            specialties_text = self._extract_from_list(soup, 'Specialties')
            if specialties_text:
                details['specialties'] = [s.strip() for s in specialties_text.split(',')]
            
            logger.debug(f"   ✓ Extracted: {details['followers_count']} followers, {details['employees_count']} employees")
            
            return details
        
        except Exception as e:
            logger.error(f"   Error parsing page details: {str(e)}")
            return None
    
    def _get_demo_page_data(self, page_id: str) -> Dict:
        """Get demo/mock data for a page (for testing when LinkedIn blocks scraping)"""
        demo_data = {
            'google': {
                'name': 'Google',
                'description': 'Google is an American multinational technology company that specializes in internet-related services and products.',
                'industry': 'Information Technology',
                'company_size': '10,000+',
                'headquarters': 'Mountain View, CA',
                'founded_year': '1998',
                'website': 'www.google.com',
                'specialties': ['Search Engine', 'Cloud Computing', 'AI/ML', 'Online Advertising'],
                'followers_count': 8500000,
                'employees_count': 190234,
            },
            'microsoft': {
                'name': 'Microsoft',
                'description': 'Microsoft is a technology corporation that develops software, computers, and related services.',
                'industry': 'Information Technology',
                'company_size': '10,000+',
                'headquarters': 'Redmond, WA',
                'founded_year': '1975',
                'website': 'www.microsoft.com',
                'specialties': ['Software Development', 'Cloud Computing (Azure)', 'Office Suite', 'Gaming (Xbox)'],
                'followers_count': 5200000,
                'employees_count': 221000,
            },
            'apple': {
                'name': 'Apple',
                'description': 'Apple Inc. is an American technology company that designs, manufactures, and markets consumer electronics.',
                'industry': 'Information Technology',
                'company_size': '10,000+',
                'headquarters': 'Cupertino, CA',
                'founded_year': '1976',
                'website': 'www.apple.com',
                'specialties': ['Consumer Electronics', 'Software', 'Hardware', 'Mobile Devices'],
                'followers_count': 6800000,
                'employees_count': 161000,
            },
            'amazon': {
                'name': 'Amazon',
                'description': 'Amazon.com, Inc. is an American multinational technology and e-commerce company.',
                'industry': 'Internet Retail',
                'company_size': '10,000+',
                'headquarters': 'Seattle, WA',
                'founded_year': '1994',
                'website': 'www.amazon.com',
                'specialties': ['E-commerce', 'Cloud Computing (AWS)', 'Digital Streaming', 'Logistics'],
                'followers_count': 7300000,
                'employees_count': 1540000,
            },
            'deepsolv': {
                'name': 'DeepSolv',
                'description': 'DeepSolv is an innovative technology company focused on AI solutions and data analytics.',
                'industry': 'Information Technology',
                'company_size': '100-500',
                'headquarters': 'Tech Hub',
                'founded_year': '2015',
                'website': 'www.deepsolv.com',
                'specialties': ['AI/ML', 'Data Analytics', 'Software Solutions', 'Consulting'],
                'followers_count': 50000,
                'employees_count': 250,
            }
        }
        
        # Get demo data or create generic one
        if page_id.lower() in demo_data:
            data = demo_data[page_id.lower()].copy()
        else:
            # Generate generic data for unknown companies
            data = {
                'name': page_id.replace('-', ' ').title(),
                'description': f'{page_id.replace("-", " ").title()} is a professional company listed on LinkedIn.',
                'industry': 'Technology',
                'company_size': '100-500',
                'headquarters': 'USA',
                'founded_year': '2010',
                'website': None,
                'specialties': ['Business', 'Technology'],
                'followers_count': 10000 + hash(page_id) % 100000,
                'employees_count': 100 + hash(page_id) % 1000,
            }
        
        return {
            'page_id': page_id,
            'url': f"{self.LINKEDIN_BASE_URL}/company/{page_id}",
            'profile_picture_url': None,  # Will be fetched from real scrape if available
            **data
        }
    
    def _extract_text(self, soup: BeautifulSoup, tag: str) -> Optional[str]:
        """Extract text from first occurrence of tag"""
        element = soup.find(tag)
        return element.get_text(strip=True) if element else None
    
    def _extract_meta(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """Extract from meta tag"""
        meta = soup.find('meta', property=property_name)
        if not meta:
            meta = soup.find('meta', attrs={'name': property_name})
        return meta.get('content') if meta else None
    
    def _extract_from_list(self, soup: BeautifulSoup, label: str) -> Optional[str]:
        """Extract value from info list by label"""
        try:
            # Look for the label
            label_elem = soup.find(string=lambda text: text and label in text)
            if label_elem:
                # Get the parent and then the next sibling
                parent = label_elem.parent
                next_elem = parent.find_next('div')
                if next_elem:
                    return next_elem.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Error extracting {label}: {str(e)}")
        return None
    
    def _extract_year_from_list(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract founded year from page"""
        try:
            text = self._extract_from_list(soup, 'Founded')
            if text:
                import re
                match = re.search(r'(\d{4})', text)
                if match:
                    return int(match.group(1))
        except Exception as e:
            logger.debug(f"Error extracting founded year: {str(e)}")
        return None
    
    def _extract_follower_count(self, soup: BeautifulSoup) -> int:
        """Extract follower count from page"""
        try:
            # Look for follower text
            text = soup.find(string=lambda s: s and 'followers' in s.lower())
            if text:
                import re
                match = re.search(r'([\d.]+[KMB]?)', str(text))
                if match:
                    return self._parse_number(match.group(1))
        except Exception as e:
            logger.debug(f"Error extracting followers: {str(e)}")
        return 0
    
    def _extract_employee_count(self, soup: BeautifulSoup) -> int:
        """Extract employee count from page"""
        try:
            text = self._extract_from_list(soup, 'Employees on LinkedIn')
            if text:
                import re
                match = re.search(r'([\d.]+[KMB]?)', text)
                if match:
                    return self._parse_number(match.group(1))
        except Exception as e:
            logger.debug(f"Error extracting employees: {str(e)}")
        return 0
    
    @staticmethod
    def _parse_number(num_str: str) -> int:
        """Parse number string like '152,472', '1.2K', '1M' to integer"""
        try:
            num_str = num_str.upper().strip()
            
            # Remove commas (for numbers like 152,472)
            num_str = num_str.replace(',', '')
            
            # Handle K, M, B multipliers
            multipliers = {'K': 1000, 'M': 1_000_000, 'B': 1_000_000_000}
            
            for suffix, mult in multipliers.items():
                if suffix in num_str:
                    # Remove the suffix and parse the number
                    base_num = num_str.replace(suffix, '').strip()
                    return int(float(base_num) * mult)
            
            # Plain number
            return int(float(num_str))
        except (ValueError, AttributeError):
            return 0
    
    def _extract_followers_from_json(self, html: str) -> Optional[int]:
        """Extract followers count from JSON-LD or other structured data"""
        try:
            # Look for JSON-LD data
            import re
            json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
            
            for json_str in json_ld_matches:
                try:
                    data = json.loads(json_str)
                    if isinstance(data, dict):
                        # Look for followers in different possible locations
                        followers = data.get('interactionCount', data.get('follows', data.get('numberOfReviews')))
                        if isinstance(followers, str):
                            return self._parse_number(followers)
                        elif isinstance(followers, int) and followers > 0:
                            return followers
                except json.JSONDecodeError:
                    continue
            
            # Look for followers in meta tags or other structures
            if 'followers' in html.lower():
                # Try regex patterns in order of specificity
                # IMPORTANT: Check comma-separated (full numbers) BEFORE K/M/B
                patterns = [
                    # Full numbers with commas - HIGHEST PRIORITY
                    (r'(\d+(?:,\d{3})+)\s+followers', 'full with commas'),
                    (r'(\d+(?:,\d{3})+)\s*followers', 'full with commas flexible'),
                    # K/M/B notation
                    (r'(\d+[.,]\d+[KMB]?)\s*followers', 'decimal K/M/B'),
                    (r'(\d+[KMB])\s*followers', 'integer K/M/B'),
                    # JSON fields
                    (r'"followers":\s*(\d+)', 'JSON followers'),
                    (r'"followerCount":\s*(\d+)', 'JSON followerCount'),
                ]
                
                for pattern, desc in patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        num = self._parse_number(match.group(1))
                        if num > 100:  # Must be reasonable
                            logger.debug(f"   Found followers ({desc}): {match.group(1)} -> {num}")
                            return num
        
        except Exception as e:
            logger.debug(f"Error extracting followers from JSON: {str(e)}")
        
        return None
    
    def _extract_employees_from_json(self, html: str) -> Optional[int]:
        """Extract employees count from JSON-LD or other structured data"""
        try:
            import re
            
            # Look for employees/staff in meta tags
            # IMPORTANT: Check full numbers with commas FIRST
            patterns = [
                # Full numbers with ranges (501-1,000) - HIGHEST PRIORITY
                (r'(\d+(?:,\d{3})*)\s*-\s*(\d+(?:,\d{3})*)\s*employees', 'range with commas'),
                # Full numbers with commas
                (r'(\d+(?:,\d{3})+)\s+employees', 'full with commas'),
                (r'(\d+(?:,\d{3})+)\s*employees', 'full with commas flexible'),
                # K/M/B notation
                (r'(\d+[.,]\d+[KMB]?)\s*employees', 'decimal K/M/B'),
                (r'(\d+[KMB])\s*employees', 'integer K/M/B'),
                # JSON fields
                (r'"employees":\s*(\d+)', 'JSON employees'),
                (r'"numberOfEmployees":\s*(\d+)', 'JSON numberOfEmployees'),
            ]
            
            for pattern, desc in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    # Handle ranges - use the higher number
                    if '-' in match.group(0) and len(match.groups()) > 1:
                        num = self._parse_number(match.group(2))  # Use second number (higher)
                    else:
                        num = self._parse_number(match.group(1))
                    
                    if num > 0:
                        logger.debug(f"   Found employees ({desc}): {match.group(0)} -> {num}")
                        return num
        
        except Exception as e:
            logger.debug(f"Error extracting employees from JSON: {str(e)}")
        
        return None
    
    async def fetch_posts(self, page_id: str, limit: int = 20) -> List[Dict]:
        """
        Fetch recent posts from company page
        
        Args:
            page_id: LinkedIn page ID
            limit: Number of posts to fetch
        
        Returns:
            List of post dictionaries
        """
        try:
            posts = []
            url = f"{self.LINKEDIN_BASE_URL}/company/{page_id}/posts"
            
            html = await self._fetch_with_requests(url)
            if not html and self.use_browser:
                html = await self._fetch_with_browser(url)
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                posts = self._parse_posts(soup, page_id, limit)
            
            logger.info(f"Fetched {len(posts)} posts for {page_id}")
            return posts
        
        except Exception as e:
            logger.error(f"Error fetching posts for {page_id}: {str(e)}")
            return []
    
    def _parse_posts(self, soup: BeautifulSoup, page_id: str, limit: int) -> List[Dict]:
        """Parse posts from page HTML"""
        posts = []
        
        # Note: LinkedIn's HTML structure is complex and changes frequently
        # This is a simplified parser - in production you'd want to update regularly
        post_elements = soup.find_all(attrs={'data-id': True})[:limit]
        
        for i, elem in enumerate(post_elements):
            try:
                post = {
                    'post_id': f"{page_id}_post_{i}_{int(time.time())}",
                    'page_id': page_id,
                    'content': self._extract_post_content(elem),
                    'image_url': self._extract_post_image(elem),
                    'likes_count': self._extract_post_metric(elem, 'like'),
                    'comments_count': self._extract_post_metric(elem, 'comment'),
                    'shares_count': self._extract_post_metric(elem, 'share'),
                    'views_count': self._extract_post_metric(elem, 'view'),
                    'posted_at': datetime.utcnow().isoformat(),
                }
                
                if post['content']:  # Only add if we got content
                    posts.append(post)
            
            except Exception as e:
                logger.debug(f"Error parsing post element: {str(e)}")
                continue
        
        return posts
    
    def _extract_post_content(self, elem) -> Optional[str]:
        """Extract post content/text"""
        try:
            text_elem = elem.find(['p', 'span'])
            if text_elem:
                return truncate_text(text_elem.get_text(strip=True), 500)
        except:
            pass
        return None
    
    def _extract_post_image(self, elem) -> Optional[str]:
        """Extract post image URL"""
        try:
            img = elem.find('img')
            if img and img.get('src'):
                return img['src']
        except:
            pass
        return None
    
    def _extract_post_metric(self, elem, metric_type: str) -> int:
        """Extract engagement metrics from post"""
        try:
            # Look for metric text
            metric_text = elem.find(string=lambda s: s and metric_type in s.lower())
            if metric_text:
                import re
                match = re.search(r'(\d+[KMB]?)', str(metric_text))
                if match:
                    return self._parse_number(match.group(1))
        except:
            pass
        return 0
    
    async def fetch_employees(self, page_id: str, limit: int = 50) -> List[Dict]:
        """
        Fetch employees working at the company
        
        Args:
            page_id: LinkedIn page ID
            limit: Number of employees to fetch
        
        Returns:
            List of employee dictionaries
        """
        try:
            employees = []
            url = f"{self.LINKEDIN_BASE_URL}/company/{page_id}/employees"
            
            html = await self._fetch_with_requests(url)
            if not html and self.use_browser:
                html = await self._fetch_with_browser(url)
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                employees = self._parse_employees(soup, limit)
            
            logger.info(f"Fetched {len(employees)} employees for {page_id}")
            return employees
        
        except Exception as e:
            logger.error(f"Error fetching employees for {page_id}: {str(e)}")
            return []
    
    def _parse_employees(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """Parse employee profiles from page"""
        employees = []
        
        # Find employee profile links/cards
        profile_elements = soup.find_all('div', class_=lambda x: x and 'profile' in x.lower())[:limit]
        
        for elem in profile_elements:
            try:
                employee = {
                    'linkedin_id': self._extract_from_element(elem, 'data-linkedin-id'),
                    'username': self._extract_from_element(elem, 'data-username'),
                    'first_name': self._extract_from_element(elem, 'data-first-name'),
                    'last_name': self._extract_from_element(elem, 'data-last-name'),
                    'headline': self._extract_text(elem, 'h3'),
                    'current_position': self._extract_from_element(elem, 'data-position'),
                }
                
                if employee['username'] or employee['linkedin_id']:
                    employees.append(employee)
            
            except Exception as e:
                logger.debug(f"Error parsing employee: {str(e)}")
                continue
        
        return employees
    
    @staticmethod
    def _extract_from_element(elem, attr: str) -> Optional[str]:
        """Extract attribute value from element"""
        if elem.has_attr(attr):
            return elem[attr]
        return None
