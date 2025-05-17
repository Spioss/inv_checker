#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CS:GO Inventory Checker
A tool to check the value of your CS:GO inventory items by fetching
current market prices from the Steam Community Market.

Author: Lukas Mader
GitHub: 
Version: 1.0.0
"""

import requests
import time
import json
import os
from urllib.parse import quote
from datetime import datetime, timedelta
import random

# RateLimiter for requirements management bcs of 429 (too many requests)
class RateLimiter:
    def __init__(self, base_delay=1.0, max_delay=60.0, jitter=0.2):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.last_request_time = 0
        self.consecutive_429 = 0
    
    def wait(self):
        now = time.time()
        elapsed = now - self.last_request_time
        delay = self.base_delay
        
        jitter_amount = random.uniform(-self.jitter * delay, self.jitter * delay)
        delay += jitter_amount
        
        if elapsed < delay:
            time.sleep(delay - elapsed)
        
        self.last_request_time = time.time()
    
    def handle_429(self):
        self.consecutive_429 += 1
        delay = min(self.base_delay * (2 ** self.consecutive_429), self.max_delay)
        print(f"[429] Too many requests. Waiting for {delay:.1f}s before next attempt.")
        time.sleep(delay)
    
    def success(self):
        self.consecutive_429 = 0


# Cache system for storing
class PriceCache:
    def __init__(self, cache_file='price_cache.json', cache_duration_hours=24):
        self.cache_file = cache_file
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache = self._load_cache()
    
    def _load_cache(self):
        if not os.path.exists(self.cache_file):
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                return cache_data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading cache: {e}")
            return {}
    
    def save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except IOError as e:
            print(f"Failed to save cache: {e}")
    
    def get(self, item_name):
        if item_name not in self.cache:
            return None
        
        cached_item = self.cache[item_name]
        timestamp = cached_item.get('timestamp')
        
        if timestamp:
            cached_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - cached_time > self.cache_duration:
                return None
            
        return cached_item.get('data')
    
    def set(self, item_name, data):
        self.cache[item_name] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
        self.save_cache()


# API Client for prices and inventory items
class SteamMarketAPI:
    def __init__(self, steam_id, cache_duration_hours=24):
        self.steam_id = steam_id
        self.limiter = RateLimiter(base_delay=1.0)
        self.cache = PriceCache(cache_duration_hours=cache_duration_hours)
        self.session = requests.Session() 
    
    def fetch_csgo_inventory(self, count=100, lang='english'):
        appid = 730  # CS:GO
        contextid = 2  # CS:GO
        
        url = f'http://steamcommunity.com/inventory/{self.steam_id}/{appid}/{contextid}'
        params = {'l': lang, 'count': count}
        
        all_assets = []
        descriptions = []
        last_assetid = None
        more_items = True
        first = True
        
        while more_items:
            if last_assetid:
                params['start_assetid'] = last_assetid
            
            self.limiter.wait()
            
            max_retries = 5
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    resp = self.session.get(url, params=params, timeout=10)
                    
                    if resp.status_code == 429:
                        self.limiter.handle_429()
                        retry_count += 1
                        continue
                    
                    resp.raise_for_status()
                    self.limiter.success()
                    
                    data = resp.json()
                    break 
                    
                except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"Failed to retrieve inventory after {max_retries} attempts: {e}")
                        return {'assets': all_assets, 'descriptions': descriptions}
                    
                    delay = min(2 ** retry_count, 60)
                    print(f"Inventory retrieval error: {e}. Waiting for {delay}s before next attempt.")
                    time.sleep(delay)
            
            if not data:
                break
                
            if first:
                descriptions = data.get('descriptions', [])
                first = False
            
            current_assets = data.get('assets', [])
            all_assets.extend(current_assets)
            
            more_items = data.get('more_items', 0) == 1
            last_assetid = data.get('last_assetid')
            
            print(f"The retrieved {len(current_assets)} entries. Total: {len(all_assets)}. Other items: {more_items}")
            
            if not more_items or not last_assetid:
                break
        
        return {'assets': all_assets, 'descriptions': descriptions}
    
    def get_price(self, market_hash_name, currency=3, max_retries=5):
        # first try from cache (if exists)
        cache_result = self.cache.get(market_hash_name)
        if cache_result is not None:
            return cache_result
        
        encoded_name = quote(market_hash_name, safe='')
        url = f'https://steamcommunity.com/market/listings/730/{encoded_name}/render'
        
        params = {
            'start': 0,
            'count': 1,
            'currency': currency,
            'format': 'json',
            'language': 'english'
        }
        
        for attempt in range(max_retries + 1):
            self.limiter.wait()
            
            try:
                resp = self.session.get(url, params=params, timeout=10)
                
                if resp.status_code == 429:
                    self.limiter.handle_429()
                    continue
                
                resp.raise_for_status()
                self.limiter.success()
                
                data = resp.json()
                listinginfo = data.get('listinginfo', {})
                
                if not listinginfo:
                    result = {'price': 0.0, 'quantity': 0}
                else:
                    info = next(iter(listinginfo.values()))
                    price_raw = info.get('converted_price')
                    fee_raw = info.get('converted_fee', 0)
                    quantity = info.get('quantity', 0)
                    
                    price = (price_raw + fee_raw) / 100 if price_raw is not None else 0.0
                    result = {'price': price, 'quantity': quantity}
                
                # Cache save
                self.cache.set(market_hash_name, result)
                return result
                
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else None
                if status == 429 and attempt < max_retries:
                    self.limiter.handle_429()
                    continue
                print(f"Chyba pri načítaní {market_hash_name}: {e}")
            except Exception as e:
                print(f"Neočekávaná chyba pre {market_hash_name}: {e}")
            
            if attempt == max_retries:
                return {'price': 0.0, 'quantity': 0}


def main():
    STEAM_ID = "YOUR_STEAM_ID_HERE"  # STEAM_ID

    api = SteamMarketAPI(STEAM_ID, cache_duration_hours=24)
    inventory = api.fetch_csgo_inventory()
    
    if not inventory['assets']:
        print("Failed to retrieve inventory items.")
        return
    
    print(f"Items in inventory : {len(inventory['assets'])}")
    
    # Vytvorenie mapy pre popis položiek
    desc_map = {
        (d['classid'], d['instanceid']): d
        for d in inventory['descriptions']
    }
    
    total = 0.0
    items = []
    for asset in inventory['assets']:
        key = (asset['classid'], asset['instanceid'])
        desc = desc_map.get(key)
        if not desc:
            continue
        
        name = desc['market_hash_name']
        items.append((name, desc))
    
    
    print("\n" + "-" * 60)
    print(f"{'NAME':<40} {'PRICE (€)':>10} {'COUNT':>8}")
    print("-" * 60)
    
    # price for all assets
    for name, desc in items:
        price_info = api.get_price(name)
        price = price_info.get('price', 0.0) if price_info else 0.0
        
        if price > 0:
            total += price
            print(f"{name:<40} {price:>10.2f} € {1:>8}")
    
    # total value
    print("-" * 60)
    print(f"{'Total Value:':<40} {total:>10.2f} €")
    print("-" * 60)
    
    api.cache.save_cache()
    print("\nCache saved.")


if __name__ == '__main__':
    main()