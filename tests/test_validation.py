"""Tests for validation functions."""
import pytest
from export_all import validate_ergo_address, validate_wallet_addresses


class TestValidateErgoAddress:
    """Tests for validate_ergo_address function."""
    
    def test_valid_address_starting_with_9(self):
        """Test that a valid address starting with 9 is accepted."""
        address = "9fRusAarL1KkrWQVsxSRVYnvWzD4SiWEFKvYrasQPvQMZarM7Ks"
        assert validate_ergo_address(address) is True
    
    def test_valid_address_starting_with_3(self):
        """Test that a valid address starting with 3 is accepted."""
        address = "3WwKzFjZGrtKAV7qSCoJsZK9iJhLLrUa3uwd4yw52bVtDVv6j5TL"
        assert validate_ergo_address(address) is True
    
    def test_invalid_address_too_short(self):
        """Test that an address that is too short is rejected."""
        address = "9fRusAarL1KkrWQVsxSRVYnvWzD4SiWEF"
        assert validate_ergo_address(address) is False
    
    def test_invalid_address_too_long(self):
        """Test that an address that is too long is rejected."""
        address = "9" * 60
        assert validate_ergo_address(address) is False
    
    def test_invalid_address_wrong_starting_character(self):
        """Test that an address with wrong starting character is rejected."""
        address = "5fRusAarL1KkrWQVsxSRVYnvWzD4SiWEFKvYrasQPvQMZarM7Ks"
        assert validate_ergo_address(address) is False
    
    def test_invalid_address_invalid_characters(self):
        """Test that an address with invalid Base58 characters is rejected."""
        address = "9fRusAarL1KkrWQVsxSRVYnvWzD4SiWEFKvYrasQPvQMZarM7K0"  # Contains '0'
        assert validate_ergo_address(address) is False
    
    def test_empty_address(self):
        """Test that an empty address is rejected."""
        assert validate_ergo_address("") is False
    
    def test_none_address(self):
        """Test that None is rejected."""
        assert validate_ergo_address(None) is False
    
    def test_non_string_address(self):
        """Test that non-string input is rejected."""
        assert validate_ergo_address(123) is False


class TestValidateWalletAddresses:
    """Tests for validate_wallet_addresses function."""
    
    def test_all_valid_addresses(self):
        """Test validation with all valid addresses."""
        addresses = [
            "9fRusAarL1KkrWQVsxSRVYnvWzD4SiWEFKvYrasQPvQMZarM7Ks",
            "3WwKzFjZGrtKAV7qSCoJsZK9iJhLLrUa3uwd4yw52bVtDVv6j5TL"
        ]
        valid, invalid = validate_wallet_addresses(addresses)
        assert len(valid) == 2
        assert len(invalid) == 0
    
    def test_all_invalid_addresses(self):
        """Test validation with all invalid addresses."""
        addresses = ["invalid1", "invalid2", ""]
        valid, invalid = validate_wallet_addresses(addresses)
        assert len(valid) == 0
        assert len(invalid) == 3
    
    def test_mixed_addresses(self):
        """Test validation with mixed valid and invalid addresses."""
        addresses = [
            "9fRusAarL1KkrWQVsxSRVYnvWzD4SiWEFKvYrasQPvQMZarM7Ks",
            "invalid",
            "3WwKzFjZGrtKAV7qSCoJsZK9iJhLLrUa3uwd4yw52bVtDVv6j5TL"
        ]
        valid, invalid = validate_wallet_addresses(addresses)
        assert len(valid) == 2
        assert len(invalid) == 1
    
    def test_addresses_with_whitespace(self):
        """Test that addresses with whitespace are properly trimmed."""
        addresses = [
            "  9fRusAarL1KkrWQVsxSRVYnvWzD4SiWEFKvYrasQPvQMZarM7Ks  ",
            "3WwKzFjZGrtKAV7qSCoJsZK9iJhLLrUa3uwd4yw52bVtDVv6j5TL\n"
        ]
        valid, invalid = validate_wallet_addresses(addresses)
        assert len(valid) == 2
        assert len(invalid) == 0
    
    def test_empty_list(self):
        """Test validation with empty list."""
        valid, invalid = validate_wallet_addresses([])
        assert len(valid) == 0
        assert len(invalid) == 0
