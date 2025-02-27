import os
import certifi
import ssl
import shutil

# Get the path to the certifi certificate file
certifi_path = certifi.where()

# Create a new directory for the SSL certificates
ssl_dir = os.path.join(os.path.dirname(certifi_path), 'ssl')
if not os.path.exists(ssl_dir):
    os.makedirs(ssl_dir)

# Copy the certifi certificate file to the new directory
shutil.copy(certifi_path, os.path.join(ssl_dir, 'cacert.pem'))

# Set the environment variable to point to the new certificate file
os.environ['SSL_CERT_FILE'] = os.path.join(ssl_dir, 'cacert.pem')

# Verify the SSL certificate
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(os.environ['SSL_CERT_FILE'])

print("SSL certificates installed successfully.")
