
class Crawler:
    """Crawler
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    def fetch_source(self):
        """Fetch target data source
        """
        pass

    def to_html(self):
        """Parsed beautiful soap html data
        """
        pass

    def extract_data(self):
        """Extract tv show metadata from html data
        """
        pass

    def clean_data(self):
        """Expect to clean html data, and extract tv source link
        """
        pass

    def parse_to_schema(self):
        """Parse data to table schema
        """
        pass

    def store_in_db(self):
        """Store data into database
        """
        pass

    def run(self):
        """Run crawler to do right thing
        """
        pass
