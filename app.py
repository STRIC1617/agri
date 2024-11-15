from flask import Flask, jsonify, request, send_file
import ee
import os
import io
import requests
import rasterio
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
import numpy as np

app = Flask(__name__)

# Initialize Earth Engine API
try:
    ee.Initialize(project='ee-madiganiprasannakumar13')
    print("Earth Engine initialized successfully!")
except Exception as e:
    print(f"Error initializing Earth Engine: {e}")

@app.route('/download_image', methods=['GET'])
def download_image():
    # Get polygon coordinates from the query string or request body
    coords = request.args.get('coords', None)  # Example: "81.27683275539135,16.953016928318974,..."
    if coords is None:
        return jsonify({'error': 'No coordinates provided'}), 400
    
    coords = [tuple(map(float, coord.split(','))) for coord in coords.split(';')]

    # Define the polygon area of interest
    geometry = ee.Geometry.Polygon(coords)

    # Load the Sentinel-2 image collection and filter it by date and cloud cover
    imageCollection = ee.ImageCollection('COPERNICUS/S2') \
        .filterBounds(geometry) \
        .filterDate('2023-01-01', '2023-12-31') \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
        .sort('CLOUDY_PIXEL_PERCENTAGE') \
        .first()

    # Clip the image to the area of interest
    clipped_image = imageCollection.clip(geometry)

    # Cast all bands to Uint16 for consistency
    casted_image = clipped_image.select(['B4', 'B3', 'B2', 'B8']).toUint16()  # RGB + NIR bands

    # Get the download URL for the image (in GeoTIFF format)
    url = casted_image.getDownloadURL({
        'scale': 10,  # 10m resolution for Sentinel-2
        'region': geometry,
        'format': 'GeoTIFF'
    })
    
    # Download the image using the URL
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        # Save the image as a file on the local system
        img = io.BytesIO(response.content)

        # Read the downloaded image with rasterio
        with rasterio.open(img) as src:
            # Read bands: Band 4 (Red), Band 3 (Green), Band 2 (Blue), Band 8 (NIR)
            red = src.read(1)  # Band 4
            green = src.read(2)  # Band 3
            blue = src.read(3)  # Band 2
            nir = src.read(4)  # Band 8

            # Calculate NDVI: (NIR - Red) / (NIR + Red)
            ndvi = (nir - red) / (nir + red)

            # Plot NDVI using matplotlib
            plt.imshow(ndvi, cmap='YlGn')
            plt.colorbar()
            plt.title("NDVI Analysis")
            plt.show()

        # Send the image file as download
        img.seek(0)  # Reset the image pointer to the beginning
        return send_file(img, as_attachment=True, download_name="soil_field_image.tif", mimetype='image/tiff')
    else:
        return jsonify({'error': 'Failed to download image'}), 500


@app.route('/view_geotiff', methods=['POST'])
def view_geotiff():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    try:
        # Open the GeoTIFF image using rasterio
        with rasterio.open(file) as src:
            # Read bands: Band 4 (Red), Band 3 (Green), Band 2 (Blue), Band 8 (NIR)
            red = src.read(1)  # Band 4
            green = src.read(2)  # Band 3
            blue = src.read(3)  # Band 2

            # Calculate NDVI: (NIR - Red) / (NIR + Red)
            ndvi = (blue - red) / (blue + red)

            # Plot NDVI using matplotlib
            plt.imshow(green, cmap='YlGn')
            plt.colorbar()
            plt.title("NDVI Analysis")
            plt.show()
            img_io = io.BytesIO()

            return send_file(img_io, mimetype='image/png', as_attachment=False, download_name='image.png')

    except Exception as e:
        return jsonify({'error': f'Failed to process GeoTIFF image: {str(e)}'}), 500
    
    
if __name__ == '__main__':
    app.run(debug=True)
