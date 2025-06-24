# -*- coding: utf-8 -*-
"""
WADE Certificate Handler
TLS certificate management and SSL/TLS operations.
"""

import os
import ssl
import socket
import datetime
from typing import Dict, List, Optional, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import ipaddress


class CertificateHandler:
    """
    Certificate Handler for WADE.
    Manages TLS certificates, SSL contexts, and certificate validation.
    """
    
    def __init__(self, cert_dir: str = None):
        """Initialize the certificate handler."""
        self.cert_dir = cert_dir or os.path.join(os.path.dirname(__file__), '..', 'certs')
        os.makedirs(self.cert_dir, exist_ok=True)
        
        self.ca_cert_path = os.path.join(self.cert_dir, 'ca.crt')
        self.ca_key_path = os.path.join(self.cert_dir, 'ca.key')
        self.server_cert_path = os.path.join(self.cert_dir, 'server.crt')
        self.server_key_path = os.path.join(self.cert_dir, 'server.key')
        
        # Initialize CA if not exists
        if not os.path.exists(self.ca_cert_path):
            self._create_ca_certificate()
    
    def _create_ca_certificate(self):
        """Create a Certificate Authority certificate."""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "WADE"),
            x509.NameAttribute(NameOID.COMMON_NAME, "WADE CA"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=3650)  # 10 years
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("wade.local"),
            ]),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                key_cert_sign=True,
                crl_sign=True,
                digital_signature=False,
                key_encipherment=False,
                key_agreement=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # Save certificate
        with open(self.ca_cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Save private key
        with open(self.ca_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Set secure permissions
        os.chmod(self.ca_key_path, 0o600)
        os.chmod(self.ca_cert_path, 0o644)
    
    def create_server_certificate(self, hostname: str = "localhost", 
                                 ip_addresses: List[str] = None) -> bool:
        """
        Create a server certificate signed by the CA.
        
        Args:
            hostname: Server hostname
            ip_addresses: List of IP addresses for the certificate
            
        Returns:
            True if certificate created successfully, False otherwise
        """
        try:
            # Load CA certificate and key
            with open(self.ca_cert_path, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            with open(self.ca_key_path, "rb") as f:
                ca_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            
            # Generate server private key
            server_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Create server certificate
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "WADE"),
                x509.NameAttribute(NameOID.COMMON_NAME, hostname),
            ])
            
            # Build SAN list
            san_list = [x509.DNSName(hostname)]
            if hostname != "localhost":
                san_list.append(x509.DNSName("localhost"))
            
            # Add IP addresses
            if ip_addresses:
                for ip in ip_addresses:
                    try:
                        san_list.append(x509.IPAddress(ipaddress.ip_address(ip)))
                    except ValueError:
                        continue
            else:
                san_list.append(x509.IPAddress(ipaddress.ip_address("127.0.0.1")))
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                ca_cert.subject
            ).public_key(
                server_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)  # 1 year
            ).add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            ).add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            ).add_extension(
                x509.KeyUsage(
                    key_cert_sign=False,
                    crl_sign=False,
                    digital_signature=True,
                    key_encipherment=True,
                    key_agreement=False,
                    content_commitment=False,
                    data_encipherment=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True,
            ).add_extension(
                x509.ExtendedKeyUsage([
                    x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                ]),
                critical=True,
            ).sign(ca_key, hashes.SHA256(), default_backend())
            
            # Save server certificate
            with open(self.server_cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Save server private key
            with open(self.server_key_path, "wb") as f:
                f.write(server_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Set secure permissions
            os.chmod(self.server_key_path, 0o600)
            os.chmod(self.server_cert_path, 0o644)
            
            return True
            
        except Exception as e:
            print(f"Error creating server certificate: {e}")
            return False
    
    def get_ssl_context(self, purpose: str = "server") -> ssl.SSLContext:
        """
        Get SSL context for server or client.
        
        Args:
            purpose: "server" or "client"
            
        Returns:
            SSL context
        """
        if purpose == "server":
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            
            # Ensure server certificate exists
            if not os.path.exists(self.server_cert_path):
                self.create_server_certificate()
            
            context.load_cert_chain(self.server_cert_path, self.server_key_path)
            
            # Security settings
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
            context.options |= ssl.OP_SINGLE_DH_USE
            context.options |= ssl.OP_SINGLE_ECDH_USE
            
        else:  # client
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Load CA certificate for verification
            if os.path.exists(self.ca_cert_path):
                context.load_verify_locations(self.ca_cert_path)
                context.verify_mode = ssl.CERT_REQUIRED
                context.check_hostname = True
        
        return context
    
    def validate_certificate(self, cert_path: str) -> Dict:
        """
        Validate a certificate and return information.
        
        Args:
            cert_path: Path to certificate file
            
        Returns:
            Certificate validation information
        """
        try:
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            # Extract certificate information
            subject = cert.subject
            issuer = cert.issuer
            
            # Get common name
            cn = None
            for attribute in subject:
                if attribute.oid == NameOID.COMMON_NAME:
                    cn = attribute.value
                    break
            
            # Get SAN
            san_list = []
            try:
                san_ext = cert.extensions.get_extension_for_oid(
                    x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                )
                for name in san_ext.value:
                    if isinstance(name, x509.DNSName):
                        san_list.append(f"DNS:{name.value}")
                    elif isinstance(name, x509.IPAddress):
                        san_list.append(f"IP:{name.value}")
            except x509.ExtensionNotFound:
                pass
            
            # Check validity
            now = datetime.datetime.utcnow()
            is_valid = cert.not_valid_before <= now <= cert.not_valid_after
            
            return {
                'valid': True,
                'common_name': cn,
                'subject': str(subject),
                'issuer': str(issuer),
                'not_before': cert.not_valid_before.isoformat(),
                'not_after': cert.not_valid_after.isoformat(),
                'is_valid': is_valid,
                'san': san_list,
                'serial_number': str(cert.serial_number),
                'signature_algorithm': cert.signature_algorithm_oid._name
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def check_certificate_expiry(self, cert_path: str, days_warning: int = 30) -> Dict:
        """
        Check if certificate is expiring soon.
        
        Args:
            cert_path: Path to certificate file
            days_warning: Days before expiry to warn
            
        Returns:
            Expiry check information
        """
        try:
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            now = datetime.datetime.utcnow()
            expiry_date = cert.not_valid_after
            days_until_expiry = (expiry_date - now).days
            
            return {
                'expires_on': expiry_date.isoformat(),
                'days_until_expiry': days_until_expiry,
                'is_expired': days_until_expiry < 0,
                'expires_soon': 0 <= days_until_expiry <= days_warning,
                'warning_threshold': days_warning
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def verify_certificate_chain(self, cert_path: str, ca_path: str = None) -> bool:
        """
        Verify certificate chain.
        
        Args:
            cert_path: Path to certificate to verify
            ca_path: Path to CA certificate (uses default if None)
            
        Returns:
            True if chain is valid, False otherwise
        """
        try:
            ca_path = ca_path or self.ca_cert_path
            
            # Load certificates
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            with open(ca_path, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            # Verify signature
            ca_public_key = ca_cert.public_key()
            ca_public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                cert.signature_algorithm_oid._name
            )
            
            return True
            
        except Exception:
            return False
    
    def get_certificate_fingerprint(self, cert_path: str, algorithm: str = "sha256") -> str:
        """
        Get certificate fingerprint.
        
        Args:
            cert_path: Path to certificate file
            algorithm: Hash algorithm (sha1, sha256)
            
        Returns:
            Certificate fingerprint
        """
        try:
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            if algorithm.lower() == "sha1":
                fingerprint = cert.fingerprint(hashes.SHA1())
            else:
                fingerprint = cert.fingerprint(hashes.SHA256())
            
            return ":".join([f"{b:02x}" for b in fingerprint])
            
        except Exception as e:
            return f"Error: {e}"
    
    def create_client_certificate(self, client_name: str) -> Tuple[str, str]:
        """
        Create a client certificate for mutual TLS authentication.
        
        Args:
            client_name: Name for the client certificate
            
        Returns:
            Tuple of (cert_path, key_path)
        """
        try:
            # Load CA certificate and key
            with open(self.ca_cert_path, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            with open(self.ca_key_path, "rb") as f:
                ca_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            
            # Generate client private key
            client_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Create client certificate
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "WADE"),
                x509.NameAttribute(NameOID.COMMON_NAME, client_name),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                ca_cert.subject
            ).public_key(
                client_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            ).add_extension(
                x509.KeyUsage(
                    key_cert_sign=False,
                    crl_sign=False,
                    digital_signature=True,
                    key_encipherment=True,
                    key_agreement=False,
                    content_commitment=False,
                    data_encipherment=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True,
            ).add_extension(
                x509.ExtendedKeyUsage([
                    x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                ]),
                critical=True,
            ).sign(ca_key, hashes.SHA256(), default_backend())
            
            # Save client certificate and key
            client_cert_path = os.path.join(self.cert_dir, f"{client_name}.crt")
            client_key_path = os.path.join(self.cert_dir, f"{client_name}.key")
            
            with open(client_cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(client_key_path, "wb") as f:
                f.write(client_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Set secure permissions
            os.chmod(client_key_path, 0o600)
            os.chmod(client_cert_path, 0o644)
            
            return client_cert_path, client_key_path
            
        except Exception as e:
            print(f"Error creating client certificate: {e}")
            return None, None
    
    def list_certificates(self) -> List[Dict]:
        """
        List all certificates in the certificate directory.
        
        Returns:
            List of certificate information
        """
        certificates = []
        
        for filename in os.listdir(self.cert_dir):
            if filename.endswith('.crt'):
                cert_path = os.path.join(self.cert_dir, filename)
                cert_info = self.validate_certificate(cert_path)
                cert_info['filename'] = filename
                cert_info['path'] = cert_path
                certificates.append(cert_info)
        
        return certificates