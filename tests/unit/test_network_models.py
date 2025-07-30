"""
Unit tests for network models and DTOs.
Tests the data transfer objects and protocol message handling.
"""
import pytest
from unittest.mock import Mock, patch
from ipaddress import IPv4Address, AddressValueError

from src.dto.network_models import (
    ProtocolConstants, 
    ScannerProtocolMessage, 
    FieldValidator,
    Serializable,
    Deserializable,
    Debuggable
)


class TestProtocolConstants:
    """Test cases for ProtocolConstants"""
    
    def test_constants_values(self):
        """Test that protocol constants have expected values"""
        assert ProtocolConstants.SIGNATURE == b'\x55\x00\x00'
        assert ProtocolConstants.TYPE_OF_REQUEST == b'\x5a\x00\x00'
        assert ProtocolConstants.TYPE_OF_FILE_TRANSFER == b'\x5a\x54\x00'
        assert ProtocolConstants.EXPECTED_MESSAGE_SIZE == 90
        assert ProtocolConstants.SRC_NAME_SIZE == 20
        assert ProtocolConstants.DST_NAME_SIZE == 40
        assert ProtocolConstants.RESERVED1_SIZE == 6
        assert ProtocolConstants.RESERVED2_SIZE == 4
        assert ProtocolConstants.RESERVED3_SIZE == 10
        assert ProtocolConstants.IP_SIZE == 4
    
    def test_constants_types(self):
        """Test that constants have correct types"""
        assert isinstance(ProtocolConstants.SIGNATURE, bytes)
        assert isinstance(ProtocolConstants.TYPE_OF_REQUEST, bytes)
        assert isinstance(ProtocolConstants.TYPE_OF_FILE_TRANSFER, bytes)
        assert isinstance(ProtocolConstants.EXPECTED_MESSAGE_SIZE, int)


class TestFieldValidator:
    """Test cases for FieldValidator utility class"""
    
    def test_validate_ip_address_string_valid(self):
        """Test IP validation with valid string"""
        result = FieldValidator.validate_ip_address("192.168.1.100")
        assert isinstance(result, IPv4Address)
        assert str(result) == "192.168.1.100"
    
    def test_validate_ip_address_string_invalid(self):
        """Test IP validation with invalid string"""
        with pytest.raises(ValueError) as exc_info:
            FieldValidator.validate_ip_address("300.300.300.300")
        
        assert "Invalid IP address" in str(exc_info.value)
    
    def test_validate_ip_address_ipv4_object(self):
        """Test IP validation with IPv4Address object"""
        ip = IPv4Address("10.0.0.1")
        result = FieldValidator.validate_ip_address(ip)
        assert result == ip
        assert isinstance(result, IPv4Address)
    
    def test_validate_ip_address_bytes(self):
        """Test IP validation with bytes"""
        ip_bytes = b'\xc0\xa8\x01\x64'  # 192.168.1.100
        result = FieldValidator.validate_ip_address(ip_bytes)
        assert isinstance(result, IPv4Address)
        assert str(result) == "192.168.1.100"
    
    def test_validate_ip_address_int(self):
        """Test IP validation with integer"""
        ip_int = 3232235876  # 192.168.1.100
        result = FieldValidator.validate_ip_address(ip_int)
        assert isinstance(result, IPv4Address)
        assert str(result) == "192.168.1.100"
    
    def test_validate_bytes_field_valid_string(self):
        """Test bytes field validation with valid string"""
        result = FieldValidator.validate_bytes_field("test", 10, "test_field")
        assert result == b"test\x00\x00\x00\x00\x00\x00"
        assert len(result) == 10
    
    def test_validate_bytes_field_valid_bytes(self):
        """Test bytes field validation with valid bytes"""
        test_bytes = b"test"
        result = FieldValidator.validate_bytes_field(test_bytes, 10, "test_field")
        assert result == b"test\x00\x00\x00\x00\x00\x00"
        assert len(result) == 10
    
    def test_validate_bytes_field_exact_size(self):
        """Test bytes field validation with exact size"""
        test_bytes = b"exact_size"  # 10 bytes
        result = FieldValidator.validate_bytes_field(test_bytes, 10, "test_field")
        assert result == test_bytes
        assert len(result) == 10
    
    def test_validate_bytes_field_too_long(self):
        """Test bytes field validation with oversized input"""
        test_bytes = b"this_is_too_long_for_the_field"
        result = FieldValidator.validate_bytes_field(test_bytes, 10, "test_field")
        assert result == test_bytes[:10]
        assert len(result) == 10
    
    def test_validate_bytes_field_invalid_type(self):
        """Test bytes field validation with invalid type"""
        with pytest.raises(ValueError) as exc_info:
            FieldValidator.validate_bytes_field(12345, 10, "test_field")
        
        assert "must be string or bytes" in str(exc_info.value)


