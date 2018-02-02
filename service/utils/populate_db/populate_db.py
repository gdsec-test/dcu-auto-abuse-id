from PIL import Image
from settings import config_by_name
import pymongo.errors
import gridfs
import bson
import imagehash
import io
import os
import sys
import yaml
import logging.config


# Utility to search production mongodb INCIDENTS collection for specific targets, as defined in top_phish
#  who match a specific abuse_type and were closed with closed_reasons, and return the screenshot_id
#  which will be used to extract a perceptual hash from, so the data can be archived off in a hash
#  truth model database collection that will be used to compare new abuse report screenshot hashes to
# 7 environment variables need to be set: sysenv, DB_PASS, ABUSE_DB_PASS, ABUSE_DB_DB, ABUSE_DB_HOST,
#  ABUSE_DB_COLLECTION, ABUSE_DB_USER

# Way to search production db for specific targets via RoboMongo
# db.incidents.find({
#         "phishstory_status": 'CLOSED',
#         'type': 'PHISHING',
#         'target': {$regex: /Wells Fargo/ig},
#         'close_reason': {$in: ['resolved', 'suspended', 'intentionally_malicious']}
#     }).sort({'closed': -1})


env = os.getenv('sysenv', 'dev')
config = config_by_name[env]()

# Walk the tree up to find where the logging yaml file is
path = None
cur_dir = os.path.dirname(os.path.abspath(__file__))
while path is None:
    file_path = cur_dir + '/logging.yml'
    if os.path.isfile(file_path):
        path = file_path
        break
    cur_dir = os.path.dirname(cur_dir)

# Set up the logging handle
value = os.getenv('LOG_CFG', None)
if value:
    path = value
if os.path.exists(path):
    with open(path, 'rt') as f:
        lconfig = yaml.safe_load(f.read())
    logging.config.dictConfig(lconfig)
else:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    sys.exit("You'll need to uncomment this line if you want to run.  DO NOT OVERWRITE EXISTING DB RECORDS!!!")

    # Top 5 phishing targets from the past 2 years, along with most popular user-provided names:
    top_phish = {
        'netflix': ['netflix',
                    'Netflix'],
        'apple': ['Apple ID',
                  'Apple iTunes Connect',
                  'Apple Online Store',
                  'applecomputer',
                  'Apple Inc',
                  'Apple, Inc.'],
        'amazon': ['amazon',
                   'Amazon'],
        'hmrevenuecustoms': ['hmrevenuecustoms',
                             'HMRC'],
        'paypal': ['paypal',
                   'This is targeting a PayPal user by trying to phish them.',
                   'PayPal',
                   'Paypal']
    }
    abuse_type = 'PHISHING'
    closed_reasons = ['resolved', 'suspended', 'intentionally_malicious']

    # DCU PRODUCTION db (read)
    conn = pymongo.MongoClient(
        'mongodb://{}:{}@{}/{}'.format(os.getenv('ABUSE_DB_USER'),
                                       os.getenv('ABUSE_DB_PASS'),
                                       os.getenv('ABUSE_DB_HOST'),
                                       os.getenv('ABUSE_DB_DB')), 27017)
    db = conn[os.getenv('ABUSE_DB_DB')]
    collection = db[os.getenv('ABUSE_DB_COLLECTION')]
    fs = gridfs.GridFS(db)

    # DCU DEVELOPMENT db (write)
    local = pymongo.MongoClient(config.DB_URL, 27017)
    local_db = local[config.DB]
    local_collection = local_db[config.COLLECTION]

    for top_target, user_provided_targets in top_phish.iteritems():

        results = db.incidents.find({
            "phishstory_status": 'CLOSED',
            'type': abuse_type,
            'target': {'$in': user_provided_targets},
            'close_reason': {'$in': closed_reasons}
        }).sort('closed', pymongo.DESCENDING)

        if results:
            for doc in results:
                iid = doc.get('screenshot_id', None)
                if iid:
                    with fs.get(bson.objectid.ObjectId(iid)) as fs_read:
                        try:
                            hash_phish = imagehash.phash(
                                Image.open(io.BytesIO(fs_read.read())))
                            chunk1 = str(hash_phish)[0:4]
                            chunk2 = str(hash_phish)[4:8]
                            chunk3 = str(hash_phish)[8:12]
                            chunk4 = str(hash_phish)[12:16]
                            local_collection.insert_one({
                                'chunk1': chunk1,
                                'chunk2': chunk2,
                                'chunk3': chunk3,
                                'chunk4': chunk4,
                                'target': top_target,
                                'type': abuse_type,
                                'image': doc.get('screenshot_id')
                            })
                        except pymongo.errors.DuplicateKeyError as e:
                            pass
                        except IOError as e:
                            logger.error(e.message)
                            pass
                        except Exception as e:
                            logger.error(e)
                            pass
