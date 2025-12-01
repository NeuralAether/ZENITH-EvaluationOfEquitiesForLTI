"""
Book Value per share is basically 
the total equity of a company divided by 
the number of outstanding shares.
"""

from config import *

class BookData:
    def __init__(self, ticker: str): 
        self.ticker = ticker

    def get_book_value_per_share(self) -> float:
        """
        Get the book value per share for the ticker.
        """
        # Uses quarterly balance sheet data