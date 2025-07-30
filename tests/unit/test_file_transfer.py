"""
Unit tests for the FileTransferService class.
Tests file transfer operations including UDP discovery and TCP file transfers.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import socket
import os
from ipaddress import IPv4Address

from src.services.file_transfer import FileTransferService
from src.dto.network_models import ScannerProtocolMessage, ProtocolConstants


class TestFileTransferService:
    """Test cases for FileTransferService class"""
    
    def test_init(self):
        """Test FileTransferService initialization"""
        service = FileTransferService(
            local_ip="192.168.1.100",
            port=706,
            tcp_port=708
        )
        
        assert service.local_ip == "192.168.1.100"
        assert service.port == 706
        assert service.tcp_port == 708
        assert service.logger is not None
    
    @patch('src.services.file_transfer.MessageBuilder')
    @patch('socket.socket')
    def test_send_file_transfer_request_success_with_response(self, mock_socket_class, mock_message_builder, sample_file_transfer_message, temp_file):
        """Test successful file transfer request with UDP response"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock UDP response
        response_data = b"mock_response_data"
        mock_socket.recvfrom.return_value = (response_data, ("192.168.1.101", 706))
        
        # Mock message builder
        mock_request_message = sample_file_transfer_message
        mock_message_builder.create_file_transfer_request.return_value = mock_request_message
        
        # Mock message deserialization
        mock_response_message = ScannerProtocolMessage(
            src_name=b"Agent1",
            dst_name=b"Scanner"
        )
        
        service = FileTransferService("192.168.1.100", 706, 708)
        
        with patch.object(service, '_initiate_tcp_connection') as mock_tcp:
            mock_tcp.return_value = True
            
            with patch('src.services.file_transfer.ScannerProtocolMessage.from_bytes') as mock_from_bytes:
                mock_from_bytes.return_value = mock_response_message
                
                # Test the method
                success, response = service.send_file_transfer_request(
                    target_ip="192.168.1.101",
                    src_name="Scanner",
                    dst_name="Agent1",
                    file_path=temp_file
                )
        
        # Verify results
        assert success is True
        assert response == mock_response_message
        
        # Verify UDP socket operations
        mock_socket.bind.assert_called_once_with(("192.168.1.100", 706))
        mock_socket.sendto.assert_called_once()
        mock_socket.recvfrom.assert_called_once()
        mock_socket.close.assert_called_once()
        
        # Verify TCP connection was initiated
        mock_tcp.assert_called_once()
    
    @patch('src.services.file_transfer.MessageBuilder')
    @patch('socket.socket')
    def test_send_file_transfer_request_no_response(self, mock_socket_class, mock_message_builder, sample_file_transfer_message, temp_file):
        """Test file transfer request with no UDP response (timeout)"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock timeout exception
        mock_socket.recvfrom.side_effect = socket.timeout("No response")
        
        # Mock message builder
        mock_request_message = sample_file_transfer_message
        mock_message_builder.create_file_transfer_request.return_value = mock_request_message
        
        service = FileTransferService("192.168.1.100", 706, 708)
        
        # Test the method
        success, response = service.send_file_transfer_request(
            target_ip="192.168.1.101",
            src_name="Scanner",
            dst_name="Agent1",
            file_path=temp_file
        )
        
        # Verify results
        assert success is True  # UDP sent successfully
        assert response is None  # No response received
        
        # Verify socket operations
        mock_socket.sendto.assert_called_once()
        mock_socket.recvfrom.assert_called_once()
        mock_socket.close.assert_called_once()
    
    @patch('src.services.file_transfer.MessageBuilder')
    @patch('socket.socket')
    def test_send_file_transfer_request_socket_error(self, mock_socket_class, mock_message_builder, sample_file_transfer_message, temp_file):
        """Test file transfer request with socket error"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock socket error
        mock_socket.sendto.side_effect = socket.error("Socket error")
        
        # Mock message builder
        mock_request_message = sample_file_transfer_message
        mock_message_builder.create_file_transfer_request.return_value = mock_request_message
        
        service = FileTransferService("192.168.1.100", 706, 708)
        
        # Test the method
        success, response = service.send_file_transfer_request(
            target_ip="192.168.1.101",
            src_name="Scanner",
            dst_name="Agent1",
            file_path=temp_file
        )
        
        # Verify results
        assert success is False
        assert response is None
        
        # Verify socket was closed
        mock_socket.close.assert_called_once()
    
    @patch('src.services.file_transfer.MessageBuilder')
    @patch('socket.socket')
    def test_send_file_transfer_request_file_not_found(self, mock_socket_class, mock_message_builder, sample_file_transfer_message):
        """Test file transfer request with non-existent file"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock message builder
        mock_request_message = sample_file_transfer_message
        mock_message_builder.create_file_transfer_request.return_value = mock_request_message
        
        service = FileTransferService("192.168.1.100", 706, 708)
        
        # Test with non-existent file
        success, response = service.send_file_transfer_request(
            target_ip="192.168.1.101",
            src_name="Scanner",
            dst_name="Agent1",
            file_path="/non/existent/file.raw"
        )
        
        # Verify results - should still attempt UDP but fail at TCP
        assert success is True  # UDP part succeeds
        assert response is None
    
    @patch('socket.socket')
    def test_initiate_tcp_connection_success(self, mock_socket_class, temp_file):
        """Test successful TCP connection and file transfer"""
        # Setup mocks
        mock_tcp_socket = Mock()
        mock_socket_class.return_value = mock_tcp_socket
        
        # Mock file operations
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.side_effect = [b"chunk1", b"chunk2", b""]  # Simulate file reading
            mock_open.return_value.__enter__.return_value = mock_file
            
            with patch('os.path.getsize') as mock_getsize:
                mock_getsize.return_value = 12  # Total file size
                
                service = FileTransferService("192.168.1.100", 706, 708)
                
                # Test TCP connection
                success = service._initiate_tcp_connection("192.168.1.101", temp_file)
        
        # Verify success
        assert success is True
        
        # Verify TCP socket operations
        mock_tcp_socket.connect.assert_called_once_with(("192.168.1.101", 708))
        mock_tcp_socket.send.assert_called()  # Called multiple times for chunks
        mock_tcp_socket.close.assert_called_once()
    
    @patch('socket.socket')
    def test_initiate_tcp_connection_connect_error(self, mock_socket_class, temp_file):
        """Test TCP connection failure"""
        # Setup mocks
        mock_tcp_socket = Mock()
        mock_socket_class.return_value = mock_tcp_socket
        
        # Mock connection error
        mock_tcp_socket.connect.side_effect = socket.error("Connection refused")
        
        service = FileTransferService("192.168.1.100", 706, 708)
        
        # Test TCP connection
        success = service._initiate_tcp_connection("192.168.1.101", temp_file)
        
        # Verify failure
        assert success is False
        
        # Verify socket was closed
        mock_tcp_socket.close.assert_called_once()
    
    @patch('socket.socket')
    def test_initiate_tcp_connection_file_error(self, mock_socket_class, temp_file):
        """Test TCP connection with file reading error"""
        # Setup mocks
        mock_tcp_socket = Mock()
        mock_socket_class.return_value = mock_tcp_socket
        
        # Mock file error
        with patch('builtins.open', create=True) as mock_open:
            mock_open.side_effect = IOError("File read error")
            
            service = FileTransferService("192.168.1.100", 706, 708)
            
            # Test TCP connection
            success = service._initiate_tcp_connection("192.168.1.101", temp_file)
        
        # Verify failure
        assert success is False
        
        # Verify socket was closed
        mock_tcp_socket.close.assert_called_once()
    
    @patch('socket.socket')
    def test_send_file_over_tcp_with_progress(self, mock_socket_class, temp_file):
        """Test TCP file transfer with progress callback"""
        # Setup mocks
        mock_tcp_socket = Mock()
        mock_socket_class.return_value = mock_tcp_socket
        
        # Mock progress callback
        mock_progress_callback = Mock()
        
        # Create test file content
        test_content = b"Test file content for progress tracking"
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.side_effect = [test_content[:10], test_content[10:20], test_content[20:], b""]
            mock_open.return_value.__enter__.return_value = mock_file
            
            with patch('os.path.getsize') as mock_getsize:
                mock_getsize.return_value = len(test_content)
                
                service = FileTransferService("192.168.1.100", 706, 708)
                
                # Test file transfer with progress
                success = service._send_file_over_tcp(
                    mock_tcp_socket, 
                    temp_file, 
                    progress_callback=mock_progress_callback
                )
        
        # Verify success
        assert success is True
        
        # Verify progress callback was called
        assert mock_progress_callback.call_count > 0
        
        # Verify final progress call
        final_call = mock_progress_callback.call_args_list[-1]
        assert final_call[0] == (len(test_content), len(test_content))  # (bytes_sent, total_bytes)
    
    @patch('socket.socket')
    def test_send_file_over_tcp_without_progress(self, mock_socket_class, temp_file):
        """Test TCP file transfer without progress callback"""
        # Setup mocks
        mock_tcp_socket = Mock()
        mock_socket_class.return_value = mock_tcp_socket
        
        # Create test file content
        test_content = b"Test file content without progress"
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.side_effect = [test_content, b""]
            mock_open.return_value.__enter__.return_value = mock_file
            
            with patch('os.path.getsize') as mock_getsize:
                mock_getsize.return_value = len(test_content)
                
                service = FileTransferService("192.168.1.100", 706, 708)
                
                # Test file transfer without progress
                success = service._send_file_over_tcp(mock_tcp_socket, temp_file)
        
        # Verify success
        assert success is True
        
        # Verify file was sent
        mock_tcp_socket.send.assert_called()
    
    @patch('socket.socket')
    def test_send_file_over_tcp_send_error(self, mock_socket_class, temp_file):
        """Test TCP file transfer with send error"""
        # Setup mocks
        mock_tcp_socket = Mock()
        mock_socket_class.return_value = mock_tcp_socket
        
        # Mock send error
        mock_tcp_socket.send.side_effect = socket.error("Send error")
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"test content"
            mock_open.return_value.__enter__.return_value = mock_file
            
            with patch('os.path.getsize') as mock_getsize:
                mock_getsize.return_value = 12
                
                service = FileTransferService("192.168.1.100", 706, 708)
                
                # Test file transfer with send error
                success = service._send_file_over_tcp(mock_tcp_socket, temp_file)
        
        # Verify failure
        assert success is False
    
    def test_validate_file_path_valid(self, temp_file):
        """Test file path validation with valid file"""
        service = FileTransferService("192.168.1.100", 706, 708)
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            result = service._validate_file_path(temp_file)
            assert result is True
    
    def test_validate_file_path_invalid(self):
        """Test file path validation with invalid file"""
        service = FileTransferService("192.168.1.100", 706, 708)
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = service._validate_file_path("/non/existent/file.raw")
            assert result is False
    
    def test_validate_file_path_none(self):
        """Test file path validation with None"""
        service = FileTransferService("192.168.1.100", 706, 708)
        
        result = service._validate_file_path(None)
        assert result is False
    
    def test_validate_file_path_empty(self):
        """Test file path validation with empty string"""
        service = FileTransferService("192.168.1.100", 706, 708)
        
        result = service._validate_file_path("")
        assert result is False


class TestFileTransferServiceIntegration:
    """Integration-style tests for FileTransferService"""
    
    @patch('src.services.file_transfer.MessageBuilder')
    @patch('socket.socket')
    def test_full_file_transfer_workflow(self, mock_socket_class, mock_message_builder, sample_file_transfer_message, temp_file):
        """Test complete file transfer workflow: UDP discovery -> TCP transfer"""
        # Setup UDP socket mock
        mock_udp_socket = Mock()
        
        # Setup TCP socket mock
        mock_tcp_socket = Mock()
        
        # Configure socket class to return different sockets
        socket_instances = [mock_udp_socket, mock_tcp_socket]
        mock_socket_class.side_effect = socket_instances
        
        # Mock UDP response
        response_data = b"mock_udp_response"
        mock_udp_socket.recvfrom.return_value = (response_data, ("192.168.1.101", 706))
        
        # Mock message builder and deserialization
        mock_request_message = sample_file_transfer_message
        mock_message_builder.create_file_transfer_request.return_value = mock_request_message
        
        mock_response_message = ScannerProtocolMessage(
            src_name=b"Agent1",
            dst_name=b"Scanner"
        )
        
        # Mock file operations
        test_content = b"Test file content for full workflow"
        
        with patch('src.services.file_transfer.ScannerProtocolMessage.from_bytes') as mock_from_bytes, \
             patch('builtins.open', create=True) as mock_open, \
             patch('os.path.getsize') as mock_getsize, \
             patch('os.path.exists') as mock_exists:
            
            mock_from_bytes.return_value = mock_response_message
            mock_exists.return_value = True
            mock_getsize.return_value = len(test_content)
            
            mock_file = MagicMock()
            mock_file.read.side_effect = [test_content, b""]
            mock_open.return_value.__enter__.return_value = mock_file
            
            service = FileTransferService("192.168.1.100", 706, 708)
            
            # Test full workflow
            success, response = service.send_file_transfer_request(
                target_ip="192.168.1.101",
                src_name="Scanner",
                dst_name="Agent1",
                file_path=temp_file
            )
        
        # Verify complete workflow
        assert success is True
        assert response == mock_response_message
        
        # Verify UDP operations
        mock_udp_socket.bind.assert_called_once()
        mock_udp_socket.sendto.assert_called_once()
        mock_udp_socket.recvfrom.assert_called_once()
        mock_udp_socket.close.assert_called_once()
        
        # Verify TCP operations
        mock_tcp_socket.connect.assert_called_once_with(("192.168.1.101", 708))
        mock_tcp_socket.send.assert_called()
        mock_tcp_socket.close.assert_called_once()
    
    @patch('src.services.file_transfer.MessageBuilder')
    @patch('socket.socket')
    def test_file_transfer_with_large_file(self, mock_socket_class, mock_message_builder, sample_file_transfer_message, temp_file):
        """Test file transfer with large file (chunked transfer)"""
        # Setup mocks
        mock_udp_socket = Mock()
        mock_tcp_socket = Mock()
        socket_instances = [mock_udp_socket, mock_tcp_socket]
        mock_socket_class.side_effect = socket_instances
        
        # Mock UDP response
        response_data = b"mock_udp_response"
        mock_udp_socket.recvfrom.return_value = (response_data, ("192.168.1.101", 706))
        
        # Mock message builder
        mock_request_message = sample_file_transfer_message
        mock_message_builder.create_file_transfer_request.return_value = mock_request_message
        
        mock_response_message = ScannerProtocolMessage()
        
        # Create large file content (simulate 10KB file)
        chunk_size = 1024
        large_content = b"X" * (chunk_size * 10)
        chunks = [large_content[i:i+chunk_size] for i in range(0, len(large_content), chunk_size)]
        chunks.append(b"")  # End of file
        
        with patch('src.services.file_transfer.ScannerProtocolMessage.from_bytes') as mock_from_bytes, \
             patch('builtins.open', create=True) as mock_open, \
             patch('os.path.getsize') as mock_getsize, \
             patch('os.path.exists') as mock_exists:
            
            mock_from_bytes.return_value = mock_response_message
            mock_exists.return_value = True
            mock_getsize.return_value = len(large_content)
            
            mock_file = MagicMock()
            mock_file.read.side_effect = chunks
            mock_open.return_value.__enter__.return_value = mock_file
            
            service = FileTransferService("192.168.1.100", 706, 708)
            
            # Test large file transfer
            success, response = service.send_file_transfer_request(
                target_ip="192.168.1.101",
                src_name="Scanner",
                dst_name="Agent1",
                file_path=temp_file
            )
        
        # Verify success
        assert success is True
        assert response == mock_response_message
        
        # Verify multiple send calls (one per chunk)
        assert mock_tcp_socket.send.call_count == len(chunks) - 1  # Excluding empty chunk
