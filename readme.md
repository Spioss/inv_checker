# CS:GO Inventory Checker

A Python script to check the value of your CS:GO inventory items by fetching current market prices from the Steam Community Market.

## Features

- Retrieves your complete CS:GO inventory from Steam
- Fetches current market prices for each item
- Calculates total inventory value
- Handles Steam API rate limiting with exponential backoff

## Requirements

- Python 3.6+
- `requests` library

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/csgo-inventory-checker.git
cd csgo-inventory-checker
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

Or just install the requests library:
```bash
pip install requests
```

## Usage

1. Open `inv-checker.py` and change the `STEAM_ID` variable to your Steam ID:
```python
STEAM_ID = "YOUR_STEAM_ID_HERE"  # Replace with your Steam ID
```

2. Run the script:
```bash
python inv-checker.py
```

3. The script will:
   - Fetch your CS:GO inventory
   - Retrieve current market prices for each item
   - Display a table with item names, prices, and quantities
   - Show the total value of your inventory

## Finding Your Steam ID

Your Steam ID is required for this tool to work. To find it:

1. Go to your Steam profile page
2. Your Steam ID is in the URL: `https://steamcommunity.com/profiles/XXXXXXXXXXXXXXXXX/`
3. The 17-digit number is your Steam ID

Alternatively, if you have a custom URL, you can find your steamID64 using a [Steam ID finder](https://steamid.io/).

## Output Example

```
Items in inventory: 42

------------------------------------------------------------
NAME                                     PRICE (€)     COUNT
------------------------------------------------------------
AK-47 | Redline (Field-Tested)              10.23 €        1
AWP | Asiimov (Battle-Scarred)              21.45 €        1
★ Karambit | Doppler (Factory New)         573.21 €        1
...
------------------------------------------------------------
Total Value:                                642.67 €
------------------------------------------------------------

Cache saved.
```

## How It Works

1. **Inventory Retrieval**: Fetches your CS:GO inventory items from Steam using the Steam Community API
2. **Price Checking**: For each item, retrieves the current market price from the Steam Market
3. **Caching**: Caches prices to avoid repeated API calls (default cache duration: 24 hours)
4. **Rate Limiting**: Implements smart rate limiting with exponential backoff to avoid HTTP 429 errors

## Configuration

You can modify these parameters in the code:

- `cache_duration_hours`: How long to cache prices (default: 24 hours)
- `currency`: Currency code for prices (default: 3 for Euro €)
- `count`: Number of inventory items to fetch per request (default: 100)

## Troubleshooting

- **"Failed to retrieve inventory items"**: Make sure your Steam profile and inventory are public
- **Rate limiting errors**: The tool implements backoff strategies, but if you encounter persistent rate limiting, try increasing the base delay in the `RateLimiter` class (it will take longer)
- **Missing items**: Some items might not have market prices (e.g., untradable items)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for personal use only and has no affiliation with Valve Corporation or Steam. Use responsibly and be aware of Steam's rate limiting policies.