class TestScannerProtocolMessage:
    """Test cases for ScannerProtocolMessage"""
    
    def test_create_default_message(self):
        """Test creating message with default values"""
        message = ScannerProtocolMessage()
        
        assert message.signature == ProtocolConstants.SIGNATURE
        assert message.type_of_request == ProtocolConstants.TYPE_OF_REQUEST
        assert len(message.reserved1) == ProtocolConstants.RESERVED1_SIZE
        assert isinstance(message.initiator_ip, IPv4Address)
        assert len(message.reserved2) == ProtocolConstants.RESERVED2_SIZE
        assert len(message.reserved3) == ProtocolConstants.RESERVED3_SIZE
    
    def test_create_custom_message(self, sample_ip):
        """Test creating message with custom values"""
        message = ScannerProtocolMessage(
            type_of_request=ProtocolConstants.TYPE_OF_FILE_TRANSFER,
            initiator_ip=sample_ip,
            src_name=b"CustomSource",
            dst_name=b"CustomDestination"
        )
        
        assert message.signature == ProtocolConstants.SIGNATURE
        assert message.type_of_request == ProtocolConstants.TYPE_OF_FILE_TRANSFER
        assert message.initiator_ip == sample_ip
        assert message.src_name == b"CustomSource"
        assert message.dst_name == b"CustomDestination"
    
    def test_ip_validation_string(self):
        """Test IP validation in message creation with string"""
        message = ScannerProtocolMessage(initiator_ip="10.0.0.1")
        assert isinstance(message.initiator_ip, IPv4Address)
        assert str(message.initiator_ip) == "10.0.0.1"
    
    def test_ip_validation_invalid(self):
        """Test IP validation with invalid IP"""
        with pytest.raises(ValueError):
            ScannerProtocolMessage(initiator_ip="invalid.ip.address")
    
    def test_src_name_validation_string(self):
        """Test src_name validation with string"""
        message = ScannerProtocolMessage(src_name="TestSource")
        assert len(message.src_name) == ProtocolConstants.SRC_NAME_SIZE
        assert message.src_name.startswith(b"TestSource")
    
    def test_src_name_validation_bytes(self):
        """Test src_name validation with bytes"""
        test_name = b"TestBytes"
        message = ScannerProtocolMessage(src_name=test_name)
        assert len(message.src_name) == ProtocolConstants.SRC_NAME_SIZE
        assert message.src_name.startswith(test_name)
    
    def test_dst_name_validation_string(self):
        """Test dst_name validation with string"""
        message = ScannerProtocolMessage(dst_name="TestDestination")
        assert len(message.dst_name) == ProtocolConstants.DST_NAME_SIZE
        assert message.dst_name.startswith(b"TestDestination")
    
    def test_dst_name_validation_bytes(self):
        """Test dst_name validation with bytes"""
        test_name = b"TestDestBytes"
        message = ScannerProtocolMessage(dst_name=test_name)
        assert len(message.dst_name) == ProtocolConstants.DST_NAME_SIZE
        assert message.dst_name.startswith(test_name)
    
    @patch('src.dto.network_models.MessageSerializer')
    def test_to_bytes(self, mock_serializer):
        """Test message serialization to bytes"""
        mock_serializer.serialize_message.return_value = b"serialized_data"
        
        message = ScannerProtocolMessage()
        result = message.to_bytes()
        
        assert result == b"serialized_data"
        mock_serializer.serialize_message.assert_called_once_with(message)
    
    @patch('src.dto.network_models.MessageDebugger')
    def test_debug_info(self, mock_debugger):
        """Test getting debug information"""
        mock_debugger.get_debug_info.return_value = "Debug info string"
        
        message = ScannerProtocolMessage()
        result = message.debug_info()
        
        assert result == "Debug info string"
        mock_debugger.get_debug_info.assert_called_once_with(message)
    
    @patch('src.dto.network_models.MessageDebugger')
    def test_debug(self, mock_debugger):
        """Test printing debug information"""
        message = ScannerProtocolMessage()
        message.debug()
        
        mock_debugger.print_debug_info.assert_called_once_with(message)
    
    @patch('src.dto.network_models.MessageDeserializer')
    def test_from_bytes(self, mock_deserializer):
        """Test message deserialization from bytes"""
        test_data = b"test_message_data"
        mock_message = ScannerProtocolMessage()
        mock_deserializer.deserialize_message.return_value = mock_message
        
        result = ScannerProtocolMessage.from_bytes(test_data)
        
        assert result == mock_message
        mock_deserializer.deserialize_message.assert_called_once_with(test_data)
    
    def test_message_equality(self):
        """Test message equality comparison"""
        message1 = ScannerProtocolMessage(
            initiator_ip="192.168.1.100",
            src_name="Source1",
            dst_name="Dest1"
        )
        
        message2 = ScannerProtocolMessage(
            initiator_ip="192.168.1.100",
            src_name="Source1",
            dst_name="Dest1"
        )
        
        message3 = ScannerProtocolMessage(
            initiator_ip="192.168.1.101",
            src_name="Source2",
            dst_name="Dest2"
        )
        
        assert message1 == message2
        assert message1 != message3
    
    def test_message_repr(self):
        """Test message string representation"""
        message = ScannerProtocolMessage(
            initiator_ip="192.168.1.100",
            src_name="TestSrc",
            dst_name="TestDst"
        )
        
        repr_str = repr(message)
        assert "ScannerProtocolMessage" in repr_str
        assert "192.168.1.100" in repr_str


