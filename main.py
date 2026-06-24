import requests, base64, json, time
from secrets import token_bytes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.backends import default_backend


class Microsoft_account_xbox_register:
    def __init__(self):
        print('\033c', end = '')
        
    def generate_uuid(self):
        byte = bytearray(token_bytes(16))
        byte[6] = (byte[6] & 0x0F) | 0x40
        byte[8] = (byte[8] & 0x3F) | 0x80
        hexadecimal = byte.hex()
        generated_uuid = (
            f'{hexadecimal[0:8]}-'
            f'{hexadecimal[8:12]}-'
            f'{hexadecimal[12:16]}-'
            f'{hexadecimal[16:20]}-'
            f'{hexadecimal[20:32]}' ).lower()
        return generated_uuid
    
    def encoding_base64(self, coordinate):
        byte = int.to_bytes(coordinate, (coordinate.bit_length() + 7 ) >> 3, 'big')
        return base64.urlsafe_b64encode(byte).rstrip(b'=').decode()
    
    def generate_keys(self):
        private = ec.generate_private_key(ec.SECP256R1(), default_backend())
        public = private.public_key().public_numbers()
        return private, public
    
    def generate_payload(self):
        private, public = self.generate_keys()
        x, y = self.encoding_base64(public.x), self.encoding_base64(public.y)
        base_payload = {
            'RelyingParty': 'http://auth.xboxlive.com', 
            'TokenType': 'JWT', 
            'Properties': {'AuthMethod': 'ProofOfPossession', 
                           'Id': self.generate_uuid(),
                           'DeviceType': 'Nintendo', 
                           'Version': '14.4.0', 
                           'ProofKey': {'crv': 'P-256', 
                                        'alg': 'ES256', 
                                        'use': 'sig',
                                        'kty': 'EC', 
                                        'x': x,
                                        'y': y}}}
        generated_payload = json.dumps(base_payload, separators=(',', ':'))
        return self.generate_signature(private, generated_payload)
        
    def generate_signature(self, private, generated_payload):
        windows_timestamp = int((time.time() + 11644473600) * 1e7)
        base_signature = (
            b'\0\0\0\1\0' + 
            int.to_bytes(windows_timestamp, 8, 'big') + 
            b'\0' + 
            b'POST\0' + 
            b'/device/authenticate' + 
            b'\0' + 
            b'\0' + 
            generated_payload.encode() + 
            b'\0'  )
        signder = private.sign(base_signature, ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(signder)
        raw_signature = b'\0\0\0\1' + int.to_bytes(windows_timestamp, 8, 'big') + self.generate_i2b_dss(r) + self.generate_i2b_dss(s)
        signature = base64.b64encode(raw_signature).decode()
        return signature, generated_payload
    
    def generate_i2b_dss(self, integer):
        return int.to_bytes(integer, (integer.bit_length() + 7) >> 3, 'big')
        
    def generate_device_token(self):
        signature, generated_payload = self.generate_payload()
        locator = 'https://device.auth.xboxlive.com/device/authenticate'
        headers = {'Signature': signature, 'Content-Type': 'application/json', 'x-xbl-contract-version': '1'}
        response = requests.post(locator, headers = headers, data = generated_payload, timeout = 5)
        if response.status_code == 200:
            json_response = response.json()
            token = json_response.get('Token')
            return token
        
microsoft_account_xbox_register = Microsoft_account_xbox_register()
device_token = microsoft_account_xbox_register.generate_device_token()
print(f'Device token: {device_token}')