from datetime import datetime

def get_version():
   return datetime.today().strftime('%Y.%m.%d')
