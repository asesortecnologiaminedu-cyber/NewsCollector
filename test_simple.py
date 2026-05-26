import sys
sys.path.insert(0, '/home/nicolai/workspaces/me/NewsCollector')

try:
    from newscollector.newscollector import NewsCollector
    print("SUCCESS: NewsCollector imported")
    
    nc = NewsCollector(sources='newscollector/sources.json', news_name='Test News')
    print("SUCCESS: NewsCollector instantiated")
    
    print("Calling create method...")
    result = nc.create()
    print(f"SUCCESS: Create method returned: {result}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
