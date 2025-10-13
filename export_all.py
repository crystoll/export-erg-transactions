import csv
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional, Callable

import pandas as pd
import requests
import dotenv


# API Configuration
main_url = 'https://api.ergoplatform.com'
addresses_url = '/api/v1/addresses/'

# Constants
ERG_DECIMALS = 1_000_000_000  # ERG has 9 decimal places
API_LIMIT_PER_REQUEST = 20    # Number of transactions per API request
HTTP_TIMEOUT_SECONDS = 30     # HTTP request timeout
MAX_RETRIES = 3               # Maximum number of retry attempts
RETRY_DELAY_SECONDS = 2       # Delay between retry attempts
RESPONSE_PREVIEW_LENGTH = 200 # Length of response content to show in error messages
CONSOLIDATION_THRESHOLD = 0.0000000000001  # Threshold for detecting wallet consolidation

# Dataset size thresholds for performance optimization
LARGE_DATASET_THRESHOLD = 10_000  # Threshold for using streaming CSV export
PROGRESS_DISPLAY_THRESHOLD = 5_000  # Threshold for showing export progress
CHUNK_SIZE = 1_000  # Chunk size for streaming export

# Ergo Platform Addresses
ERG_FEES_ADDRESS = '2iHkR7CWvD1R4j1yZg5bkeDRQavjAaVPeTDFGGLZduHyfWMuYpmhHocX8GJoaieTx78FntzJbCBVL6rf96ocJoZdmWBL2fci7NqWgAirppPQmZ7fN9V6z13Ay6brPriBKYqLp1bT2Fk4FkFLCfdPpe'

# Global cache for transaction data to avoid re-fetching
_transaction_cache: Dict[str, Dict[str, Any]] = {}


