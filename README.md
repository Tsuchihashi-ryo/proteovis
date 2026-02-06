# proteovis

A Python module for extracting and visualizing data from ÄKTA/UNICORN and SDS-PAGE images.

## Features

1. **pycorn**: Extract data (zip) from ÄKTA/UNICORN and create plotly chromatograms.
2. **pypage**: Annotate SDS-PAGE images, automatically input marker size, and add lane information.
3. **api**: High-level functions for combined visualization and data loading.

## Installation

```bash
pip install proteovis
```

## Distribution (for developers)

To build and upload the package to PyPI:

1. Install build tools:
   ```bash
   pip install build twine
   ```

2. Build the distribution files:
   ```bash
   python -m build
   ```

3. Upload to PyPI (requires a PyPI account):
   ```bash
   python -m twine upload dist/*
   ```

## Usage

### High-level API

```python
import proteovis as pv

# Load AKTA data (zip file)
# Returns:
# - akta_df: Main data (UV, Cond, etc.)
# - frac_df: Fraction data
# - phase_df: Phase data
# - akta_fig: Plotly figure
akta_df, frac_df, phase_df, akta_fig = pv.get_akta_data("samples/sample.zip")

# Show the interactive chromatogram
akta_fig.show()

# Load PAGE image and check lanes
page_fig = pv.get_page_image("samples/cbb.jpg", lane_width=50)
page_fig.show()

# Get lane indices
lane_ids = pv.get_page_lane_ids("samples/cbb.jpg")
print(f"Lanes found: {lane_ids}")
```

### Advanced Usage (Low-level modules)

#### pycorn

```python
import proteovis as pv

data = pv.pycorn.load_uni_zip("samples/sample.zip")
df = pv.pycorn.utils.get_series_from_data(data, ["UV 1_280", "Cond", "pH", "Fractions"])
```

#### pypage

```python
import proteovis as pv

cbb = pv.pypage.PageImage("samples/cbb.jpg", lane_width=50)
cbb.annotate_lanes(["marker", "lane1", "lane2"])
fig = cbb.annotated_imshow({}, rectangle=True)
fig.show()
```

## Contributors

- [pyahmed](https://github.com/pyahmed)
- [Tsuchihashi-ryo](https://github.com/Tsuchihashi-ryo)
- [wackywendell](https://github.com/wackywendell)
