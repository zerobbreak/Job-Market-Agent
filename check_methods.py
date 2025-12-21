from appwrite.services.databases import Databases
from appwrite.client import Client

db = Databases(Client())
methods = dir(db)
print(f"Has list_rows: {'list_rows' in methods}")
print(f"Has create_string_column: {'create_string_column' in methods}")
print(f"Has list_documents: {'list_documents' in methods}")
print(f"Has create_string_attribute: {'create_string_attribute' in methods}")
print(f"Has create_row: {'create_row' in methods}")
