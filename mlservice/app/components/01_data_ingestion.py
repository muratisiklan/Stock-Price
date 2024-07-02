import os.path as path
import pandas as pd
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from ..exception import CustomException
from ..logger import logging
from ..utils import get_data_from_yfinance
from ..database import client


@dataclass
class StockIngestionConfig:
    """
    Configuration class for stock data ingestion.
    It reads the symbols from a CSV file and stores them in a list.
    """
    path_to_file: str = path.abspath(
        path.join(__file__, "../../artifacts/base_data/bist_data.csv"))

    try:
        # Read the symbols list from the CSV file
        symbols_list: list = list(pd.read_csv(path_to_file)["Symbol"])
        if not symbols_list:
            raise ValueError("Symbols list is empty.")
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise CustomException(f"File not found: {e}", sys)
    except pd.errors.EmptyDataError as e:
        logging.error(f"Empty data error: {e}")
        raise CustomException(f"Empty data error: {e}", sys)
    except Exception as e:
        logging.error(f"Error reading symbols list: {e}")
        raise CustomException(f"Error reading symbols list: {e}", sys)


class StockIngestion:
    """
    Class responsible for the ingestion of stock data.
    """

    def __init__(self) -> None:
        self.ingestion_config = StockIngestionConfig()

    def get_date_range(self, collection):
        """
        Determine the date range for which data needs to be fetched.
        
        Parameters:
            collection: MongoDB collection for the symbol.

        Returns:
            tuple: Start and end dates for the data retrieval.
        """
        try:
            most_recent_document = collection.find_one({}, sort=[('_id', -1)])
            if most_recent_document:
                most_recent_date = datetime.strptime(
                    most_recent_document["_id"], "%Y-%m-%d")
                start_date = (most_recent_date + timedelta(days=1)
                              ).strftime("%Y-%m-%d")
            else:
                start_date = "2015-01-01"

            end_date = (datetime.now() + timedelta(days=1)
                        ).strftime("%Y-%m-%d")
            return start_date, end_date
        except Exception as e:
            logging.error(f"Error determining date range: {e}")
            raise CustomException(e, sys)

    def ingest_data_for_symbol(self, symbol, collection):
        """
        Ingest data for a given stock symbol into the corresponding MongoDB collection.
        
        Parameters:
            symbol (str): The stock symbol.
            collection: MongoDB collection for the symbol.
        """
        try:
            start_date, end_date = self.get_date_range(collection)
            data = get_data_from_yfinance(symbol, start_date, end_date)

            if not data.empty:
                data['_id'] = pd.to_datetime(
                    data['Date']).dt.strftime("%Y-%m-%d")
                data.drop(columns=['Date'], inplace=True)
                collection.insert_many(data.to_dict(orient='records'))
                logging.info(f"Data ingestion completed for symbol: {symbol}")
            else:
                logging.warning(f"No data retrieved for {symbol}")
        except Exception as e:
            logging.error(f"Error ingesting data for symbol {symbol}: {e}")
            raise CustomException(e, sys)

    def initiate_stock_ingestion(self) -> None:
        """
        Initiates the data ingestion process for all stock symbols.
        """
        stock_db = client.stockdata
        try:
            for symbol in self.ingestion_config.symbols_list:
                logging.info(f"Starting data ingestion for symbol: {symbol}")
                collection = stock_db[symbol]
                self.ingest_data_for_symbol(symbol, collection)
        except CustomException as e:
            logging.error(f"Custom Exception during ingestion: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during ingestion: {e}")
            raise CustomException(e, sys)
        finally:
            client.close()
            logging.info("MongoDB client closed.")


# Example usage
if __name__ == "__main__":
    try:
        stock_ingestion = StockIngestion()
        stock_ingestion.initiate_stock_ingestion()
    except CustomException as e:
        logging.error(f"Failed to ingest stock data: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
