"""Tests for transaction processing functions."""
import pytest
from export_all import (
    filter_transaction_inputs_outputs,
    calculate_transaction_values,
    process_outgoing_transaction,
    process_incoming_transaction,
    ERG_DECIMALS,
    CONSOLIDATION_THRESHOLD
)


class TestFilterTransactionInputsOutputs:
    """Tests for filter_transaction_inputs_outputs function."""
    
    def test_filter_with_matching_addresses(self):
        """Test filtering with addresses that match inputs and outputs."""
        transaction = {
            'inputs': [
                {'address': 'addr1', 'value': 1000000000},
                {'address': 'addr2', 'value': 2000000000},
                {'address': 'addr3', 'value': 3000000000}
            ],
            'outputs': [
                {'address': 'addr1', 'value': 500000000},
                {'address': 'addr4', 'value': 1000000000}
            ]
        }
        addresses = ['addr1', 'addr2']
        
        inputs, outputs, fees = filter_transaction_inputs_outputs(transaction, addresses)
        
        assert len(inputs) == 2
        assert len(outputs) == 1
        assert inputs[0]['address'] == 'addr1'
        assert inputs[1]['address'] == 'addr2'
        assert outputs[0]['address'] == 'addr1'
    
    def test_filter_with_no_matching_addresses(self):
        """Test filtering with no matching addresses."""
        transaction = {
            'inputs': [{'address': 'addr1', 'value': 1000000000}],
            'outputs': [{'address': 'addr2', 'value': 1000000000}]
        }
        addresses = ['addr3', 'addr4']
        
        inputs, outputs, fees = filter_transaction_inputs_outputs(transaction, addresses)
        
        assert len(inputs) == 0
        assert len(outputs) == 0


class TestCalculateTransactionValues:
    """Tests for calculate_transaction_values function."""
    
    def test_calculate_values_basic(self):
        """Test basic value calculation."""
        inputs = [
            {'value': 1000000000},  # 1 ERG
            {'value': 2000000000}   # 2 ERG
        ]
        outputs = [
            {'value': 500000000}    # 0.5 ERG
        ]
        fees = [
            {'value': 1000000}      # 0.001 ERG
        ]
        
        input_total, output_total, fee_total = calculate_transaction_values(inputs, outputs, fees)
        
        assert input_total == 3.0
        assert output_total == 0.5
        assert fee_total == 0.001
    
    def test_calculate_values_empty(self):
        """Test value calculation with empty lists."""
        input_total, output_total, fee_total = calculate_transaction_values([], [], [])
        
        assert input_total == 0.0
        assert output_total == 0.0
        assert fee_total == 0.0


class TestProcessOutgoingTransaction:
    """Tests for process_outgoing_transaction function."""
    
    def test_process_normal_outgoing(self):
        """Test processing a normal outgoing transaction."""
        transaction = {
            'id': 'tx_123',
            'timestamp': 1704067200000
        }
        my_inputs = 10.0
        my_outputs = 2.0
        fees = 0.001
        
        rows = process_outgoing_transaction(transaction, my_inputs, my_outputs, fees)
        
        assert len(rows) == 1
        assert rows[0]['Sent Amount'] == 7.999  # 10 - 2 - 0.001
        assert rows[0]['Sent Currency'] == 'ERG'
        assert rows[0]['Fee Amount'] == 0.001
    
    def test_process_consolidation_transaction(self):
        """Test processing a wallet consolidation transaction."""
        transaction = {
            'id': 'tx_consolidation',
            'timestamp': 1704067200000
        }
        my_inputs = 5.0
        my_outputs = 4.999
        fees = 0.001
        
        # This should be detected as consolidation (sent amount < threshold)
        rows = process_outgoing_transaction(transaction, my_inputs, my_outputs, fees)
        
        # Consolidation creates 2 rows
        assert len(rows) == 2
        assert 'Consolidated money within wallet' in rows[0]['Description']


class TestProcessIncomingTransaction:
    """Tests for process_incoming_transaction function."""
    
    def test_process_incoming(self):
        """Test processing an incoming transaction."""
        transaction = {
            'id': 'tx_incoming',
            'timestamp': 1704067200000
        }
        my_outputs = 5.0
        
        rows = process_incoming_transaction(transaction, my_outputs)
        
        assert len(rows) == 1
        assert rows[0]['Received Amount'] == 5.0
        assert rows[0]['Received Currency'] == 'ERG'
        assert rows[0]['Sent Amount'] == ''
        assert rows[0]['Sent Currency'] == ''
