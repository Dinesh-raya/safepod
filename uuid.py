"""Custom UUID module to work around corrupted system uuid module"""
import secrets
import hashlib
from datetime import datetime
import time

class UUID:
    """Simple UUID implementation"""
    def __init__(self, hex=None, bytes=None, int=None):
        if hex:
            self.hex = hex.lower()
        elif bytes:
            self.hex = bytes.hex()
        elif int is not None:
            self.hex = format(int, '032x')
        else:
            # Generate random UUID
            self.hex = secrets.token_hex(16)
    
    @property
    def bytes(self):
        return bytes.fromhex(self.hex)
    
    @property
    def int(self):
        return int(self.hex, 16)
    
    def __str__(self):
        # Format as standard UUID: 8-4-4-4-12
        h = self.hex
        return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"
    
    def __repr__(self):
        return f"UUID('{self}')"
    
    def __eq__(self, other):
        if isinstance(other, UUID):
            return self.hex == other.hex
        return False

def uuid4():
    """Generate a random UUID (version 4)"""
    return UUID()

def uuid5(namespace, name):
    """Generate a UUID from a namespace and name (version 5)"""
    # Convert namespace to bytes if it's a UUID object
    if isinstance(namespace, UUID):
        namespace_bytes = namespace.bytes
    elif isinstance(namespace, str):
        # Parse UUID string
        namespace_bytes = bytes.fromhex(namespace.replace('-', ''))
    else:
        namespace_bytes = namespace
    
    # SHA-1 hash of namespace + name
    hash_obj = hashlib.sha1(namespace_bytes + name.encode('utf-8'))
    hash_bytes = hash_obj.digest()
    
    # Set version bits (5) and variant bits
    hash_hex = hash_bytes.hex()
    # Version 5: set bits 4-7 of time_hi_and_version to 0101
    time_hi = int(hash_hex[12:16], 16)
    time_hi = (time_hi & 0x0FFF) | 0x5000
    hash_hex = hash_hex[:12] + format(time_hi, '04x') + hash_hex[16:]
    
    # Variant: set bits 6-7 of clock_seq_hi_and_reserved to 10
    clock_seq = int(hash_hex[16:18], 16)
    clock_seq = (clock_seq & 0x3F) | 0x80
    hash_hex = hash_hex[:16] + format(clock_seq, '02x') + hash_hex[18:]
    
    return UUID(hex=hash_hex[:32])

# Common namespaces
NAMESPACE_DNS = UUID(hex='6ba7b8109dad11d180b400c04fd430c8')
NAMESPACE_URL = UUID(hex='6ba7b8119dad11d180b400c04fd430c8')
NAMESPACE_OID = UUID(hex='6ba7b8129dad11d180b400c04fd430c8')
NAMESPACE_X500 = UUID(hex='6ba7b8149dad11d180b400c04fd430c8')