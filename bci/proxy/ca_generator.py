import subprocess
import sys
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_ca_files(pem_path: str = 'bci-ca.pem', crt_path: str = 'bci-ca.crt'):
    # Generate a private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Create a new certificate builder
    builder = x509.CertificateBuilder()

    # Add a subject name to the certificate
    subject_name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, 'bci-ca'),
    ])
    builder = builder.subject_name(subject_name)

    # Set the public key for the certificate
    builder = builder.public_key(private_key.public_key())

    # Set the serial number for the certificate
    builder = builder.serial_number(x509.random_serial_number())

    # Set the validity period for the certificate
    builder = builder.not_valid_before(datetime.utcnow())
    builder = builder.not_valid_after(datetime.utcnow() + timedelta(days=365))

    # Add X509v3 extensions
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=False,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False
        ),
        critical=True
    )

    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True
    )

    builder = builder.issuer_name(subject_name)

    # Sign the certificate with the private key
    certificate = builder.sign(
        private_key=private_key,
        algorithm=hashes.SHA256(),
        backend=default_backend()
    )

    # Write the private key and certificate to a PEM file
    with open(pem_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

        f.write(certificate.public_bytes(encoding=serialization.Encoding.PEM))

    # Generate CRT file
    cmd = f"openssl x509 -outform der -in {pem_path} -out {crt_path}"
    result = subprocess.run(cmd, shell=True, check=True)
    if result.returncode != 0:
        raise Exception(f"Failed to convert PEM to CRT. Error: {result.stderr}")


if __name__ == '__main__':
    args = {
        'pem_path': sys.argv[1] if len(sys.argv) > 1 else 'bci-ca.pem',
        'crt_path': sys.argv[2] if len(sys.argv) > 2 else 'bci-ca.crt'
    }
    generate_ca_files(**args)
