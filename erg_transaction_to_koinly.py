import requests
import json
from datetime import datetime
import pandas as pd
import dotenv
import os
import itertools
import csv

dotenv.load_dotenv()

main_url = 'https://api.ergoplatform.com'
addresses_url = '/api/v1/addresses/'

addresses = os.getenv('WALLET_ADDRESSES').split(',')

ERG_FEES_ADDRESS = '2iHkR7CWvD1R4j1yZg5bkeDRQavjAaVPeTDFGGLZduHyfWMuYpmhHocX8GJoaieTx78FntzJbCBVL6rf96ocJoZdmWBL2fci7NqWgAirppPQmZ7fN9V6z13Ay6brPriBKYqLp1bT2Fk4FkFLCfdPpe'

def fetch_results(url, address, offset=0):
    url = f'{url}{address}/transactions?limit=20&offset={offset}'
    response = requests.get(url)
    response_decoded = response.content.decode()
    return json.loads(response_decoded)
    # This fails now and then with:
    #   File "/home/crystoll/.pyenv/versions/3.10.1/lib/python3.10/json/decoder.py", line 355, in raw_decode
    #     raise JSONDecodeError("Expecting value", s, err.value) from None
    #     json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)


def fetch_transactions(base_url, addresses):
    items = []
    for address in addresses:
        total = 20
        offset = 0
        while offset < total:
            response = fetch_results(base_url, address, offset)
            total = response['total']
            offset += 20
            items += response['items']
    print(f'Fetched {len(items)} transactions')
    transactions_by_id = {transaction['id']
        : transaction for transaction in items}
    return transactions_by_id


def format_timestamp_to_utf_iso8601(timestamp):
    return datetime.utcfromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')


def process_rows(addresses, all_transactions):
    exported_rows = []
    for transaction in all_transactions.values():
        inputs_from_my_wallet = [
            input for input in transaction['inputs'] if input['address'] in addresses]
        outputs_to_my_wallet = [
            output for output in transaction['outputs'] if output['address'] in addresses]
        output_fees = [output for output in transaction['outputs'] if output['address'] ==
                       ERG_FEES_ADDRESS]
        count_of_outgoing = len(inputs_from_my_wallet)
        count_of_incoming = len(outputs_to_my_wallet)
        my_inputs_total_value = sum(
            [input['value'] for input in inputs_from_my_wallet])/1000000000
        my_outputs_total_value = sum(
            [output['value'] for output in outputs_to_my_wallet])/1000000000
        fees = sum([output['value'] for output in output_fees])/1000000000
        sent_amount = ''
        sent_currency = ''
        received_amount=''
        received_currency = ''
        fee_amount = ''
        fee_currency = ''

        if count_of_outgoing > 0:
            sent_amount = my_inputs_total_value - my_outputs_total_value - fees
            sent_currency='ERG'
            fee_amount = fees
            fee_currency = 'ERG'
        elif count_of_incoming > 0:
            received_amount = my_outputs_total_value
            received_currency='ERG'
        else:
            raise Exception('WUT? Transaction inputs nor outputs match any of my addresses?')
        exported_rows.append({
            'Date': format_timestamp_to_utf_iso8601(transaction['timestamp']),
            'Sent Amount': sent_amount,
            'Sent Currency': sent_currency,
            'Received Amount': received_amount,
            'Received Currency': received_currency,
            'Fee Amount': fee_amount,
            'Fee Currency': fee_currency,
            'Net Worth Amount': '',  # Not used (value of moneys)
            'Net Worth Currency': '',  # Not used (value of moneys)
            'Label': '',  # Possible values outgoing: gift, lost, cost, margin fee, realized gain, possible values incoming: airdrop, fork, mining, reward, income, loan interest, realized gain
            'Description': 'imported from ergo explorer',  # Freeform description
            'TxHash': transaction['id'],
        })
    return exported_rows

if __name__ == '__main__':
    url = main_url + addresses_url
    all_transactions = fetch_transactions(url, addresses)
    print(f'After deduplication, we have {len(all_transactions)} transactions')
    exported_rows = process_rows(addresses, all_transactions)
    print(f'Processed {len(exported_rows)} csv rows')
    df = pd.DataFrame(exported_rows)
    df.sort_values(by=['Date'], inplace=True, ascending=False)
    df.to_csv('basic_transactions.csv', index=False,
              quoting=csv.QUOTE_NONNUMERIC)
    print('Succesfully wrote to basic_transactions.csv')
