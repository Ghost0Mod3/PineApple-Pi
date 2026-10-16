import argparse
from backend.database import init_db
p=argparse.ArgumentParser();p.add_argument('command',choices=['init-db']);p.parse_args();init_db();print('Database initialized')
