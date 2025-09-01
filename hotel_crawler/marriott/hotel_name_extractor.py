import json

# Open the JSON file for reading
with open('marriott_hotel_name_extractor_response.json', 'r') as file:
    data = json.load(file)  # Load the JSON data into a Python dictionary

# Now you can use the data variable which holds the parsed JSON

edges = data['data']['search']['properties']['searchByGeolocation']['edges']
for edge in edges:
  print(edge['node']['seoNickname'])
