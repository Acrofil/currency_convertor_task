import pytest
import datetime
from unittest.mock import patch, MagicMock
import json
import cachetools

class TestValidInput:
    def test_get_date_input_no_argument(self, mocker):
        from CurrencyConversion import get_date_input

        # Mock `sys.argv` to have no argument
        mocker.patch('sys.argv', ['currency_conversion.py'])

        with pytest.raises(SystemExit):
            get_date_input()
    
    def test_get_date_input_invalid_format(self, mocker):
        from CurrencyConversion import get_date_input

        # Mock `sys.argv` with an invalid date format
        mocker.patch('sys.argv', ['currency_conversion.py', '2024-22222-333333'])

        with pytest.raises(SystemExit):
            get_date_input()

    def test_is_valid_date(self):
        from CurrencyConversion import is_valid_date

        # Set a future date for testing valid date
        future_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        
        assert is_valid_date('2024-06-01') == True # Test supported date format
        assert is_valid_date('2020-02-29') == True # Test leap year
         
        with pytest.raises(ValueError):
            is_valid_date('2024-06-32') # Test out of range date
            is_valid_date('20240601')
            is_valid_date('2023-14-33') # Test month and day
            is_valid_date('2020-02-30') # Test Feb out of range
            is_valid_date('2023-02-29') # Test non leap year
            is_valid_date(future_date) # Test future date


    # Test valid amount inputs
    def test_is_valid_amount(self):
        from CurrencyConversion import is_valid_amount

        assert is_valid_amount('10.23') == True
        assert is_valid_amount('10.2') == True
        assert is_valid_amount('10') == True
    

    # Test not valid amount inputs
    def test_is_invalid_amount(self):
        from CurrencyConversion import is_valid_amount

        assert is_valid_amount('10.235') == False
        assert is_valid_amount('10.') == False
        assert is_valid_amount('10a') == False
        assert is_valid_amount('10.5a') == False
        assert is_valid_amount('10a.23') == False
        assert is_valid_amount('-10.23') == False
    

    def test_get_currency_code_base(self, mocker):
        from CurrencyConversion import get_currency_code

        # Mock get_all_currencies to return a test dictionary
        mock_currencies = {'USD': 'US Dollar', 'EUR': 'Euro'}
        mocker.patch('CurrencyConversion.get_all_currencies', return_value=mock_currencies)

        # Mock user input for base currency
        mocker.patch('builtins.input', return_value='eur')

        base_currency = get_currency_code(mock_currencies, base_currency=True)
        assert base_currency.upper() in mock_currencies
    

    def test_get_currency_code_target(self, mocker):
        from CurrencyConversion import get_currency_code

        # Mock get_all_currencies
        mock_currencies = {'USD': 'US Dollar', 'EUR': 'Euro'}
        mocker.patch('CurrencyConversion.get_all_currencies', return_value=mock_currencies)

        # Mock user input
        mocker.patch('builtins.input', return_value='usd')

        target_currency = get_currency_code(mock_currencies, target_currency=True)
        assert target_currency.upper() in mock_currencies
    
    
    def test_get_amount(self, mocker):
        from CurrencyConversion import get_amount
        """Tests get_amount function with valid user input"""

        # Mock user input to return a valid amount
        mocker.patch('builtins.input', return_value='10.23')

        amount = get_amount()
        assert amount == 10.23

class TestApiCalls:
    @patch('requests.get')
    def test_convert_currency_mock_api(self, mock_get):
        from CurrencyConversion import convert_currency

        # Mock response data
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'EUR': 5.24}} 

        # Function call with test data
        date = '2024-06-01'
        api_key = 'my_api_key' 
        base_currency = 'BGN'
        target_currency = 'EUR'
        amount = 10.23
        headers = {"accept": "application/json"}
        result = convert_currency(base_currency, target_currency, amount, api_key, date)

        # Assertions
        assert result == {'EUR': 5.24} 
        assert mock_get.called

        # Assert API call arguments
        expected_url = f"https://api.fastforex.io/convert?from={base_currency}&to={target_currency}&amount={amount}&api_key={api_key}"
        mock_get.assert_called_with(expected_url, headers=headers)
    
    @patch('requests.get')
    def test_get_all_currencies_mock_api(self, mock_get):
        from CurrencyConversion import get_all_currencies

        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
        'currencies': {
            'USD': 'United States Dollar',
            'EUR': 'Euro',
            'GBP': 'British Pound',
            'JPY': 'Japanese Yen'
        }
    }

        api_key = 'my_api_key'
        currencies = get_all_currencies(api_key)

        # Assertions
        assert isinstance(currencies, dict)
        assert len(currencies) > 0 


class TestSaveToJson:
    # Mock cachetools
    @pytest.fixture
    def mock_cache(mocker):
        cache = mocker.MagicMock()
        cachetools.cached = mocker.patch('cachetools.cached', return_value=cache)
        return cache

    @patch('requests.get')
    @patch('builtins.open')
    def test_save_conversion_data_with_cache_or_without(self, mock_open, mock_get, mock_cache=None):
        from CurrencyConversion import save_conversion_data, convert_currency

        # Mocked response for successful conversion
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'EUR': 1.23}}

        # Sample data
        base = "USD"
        target = "EUR"
        amount = 10
        api_key = "my_api_key"
        date = "2024-06-07"

        result = {}

        # Test case 1: Successful conversion with caching
        if mock_cache is not None:
            mock_get.return_value = mock_response 

            result = convert_currency(base, target, amount, api_key, date)

            mock_open.assert_called_once_with("conversion_data.json", "a")

            assert mock_cache.called

        # Test case 2: Successful conversion without caching
        mock_get.return_value = mock_response 
        conversion_history = []  

        save_conversion_data(conversion_history, result)

        # Assertions, verify it was called once
        mock_open.assert_called_once_with("conversion_data.json", "a")

class TestEndInputs:
    def test_get_currency_code_end_input(self, mocker):
        from CurrencyConversion import get_currency_code

        # Mock get_all_currencies to return a test dictionary
        mock_currencies = {'USD': 'US Dollar', 'EUR': 'Euro'}
        mocker.patch('CurrencyConversion.get_all_currencies', return_value=mock_currencies)

        # Mock user input for quiting program
        mocker.patch('builtins.input', side_effect=['END'])

        # Expect program exit
        with pytest.raises(SystemExit):  
            get_currency_code(mock_currencies, base_currency=True)
    
    def test_get_amount_end_input(self, mocker):
        from CurrencyConversion import get_amount

        # Mock user input
        mocker.patch('builtins.input', side_effect=['END'])

        with pytest.raises(SystemExit):
            get_amount()
    
    def test_quit_program_valid_input(self):
        from CurrencyConversion import quit_program

        with pytest.raises(SystemExit):
            quit_program('end')

    def test_quit_program_invalid_input(self):
        from CurrencyConversion import quit_program

        result = quit_program('not_end')
        assert result is None 