import os
import sys

EXT_DOC = [".pdf"]
EXT_IMG = [".png", ".jpg"]

SHOW_RESULT = True
LOG_DIR = "./logs/"

# config the key for the google cloud apis -----------------------------------------------------------------------------
API_KEY = "API key"

ENDPOINT_URL = 'https://vision.googleapis.com/v1/images:annotate'

KEY_JSON = 'service_account_key.json'
KEY_DIR = './keys'
CREDENTIAL_PATH = os.path.join(KEY_DIR, KEY_JSON)
if not os.path.isfile(CREDENTIAL_PATH):
    sys.stderr.write('No exist the correct key file.{} \n'.format(CREDENTIAL_PATH))
    sys.exit(0)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIAL_PATH

# params for calibrating orientation of each page of document ----------------------------------------------------------
ORIENTATION_NORMAL = 3
ORIENTATION_90_DEGREE = 2
ORIENTATION_180_DEGREE = 1
ORIENTATION_270_DEGREE = 0

ROTATE_90_CLOCKWISE = 0
ROTATE_180 = 1
ROTATE_90_COUNTERCLOCKWISE = 2

LABEL_ORIS = ["ORIENTATION_270_DEG", "ORIENTATION_180_DEG", "ORIENTATION_90_DEG", "ORIENTATION_NORMAL"]

# config for the size of the request of api ----------------------------------------------------------------------------
MAXIMUM_SIZE = 8 * 1024 * 1024  # google could api limitation 8 MB
