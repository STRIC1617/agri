# import ee

# ee.Authenticate()
# ee.Initialize()

import ee
try:
    ee.Initialize(project='ee-madiganiprasannakumar13')
    # Test by fetching a sample dataset
    dataset = ee.Image('USGS/SRTMGL1_003')
    print("Successfully initialized Earth Engine and fetched a sample dataset!")
except Exception as e:
    print(f"Error initializing Earth Engine: {e}")
