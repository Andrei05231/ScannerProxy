"""
Unit tests for message protocol builders and handlers.
"""

import struct
from unittest.mock import Mock, patch, MagicMock
import pytest
from ipaddress import IPv4Address

from src.network.protocols.message_builder import ScannerProtocolMessageBuilder
from src.network.protocols.scanner_protocol import MessageSerializer, MessageDeserializer, MessageDebugger
from src.dto.network_models import ScannerProtocolMessage, ProtocolConstants


class TestScannerProtocolMessageBuilder:
    """Test cases for ScannerProtocolMessageBuilder"""
    
    def test_init_creates_builder_with_defaults(self):
        """Test that builder initializes with default values"""
        builder = ScannerProtocolMessageBuilder()
        
        # Should have default values
        assert builder._signature == ProtocolConstants.SIGNATURE
        assert builder._type_of_request == ProtocolConstants.TYPE_OF_REQUEST
        assert len(builder._reserved1) == ProtocolConstants.RESERVED1_SIZE
        assert builder._initiator_ip == IPv4Address("192.168.1.137")
        assert len(builder._reserved2) == ProtocolConstants.RESERVED2_SIZE
        assert builder._src_name == b"L24e"
        assert builder._dst_name == b""
        assert len(builder._reserved3) == ProtocolConstants.RESERVED3_SIZE
    
    def test_reset_returns_builder_instance(self):
        """Test that reset method returns builder instance for chaining"""
        builder = ScannerProtocolMessageBuilder()
        result = builder.reset()
        
        assert result is builder
        # Should reset to defaults
        assert builder._signature == ProtocolConstants.SIGNATURE
    
    def test_with_signature_sets_signature(self):
        """Test setting custom signature"""
        builder = ScannerProtocolMessageBuilder()
        custom_signature = b'CUSTOM'
        
        result = builder.with_signature(custom_signature)
        
        assert result is builder  # Should return self for chaining
        assert builder._signature == custom_signature
    
    def test_with_type_of_request_sets_request_type(self):
        """Test setting request type"""
        builder = ScannerProtocolMessageBuilder()
        request_type = ProtocolConstants.TYPE_OF_DISCOVERY
        
        result = builder.with_type_of_request(request_type)
        
        assert result is builder
        assert builder._type_of_request == request_type
    
    def test_with_initiator_ip_sets_ip_address(self):
        """Test setting initiator IP address"""
        builder = ScannerProtocolMessageBuilder()
        ip_address = IPv4Address("10.0.0.1")
        
        result = builder.with_initiator_ip(ip_address)
        
        assert result is builder
        assert builder._initiator_ip == ip_address
    
    def test_with_src_name_sets_source_name(self):
        """Test setting source name"""
        builder = ScannerProtocolMessageBuilder()
        src_name = b"TestSrc"
        
        result = builder.with_src_name(src_name)
        
        assert result is builder
        assert builder._src_name == src_name
    
    def test_with_dst_name_sets_destination_name(self):
        """Test setting destination name"""
        builder = ScannerProtocolMessageBuilder()
        dst_name = b"TestDst"
        
        result = builder.with_dst_name(dst_name)
        
        assert result is builder
        assert builder._dst_name == dst_name
    
    def test_build_creates_protocol_message(self):
        """Test building a complete protocol message"""
        builder = ScannerProtocolMessageBuilder()
        
        message = builder.build()
        
        assert isinstance(message, ScannerProtocolMessage)
        assert message.signature == ProtocolConstants.SIGNATURE
        assert message.type_of_request == ProtocolConstants.TYPE_OF_REQUEST
        assert message.initiator_ip == IPv4Address("192.168.1.137")
        assert message.src_name == b"L24e"
    
    def test_builder_method_chaining(self):
        """Test that builder methods can be chained"""
        builder = ScannerProtocolMessageBuilder()
        
        message = (builder
                  .with_signature(b'TEST')
                  .with_type_of_request(ProtocolConstants.TYPE_OF_DISCOVERY)
                  .with_initiator_ip(IPv4Address("172.16.0.1"))
                  .with_src_name(b"Chain")
                  .with_dst_name(b"Test")
                  .build())
        
        assert message.signature == b'TEST'
        assert message.type_of_request == ProtocolConstants.TYPE_OF_DISCOVERY
        assert message.initiator_ip == IPv4Address("172.16.0.1")
        assert message.src_name == b"Chain"
        assert message.dst_name == b"Test"


