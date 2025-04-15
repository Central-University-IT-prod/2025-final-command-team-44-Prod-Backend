import xml.etree.ElementTree as ET
from io import BytesIO
from typing import List


def extract_table_ids(svg_content: bytes) -> List[str]:
    try:
        svg_file = BytesIO(initial_bytes=svg_content)

        tree = ET.parse(svg_file)
        root = tree.getroot()

        table_ids = []

        for elem in root.iter():
            id_attr: str = elem.attrib.get("id")
            if id_attr and (id_attr.startswith("table") or id_attr.startswith("room")):
                table_ids.append(id_attr)

        print(table_ids)

        return table_ids
    except:
        pass
