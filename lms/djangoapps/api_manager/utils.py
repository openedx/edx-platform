""" API implementation for Secure api calls. """


import socket
import struct


def address_exists_in_network(ip_address, net_n_bits):
    """
    return True if the ip address exists in the subnet address
    otherwise return False
    """
    ip_address = struct.unpack('<L', socket.inet_aton(ip_address))[0]
    net, bits = net_n_bits.split('/')
    net_address = struct.unpack('<L', socket.inet_aton(net))[0]
    net_mask = ((1L << int(bits)) - 1)
    return ip_address & net_mask == net_address & net_mask


def get_client_ip_address(request):
    """
    get the client IP Address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[-1].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    return ip_address
