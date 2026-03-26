import csv
import json
import re
from datetime import datetime


class CleanAndExportPipeline:
    def open_spider(self, spider):
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base = getattr(spider, "export_base", f"export_{spider.name}_{timestamp}")
        self.json_path = f"{base}.jsonl"
        self.csv_path = f"{base}.csv"
        self.jsonfile = open(self.json_path, "w", encoding="utf-8")
        self.csvfile = open(self.csv_path, "w", encoding="utf-8", newline="")
        self.fieldnames = ["url", "source", "title", "price", "rating", "description", "images"]
        self.writer = csv.DictWriter(self.csvfile, fieldnames=self.fieldnames)
        self.writer.writeheader()

    def _clean_text(self, value):
        if value is None:
            return None
        value = re.sub(r"\s+", " ", str(value)).strip()
        return value or None

    def _clean_price(self, value):
        if value is None:
            return None
        txt = re.sub(r"[^\d.,]", "", str(value)).replace(",", ".")
        m = re.search(r"\d+(?:\.\d+)?", txt)
        return m.group(0) if m else None

    def _clean_rating(self, value):
        if value is None:
            return None
        m = re.search(r"(\d+(?:\.\d+)?)", str(value))
        return float(m.group(1)) if m else None

    def process_item(self, item, spider):
        data = dict(item)
        data["title"] = self._clean_text(data.get("title"))
        data["description"] = self._clean_text(data.get("description"))
        data["price"] = self._clean_price(data.get("price"))
        data["rating"] = self._clean_rating(data.get("rating"))
        images = data.get("images") or []
        if isinstance(images, (tuple, set)):
            images = list(images)
        data["images"] = images
        self.jsonfile.write(json.dumps(data, ensure_ascii=False) + "\n")
        row = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in data.items()}
        self.writer.writerow(row)
        return item

    def close_spider(self, spider):
        try:
            self.jsonfile.close()
        finally:
            self.csvfile.close()
