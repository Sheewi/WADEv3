#!/usr/bin/env python3
"""
Wade CrewAI - Research and Intelligence Tools
"""

import requests
import json
import time
import random
import subprocess
from typing import Dict, List, Any, Optional
from crewai_tools import BaseTool
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import stem
from stem import Signal
from stem.control import Controller
import socket
import threading

class TorBrowserTool(BaseTool):
    name: str = "Tor Browser Research Tool"
    description: str = "Browse and research using Tor network for anonymity"
    
    def __init__(self):
        super().__init__()
        self.tor_proxy = {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050'
        }
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0"
        ]
    
    def _run(self, url: str, action: str = "browse", search_term: str = "") -> str:
        """
        Browse or search using Tor network
        
        Args:
            url: URL to browse or search engine URL
            action: Action to perform (browse, search, crawl)
            search_term: Term to search for
        """
        try:
            # Start Tor if not running
            self._ensure_tor_running()
            
            if action == "browse":
                return self._browse_url(url)
            elif action == "search":
                return self._search_darkweb(search_term)
            elif action == "crawl":
                return self._crawl_onion_site(url)
            else:
                return "Invalid action. Use: browse, search, or crawl"
                
        except Exception as e:
            return f"Error using Tor browser: {str(e)}"
    
    def _ensure_tor_running(self):
        """Ensure Tor service is running"""
        try:
            # Check if Tor is running
            result = subprocess.run(['pgrep', 'tor'], capture_output=True)
            if result.returncode != 0:
                # Start Tor service
                subprocess.run(['sudo', 'systemctl', 'start', 'tor'], check=True)
                time.sleep(5)  # Wait for Tor to start
        except Exception as e:
            raise Exception(f"Failed to start Tor: {e}")
    
    def _browse_url(self, url: str) -> str:
        """Browse a URL through Tor"""
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents)
            }
            
            response = requests.get(url, proxies=self.tor_proxy, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract useful information
                title = soup.find('title')
                title_text = title.get_text() if title else "No title"
                
                # Extract text content
                text_content = soup.get_text()[:2000]  # First 2000 chars
                
                return f"Successfully browsed {url}\n\nTitle: {title_text}\n\nContent preview:\n{text_content}"
            else:
                return f"Failed to browse {url}. Status code: {response.status_code}"
                
        except Exception as e:
            return f"Error browsing URL: {str(e)}"
    
    def _search_darkweb(self, search_term: str) -> str:
        """Search dark web using Tor"""
        try:
            # Common dark web search engines
            search_engines = [
                "http://3g2upl4pq6kufc4m.onion/?q=",  # DuckDuckGo onion
                "http://facebookcorewwwi.onion/search/top/?q=",  # Facebook onion
            ]
            
            results = []
            
            for engine in search_engines:
                try:
                    search_url = f"{engine}{search_term}"
                    headers = {'User-Agent': random.choice(self.user_agents)}
                    
                    response = requests.get(search_url, proxies=self.tor_proxy, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract search results (basic implementation)
                        links = soup.find_all('a', href=True)
                        for link in links[:5]:  # First 5 results
                            if search_term.lower() in link.get_text().lower():
                                results.append(f"- {link.get_text()}: {link['href']}")
                    
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    continue
            
            if results:
                return f"Dark web search results for '{search_term}':\n\n" + "\n".join(results)
            else:
                return f"No results found for '{search_term}' on dark web"
                
        except Exception as e:
            return f"Error searching dark web: {str(e)}"
    
    def _crawl_onion_site(self, url: str) -> str:
        """Crawl an onion site for information"""
        try:
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.get(url, proxies=self.tor_proxy, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract all links
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http') or href.startswith('/'):
                        links.append(href)
                
                # Extract forms (potential attack vectors)
                forms = []
                for form in soup.find_all('form'):
                    action = form.get('action', '')
                    method = form.get('method', 'GET')
                    forms.append(f"Form: {method} {action}")
                
                # Extract emails
                import re
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', response.text)
                
                result = f"Crawled {url}\n\n"
                result += f"Links found: {len(links)}\n"
                result += f"Forms found: {len(forms)}\n"
                result += f"Emails found: {len(emails)}\n\n"
                
                if links:
                    result += "Sample links:\n" + "\n".join(links[:10]) + "\n\n"
                
                if forms:
                    result += "Forms:\n" + "\n".join(forms) + "\n\n"
                
                if emails:
                    result += "Emails:\n" + "\n".join(emails[:5])
                
                return result
            else:
                return f"Failed to crawl {url}. Status code: {response.status_code}"
                
        except Exception as e:
            return f"Error crawling onion site: {str(e)}"

class OSINTTool(BaseTool):
    name: str = "OSINT Intelligence Gathering"
    description: str = "Open Source Intelligence gathering from various sources"
    
    def _run(self, target: str, source: str = "all", data_type: str = "general") -> str:
        """
        Gather OSINT on target
        
        Args:
            target: Target person, company, or domain
            source: Source to search (social_media, search_engines, databases, all)
            data_type: Type of data to gather (personal, corporate, technical)
        """
        try:
            if source == "all":
                return self._comprehensive_osint(target, data_type)
            elif source == "social_media":
                return self._social_media_osint(target)
            elif source == "search_engines":
                return self._search_engine_osint(target)
            elif source == "databases":
                return self._database_osint(target)
            else:
                return "Invalid source. Use: social_media, search_engines, databases, or all"
                
        except Exception as e:
            return f"Error gathering OSINT: {str(e)}"
    
    def _comprehensive_osint(self, target: str, data_type: str) -> str:
        """Comprehensive OSINT gathering"""
        results = []
        
        # Search engines
        results.append(self._search_engine_osint(target))
        
        # Social media
        results.append(self._social_media_osint(target))
        
        # Technical reconnaissance
        if data_type == "technical":
            results.append(self._technical_osint(target))
        
        return "\n\n" + "="*50 + "\n\n".join(results)
    
    def _search_engine_osint(self, target: str) -> str:
        """Search engine OSINT"""
        try:
            search_queries = [
                f'"{target}"',
                f'{target} email',
                f'{target} phone',
                f'{target} address',
                f'{target} linkedin',
                f'{target} facebook',
                f'{target} twitter',
                f'site:linkedin.com "{target}"',
                f'site:facebook.com "{target}"',
                f'filetype:pdf "{target}"'
            ]
            
            results = []
            
            for query in search_queries:
                try:
                    # Use DuckDuckGo for privacy
                    search_url = f"https://duckduckgo.com/html/?q={query}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    response = requests.get(search_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract search results
                        for result in soup.find_all('a', class_='result__a')[:3]:
                            title = result.get_text()
                            link = result.get('href', '')
                            results.append(f"- {title}: {link}")
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception:
                    continue
            
            return f"Search Engine OSINT for '{target}':\n\n" + "\n".join(results[:20])
            
        except Exception as e:
            return f"Error in search engine OSINT: {str(e)}"
    
    def _social_media_osint(self, target: str) -> str:
        """Social media OSINT"""
        try:
            platforms = {
                'LinkedIn': f'https://www.linkedin.com/search/results/people/?keywords={target}',
                'Twitter': f'https://twitter.com/search?q={target}',
                'Facebook': f'https://www.facebook.com/search/people/?q={target}',
                'Instagram': f'https://www.instagram.com/{target}/',
                'GitHub': f'https://github.com/{target}'
            }
            
            results = []
            
            for platform, url in platforms.items():
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        results.append(f"✓ {platform}: Profile found at {url}")
                    else:
                        results.append(f"✗ {platform}: No profile found")
                    
                    time.sleep(2)  # Rate limiting
                    
                except Exception:
                    results.append(f"? {platform}: Unable to check")
            
            return f"Social Media OSINT for '{target}':\n\n" + "\n".join(results)
            
        except Exception as e:
            return f"Error in social media OSINT: {str(e)}"
    
    def _technical_osint(self, target: str) -> str:
        """Technical OSINT for domains/IPs"""
        try:
            results = []
            
            # DNS lookup
            try:
                import socket
                ip = socket.gethostbyname(target)
                results.append(f"IP Address: {ip}")
            except:
                results.append("IP Address: Unable to resolve")
            
            # Whois lookup
            try:
                whois_result = subprocess.run(['whois', target], capture_output=True, text=True, timeout=30)
                if whois_result.returncode == 0:
                    results.append(f"WHOIS Data:\n{whois_result.stdout[:500]}...")
            except:
                results.append("WHOIS: Unable to retrieve")
            
            # Subdomain enumeration
            try:
                subdomains = ['www', 'mail', 'ftp', 'admin', 'test', 'dev', 'api']
                found_subdomains = []
                
                for sub in subdomains:
                    try:
                        subdomain = f"{sub}.{target}"
                        socket.gethostbyname(subdomain)
                        found_subdomains.append(subdomain)
                    except:
                        continue
                
                if found_subdomains:
                    results.append(f"Subdomains found: {', '.join(found_subdomains)}")
                else:
                    results.append("Subdomains: None found")
                    
            except:
                results.append("Subdomains: Unable to enumerate")
            
            return f"Technical OSINT for '{target}':\n\n" + "\n".join(results)
            
        except Exception as e:
            return f"Error in technical OSINT: {str(e)}"
    
    def _database_osint(self, target: str) -> str:
        """Database and breach data OSINT"""
        try:
            # This would integrate with breach databases
            # For demo purposes, showing structure
            results = [
                f"Searching breach databases for '{target}'...",
                "Note: This would check HaveIBeenPwned, DeHashed, etc.",
                "Implement actual API calls for production use"
            ]
            
            return f"Database OSINT for '{target}':\n\n" + "\n".join(results)
            
        except Exception as e:
            return f"Error in database OSINT: {str(e)}"

class WebScrapingTool(BaseTool):
    name: str = "Advanced Web Scraping Tool"
    description: str = "Scrape websites for intelligence and data gathering"
    
    def _run(self, url: str, data_type: str = "all", depth: int = 1) -> str:
        """
        Scrape website for data
        
        Args:
            url: Target URL to scrape
            data_type: Type of data to extract (emails, links, forms, all)
            depth: Crawling depth
        """
        try:
            if data_type == "all":
                return self._comprehensive_scrape(url, depth)
            elif data_type == "emails":
                return self._extract_emails(url)
            elif data_type == "links":
                return self._extract_links(url)
            elif data_type == "forms":
                return self._extract_forms(url)
            else:
                return "Invalid data type. Use: emails, links, forms, or all"
                
        except Exception as e:
            return f"Error scraping website: {str(e)}"
    
    def _comprehensive_scrape(self, url: str, depth: int) -> str:
        """Comprehensive website scraping"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                return f"Failed to access {url}. Status code: {response.status_code}"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract various data types
            emails = self._find_emails(response.text)
            links = self._find_links(soup, url)
            forms = self._find_forms(soup)
            phone_numbers = self._find_phone_numbers(response.text)
            
            # Technology detection
            technologies = self._detect_technologies(response)
            
            result = f"Comprehensive scrape of {url}\n\n"
            result += f"Emails found: {len(emails)}\n"
            result += f"Links found: {len(links)}\n"
            result += f"Forms found: {len(forms)}\n"
            result += f"Phone numbers found: {len(phone_numbers)}\n\n"
            
            if emails:
                result += "Emails:\n" + "\n".join(emails[:10]) + "\n\n"
            
            if phone_numbers:
                result += "Phone numbers:\n" + "\n".join(phone_numbers[:5]) + "\n\n"
            
            if forms:
                result += "Forms:\n" + "\n".join(forms[:5]) + "\n\n"
            
            if technologies:
                result += "Technologies detected:\n" + "\n".join(technologies) + "\n\n"
            
            return result
            
        except Exception as e:
            return f"Error in comprehensive scrape: {str(e)}"
    
    def _find_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text)))
    
    def _find_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers"""
        import re
        phone_patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',
            r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',
            r'\b\d{3}\.\d{3}\.\d{4}\b',
            r'\b\+\d{1,3}\s*\d{3,4}\s*\d{3,4}\s*\d{3,4}\b'
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        return list(set(phones))
    
    def _find_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                links.append(href)
            elif href.startswith('/'):
                from urllib.parse import urljoin
                links.append(urljoin(base_url, href))
        
        return list(set(links))
    
    def _find_forms(self, soup: BeautifulSoup) -> List[str]:
        """Extract form information"""
        forms = []
        for form in soup.find_all('form'):
            action = form.get('action', '')
            method = form.get('method', 'GET')
            
            inputs = []
            for input_tag in form.find_all(['input', 'textarea', 'select']):
                input_type = input_tag.get('type', 'text')
                input_name = input_tag.get('name', '')
                inputs.append(f"{input_type}:{input_name}")
            
            forms.append(f"Form: {method} {action} - Inputs: {', '.join(inputs)}")
        
        return forms
    
    def _detect_technologies(self, response) -> List[str]:
        """Detect web technologies"""
        technologies = []
        
        # Check headers
        headers = response.headers
        
        if 'Server' in headers:
            technologies.append(f"Server: {headers['Server']}")
        
        if 'X-Powered-By' in headers:
            technologies.append(f"Powered by: {headers['X-Powered-By']}")
        
        # Check content
        content = response.text.lower()
        
        if 'wordpress' in content:
            technologies.append("CMS: WordPress")
        elif 'drupal' in content:
            technologies.append("CMS: Drupal")
        elif 'joomla' in content:
            technologies.append("CMS: Joomla")
        
        if 'jquery' in content:
            technologies.append("JavaScript: jQuery")
        
        if 'bootstrap' in content:
            technologies.append("CSS Framework: Bootstrap")
        
        return technologies

# Export research tools
research_tools = [
    TorBrowserTool(),
    OSINTTool(),
    WebScrapingTool()
]