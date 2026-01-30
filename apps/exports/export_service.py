import pandas as pd
import json

class ExportService:
    """
    Service for exporting data to various formats.
    """
    
    @staticmethod
    def to_csv(data, filename):
        df = pd.DataFrame(data)
        return df.to_csv(index=False)

    @staticmethod
    def to_json(data, filename):
        return json.dumps(data, indent=4)
    
    @staticmethod
    def to_excel(data, filename):
        # Implementation for Excel export
        pass