class TestMessageSerializer:
    """Test cases for MessageSerializer"""
    
    def test_serialize_message_creates_bytes(self):
        """Test that serialize_message returns bytes"""
        # Create a sample message
        message = ScannerProtocolMessage(
            signature=ProtocolConstants.SIGNATURE,
            type_of_request=ProtocolConstants.TYPE_OF_REQUEST,
            reserved1=b'\x00' * ProtocolConstants.RESERVED1_SIZE,
            initiator_ip=IPv4Address("192.168.1.100"),
            reserved2=b'\x00' * ProtocolConstants.RESERVED2_SIZE,
            src_name=b"Test",
            dst_name=b"Dest",
            reserved3=b'\x00' * ProtocolConstants.RESERVED3_SIZE
        )
        
        serialized = MessageSerializer.serialize_message(message)
        
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0
    
    def test_serialize_with_custom_values(self):
        """Test serialization with custom message values"""
        message = ScannerProtocolMessage(
            signature=b'CUSTOM',
            type_of_request=ProtocolConstants.TYPE_OF_DISCOVERY,
            reserved1=b'\x00' * ProtocolConstants.RESERVED1_SIZE,
            initiator_ip=IPv4Address("10.0.0.1"),
            reserved2=b'\x00' * ProtocolConstants.RESERVED2_SIZE,
            src_name=b"CustomSrc",
            dst_name=b"CustomDst",
            reserved3=b'\x00' * ProtocolConstants.RESERVED3_SIZE
        )
        
        serialized = MessageSerializer.serialize_message(message)
        
        assert isinstance(serialized, bytes)
        # Should contain the custom signature at the beginning
        assert serialized.startswith(b'CUSTOM')
    
    def test_serialize_handles_none_message(self):
        """Test serialization with None message"""
        with pytest.raises((TypeError, AttributeError)):
            MessageSerializer.serialize_message(None)
    
    def test_serialize_maintains_field_order(self):
        """Test that serialization maintains correct field order"""
        message = ScannerProtocolMessage(
            signature=b'ABCD',
            type_of_request=b'\x01',
            reserved1=b'\x00' * ProtocolConstants.RESERVED1_SIZE,
            initiator_ip=IPv4Address("192.168.1.1"),
            reserved2=b'\x00' * ProtocolConstants.RESERVED2_SIZE,
            src_name=b"Src1",
            dst_name=b"Dst1",
            reserved3=b'\x00' * ProtocolConstants.RESERVED3_SIZE
        )
        
        serialized = MessageSerializer.serialize_message(message)
        
        # Signature should be at the beginning
        assert serialized[:4] == b'ABCD'


class TestMessageDeserializer:
    """Test cases for MessageDeserializer"""
    
    def test_deserialize_message_recreates_object(self):
        """Test that deserialize_message recreates ScannerProtocolMessage"""
        # First create and serialize a message
        original_message = ScannerProtocolMessage(
            signature=ProtocolConstants.SIGNATURE,
            type_of_request=ProtocolConstants.TYPE_OF_REQUEST,
            reserved1=b'\x00' * ProtocolConstants.RESERVED1_SIZE,
            initiator_ip=IPv4Address("192.168.1.100"),
            reserved2=b'\x00' * ProtocolConstants.RESERVED2_SIZE,
            src_name=b"Original",
            dst_name=b"Message",
            reserved3=b'\x00' * ProtocolConstants.RESERVED3_SIZE
        )
        
        serialized = MessageSerializer.serialize_message(original_message)
        deserialized = MessageDeserializer.deserialize_message(serialized)
        
        assert isinstance(deserialized, ScannerProtocolMessage)
        assert deserialized.signature == original_message.signature
        assert deserialized.type_of_request == original_message.type_of_request
        assert deserialized.initiator_ip == original_message.initiator_ip
        assert deserialized.src_name == original_message.src_name
        assert deserialized.dst_name == original_message.dst_name
    
    def test_deserialize_invalid_data_raises_exception(self):
        """Test that deserializing invalid data raises exception"""
        invalid_data = b'invalid_message_data'
        
        with pytest.raises((ValueError, struct.error, IndexError)):
            MessageDeserializer.deserialize_message(invalid_data)
    
    def test_deserialize_insufficient_data_raises_exception(self):
        """Test that deserializing insufficient data raises exception"""
        short_data = b'short'
        
        with pytest.raises((ValueError, struct.error, IndexError)):
            MessageDeserializer.deserialize_message(short_data)
    
    def test_deserialize_oversized_data_handles_gracefully(self):
        """Test deserializing oversized data"""
        # Create valid message data then append extra bytes
        valid_message = ScannerProtocolMessage(
            signature=ProtocolConstants.SIGNATURE,
            type_of_request=ProtocolConstants.TYPE_OF_REQUEST,
            reserved1=b'\x00' * ProtocolConstants.RESERVED1_SIZE,
            initiator_ip=IPv4Address("192.168.1.1"),
            reserved2=b'\x00' * ProtocolConstants.RESERVED2_SIZE,
            src_name=b"Test",
            dst_name=b"Test",
            reserved3=b'\x00' * ProtocolConstants.RESERVED3_SIZE
        )
        
        serialized = MessageSerializer.serialize_message(valid_message)
        long_data = serialized + b'extra_data'
        
        # Should still deserialize correctly, ignoring extra data
        deserialized = MessageDeserializer.deserialize_message(long_data)
        assert isinstance(deserialized, ScannerProtocolMessage)
    
    def test_deserialize_empty_data_raises_exception(self):
        """Test that deserializing empty data raises exception"""
        with pytest.raises((ValueError, struct.error, IndexError)):
            MessageDeserializer.deserialize_message(b'')
    
    def test_deserialize_none_data_raises_exception(self):
        """Test that deserializing None data raises exception"""
        with pytest.raises(TypeError):
            MessageDeserializer.deserialize_message(None)


