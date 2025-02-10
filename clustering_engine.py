import pandas as pd
from sklearn.cluster import KMeans
# from geopy.geocoders import Nominatim
# from geopy.exc import GeocoderTimedOut
import folium
import os
from pyproj import Transformer
import sys

# Extract non-numeric prefix from postcode
def extract_postcode_prefix(postcode):
    """
    Extract the non-numeric prefix from a postcode
    
    Args:
        postcode (str): UK postcode to extract prefix from
        
    Returns:
        str: Non-numeric prefix of the postcode
    """
    prefix = ""
    for char in postcode:
        if not char.isdigit():
            prefix += char
        else:
            break
    return prefix

# Create a transformer object for converting between coordinate systems
# EPSG:27700 is British National Grid
# EPSG:4326 is WGS84 (latitude/longitude)
transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326")

# Function to convert postcodes to coordinates with retry
def get_coordinates(postcode, geolocator=None, retries=None):
    """
    Get coordinates for a postcode from local data files in data/Data/CSV
    
    Args:
        postcode (str): UK postcode
        geolocator: Not used (kept for compatibility)
        retries: Not used (kept for compatibility)
    
    Returns:
        tuple: (latitude, longitude) or None if postcode not found
    """
    try:
        postcode = postcode.strip().upper()
        prefix = extract_postcode_prefix(postcode)
        
        # Update path resolution for PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(__file__)
        
        data_dir = os.path.join(base_path, 'data', 'Data', 'CSV')
        file_path = os.path.join(data_dir, f"{prefix.lower()}.csv")
        
        # Add debug logging
        print(f"Looking for postcode data in: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"No data file found for prefix {prefix} at {file_path}")
            return None
            
        # 3. Read the specific file (no headers, specific columns)
        df = pd.read_csv(file_path, header=None)
        
        # Look for the postcode in first column (index 0)
        match = df[df[0].str.strip().str.upper() == postcode]
        
        if not match.empty:
            # Get easting and northing from columns 3 and 4 (indices 2 and 3)
            easting = float(match.iloc[0][2])
            northing = float(match.iloc[0][3])
            
            # Convert to latitude and longitude
            lat, lon = transformer.transform(easting, northing)
            return (lat, lon)
        else:
            print(f"Postcode {postcode} not found in database")
            return None
            
    except Exception as e:
        print(f"Error getting coordinates for {postcode}: {str(e)}")
        return None


# Main function for grouping postcodes
def group_postcodes(file_path, num_groups):
    try:
        # Read the postcodes from the file (no header, single column)
        print(f"Reading file: {file_path}")
        df = pd.read_csv(file_path, header=None)
        
        # Get postcodes from the first column
        postcodes = df[0].dropna().tolist()
        print(f"Found {len(postcodes)} postcodes")

        # Convert postcodes to coordinates
        coordinates = []
        valid_postcodes = []
        invalid_postcodes = []  # New list to track invalid postcodes

        print("Converting postcodes to coordinates...")
        for postcode in postcodes:
            coords = get_coordinates(postcode)
            if coords:
                coordinates.append(coords)
                valid_postcodes.append(postcode)
            else:
                print(f"Could not find coordinates for postcode: {postcode}")
                invalid_postcodes.append(postcode)  # Track invalid postcodes

        print(f"Successfully got coordinates for {len(coordinates)} out of {len(postcodes)} postcodes")

        if len(coordinates) < num_groups:
            raise ValueError(f"The number of valid coordinates ({len(coordinates)}) is less than the number of groups ({num_groups}).")

        # Apply KMeans clustering
        print(f"Grouping {len(coordinates)} postcodes into {num_groups} groups...")
        kmeans = KMeans(n_clusters=num_groups, random_state=42)
        clusters = kmeans.fit_predict(coordinates)

        # Create a new dataframe with the clusters
        result_df = pd.DataFrame({
            'Postcode': valid_postcodes,
            'Latitude': [coord[0] for coord in coordinates],
            'Longitude': [coord[1] for coord in coordinates],
            'Group': clusters
        })

        # Create a dataframe for invalid postcodes
        invalid_df = pd.DataFrame({
            'Invalid_Postcodes': invalid_postcodes
        })

        print(f"Final dataframe has {len(result_df)} rows")
        print(f"Invalid postcodes: {len(invalid_df)} rows")
        print("Sample of coordinates:", result_df[['Latitude', 'Longitude']].head())
        return result_df, invalid_df  # Return both dataframes

    except Exception as e:
        print(f"Error in group_postcodes: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

# Function to create a map with grouped postcodes
def create_map(grouped_postcodes):
    print("Creating map...")
    print(f"Number of points to plot: {len(grouped_postcodes)}")
    
    # Initialize the map centered around the UK
    m = folium.Map(location=[54.0, -2.0], zoom_start=6)

    # Add points to the map with color-coded groups
    colors = ["red", "blue", "green", "purple", "orange", "darkred", "lightred", "beige", "darkblue", "darkgreen"]
    
    points_added = 0
    for _, row in grouped_postcodes.iterrows():
        try:
            folium.CircleMarker(
                location=(row['Latitude'], row['Longitude']),
                radius=5,
                color=colors[row['Group'] % len(colors)],
                fill=True,
                fill_color=colors[row['Group'] % len(colors)],
                fill_opacity=0.7,
                popup=f"Postcode: {row['Postcode']}\nGroup: {row['Group']}"
            ).add_to(m)
            points_added += 1
        except Exception as e:
            print(f"Error adding point for postcode {row['Postcode']}: {str(e)}")

    print(f"Successfully added {points_added} points to the map")
    return m

# Main code run
if __name__ == "__main__":
    input_file = "postcodes_list_column.csv"  # Replace with your file path
    number_of_groups = 4  # Replace with the desired number of groups of close postcodes

    try:
        grouped_postcodes, invalid_postcodes = group_postcodes(input_file, number_of_groups)  # Get both dataframes
        output_file = "grouped_postcodes.xlsx"
        
        # Create Excel writer object
        with pd.ExcelWriter(output_file) as writer:
            grouped_postcodes.to_excel(writer, sheet_name='Valid Postcodes', index=False)
            invalid_postcodes.to_excel(writer, sheet_name='Invalid Postcodes', index=False)
        
        print(f"Grouped postcodes and invalid postcodes saved to {output_file}")

        # Create and save the map
        postcode_map = create_map(grouped_postcodes)
        map_file = "grouped_postcodes_map.html"
        postcode_map.save(map_file)
        print(f"Map saved to {map_file}")

    except Exception as e:
        print(f"Error: {e}")
