#### Currency convertor task by "Apollica"

The task is to create currency converting cli application that integrates with [Fast Forex](https://www.fastforex.io/)
and allows the users to convert currencies with exchange rates from past dates.

### Task summary and objectives

- Use Python, Node.js or Kotlin.
- The application must accept a command line argument for the date in format '2024-12-31'.
- The application must be able to process multiple conversions.
- The application must continuously validate all inputs until a correct one is submitted. Мonetary values should be constrained to two decimal places. Currencies must be in ISO 4217 three letter currency code format.
- The application must be case-insensitive.
- The application must cache the exchange rates for each requested base currency. Subsequent conversions with this base currency should use the cached data, instead of calling the API.
- Each successful conversion must be saved in a json file with the provided format.
- The application must be terminated by typing 'END' on any input.
- The application must load the api_key for Fast Forex from a config.json file which must be ignored by the version control.
- The executable must be named CurrencyConversion.