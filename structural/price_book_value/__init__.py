"""
P/B calculation and analysis module.
"""

from config import *
from structural.first_level_data.ticker_data import TickerData
from structural.first_level_data.book_data import BookData

class PriceBookValue:
    def __init__(self, ticker: str, start_date: str = None, end_date: str = None):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.ticker_data = TickerData(ticker, start_date, end_date)
        self.book_data = BookData(ticker)

    def plot_price_to_book(self, **kwargs):
        """
        Plot the Price to Book ratio for the given ticker and date range.
        """
        pb_data = self.calculate_price_to_book()
        pb_data['Price to Book'].plot(title=kwargs.get("title", f"{self.ticker} Price to Book Ratio"))
        plt.xlabel(kwargs.get("xlabel", "Date"))
        plt.ylabel(kwargs.get("ylabel", "Price to Book Ratio"))
        plt.grid()
        plt.show()
    
    def plot_price_data(self, **kwargs):
        """
        Plot the stock price data for the given ticker and date range.
        """
        self.ticker_data.get_ticker_data_between_dates()
        price_data = self.ticker_data.get_data()

        # Add the interpolated book value series on top of the mpf price plot.
        interpolator = kwargs.get("interpolator", "linear")
        book_value_data = self.book_data.get_book_value_per_share_interpolated(interpolator)
        aligned_book_value = book_value_data['Book Value Per Share'].reindex(price_data.index)
        aligned_book_value = aligned_book_value.interpolate(method='time').ffill().bfill()

        book_overlay = mpf.make_addplot(
            aligned_book_value,
            panel=0,
            color=kwargs.get("book_color", "tab:blue"),
            width=kwargs.get("book_linewidth", 1.2),
            secondary_y=kwargs.get("book_secondary_y", True)
        )

        mpf.plot(
            price_data,
            type=kwargs.get("type", "candle"),
            style=kwargs.get("style", "yahoo"),
            title=kwargs.get("title", f"{self.ticker} Price Data"),
            volume=kwargs.get("volume", True),
            addplot=book_overlay,
            ylabel=kwargs.get("ylabel", "Price"),
            ylabel_lower=kwargs.get("ylabel_lower", "Volume")
        )

    def calculate_price_to_book(self) -> pd.DataFrame:
        """
        Calculate the Price to Book ratio for the given ticker and date range.
        """
        # Get the stock price data
        self.ticker_data.get_ticker_data_between_dates()
        price_data = self.ticker_data.get_data()
        
        # Get the interpolated book value per share data
        book_value_data = self.book_data.get_book_value_per_share_interpolated()
        
        # Merge the price data and book value data on the date index
        merged_data = price_data.merge(book_value_data, left_index=True, right_index=True, how='inner')
        
        # Calculate the Price to Book ratio
        merged_data['Price to Book'] = merged_data['Close'] / merged_data['Book Value Per Share']
        
        return merged_data[['Price to Book']]