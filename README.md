# ERG Transactions Exporter

Free yourself from the tyranny and limitations of ERG wallets!
This little tool will fetch your ERG address details from explorer API, and export them to Koinly CSV format.
Can be easily modified for any other format as well.

## How to use?

1) Copy sample_dotenv by name .env
2) Edit it and set your ERG wallet addresses (comma-separated list). For best results, include all addresses your wallet is using (otherwise it cannot track internal transfers correctly)
3) Run the tool:
    python3 erg_transactions_to_koinly.py
4) Observe a basic_transactions.csv file getting created

## Prerequisites

Need to have Python 3
Need to have some Python libs installed, with pip.
You can get a pretty good idea from tool imports, but at least:

```bash
pip install requests
pip install pandas
pip install dotenv
```
