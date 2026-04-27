"""
Stock Fetcher Module - Fetch stock information and historical data
"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockFetcher:
    """Class to fetch stock/ETF information from wantgoo.com"""
    
    BASE_URL = "https://www.wantgoo.com/stock"
    
    def __init__(self):
        """Initialize StockFetcher with default headers"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_etf_info(self, stock_code: str) -> Optional[Dict]:
        """
        Fetch ETF information from wantgoo.com
        
        Args:
            stock_code: ETF code (e.g., '00878')
            
        Returns:
            Dictionary containing stock information or None if failed
        """
        try:
            url = f"{self.BASE_URL}/etf/{stock_code}"
            logger.info(f"Fetching data from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            stock_info = self._parse_stock_data(soup, stock_code)
            
            return stock_info
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data for {stock_code}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing data for {stock_code}: {str(e)}")
            return None
    
    def fetch_stock_info(self, stock_code: str) -> Optional[Dict]:
        """
        Fetch stock information from wantgoo.com
        
        Args:
            stock_code: Stock code (e.g., '2330')
            
        Returns:
            Dictionary containing stock information or None if failed
        """
        try:
            url = f"{self.BASE_URL}/{stock_code}"
            logger.info(f"Fetching data from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            stock_info = self._parse_stock_data(soup, stock_code)
            
            return stock_info
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data for {stock_code}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing data for {stock_code}: {str(e)}")
            return None
    
    def _parse_stock_data(self, soup: BeautifulSoup, stock_code: str) -> Dict:
        """
        Parse stock data from BeautifulSoup object
        
        Args:
            soup: BeautifulSoup object
            stock_code: Stock code
            
        Returns:
            Dictionary with parsed stock information
        """
        stock_info = {
            'code': stock_code,
            'url': f"{self.BASE_URL}/etf/{stock_code}" if stock_code.startswith('0') else f"{self.BASE_URL}/{stock_code}",
            'title': None,
            'price': None,
            'status': 'fetched'
        }
        
        # Try to extract title
        title_tag = soup.find('title')
        if title_tag:
            stock_info['title'] = title_tag.get_text(strip=True)
        
        # You can add more specific parsing rules here based on wantgoo.com structure
        # Example: parse price, change percentage, etc.
        
        return stock_info
    
    def fetch_historical_data(self, stock_code: str, days: int = 250) -> Optional[pd.DataFrame]:
        """
        Fetch historical price data using yfinance
        
        Args:
            stock_code: Stock code (台灣股票需要加 .TW 後綴)
            days: Number of days of history to fetch
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            # Add .TW suffix for Taiwan stocks
            if not stock_code.endswith('.TW'):
                yahoo_code = f"{stock_code}.TW"
            else:
                yahoo_code = stock_code
            
            logger.info(f"Fetching historical data for {yahoo_code}")
            
            # Fetch data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            data = yf.download(
                yahoo_code,
                start=start_date,
                end=end_date,
                progress=False,
                interval='1d'
            )
            
            if data.empty:
                logger.warning(f"No data found for {yahoo_code}")
                return None
            
            # Ensure index is datetime
            data.index = pd.to_datetime(data.index)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {stock_code}: {str(e)}")
            return None
