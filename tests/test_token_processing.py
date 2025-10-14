"""Tests for token processing functions."""
import pytest
import pandas as pd
from export_all import (
    extract_transaction_assets,
    calculate_net_token_amounts,
    process_token_asset,
    KoinlyCSVSchema
)


class TestExtractTransactionAssets:
    """Tests for extract_transaction_assets function."""
    
    def test_extract_with_assets(self):
        """Test extracting assets from transaction."""
        transaction = {
            'inputs': [
                {
                    'address': 'addr1',
                    'assets': [
                        {'name': 'Token1', 'tokenId': 'id1', 'type': 'EIP-004', 'decimals': 2, 'amount': 100}
                    ]
                },
                {
                    'address': 'addr2',
                    'assets': []
                }
            ],
            'outputs': [
                {
                    'address': 'addr1',
                    'assets': [
                        {'name': 'Token2', 'tokenId': 'id2', 'type': 'EIP-004', 'decimals': 4, 'amount': 200}
                    ]
                }
            ]
        }
        addresses = ['addr1']
        
        outgoing, incoming = extract_transaction_assets(transaction, addresses)
        
        assert len(outgoing) == 1
        assert len(incoming) == 1
        assert outgoing[0]['name'] == 'Token1'
        assert incoming[0]['name'] == 'Token2'
    
    def test_extract_with_no_assets(self):
        """Test extracting when there are no assets."""
        transaction = {
            'inputs': [{'address': 'addr1', 'assets': []}],
            'outputs': [{'address': 'addr1', 'assets': []}]
        }
        addresses = ['addr1']
        
        outgoing, incoming = extract_transaction_assets(transaction, addresses)
        
        assert len(outgoing) == 0
        assert len(incoming) == 0
    
    def test_extract_with_no_matching_addresses(self):
        """Test extracting when addresses don't match."""
        transaction = {
            'inputs': [
                {
                    'address': 'addr1',
                    'assets': [{'name': 'Token1', 'tokenId': 'id1', 'type': 'EIP-004', 'decimals': 2, 'amount': 100}]
                }
            ],
            'outputs': [
                {
                    'address': 'addr2',
                    'assets': [{'name': 'Token2', 'tokenId': 'id2', 'type': 'EIP-004', 'decimals': 4, 'amount': 200}]
                }
            ]
        }
        addresses = ['addr3']
        
        outgoing, incoming = extract_transaction_assets(transaction, addresses)
        
        assert len(outgoing) == 0
        assert len(incoming) == 0


class TestCalculateNetTokenAmounts:
    """Tests for calculate_net_token_amounts function."""
    
    def test_calculate_net_outgoing(self):
        """Test calculating net amounts for outgoing tokens."""
        outgoing = [
            {'name': 'Token1', 'tokenId': 'id1', 'type': 'EIP-004', 'decimals': 2, 'amount': 100}
        ]
        incoming = []
        
        result = calculate_net_token_amounts(outgoing, incoming)
        
        assert len(result) == 1
        assert result[0]['amount'] == -100
        assert result[0]['name'] == 'Token1'
    
    def test_calculate_net_incoming(self):
        """Test calculating net amounts for incoming tokens."""
        outgoing = []
        incoming = [
            {'name': 'Token1', 'tokenId': 'id1', 'type': 'EIP-004', 'decimals': 2, 'amount': 200}
        ]
        
        result = calculate_net_token_amounts(outgoing, incoming)
        
        assert len(result) == 1
        assert result[0]['amount'] == 200
        assert result[0]['name'] == 'Token1'
    
    def test_calculate_net_same_token_both_directions(self):
        """Test calculating net amounts when same token goes both ways."""
        outgoing = [
            {'name': 'Token1', 'tokenId': 'id1', 'type': 'EIP-004', 'decimals': 2, 'amount': 100}
        ]
        incoming = [
            {'name': 'Token1', 'tokenId': 'id1', 'type': 'EIP-004', 'decimals': 2, 'amount': 150}
        ]
        
        result = calculate_net_token_amounts(outgoing, incoming)
        
        assert len(result) == 1
        assert result[0]['amount'] == 50  # 150 - 100
    
    def test_calculate_net_multiple_tokens(self):
        """Test calculating net amounts for multiple different tokens."""
        outgoing = [
            {'name': 'Token1', 'tokenId': 'id1', 'type': 'EIP-004', 'decimals': 2, 'amount': 100},
            {'name': 'Token2', 'tokenId': 'id2', 'type': 'EIP-004', 'decimals': 4, 'amount': 200}
        ]
        incoming = [
            {'name': 'Token3', 'tokenId': 'id3', 'type': 'EIP-004', 'decimals': 6, 'amount': 300}
        ]
        
        result = calculate_net_token_amounts(outgoing, incoming)
        
        assert len(result) == 3


