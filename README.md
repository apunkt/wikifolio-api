# wikifolio-api
A Python API-Wrapper for the unofficial wikifolio API

## Usage
- Clone this repo
- Create a new file inside it with the following content (the wikifolio-ID is the name of your wikifolio, e.g. "wf000igb03")

```python
from wikifolio import Wikifolio

wf = Wikifolio("email", "password", "wikifolioID")
print(wf.performance_ever)
```

## Current state of functionality
- tested on a wikifolio which is (not yet) investible [19.02.2023], all things except buy_quote/sell_quote succesfully tested. For my purpose limit (and stop-limit) orders are sufficient.

## Features
- Perfomance Indicators (`wf.performance_since_emission`, `wf.performance_ever`, ...)
- Properties (see [#2](https://github.com/henrydatei/wikifolio-api/issues/2))
- Buy and Sell orders (limit order and quote order)

## TODOs
- 2FA (implemented, but needs testing)
- provide some Jupyter notebooks to demonstrate proper use of the "key features"
