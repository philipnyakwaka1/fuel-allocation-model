# Distance and Elevation Calculator

This project involves using Azure Maps and Google Maps API keys to calculate distances and elevation differences between two points. The repository contains two Python scripts:

- **Distance Calculation Script:** [distance_matrix_Azure.py](https://github.com/philipnyakwaka1/distance-matrix/blob/main/elevation_changes_Azure.py)
- **Elevation Calculation Script:** [elevation_changes_Azure.py](https://github.com/philipnyakwaka1/distance-matrix/blob/main/elevation_changes_Azure.py)

## Requirements

- **API Keys:**
  - `subscription_key`: Google Maps API key.
  - `api_key`: Azure Maps API key.
- **Python Packages:** Specified in the `requirements.txt` file.

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/philipnyakwaka1/distance-matrix.git
   ```

2. Navigate to the project directory:
   ```bash
   cd distance-matrix
   ```

3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

4. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Input Data

The scripts read from an Excel file with the following structure:

| origin         | destination    | region         |
|----------------|----------------|----------------|
| 1.2921,36.8219 | -1.2867,36.8172 | Nairobi County |

- **origin**: Latitude, Longitude of the origin point (e.g., `1.2921,36.8219`).
- **destination**: Latitude, Longitude of the destination point (e.g., `-1.2867,36.8172`).
- **region**: The administrative area where the points lie (optional).

### Additional Columns

Before running the script, add the following columns to the input Excel file:

- **cluster**: Administrative sub-boundary (e.g., ward).
- **territory**: Administrative mid-boundary (e.g., district).
- **region**: Administrative top-level boundary (e.g., county).

### Running the Scripts

1. Update the file paths in the scripts to match your input Excel file location.
2. Run the scripts:

   For distance calculation:
   ```bash
   python distance_matrix_Azure.py
   ```

   For elevation calculation:
   ```bash
   python elevation_changes_Azure.py
   ```

## Notes

- Ensure that your input Excel file is properly formatted before running the scripts.
- The scripts are executable and designed to handle latitude and longitude coordinate strings separated by commas.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Feel free to contribute to the project by submitting issues or pull requests!
