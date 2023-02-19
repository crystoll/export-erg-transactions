# ERG Transactions Exporter

Free yourself from the tyranny and limitations of ERG wallets!
This little tool will fetch your ERG address details from explorer API, and export them to Koinly CSV format.
Can be easily modified for any other format as well.

## How to use?

1) Copy sample_dotenv by name .env
2) Edit it and set nice environment variable names, and comma-separated list of your wallet addresses. For best results, include all addresses your wallet is using (otherwise it cannot track internal transfers correctly). Currently the code uses two env variables, adjust .env file to add any number of wallets.
3) Run the tool:
    python3 export_all.py
4) Observe transaction .csv files getting created

## Prerequisites

Python 3
The `requirements.txt` file lists all Python libraries the script depends on.  They can be installed using:

```
pip install -r requirements.txt
```
