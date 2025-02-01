import argparse
from werkzeug.security import generate_password_hash
from pelicandb import Pelican
import pathlib

parser = argparse.ArgumentParser(description='Bus-lite user manager')

parser.add_argument('user', type=str,
                    help='username')
parser.add_argument('password', type=str,
                    help='password')
if __name__ == "__main__":
    args = parser.parse_args()
    APP_PATH=str(pathlib.Path(__file__).parent.absolute())
    maindb = Pelican("SimpleBusDB", path =APP_PATH)
    maindb['users'].insert({"_id":args.user,"password": generate_password_hash(args.password)},upsert=True)    
    print('user added')