class TestMessageDebugger:
    """Test cases for MessageDebugger"""
    
    def test_get_debug_info_returns_dict(self):
        """Test that get_debug_info returns a dictionary"""
        message = ScannerProtocolMessage(
            signature=ProtocolConstants.SIGNATURE,
            type_of_request=ProtocolConstants.TYPE_OF_REQUEST,
            reserved1=b'\x00' * ProtocolConstants.RESERVED1_SIZE,
            initiator_ip=IPv4Address("192.168.1.100"),
            reserved2=b'\x00' * ProtocolConstants.RESERVED2_SIZE,
            src_name=b"Debug",
            dst_name=b"Test",
            reserved3=b'\x00' * ProtocolConstants.RESERVED3_SIZE
        )
        
        debug_info = MessageDebugger.get_debug_info(message)
        
        assert isinstance(debug_info, dict)
        assert 'signature' in debug_info
        assert 'type_of_request' in debug_info
        assert 'initiator_ip' in debug_info
        assert 'src_name' in debug_info
        assert 'dst_name' in debug_info
    
    def test_debug_info_contains_readable_values(self):
        """Test that debug info contains human-readable values"""
        message = ScannerProtocolMessage(
            signature=b'TEST',
            type_of_request=ProtocolConstants.TYPE_OF_DISCOVERY,
            reserved1=b'\x00' * ProtocolConstants.RESERVED1_SIZE,
            initiator_ip=IPv4Address("10.0.0.1"),
            reserved2=b'\x00' * ProtocolConstants.RESERVED2_SIZE,
            src_name=b"DebugSrc",
            dst_name=b"DebugDst",
            reserved3=b'\x00' * ProtocolConstants.RESERVED3_SIZE
        )
        
        debug_info = MessageDebugger.get_debug_info(message)
        
        # Should contain string representations
        assert isinstance(debug_info['signature'], str)
        assert isinstance(debug_info['initiator_ip'], str)
        assert '10.0.0.1' in debug_info['initiator_ip']
    
    def test_debug_info_handles_none_message(self):
        """Test debug info with None message"""
        with pytest.raises((TypeError, AttributeError)):
            MessageDebugger.get_debug_info(None)


class TestSerializationRoundTrip:
    """Test round-trip serialization/deserialization"""
    
    def test_round_trip_preserves_message_data(self):
        """Test that serialize->deserialize preserves all message data"""
        original_messages = [
            ScannerProtocolMessage(
                signature=ProtocolConstants.SIGNATURE,
                type_of_request=ProtocolConstants.TYPE_OF_REQUEST,
                reserved1=b'\x00' * ProtocolConstants.RESERVED1_SIZE,
                initiator_ip=IPv4Address("192.168.1.1"),
                reserved2=b'\x00' * ProtocolConstants.RESERVED2_SIZE,
                src_name=b"Round",
                dst_name=b"Trip",
                reserved3=b'\x00' * ProtocolConstants.RESERVED3_SIZE
            ),
            ScannerProtocolMessage(
                signature=b'CUSTOM',
                type_of_request=ProtocolConstants.TYPE_OF_DISCOVERY,
                reserved1=b'\x00' * ProtocolConstants.RESERVED1_SIZE,
                initiator_ip=IPv4Address("10.0.0.1"),
                reserved2=b'\x00' * ProtocolConstants.RESERVED2_SIZE,
                src_name=b"Custom",
                dst_name=b"Test",
                reserved3=b'\x00' * ProtocolConstants.RESERVED3_SIZE
            )
        ]
        
        for original in original_messages:
            serialized = MessageSerializer.serialize_message(original)
            deserialized = MessageDeserializer.deserialize_message(serialized)
            
            assert deserialized.signature == original.signature
            assert deserialized.type_of_request == original.type_of_request
            assert deserialized.initiator_ip == original.initiator_ip
            assert deserialized.src_name == original.src_name
            assert deserialized.dst_name == original.dst_name


class TestProtocolMessageIntegration:
    """Integration tests for protocol message handling"""
    
    def test_builder_message_serialization_integration(self):
        """Test that builder-created messages serialize correctly"""
        builder = ScannerProtocolMessageBuilder()
        
        message = (builder
                  .with_signature(b'INTG')
                  .with_type_of_request(ProtocolConstants.TYPE_OF_DISCOVERY)
                  .with_initiator_ip(IPv4Address("172.16.0.100"))
                  .with_src_name(b"Integration")
                  .with_dst_name(b"Test")
                  .build())
        
        # Should serialize without errors
        serialized = MessageSerializer.serialize_message(message)
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0
        
        # Should deserialize back to equivalent message
        deserialized = MessageDeserializer.deserialize_message(serialized)
        assert deserialized.signature == b'INTG'
        assert deserialized.type_of_request == ProtocolConstants.TYPE_OF_DISCOVERY
        assert deserialized.initiator_ip == IPv4Address("172.16.0.100")
        assert deserialized.src_name == b"Integration"
        assert deserialized.dst_name == b"Test"
