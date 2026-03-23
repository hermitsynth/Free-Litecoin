# Free Litecoin / Faucet Automation

This project automates signing up for, and then auto-rolling for accounts on https://free-litecoin.com/

## How To Use:

This project is very simple to run.

### Account "mining":
To begin "mining" for accounts, simply input your details into the .env file, all you need is one password that will be used for registration across all accounts,
your referer ID (you will have to make one main account, this ID is what all your funds will get funneled to), and your LTC address for payout.

To start automatically making the accounts, just run :
```
python litecoinstealer.py
```

This will automatically start signing up for accounts, and then appending the login details to those accounts in a text file, 
and claiming their first free roll automatically.

The site will eventually block the script from signing up from more accounts, the most accounts I could get on ONE IP was 15.
To circumvent this, use a VPN (even a free one like windscribe will do), and then just let it keep running on a new IP.
A list of proxies is also included that requests are tunneled through, this helps circumvent this even more, but sometimes a VPN is still neccasary.

Now, for the second part.

### Auto-rolling:

Once you have built up a decent amount of accounts (I recommend trying to get 50 or more, this can take a while!), you can let the auto-roll script run indefinitely.
This script simply logs into every account listed in accounts.txt, rolls, and then logs into the next account to roll again.
These are processed in "chunks" of 10 accounts at a time, it will run 1 instance per chunk, and login to multiple accounts at once.

To start auto-rolling, AFTER getting your accounts, run:

```
python litecoinROLLER.py
```

## Features:

This project has a number of features to allow it to run indefinitely and smoothly

- Automatically solves captchas
- Routes traffic through proxies to avoid detection
- Processes multiple accounts at once to maintain efficency, usually able to finish the process within 20-25 minutes for either script. (For litecoinstealer, this applies to the rate-limit rather than completion)

## Dependencies:

To run this project, you must install the following libraries:

```
pip install selenium

pip install ddddocr

pip install pillow
```
## Development:

LitecoinROLLER.py was made primarily by me (hermitsynth)

litecoinstealer.py was developed by [Imusing](https://github.com/imusing) , thanks to their contribution, this project was possible


## Synopsis:

Enjoy your free litecoin! This typically results in profit / payout within about a week.

