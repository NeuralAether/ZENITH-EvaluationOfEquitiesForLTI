"""
Book Value per share is basically 
the total equity of a company divided by 
the number of outstanding shares.
"""

from config import *

class BookData:
    def __init__(self, ticker: str): 
        self.ticker = ticker

    def get_balance_sheet_data(self) -> pd.DataFrame:
        """
        Get the balance sheet data for the ticker.
        """
        ticker_obj = yf.Ticker(self.ticker)
        balance_sheet_data = ticker_obj.quarterly_balance_sheet
        return balance_sheet_data

    def get_book_value_per_share(self) -> pd.DataFrame:
        """
        Get the book value per share for all periods in the dataset.
        """
        balance_sheet_data = self.get_balance_sheet_data()
        book_values = []
        dates = []
        for date, column_data in balance_sheet_data.items():
            total_equity = column_data.get('Stockholders Equity', 0)  # Total equity from the balance sheet
            shares_outstanding = column_data.get('Ordinary Shares Number', 1)  # Number of outstanding shares
            if shares_outstanding == 0:
                book_value_per_share = 0  # Avoid division by zero
            else:
                book_value_per_share = total_equity / shares_outstanding
            
            book_values.append(book_value_per_share)
            dates.append(date)
        result_df = pd.DataFrame({
            'Date': dates,
            'Book Value Per Share': book_values
        })
        result_df.set_index('Date', inplace=True)
        result_df.sort_index(ascending=True, inplace=True)
        return result_df
        
    def get_book_value_per_share_interpolated(self, interpolator: str = 'linear') -> pd.DataFrame: 
        """
        Get the book value per share but interpolated. 
        Date indices are not spanning the entire period, so we need to interpolate the values for the missing dates.
        """
        book_value_df = self.get_book_value_per_share()
        # Create a date range from the earliest to the latest date in the book value data
        date_range = pd.date_range(start=book_value_df.index.min(), end=book_value_df.index.max(), freq='D')
        # Reindex the book value dataframe to this date range
        book_value_df = book_value_df.reindex(date_range)
        # Interpolate the missing values
        book_value_df['Book Value Per Share'] = book_value_df['Book Value Per Share'].interpolate(method=interpolator)
        return book_value_df