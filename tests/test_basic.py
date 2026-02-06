import os
import sys

# Add the parent directory (project root) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import proteovis as pv
    print("Successfully imported proteovis")
except ImportError as e:
    print(f"Failed to import proteovis: {e}")
    sys.exit(1)

def test_akta_loading():
    print("Testing AKTA data loading...")
    sample_zip = "samples/sample.zip"
    if not os.path.exists(sample_zip):
        print(f"Skipping AKTA test: {sample_zip} not found")
        return

    try:
        akta_df, frac_df, phase_df, akta_fig = pv.get_akta_data(sample_zip)
        print(f"Successfully loaded AKTA data.")
        print(f"  akta_df shape: {akta_df.shape}")
        print(f"  frac_df rows: {len(frac_df)}")
        print(f"  phase_df rows: {len(phase_df)}")
        print(f"  akta_fig type: {type(akta_fig)}")
    except Exception as e:
        print(f"Failed to load AKTA data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def test_page_loading():
    print("Testing PAGE image loading...")
    sample_img = "samples/cbb.jpg"
    if not os.path.exists(sample_img):
        print(f"Skipping PAGE test: {sample_img} not found")
        return

    try:
        page_fig = pv.get_page_image(sample_img)
        lane_ids = pv.get_page_lane_ids(sample_img)
        print(f"Successfully loaded PAGE image.")
        print(f"  page_fig type: {type(page_fig)}")
        print(f"  lane_ids: {lane_ids}")
    except Exception as e:
        print(f"Failed to load PAGE image: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_akta_loading()
    test_page_loading()
    print("All tests passed!")
