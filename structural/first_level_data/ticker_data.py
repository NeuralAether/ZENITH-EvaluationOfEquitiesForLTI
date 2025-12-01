"""
You give a ticker, and the class manages all functions to get first level data
for that ticker.
"""

from config import * 

class TickerData:
    def __init__(self, ticker: str, start_date: str = None, end_date: str = None): 
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.__data_df = pd.DataFrame() # to store the downloaded data

    """
    Building data between dates function
    """
    
    def get_ticker_data_between_dates(self, **kwargs) -> pd.DataFrame:
        """
        Get first level data for the ticker between the given dates.
        """
        # Check if start_date and end_date are provided in kwargs, else use instance variables
        self.start_date = kwargs.get("start_date", self.start_date)
        self.end_date = kwargs.get("end_date", self.end_date)
        self.__data_df = yf.download(self.ticker, start=self.start_date, end=self.end_date, progress=False)
        self.__data_df.columns = [col[0] if isinstance(col, tuple) else col for col in self.__data_df.columns]
        if kwargs.get("show_data", False):
            return self.__data_df
        
    def get_data(self) -> pd.DataFrame:
        """
        Return the downloaded data.
        """
        return self.__data_df
    
    """
    Plotting with mplfinance
    """

    def plot_data(self, **kwargs):
        """
        Plot the downloaded data using mplfinance.
        """
        if self.__data_df.empty:
            raise ValueError("No data available to plot. Please download data first.")
        
        mpf.plot(self.__data_df, type=kwargs.get("type", "candle"), style=kwargs.get("style", "yahoo"),
                 title=kwargs.get("title", f"{self.ticker} Price Data"),
                 volume=kwargs.get("volume", True))
        
    """
    Some more functions can be added here as needed
    """

    def plot_volumes(self, **kwargs):
        """
        Plot the trading volumes using mplfinance.
        """
        if self.__data_df.empty:
            raise ValueError("No data available to plot. Please download data first.")
        
        sns.lineplot(data=self.__data_df, x=self.__data_df.index, y="Volume")
        plt.title(kwargs.get("title", f"{self.ticker} Trading Volumes"))
        plt.xlabel("Date")
        plt.ylabel("Volume")
        plt.show() 