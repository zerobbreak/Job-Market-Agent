from appwrite.client import Client
from appwrite.services.databases import Databases
import os

try:
    client = Client()
    databases = Databases(client)
    
    print("Methods on Databases object:")
    for method in dir(databases):
        if not method.startswith('_'):
            print(method)
            
except Exception as e:
    print(f"Error: {e}")
