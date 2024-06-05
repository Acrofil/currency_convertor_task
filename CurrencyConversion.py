#!/usr/bin/env python

import sys
import re
import datetime
import requests
import json
from cachetools import TTLCache
import cachetools

# Set cache with max size of 200 and ttl of 5 min
cache = TTLCache(maxsize=200, ttl=300)

# Quit the program on end input
def quit_program(user_input):
    """ Quit """
    if user_input.lower() == 'end':
        sys.exit(0)

# Load api key from config
def load_api_key():
    """ Load api key from config.json"""

    config_path = 'config.json'

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    return config['api_key']

# Get date input from command line argument
def get_date_input():
    """ Get the command line argument """
    try: 

        try:
            # Get user command line argument
            date_input = sys.argv[1]
        
        except IndexError:
            print("You must enter date as command line argument!")
            sys.exit(1)

        if not is_valid_date(date_input):
            print("Please enter a valid date format!")
            sys.exit(1)
        
        return True
    except Exception as e:
        print(f'An error occured: {e}')

# Validate date
def is_valid_date(date_str):
    """ Validate the date submited as command line argument when the program is started"""
    
    # Parse the date string
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")

    # Extract the date
    date = date_obj.date()

    # Get todays date
    today = datetime.date.today()

    if date > today:
        raise ValueError('Date cant be in the future!')

    # Match days 0-31
    day_regex = re.compile(r'(?:0[1-9]|[12]\d|3[01])')
    # Match months 01-12
    month_regex = re.compile(r'(?:0[1-9]|1[0-2])')

    """Checks if the date string is in YYYY-MM-DD format with valid day based on month and year"""
    try:
        if not (day_regex.match(date_str.split('-')[2]) and month_regex.match(date_str.split('-')[1])):
            raise ValueError("Invalid date format")  # Invalid day or month format

        # Validation based on month, day and year (leap or not)
        day = int(date_str.split('-')[2])
        month = int(date_str.split('-')[1])
        year = int(date_str.split('-')[0])

        try:
            if month in (4, 6, 9, 11) and day > 30:  # Months with 30 days
                raise ValueError("Invalid day for month!")
            elif month == 2 and day > 28:
                # Leap year validation
                if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                    return True # Leap year, February can have 29 days
                else:
                    raise ValueError("Invalid day for February (not a leap year)!") # Not a leap year
                
        except ValueError as e:
            print(e)
            return False

        # Rest of the dates are valid
        return True
    except ValueError as e:
        return False

# Validate entered amount
def is_valid_amount(amount):
    """ Validate user amount input if its meeting the requirements specified by the task"""

    if '.' not in amount:
        return amount.isdigit()
    
    first_part, second_part = amount.split('.')

    if not first_part.isdigit() or not second_part.isdigit():
        return False

    if len(second_part) < 1 or len(second_part) > 2:
        return False

    return True

# Get all currencies available in Fast Forex using the API
def get_all_currencies(api_key): 
    """ Function that fetches all currencies that Fast Forex supports
    This data will be used later to validate user base and target currencies inputs if they exists and are valid inputs"""

    url = f"https://api.fastforex.io/currencies?api_key={api_key}"
    headers = {
        "accept": "application/json",
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        currencies = response.json()['currencies']
    else:
        print(f"Error: {response.status_code}")

    return currencies

# Cache each API call and use the cache
@cachetools.cached(cache)
def convert_currency(base, target, amount, api_key):
    """Function that makes API call to Fast Forex and converts from base to target the amount entered by the user
    Upon successfull conversion the conversion data is saved. """

    url = f"https://api.fastforex.io/convert?from={base}&to={target}&amount={amount}&api_key={api_key}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)

    conversion_history = []

    if response.status_code == 200:
        result = response.json()['result']
        date = sys.argv[1]

        # Save conversion data
        conversion_data = {
            'date': date,
            'amount': amount,
            'base_currency': base,
            'target_currency': target,
            'converted_amount': result[target.upper()]
        }

        # Save to json
        save_conversion_data(conversion_history, conversion_data)
    else:
        print(f"Error: {response.status_code}")

    return result

# Save to conversion_data.json by appending the new conversion data
def save_conversion_data(old_data, new_data, filename="conversion_data.json"):
    """Saves each new API conversion data to a JSON file."""

    try:
        old_data.append(new_data)
        with open(filename, "a") as outfile:
            json.dump(old_data, outfile, indent=4)
    except (OSError, json.JSONDecodeError) as e:  # Handle potential errors
        print(f"Error saving data: {e}")

# Get amount to be converted from user input
def get_amount():
    """Function that gets the user amount input and checks if its valid amount based on the programm requirements 
    User will be prompted until valid amount is entered or end the program"""
    
    while True:
        amount_input = input("Please enter amount to convert: ")
        quit_program(amount_input)

        if not is_valid_amount(amount_input):
            print("Please enter a valid amount!")
        
        return float(amount_input)

# Get both base and target currency codes
def get_currency_code(currencies, base_currency=False, target_currency=False):
    """Function that gets both base and target currency codes and checks if they exists
    Promt the user again if not until valid input is entered or is ended by the user with END"""

    while True:
        currency_input = input(f"Please enter {'base' if base_currency else 'target'} currency: ").lower()
        quit_program(currency_input)
        currency = currency_input.upper()
    
        if not currencies.get(f'{currency}'):
            print("Please enter a valid currency code!")
            continue

        return currency_input

# All user inputs and final result
def currency_data_input(api_key, currencies):
    """Main function that calls each needed user input by the program and shows the result. 
    It will run until end/END is entered"""

    while True:
        amount_to_convert = get_amount()
        base_currency = get_currency_code(currencies, base_currency=True).upper()
        target_currency = get_currency_code(currencies, target_currency=True).upper()
        convertion_result = convert_currency(base_currency, target_currency, float(amount_to_convert), api_key)

        if convertion_result:
            print(f'{amount_to_convert} {base_currency} is {convertion_result[target_currency]} {target_currency}')

# Start the program
# Load the api and get all currencies
def main():
    if get_date_input():
        api_key = load_api_key()
        currencies = get_all_currencies(api_key)
        currency_data_input(api_key, currencies)
        
if __name__ == "__main__":
    main()