class TestProtocolInterfaces:
    """Test protocol interface implementations"""
    
    def test_serializable_protocol(self):
        """Test that ScannerProtocolMessage implements Serializable"""
        message = ScannerProtocolMessage()
        assert isinstance(message, Serializable)
        assert hasattr(message, 'to_bytes')
        assert callable(message.to_bytes)
    
    def test_deserializable_protocol(self):
        """Test that ScannerProtocolMessage implements Deserializable"""
        assert hasattr(ScannerProtocolMessage, 'from_bytes')
        assert callable(ScannerProtocolMessage.from_bytes)
    
    def test_debuggable_protocol(self):
        """Test that ScannerProtocolMessage implements Debuggable"""
        message = ScannerProtocolMessage()
        assert isinstance(message, Debuggable)
        assert hasattr(message, 'debug_info')
        assert callable(message.debug_info)


class TestMessageValidation:
    """Test edge cases and validation scenarios"""
    
    def test_empty_src_name(self):
        """Test message with empty src_name"""
        message = ScannerProtocolMessage(src_name="")
        assert len(message.src_name) == ProtocolConstants.SRC_NAME_SIZE
        assert message.src_name == b'\x00' * ProtocolConstants.SRC_NAME_SIZE
    
    def test_empty_dst_name(self):
        """Test message with empty dst_name"""
        message = ScannerProtocolMessage(dst_name="")
        assert len(message.dst_name) == ProtocolConstants.DST_NAME_SIZE
        assert message.dst_name == b'\x00' * ProtocolConstants.DST_NAME_SIZE
    
    def test_very_long_src_name(self):
        """Test message with oversized src_name"""
        long_name = "VeryLongSourceNameThatExceedsTheMaximumSize"
        message = ScannerProtocolMessage(src_name=long_name)
        assert len(message.src_name) == ProtocolConstants.SRC_NAME_SIZE
        assert message.src_name == long_name[:ProtocolConstants.SRC_NAME_SIZE].encode('ascii')
    
    def test_very_long_dst_name(self):
        """Test message with oversized dst_name"""
        long_name = "VeryLongDestinationNameThatExceedsTheMaximumSizeAllowedByTheProtocol"
        message = ScannerProtocolMessage(dst_name=long_name)
        assert len(message.dst_name) == ProtocolConstants.DST_NAME_SIZE
        assert message.dst_name == long_name[:ProtocolConstants.DST_NAME_SIZE].encode('ascii')
    
    def test_unicode_src_name(self):
        """Test message with unicode src_name"""
        unicode_name = "测试源"  # Chinese characters
        message = ScannerProtocolMessage(src_name=unicode_name)
        assert len(message.src_name) == ProtocolConstants.SRC_NAME_SIZE
        # Should be encoded and padded correctly
        assert message.src_name.endswith(b'\x00')
    
    def test_special_characters_in_names(self):
        """Test message with special characters in names"""
        special_src = "Src@#$%"
        special_dst = "Dst!&*()"
        message = ScannerProtocolMessage(src_name=special_src, dst_name=special_dst)
        
        assert len(message.src_name) == ProtocolConstants.SRC_NAME_SIZE
        assert len(message.dst_name) == ProtocolConstants.DST_NAME_SIZE
        assert message.src_name.startswith(special_src.encode('ascii'))
        assert message.dst_name.startswith(special_dst.encode('ascii'))


class TestMessageTypes:
    """Test different message types"""
    
    def test_discovery_message(self):
        """Test creating a discovery message"""
        message = ScannerProtocolMessage(
            type_of_request=ProtocolConstants.TYPE_OF_REQUEST,
            src_name="Scanner",
            dst_name=""
        )
        
        assert message.type_of_request == ProtocolConstants.TYPE_OF_REQUEST
        assert message.src_name.startswith(b"Scanner")
        assert message.dst_name.startswith(b"")
    
    def test_file_transfer_message(self):
        """Test creating a file transfer message"""
        message = ScannerProtocolMessage(
            type_of_request=ProtocolConstants.TYPE_OF_FILE_TRANSFER,
            src_name="FileSender",
            dst_name="FileReceiver"
        )
        
        assert message.type_of_request == ProtocolConstants.TYPE_OF_FILE_TRANSFER
        assert message.src_name.startswith(b"FileSender")
        assert message.dst_name.startswith(b"FileReceiver")
    
    def test_custom_type_message(self):
        """Test creating a message with custom type"""
        custom_type = b'\x5a\x99\x00'
        message = ScannerProtocolMessage(
            type_of_request=custom_type,
            src_name="CustomSender",
            dst_name="CustomReceiver"
        )
        
        assert message.type_of_request == custom_type
        assert message.src_name.startswith(b"CustomSender")
        assert message.dst_name.startswith(b"CustomReceiver")
