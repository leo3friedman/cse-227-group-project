#!/usr/bin/env python3
import re
import struct
import os
import requests

# ─── CONFIG ────────────────────────────────────────────────────────────────
# Paste your Chrome Web Store link here:
STORE_URL      = "https://chromewebstore.google.com/detail/forums-google/ilmbfnfoopkmobbgcgodplkdmhbdfcal"
# (Optional) override the Chrome version string if needed:
CHROME_VERSION = "114.0.5735.110"
# ────────────────────────────────────────────────────────────────────────────

def extract_id(store_url: str) -> str:
    m = re.search(r'/detail/[^/]+/([a-z]{32})', store_url)
    if not m:
        raise ValueError("Couldn't parse extension ID from URL")
    return m.group(1)

def make_download_url(ext_id: str, chrome_version: str) -> str:
    return (
        "https://clients2.google.com/service/update2/crx"
        f"?response=redirect&prodversion={chrome_version}"
        "&acceptformat=crx3"
        f"&x=id%3D{ext_id}%26uc"
    )

def strip_crx_header(crx_bytes: bytes) -> bytes:
    """
    Given the full .crx bytes, detect v2/v3 header length, strip it,
    and return the raw ZIP payload bytes.
    """
    if crx_bytes[:4] != b'Cr24':
        raise RuntimeError("Not a CRX file (missing Cr24 magic)")
    version = struct.unpack_from('<I', crx_bytes, offset=4)[0]

    if version == 2:
        key_len, sig_len = struct.unpack_from('<II', crx_bytes, offset=8)
        header_size = 16 + key_len + sig_len
    elif version == 3:
        header_len = struct.unpack_from('<I', crx_bytes, offset=8)[0]
        header_size = 12 + header_len
    else:
        raise RuntimeError(f"Unsupported CRX version: {version}")

    return crx_bytes[header_size:]

def main():
    ext_id = extract_id(STORE_URL)

    # Use current working directory as the base
    base_dir   = os.getcwd()
    output_dir = os.path.join(base_dir, 'data', 'scraped_zips')
    os.makedirs(output_dir, exist_ok=True)
    zip_path   = os.path.join(output_dir, f"{ext_id}.zip")

    # 1) Download into memory
    download_url = make_download_url(ext_id, CHROME_VERSION)
    print(f"→ Fetching CRX for {ext_id} …")
    resp = requests.get(download_url, allow_redirects=True)
    resp.raise_for_status()

    # 2) Strip header → zip bytes
    print("→ Stripping CRX header …")
    zip_bytes = strip_crx_header(resp.content)

    # 3) Write out the zip
    with open(zip_path, 'wb') as f:
        f.write(zip_bytes)
    print(f"✓ Wrote ZIP to {zip_path!r}")

if __name__ == "__main__":
    main()



