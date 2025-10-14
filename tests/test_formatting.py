"""Tests for formatting and CSV creation functions."""
import pytest
from datetime import datetime, timezone
from export_all import (
    format_timestamp_to_iso8601,
    KoinlyCSVSchema,
    create_csv_row
)


class TestFormatTimestampToISO8601:
    """Tests for format_timestamp_to_iso8601 function."""
    
    def test_valid_timestamp(self):
        """Test formatting a valid timestamp."""
        # 2024-01-01 00:00:00 UTC in milliseconds
        timestamp = 1704067200000
        result = format_timestamp_to_iso8601(timestamp)
        assert result == "2024-01-01 00:00:00"
    
    def test_timestamp_with_time(self):
        """Test formatting a timestamp with specific time."""
        # 2024-06-15 14:30:45 UTC in milliseconds
        timestamp = 1718461845000
        result = format_timestamp_to_iso8601(timestamp)
        assert result == "2024-06-15 14:30:45"
    
    def test_timestamp_before_epoch(self):
        """Test formatting a timestamp before Unix epoch (handled gracefully)."""
        # Negative timestamps represent dates before 1970-01-01
        # The function should handle these without raising an error
        timestamp = -86400000  # 1 day before epoch
        result = format_timestamp_to_iso8601(timestamp)
        assert result == "1969-12-31 00:00:00"
    
    def test_invalid_timestamp_too_large(self):
        """Test that extremely large timestamp raises ValueError."""
        with pytest.raises(ValueError):
            format_timestamp_to_iso8601(9999999999999999)


class TestKoinlyCSVSchema:
    """Tests for KoinlyCSVSchema class."""
    
    def test_create_row_with_all_fields(self):
        """Test creating a CSV row with all fields populated."""
        transaction = {
            'id': 'test_tx_123',
            'timestamp': 1704067200000
        }
        row = KoinlyCSVSchema.create_row(
            transaction=transaction,
            sent_amount=1.5,
            sent_currency='ERG',
            received_amount=2.0,
            received_currency='ERG',
            fee_amount=0.001,
            fee_currency='ERG',
            label='test',
            description='Test transaction'
        )
        
        assert row[KoinlyCSVSchema.DATE] == "2024-01-01 00:00:00"
        assert row[KoinlyCSVSchema.SENT_AMOUNT] == 1.5
        assert row[KoinlyCSVSchema.SENT_CURRENCY] == 'ERG'
        assert row[KoinlyCSVSchema.RECEIVED_AMOUNT] == 2.0
        assert row[KoinlyCSVSchema.RECEIVED_CURRENCY] == 'ERG'
        assert row[KoinlyCSVSchema.FEE_AMOUNT] == 0.001
        assert row[KoinlyCSVSchema.FEE_CURRENCY] == 'ERG'
        assert row[KoinlyCSVSchema.LABEL] == 'test'
        assert row[KoinlyCSVSchema.DESCRIPTION] == 'Test transaction'
        assert row[KoinlyCSVSchema.TX_HASH] == 'test_tx_123'
    
    def test_create_row_with_defaults(self):
        """Test creating a CSV row with default values."""
        transaction = {
            'id': 'test_tx_456',
            'timestamp': 1704067200000
        }
        row = KoinlyCSVSchema.create_row(transaction=transaction)
        
        assert row[KoinlyCSVSchema.SENT_AMOUNT] == ''
        assert row[KoinlyCSVSchema.SENT_CURRENCY] == ''
        assert row[KoinlyCSVSchema.RECEIVED_AMOUNT] == ''
        assert row[KoinlyCSVSchema.RECEIVED_CURRENCY] == ''
        assert row[KoinlyCSVSchema.FEE_AMOUNT] == ''
        assert row[KoinlyCSVSchema.FEE_CURRENCY] == ''
        assert row[KoinlyCSVSchema.LABEL] == ''
        assert row[KoinlyCSVSchema.DESCRIPTION] == KoinlyCSVSchema.DEFAULT_DESCRIPTION
        assert row[KoinlyCSVSchema.NET_WORTH_AMOUNT] == ''
        assert row[KoinlyCSVSchema.NET_WORTH_CURRENCY] == ''
    
    def test_create_token_description(self):
        """Test creating a token description."""
        description = KoinlyCSVSchema.create_token_description(
            asset_name='TestToken',
            token_id='abc123',
            asset_type='EIP-004'
        )
        assert description == 'Token TestToken abc123 EIP-004'
    
    def test_create_token_description_with_special_characters(self):
        """Test creating a token description with special characters."""
        description = KoinlyCSVSchema.create_token_description(
            asset_name='Test-Token_v2',
            token_id='xyz789',
            asset_type='NFT'
        )
        assert description == 'Token Test-Token_v2 xyz789 NFT'


class TestCreateCSVRow:
    """Tests for create_csv_row function."""
    
    def test_create_csv_row_outgoing(self):
        """Test creating a CSV row for an outgoing transaction."""
        transaction = {
            'id': 'tx_out_123',
            'timestamp': 1704067200000
        }
        row = create_csv_row(
            transaction=transaction,
            sent_amount=5.0,
            sent_currency='ERG',
            fee_amount=0.001,
            fee_currency='ERG'
        )
        
        assert row[KoinlyCSVSchema.SENT_AMOUNT] == 5.0
        assert row[KoinlyCSVSchema.SENT_CURRENCY] == 'ERG'
        assert row[KoinlyCSVSchema.RECEIVED_AMOUNT] == ''
        assert row[KoinlyCSVSchema.RECEIVED_CURRENCY] == ''
        assert row[KoinlyCSVSchema.FEE_AMOUNT] == 0.001
    
    def test_create_csv_row_incoming(self):
        """Test creating a CSV row for an incoming transaction."""
        transaction = {
            'id': 'tx_in_456',
            'timestamp': 1704067200000
        }
        row = create_csv_row(
            transaction=transaction,
            received_amount=10.0,
            received_currency='ERG'
        )
        
        assert row[KoinlyCSVSchema.SENT_AMOUNT] == ''
        assert row[KoinlyCSVSchema.SENT_CURRENCY] == ''
        assert row[KoinlyCSVSchema.RECEIVED_AMOUNT] == 10.0
        assert row[KoinlyCSVSchema.RECEIVED_CURRENCY] == 'ERG'
        assert row[KoinlyCSVSchema.FEE_AMOUNT] == ''
