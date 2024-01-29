# Description
Script for claim G points from gg.zip

# Installation

1. Install python 3.10+
2. Run `pip install -r requirements.txt`
3. Fill file `wallets.txt` with your solana addresses
4. Add at least one code to `codes.txt`
5. Run `python main.py`

# Configure
You can edit `APPEND_CODES` variable. It means that new codes will be added to `codes.txt` file after claiming wallets.

Don't clean `used.txt` file. Bot memory (what wallets, codes, names was used) will be saved there.