class TestProcessTokenAsset:
    """Tests for process_token_asset function."""
    
    def test_process_incoming_token(self):
        """Test processing an incoming token asset."""
        transaction = {
            'id': 'tx_token_in',
            'timestamp': 1704067200000
        }
        asset = {
            'name': 'TestToken',
            'tokenId': 'abc123',
            'type': 'EIP-004',
            'decimals': 2,
            'amount': 100
        }
        
        row = process_token_asset(transaction, asset)
        
        assert row is not None
        assert row[KoinlyCSVSchema.RECEIVED_AMOUNT] == 1.0  # 100 / 10^2
        assert row[KoinlyCSVSchema.RECEIVED_CURRENCY] == 'TestToken'
        assert row[KoinlyCSVSchema.SENT_AMOUNT] == ''
        assert 'Token TestToken abc123 EIP-004' in row[KoinlyCSVSchema.DESCRIPTION]
    
    def test_process_outgoing_token(self):
        """Test processing an outgoing token asset."""
        transaction = {
            'id': 'tx_token_out',
            'timestamp': 1704067200000
        }
        asset = {
            'name': 'TestToken',
            'tokenId': 'xyz789',
            'type': 'NFT',
            'decimals': 0,
            'amount': -1
        }
        
        row = process_token_asset(transaction, asset)
        
        assert row is not None
        assert row[KoinlyCSVSchema.SENT_AMOUNT] == 1.0  # abs(-1) / 10^0
        assert row[KoinlyCSVSchema.SENT_CURRENCY] == 'TestToken'
        assert row[KoinlyCSVSchema.RECEIVED_AMOUNT] == ''
    
    def test_process_zero_amount_token(self):
        """Test that zero amount tokens return None."""
        transaction = {
            'id': 'tx_token_zero',
            'timestamp': 1704067200000
        }
        asset = {
            'name': 'TestToken',
            'tokenId': 'zero123',
            'type': 'EIP-004',
            'decimals': 2,
            'amount': 0
        }
        
        row = process_token_asset(transaction, asset)
        
        assert row is None
    
    def test_process_token_with_high_decimals(self):
        """Test processing token with high decimal places."""
        transaction = {
            'id': 'tx_token_decimals',
            'timestamp': 1704067200000
        }
        asset = {
            'name': 'HighDecimalToken',
            'tokenId': 'hdt123',
            'type': 'EIP-004',
            'decimals': 18,
            'amount': 1000000000000000000  # 1 token with 18 decimals
        }
        
        row = process_token_asset(transaction, asset)
        
        assert row is not None
        assert row[KoinlyCSVSchema.RECEIVED_AMOUNT] == 1.0
    
    def test_process_token_with_invalid_decimals_negative(self, capsys):
        """Test processing token with negative decimals (should warn and use 0)."""
        transaction = {
            'id': 'tx_invalid_decimals',
            'timestamp': 1704067200000
        }
        asset = {
            'name': 'InvalidToken',
            'tokenId': 'inv123',
            'type': 'EIP-004',
            'decimals': -5,
            'amount': 100
        }
        
        row = process_token_asset(transaction, asset)
        
        # Should use decimals=0 as fallback
        assert row is not None
        assert row[KoinlyCSVSchema.RECEIVED_AMOUNT] == 100.0
        
        # Check that warning was printed
        captured = capsys.readouterr()
        assert 'Warning: Invalid decimals value' in captured.out
    
    def test_process_token_with_invalid_decimals_too_large(self, capsys):
        """Test processing token with too large decimals (should warn and use 0)."""
        transaction = {
            'id': 'tx_large_decimals',
            'timestamp': 1704067200000
        }
        asset = {
            'name': 'LargeDecimalToken',
            'tokenId': 'ldt123',
            'type': 'EIP-004',
            'decimals': 50,
            'amount': 100
        }
        
        row = process_token_asset(transaction, asset)
        
        # Should use decimals=0 as fallback
        assert row is not None
        assert row[KoinlyCSVSchema.RECEIVED_AMOUNT] == 100.0
        
        # Check that warning was printed
        captured = capsys.readouterr()
        assert 'Warning: Invalid decimals value' in captured.out
