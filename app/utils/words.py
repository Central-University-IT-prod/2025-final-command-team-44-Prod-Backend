get_russion_table_name = lambda x: 'Стол ' + x.split("table")[1] if "table" in x else 'Комната ' + x.split("room")[1]