def fetch_results(url: str, address: str, offset: int = 0, max_retries: int = MAX_RETRIES) -> Dict[str, Any]:
    """Fetch transaction results from Ergo Platform API with retry logic.
    
    Args:
        url: Base API URL
        address: Ergo wallet address to fetch transactions for
        offset: Pagination offset (default: 0)
        max_retries: Maximum number of retry attempts (default: MAX_RETRIES)
        
    Returns:
        Dictionary containing 'items' (list of transactions) and 'total' (total count)
        Returns {'items': [], 'total': 0} if all retries fail
        
    Raises:
        No exceptions - all errors are handled gracefully with retries
    """
    url = f'{url}{address}/transactions?limit={API_LIMIT_PER_REQUEST}&offset={offset}'
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            if not response.content:
                print(f"Warning: Empty response for {address} at offset {offset}, attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    continue
                else:
                    return {'items': [], 'total': 0}  # Return empty result on final attempt
            
            response_decoded = response.content.decode('utf-8')
            if not response_decoded.strip():
                print(f"Warning: Empty decoded response for {address} at offset {offset}, attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    continue
                else:
                    return {'items': [], 'total': 0}
            
            return json.loads(response_decoded)
            
        except requests.exceptions.RequestException as e:
            print(f"Network error for {address} at offset {offset}, attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"Failed after {max_retries} attempts, skipping this request")
                return {'items': [], 'total': 0}
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error for {address} at offset {offset}, attempt {attempt + 1}: {e}")
            print(f"Response content: {response_decoded[:RESPONSE_PREVIEW_LENGTH]}...")  # Show first {RESPONSE_PREVIEW_LENGTH} chars
            if attempt < max_retries - 1:
                print(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"Failed to decode JSON after {max_retries} attempts, skipping this request")
                return {'items': [], 'total': 0}
                
        except Exception as e:
            print(f"Unexpected error for {address} at offset {offset}, attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"Failed after {max_retries} attempts due to unexpected error, skipping this request")
                return {'items': [], 'total': 0}


def fetch_transactions(base_url: str, addresses: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch all transactions for multiple wallet addresses with caching and progress tracking.
    
    Args:
        base_url: Base API URL
        addresses: List of Ergo wallet addresses
        
    Returns:
        Dictionary mapping transaction IDs to transaction data
    """
    # Check cache first
    cache_key = f"{base_url}:{','.join(sorted(addresses))}"
    if cache_key in _transaction_cache:
        print(f'Using cached data for {len(addresses)} addresses')
        return _transaction_cache[cache_key]
    
    items = []
    total_addresses = len(addresses)
    
    for addr_index, address in enumerate(addresses, 1):
        print(f'Processing address {addr_index}/{total_addresses}: {address[:10]}...')
        
        total = API_LIMIT_PER_REQUEST
        offset = 0
        address_transactions = 0
        
        while offset < total:
            response = fetch_results(base_url, address, offset)
            total = response['total']
            batch_size = len(response['items'])
            address_transactions += batch_size
            offset += API_LIMIT_PER_REQUEST
            items += response['items']
            
            # Progress feedback for large datasets
            if total > API_LIMIT_PER_REQUEST:
                progress = min(100, (offset / total) * 100)
                print(f'  Progress: {progress:.1f}% ({offset}/{total} transactions)')
        
        print(f'  Found {address_transactions} transactions for this address')
    
    print(f'Total fetched: {len(items)} transactions from {total_addresses} addresses')
    
    # Deduplicate and create transaction dictionary
    transactions_by_id = {transaction['id']: transaction for transaction in items}
    deduped_count = len(transactions_by_id)
    
    if len(items) != deduped_count:
        print(f'Removed {len(items) - deduped_count} duplicate transactions')
    
    # Cache the results
    _transaction_cache[cache_key] = transactions_by_id
    
    return transactions_by_id


def validate_ergo_address(address: str) -> bool:
    """Validate if a string is a valid Ergo address format.
    
    Args:
        address: Address string to validate
        
    Returns:
        True if address appears to be valid Ergo format, False otherwise
    """
    if not address or not isinstance(address, str):
        return False
    
    # Ergo addresses are typically 51-52 characters long and start with '1', '2', '3', or '9'
    if len(address) < 50 or len(address) > 53:
        return False
    
    if not address[0] in ['1', '2', '3', '9']:
        return False
    
    # Basic character set validation (Base58)
    valid_chars = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
    if not all(c in valid_chars for c in address):
        return False
    
    return True


def validate_wallet_addresses(addresses: List[str]) -> Tuple[List[str], List[str]]:
    """Validate a list of wallet addresses and separate valid from invalid ones.
    
    Args:
        addresses: List of address strings to validate
        
    Returns:
        Tuple of (valid_addresses, invalid_addresses)
    """
    valid_addresses = []
    invalid_addresses = []
    
    for address in addresses:
        address = address.strip()  # Remove whitespace
        if validate_ergo_address(address):
            valid_addresses.append(address)
        else:
            invalid_addresses.append(address)
    
    return valid_addresses, invalid_addresses


def format_timestamp_to_iso8601(timestamp: int) -> str:
    """Convert Unix timestamp to ISO8601 formatted string in UTC.
    
    Args:
        timestamp: Unix timestamp in milliseconds
        
    Returns:
        Formatted date string in 'YYYY-MM-DD HH:MM:SS' format (UTC)
        
    Raises:
        ValueError: If timestamp is invalid
    """
    try:
        # Use modern datetime.fromtimestamp with UTC to avoid deprecation warning
        dt = datetime.fromtimestamp(timestamp / 1000, timezone.utc)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, OSError) as e:
        raise ValueError(f"Invalid timestamp {timestamp}: {e}")


class KoinlyCSVSchema:
    """Standardized CSV schema for Koinly tax software compatibility."""
    
    # Column names as constants
    DATE = 'Date'
    SENT_AMOUNT = 'Sent Amount'
    SENT_CURRENCY = 'Sent Currency'
    RECEIVED_AMOUNT = 'Received Amount'
    RECEIVED_CURRENCY = 'Received Currency'
    FEE_AMOUNT = 'Fee Amount'
    FEE_CURRENCY = 'Fee Currency'
    NET_WORTH_AMOUNT = 'Net Worth Amount'
    NET_WORTH_CURRENCY = 'Net Worth Currency'
    LABEL = 'Label'
    DESCRIPTION = 'Description'
    TX_HASH = 'TxHash'
    
    # All column names in order
    COLUMNS = [
        DATE, SENT_AMOUNT, SENT_CURRENCY, RECEIVED_AMOUNT, RECEIVED_CURRENCY,
        FEE_AMOUNT, FEE_CURRENCY, NET_WORTH_AMOUNT, NET_WORTH_CURRENCY,
        LABEL, DESCRIPTION, TX_HASH
    ]
    
    # Default values
    DEFAULT_DESCRIPTION = 'imported from ergo explorer'
    EMPTY_VALUE = ''
    
    # Possible label values for reference
    OUTGOING_LABELS = ['gift', 'lost', 'cost', 'margin fee', 'realized gain']
    INCOMING_LABELS = ['airdrop', 'fork', 'mining', 'reward', 'income', 'loan interest', 'realized gain']
    
    @classmethod
    def create_row(cls, transaction, sent_amount='', sent_currency='', received_amount='', 
                   received_currency='', fee_amount='', fee_currency='', 
                   label='', description=None):
        """Create a standardized CSV row dictionary for a transaction."""
        if description is None:
            description = cls.DEFAULT_DESCRIPTION
            
        return {
            cls.DATE: format_timestamp_to_iso8601(transaction['timestamp']),
            cls.SENT_AMOUNT: sent_amount,
            cls.SENT_CURRENCY: sent_currency,
            cls.RECEIVED_AMOUNT: received_amount,
            cls.RECEIVED_CURRENCY: received_currency,
            cls.FEE_AMOUNT: fee_amount,
            cls.FEE_CURRENCY: fee_currency,
            cls.NET_WORTH_AMOUNT: cls.EMPTY_VALUE,  # Not used (value of moneys)
            cls.NET_WORTH_CURRENCY: cls.EMPTY_VALUE,  # Not used (value of moneys)
            cls.LABEL: label,
            cls.DESCRIPTION: description,
            cls.TX_HASH: transaction['id'],
        }


def filter_transaction_inputs_outputs(transaction: Dict[str, Any], addresses: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Filter transaction inputs and outputs that belong to our wallet addresses.
    
    Args:
        transaction: Transaction data dictionary
        addresses: List of wallet addresses to filter for
        
    Returns:
        Tuple of (inputs_from_my_wallet, outputs_to_my_wallet, output_fees)
    """
    inputs_from_my_wallet = [
        input for input in transaction['inputs'] if input['address'] in addresses
    ]
    outputs_to_my_wallet = [
        output for output in transaction['outputs'] if output['address'] in addresses
    ]
    output_fees = [
        output for output in transaction['outputs'] if output['address'] == ERG_FEES_ADDRESS
    ]
    return inputs_from_my_wallet, outputs_to_my_wallet, output_fees


def calculate_transaction_values(inputs_from_my_wallet: List[Dict[str, Any]], 
                               outputs_to_my_wallet: List[Dict[str, Any]], 
                               output_fees: List[Dict[str, Any]]) -> Tuple[float, float, float]:
    """Calculate total values for inputs, outputs, and fees in ERG.
    
    Args:
        inputs_from_my_wallet: List of input transactions from our wallet
        outputs_to_my_wallet: List of output transactions to our wallet
        output_fees: List of fee outputs
        
    Returns:
        Tuple of (my_inputs_total_value, my_outputs_total_value, fees) in ERG
    """
    my_inputs_total_value = sum(
        [input['value'] for input in inputs_from_my_wallet]
    ) / ERG_DECIMALS
    my_outputs_total_value = sum(
        [output['value'] for output in outputs_to_my_wallet]
    ) / ERG_DECIMALS
    fees = sum([output['value'] for output in output_fees]) / ERG_DECIMALS
    return my_inputs_total_value, my_outputs_total_value, fees


def create_csv_row(transaction: Dict[str, Any], sent_amount: str = '', sent_currency: str = '', 
                   received_amount: str = '', received_currency: str = '', fee_amount: str = '', 
                   fee_currency: str = '', label: str = '', description: Optional[str] = None) -> Dict[str, str]:
    """Create a standardized CSV row dictionary for a transaction.
    
    Args:
        transaction: Transaction data dictionary
        sent_amount: Amount sent (default: '')
        sent_currency: Currency sent (default: '')
        received_amount: Amount received (default: '')
        received_currency: Currency received (default: '')
        fee_amount: Fee amount (default: '')
        fee_currency: Fee currency (default: '')
        label: Transaction label (default: '')
        description: Transaction description (default: None, uses schema default)
        
    Returns:
        Dictionary representing a CSV row
    """
    return KoinlyCSVSchema.create_row(
        transaction=transaction,
        sent_amount=sent_amount,
        sent_currency=sent_currency,
        received_amount=received_amount,
        received_currency=received_currency,
        fee_amount=fee_amount,
        fee_currency=fee_currency,
        label=label,
        description=description
    )


def process_outgoing_transaction(transaction, my_inputs_total_value, my_outputs_total_value, fees):
    """Process an outgoing transaction and return the appropriate CSV rows."""
    exported_rows = []
    sent_amount = my_inputs_total_value - my_outputs_total_value - fees
    
    # Check if this is a wallet consolidation (very small sent amount due to rounding)
    if sent_amount < CONSOLIDATION_THRESHOLD:
        # This is a consolidation transaction - create both sent and received entries
        sent_amount = my_outputs_total_value
        description = 'Consolidated money within wallet, just the fee'
        
        # Add the receiving part of the consolidation
        exported_rows.append(create_csv_row(
            transaction=transaction,
            sent_amount=0,
            sent_currency='',
            received_amount=my_outputs_total_value,
            received_currency='ERG',
            fee_amount=0,
            fee_currency='ERG',
            description=description
        ))
    
    # Add the main transaction row
    exported_rows.append(create_csv_row(
        transaction=transaction,
        sent_amount=sent_amount,
        sent_currency='ERG',
        received_amount='',
        received_currency='',
        fee_amount=fees,
        fee_currency='ERG'
    ))
    
    return exported_rows


def process_incoming_transaction(transaction, my_outputs_total_value):
    """Process an incoming transaction and return the appropriate CSV row."""
    return [create_csv_row(
        transaction=transaction,
        sent_amount='',
        sent_currency='',
        received_amount=my_outputs_total_value,
        received_currency='ERG'
    )]


def process_transactions(addresses, all_transactions):
    """Process all transactions and return CSV rows for export."""
    exported_rows = []
    
    for transaction in all_transactions.values():
        # Filter inputs/outputs that belong to our wallet
        inputs_from_my_wallet, outputs_to_my_wallet, output_fees = filter_transaction_inputs_outputs(
            transaction, addresses
        )
        
        # Calculate transaction values
        my_inputs_total_value, my_outputs_total_value, fees = calculate_transaction_values(
            inputs_from_my_wallet, outputs_to_my_wallet, output_fees
        )
        
        # Determine transaction type and process accordingly
        count_of_outgoing = len(inputs_from_my_wallet)
        count_of_incoming = len(outputs_to_my_wallet)
        
        if count_of_outgoing > 0:
            # Outgoing transaction (possibly with consolidation)
            transaction_rows = process_outgoing_transaction(
                transaction, my_inputs_total_value, my_outputs_total_value, fees
            )
            exported_rows.extend(transaction_rows)
            
        elif count_of_incoming > 0:
            # Incoming transaction
            transaction_rows = process_incoming_transaction(transaction, my_outputs_total_value)
            exported_rows.extend(transaction_rows)
            
        else:
            # This should not happen - transaction doesn't involve our addresses
            raise Exception(
                f'Transaction {transaction["id"]} inputs nor outputs match any of our addresses'
            )
    
    return exported_rows


def process_tokens(addresses, all_transactions):
    exported_rows = []
    for transaction in all_transactions.values():
        inputs_from_my_wallet = [
            input for input in transaction['inputs'] if input['address'] in addresses]
        outputs_to_my_wallet = [
            output for output in transaction['outputs'] if output['address'] in addresses]
        outgoing_assets = [
            asset for input in inputs_from_my_wallet for asset in input['assets']]
        incoming_assets = [
            asset for input in outputs_to_my_wallet for asset in input['assets']]

        df_outgoing = pd.DataFrame(outgoing_assets, columns=[
                                   'name', 'tokenId', 'type', 'decimals', 'amount'])
        df_outgoing['amount'] = -df_outgoing['amount']

        df_incoming = pd.DataFrame(incoming_assets, columns=[
                                   'name', 'tokenId', 'type', 'decimals', 'amount'])

        df_combined = pd.concat([df_outgoing, df_incoming])

        df_summed = df_combined.groupby(
            ['name', 'tokenId', 'type', 'decimals']).sum(numeric_only=False).reset_index()
        # print(f'Token sums: {df_summed}')
        records = df_summed.to_dict('records')
        # print(f'Token sums: {records}')

        for asset in records:
            if asset['amount'] > 0:
                # Handle incoming
                amount = asset['amount'] / 10 ** asset['decimals']
                asset_name = asset['name']
                asset_tokenid = asset['tokenId']
                asset_type = asset['type']
                exported_rows.append({
                    'Date': format_timestamp_to_iso8601(transaction['timestamp']),
                    'Sent Amount': '',
                    'Sent Currency': '',
                    'Received Amount': amount,
                    'Received Currency': asset_name,
                    # Not used (because is already contained in ordinary transactions, and same fee (transaction value) covers multiple token assets)
                    'Fee Amount': '',
                    'Fee Currency': '',
                    # Not used (value of moneys)
                    'Net Worth Amount': '',
                    # Not used (value of moneys)
                    'Net Worth Currency': '',
                    'Label': '',  # Possible values outgoing: gift, lost, cost, margin fee, realized gain, possible values incoming: airdrop, fork, mining, reward, income, loan interest, realized gain
                    # Freeform description
                    'Description': f'Token {asset_name} {asset_tokenid} {asset_type}',
                    'TxHash': transaction['id'],
                })
            elif asset['amount'] < 0:
                # Handle outgoing
                amount = abs(asset['amount']) / 10 ** asset['decimals']
                asset_name = asset['name']
                asset_tokenid = asset['tokenId']
                asset_type = asset['type']
                exported_rows.append({
                    'Date': format_timestamp_to_iso8601(transaction['timestamp']),
                    'Sent Amount': amount,
                    'Sent Currency': asset_name,
                    'Received Amount': '',  # Not used
                    'Received Currency': '',  # Not used
                    # Not used (because is already contained in ordinary transactions, and same fee (transaction value) covers multiple token assets)
                    'Fee Amount': '',
                    'Fee Currency': '',  # Not used
                    # Not used (value of moneys)
                    'Net Worth Amount': '',
                    # Not used (value of moneys)
                    'Net Worth Currency': '',
                    'Label': '',  # Possible values outgoing: gift, lost, cost, margin fee, realized gain, possible values incoming: airdrop, fork, mining, reward, income, loan interest, realized gain
                    # Freeform description
                    'Description': f'Token {asset_name} {asset_tokenid} {asset_type}',
                    'TxHash': transaction['id'],
                })
    return exported_rows


def export_to_csv_file(addresses: List[str], filename: str, process_function: Callable, transaction_type_name: str) -> None:
    """Generic function to export transaction data to CSV file with performance optimizations.
    
    Args:
        addresses: List of wallet addresses to process
        filename: Output CSV filename
        process_function: Function to process transactions (process_transactions or process_tokens)
        transaction_type_name: Name for logging (e.g., 'transactions', 'token transactions')
    """
    url = main_url + addresses_url
    
    print(f'Fetching {transaction_type_name} data...')
    all_transactions = fetch_transactions(url, addresses)
    print(f'After deduplication, we have {len(all_transactions)} transactions')
    
    print(f'Processing {transaction_type_name}...')
    exported_rows = process_function(addresses, all_transactions)
    print(f'Processed {len(exported_rows)} CSV rows')
    
    if len(exported_rows) == 0:
        print(f'Zero {transaction_type_name}, skipping file output for {filename}.')
        return
    
    # Backup existing file if it exists
    if os.path.isfile(filename):
        backup_filename = filename + '.bak'
        print(f'File {filename} already exists, renaming to {backup_filename}')
        os.rename(filename, backup_filename)
    
    print(f'Writing {len(exported_rows)} rows to {filename}...')
    
    # For large datasets, use chunked processing to reduce memory usage
    if len(exported_rows) > LARGE_DATASET_THRESHOLD:
        print('Large dataset detected, using memory-efficient export...')
        _export_large_dataset_to_csv(exported_rows, filename)
    else:
        # Standard export for smaller datasets
        _export_standard_dataset_to_csv(exported_rows, filename)
    
    print(f'Successfully wrote {len(exported_rows)} rows to {filename}')


def _export_standard_dataset_to_csv(exported_rows: List[Dict[str, str]], filename: str) -> None:
    """Export standard-sized datasets using pandas DataFrame."""
    df = pd.DataFrame(exported_rows)
    df = df.reindex(columns=KoinlyCSVSchema.COLUMNS)  # Ensure consistent column order
    df.sort_values(by=[KoinlyCSVSchema.DATE], inplace=True, ascending=False)
    df.to_csv(filename, index=False, quoting=csv.QUOTE_NONNUMERIC)


def _export_large_dataset_to_csv(exported_rows: List[Dict[str, str]], filename: str) -> None:
    """Export large datasets using streaming CSV writer for memory efficiency."""
    # Sort rows by date (most recent first)
    sorted_rows = sorted(exported_rows, 
                        key=lambda x: x.get(KoinlyCSVSchema.DATE, ''), 
                        reverse=True)
    
    # Write directly to CSV using streaming approach
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, 
                               fieldnames=KoinlyCSVSchema.COLUMNS,
                               quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        
        # Write in chunks to show progress for very large datasets
        for i in range(0, len(sorted_rows), CHUNK_SIZE):
            chunk = sorted_rows[i:i + CHUNK_SIZE]
            writer.writerows(chunk)
            
            if len(sorted_rows) > PROGRESS_DISPLAY_THRESHOLD:
                progress = min(100, ((i + len(chunk)) / len(sorted_rows)) * 100)
                print(f'  Export progress: {progress:.1f}%')


def transactions_to_file(addresses: List[str], filename: str) -> None:
    """Export regular ERG transactions to CSV file."""
    export_to_csv_file(addresses, filename, process_transactions, 'transactions')


def token_transactions_to_file(addresses: List[str], filename: str) -> None:
    """Export token transactions to CSV file."""
    export_to_csv_file(addresses, filename, process_tokens, 'token transactions')


def main() -> None:
    """Main function to process all wallets and export transactions."""
    try:
        # Load wallet configuration
        wallets = dict(dotenv.dotenv_values('.env'))
        
        if not wallets:
            print("Error: No wallet configuration found in .env file")
            print("Please create a .env file with wallet addresses (see sample_dotenv for format)")
            return
        
        print(f"Found {len(wallets)} wallet configurations")
        
        for wallet_name in wallets:
            print(f"\nProcessing wallet: {wallet_name}")
            
            # Parse and validate addresses
            raw_addresses = wallets[wallet_name].split(',')
            valid_addresses, invalid_addresses = validate_wallet_addresses(raw_addresses)
            
            if invalid_addresses:
                print(f"Warning: Found {len(invalid_addresses)} invalid addresses in {wallet_name}:")
                for addr in invalid_addresses:
                    print(f"  - {addr}")
            
            if not valid_addresses:
                print(f"Error: No valid addresses found for wallet {wallet_name}, skipping")
                continue
            
            print(f"Processing {len(valid_addresses)} valid addresses")
            
            try:
                # Export regular transactions
                transactions_filename = f'{wallet_name}.csv'
                print(f"Exporting regular transactions to {transactions_filename}")
                transactions_to_file(valid_addresses, transactions_filename)
                
                # Export token transactions
                tokens_filename = f'{wallet_name}_tokens.csv'
                print(f"Exporting token transactions to {tokens_filename}")
                token_transactions_to_file(valid_addresses, tokens_filename)
                
            except Exception as e:
                print(f"Error processing wallet {wallet_name}: {e}")
                continue
        
        print("\nTransaction export completed")
        
    except FileNotFoundError:
        print("Error: .env file not found")
        print("Please create a .env file with your wallet addresses (see sample_dotenv for format)")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


if __name__ == '__main__':
    main()
