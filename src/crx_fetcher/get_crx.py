#!/usr/bin/env python3
import re
import struct
import os
import requests

def extract_id(store_url: str) -> str:
    m = re.search(r'/detail/[^/]+/([a-z]{32})', store_url)
    if not m:
        raise ValueError(f"Couldn't parse extension ID from URL: {store_url}")
    return m.group(1)


def make_download_url(ext_id: str, chrome_version: str) -> str:
    return (
        "https://clients2.google.com/service/update2/crx"
        f"?response=redirect&prodversion={chrome_version}"
        "&acceptformat=crx3"
        f"&x=id%3D{ext_id}%26uc"
    )


def strip_crx_header(crx_bytes: bytes) -> bytes:
    if crx_bytes[:4] != b'Cr24':
        raise RuntimeError("Not a CRX file (missing Cr24 magic)")
    version = struct.unpack_from('<I', crx_bytes, offset=4)[0]

    if version == 2:
        # CRX2: after magic+version (8 bytes), next two 4-byte ints are key_len & sig_len
        key_len, sig_len = struct.unpack_from('<II', crx_bytes, offset=8)
        header_size = 16 + key_len + sig_len
    elif version == 3:
        # CRX3: after magic+version (8 bytes), next 4-byte int is header_proto_len
        header_len = struct.unpack_from('<I', crx_bytes, offset=8)[0]
        header_size = 12 + header_len
    else:
        raise RuntimeError(f"Unsupported CRX version: {version}")

    return crx_bytes[header_size:]

## USE THIS FUNCTION FOR EXTRACTING CRX
def fetch_extension_zip(
    store_url: str,
    zip_filename: str = None,
    chrome_version: str = "114.0.5735.110",
    output_base_dir: str = None
) -> str:
    """
    Download a Chrome extension CRX from the given Web Store URL,
    strip its header, and save the ZIP to:
      <output_base_dir or cwd>/data/scraped_zips/<ext_id>.zip

    Returns the full path to the saved ZIP file.
    """
    ext_id = extract_id(store_url)
    output_dir = output_base_dir or os.getcwd()
    os.makedirs(output_dir, exist_ok=True)

    # Determine filename
    if zip_filename:
        filename = zip_filename if zip_filename.endswith('.zip') else f"{zip_filename}.zip"
    else:
        filename = f"{ext_id}.zip"
    
    zip_path = os.path.join(output_dir, filename)

    # 1) Download CRX
    download_url = make_download_url(ext_id, chrome_version)
    resp = requests.get(download_url, allow_redirects=True)
    resp.raise_for_status()

    # 2) Strip header
    zip_bytes = strip_crx_header(resp.content)

    # 3) Write ZIP
    with open(zip_path, 'wb') as f:
        f.write(zip_bytes)

    return zip_path


# For standalone running, can disregard for usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Download a Chrome extension CRX and save as ZIP."
    )
    parser.add_argument(
        "--url", required=True,
        help="Chrome Web Store URL for the extension."
    )
    parser.add_argument(
        "--zipname", default=None,
        help="Desired ZIP filename (with or without .zip). If omitted, uses the extension ID."
    )
    parser.add_argument(
        "--version", default="114.0.5735.110",
        help="Chrome prodversion to declare (default: %(default)s)"
    )
    parser.add_argument(
        "--outdir", default=None,
        help="Base directory to write 'data/scraped_zips' under (default: cwd)."
    )

    args = parser.parse_args()
    result_path = fetch_extension_zip(
        args.url,
        zip_filename=args.zipname,
        chrome_version=args.version,
        output_base_dir=args.outdir
    )
    print(f"✓ Saved ZIP to {result_path}")
