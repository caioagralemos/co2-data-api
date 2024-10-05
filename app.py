import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def processar_coordenadas():
  try:
    latitude = float(request.args.get('latitude'))
    longitude = float(request.args.get('longitude'))

    if latitude is None or longitude is None:
      return jsonify({'error': 'Send a latitude/longitude post request to get CO2 emissions data.'}), 400

    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
      return jsonify({'error': 'Invalid data!'}), 400

    result = getData(latitude, longitude)

    return jsonify({'result': result})

  except requests.exceptions.RequestException as e:
    return jsonify({'error': f'HTTP req error: {e}'}), 500
  except KeyError as e:
    return jsonify({'error': f'Key error: {e}'}), 500
  except ValueError as e:
    return jsonify({'error': f'Value error: {e}'}), 500
  except Exception as e:
    return jsonify({'error': str(e)}), 500


def getData(latitude, longitude):
    STAC_API_URL = "https://earth.gov/ghgcenter/api/stac"
    RASTER_API_URL = "https://earth.gov/ghgcenter/api/raster"
    collection_name = "odiac-ffco2-monthgrid-v2023"

    items = requests.get(
        f"{STAC_API_URL}/collections/{collection_name}/items?limit=300"
    ).json()["features"]

    local = {
        "type": "Feature", 
        "properties": {},
        "geometry": {
            "coordinates": [
                [
                    [longitude, latitude],
                    [longitude, latitude-0.20],
                    [longitude-0.20, latitude-0.20], 
                    [longitude-0.20, latitude], 
                    [longitude, latitude],  
                ]
            ],
            "type": "Polygon",
        },
    }

    asset_name = "co2-emissions"


    def generate_stats(item, geojson):
        result = requests.post(
            f"{RASTER_API_URL}/cog/statistics",
            params={"url": item["assets"][asset_name]["href"]},
            json=geojson,
        ).json()

        return {
            **result["properties"],
            "start_datetime": item["properties"]["start_datetime"][:7],
        }


    stats = generate_stats(items[0], local)

    co2data = stats['statistics']['b1']
    return f"CO2 data (monthly emissions on tonne C/km²/month):\n     minimal: {co2data['min']}\n     mean {co2data['mean']}\n     max {co2data['max']}\n     majority {co2data['majority']}"

if __name__ == '__main__':
  app.run(debug=True)