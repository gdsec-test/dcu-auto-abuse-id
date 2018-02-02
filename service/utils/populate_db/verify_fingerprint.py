import os
import yaml
import logging.config
import pymongo.errors

from flask import Flask
from bson.objectid import ObjectId
from settings import config_by_name


# Web page flask app allowing the user to review the images from the fingerprint hash db collection
#  in order to make a visual validation on if the image is indeed malicious or not.  The user can also
#  choose `inconclusive` if they are unsure on making a definitive call.  That is done via the "/" endpoint.
# A user can review the images validated via the "/review" endpoint.  While there, they can cycle through
#  the images, and assign different visual validation status (yes/no/inconclusive)
# 3 environment variables need to be set: sysenv, user, DB_PASS


env = os.getenv('sysenv', 'dev')
user = os.getenv('user', 'unknownUser')
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

app = Flask(__name__)
TABLE_ROW = '<tr><td>{type}</td><td><a href="https://phishstory.int.godaddy.com/getimage/{image}">{target}</a></td>' \
            '<td><a href="/{page}/yes/{image}">YES</a>&nbsp;&nbsp;&nbsp;</td><td>' \
            '<a href="/{page}/no/{image}">NO</a>&nbsp;&nbsp;&nbsp;</td><td>' \
            '<a href="/{page}/inconclusive/{image}">INCONCLUSIVE</a></td></tr><br>' \
            '<iframe height=500 width=1200 src="https://phishstory.int.godaddy.com/getimage/{image}"></iframe>'

# DCU DEVELOPMENT db (read/write)
local = pymongo.MongoClient(config.DB_URL, 27017)
local_db = local[config.DB]
local_collection = local_db[config.COLLECTION]

# Way to check the collection for a specific id via RoboMongo
# db.getCollection('fingerprints').find({'_id': ObjectId('5a6f98594fe1fb35832ce3c4')})

records_to_review = None


def get_header(h3=None):
    '''
    Just a hack to avoid having to create an HTML template
    :param h3:
    :return: html string
    '''
    header = ''
    if h3:
        header = '<h3>{}</h3>'.format(h3)
    return '<html><body>{}<table>'.format(header)


def get_footer():
    '''
    Just a hack to avoid having to create an HTML template
    :return: html string
    '''
    return '</table></body></html>'


# # # VERIFY SPECIFIC FUNCTIONS # # #


def get_records():
    '''
    Returns a cursor object of all images in fingerprints collection that has no `valid` field
    :return: Pymongo Cursor Object or False
    '''
    results = local_collection.find({'valid': {'$exists': False}}).limit(1)
    if results:
        return results
    return False


@app.route("/favicon.ico")
def favicon():
    '''
    For the annoying calls to: "GET /favicon.ico HTTP/1.1"
    :return empty string:
    '''
    return ''


@app.route("/")
def get_one_record(action_taken=None):
    '''
    Endpoint for visually validating new images added to collection
    :param action_taken:
    :return: html string
    '''
    try:
        doc = get_records().next()
        if doc:
            html = get_header(action_taken)
            html += str(TABLE_ROW.format(target=doc.get('target'),
                                         type=doc.get('type'),
                                         image=doc.get('imageId'),
                                         page='verify'))
            html += get_footer()
            return html
    except StopIteration:
        global records_to_review
        records_to_review = None
        return review('No new images to verify')


@app.route("/<string:action_taken>")
def get_next_record(action_taken):
    '''
    Endpoint that is called when a visual validation has been made on a new image, used to populate the
     `action_taken` message at the top of the page
    :param action_taken:
    :return:
    '''
    return get_one_record(action_taken)


@app.route("/verify/<string:yes_no_maybeso>/<string:image_id>/")
def verify(yes_no_maybeso, image_id):
    '''
    Endpoint that updates new fingerprint record with a visual validation status (yes/no/inconclusive)
    :param yes_no_maybeso:
    :param image_id:
    :return: html string
    '''
    action_taken = 'You chose {} for imageId {}'.format(yes_no_maybeso, image_id)
    local_collection.update({'imageId': ObjectId(image_id)}, {'$set': {'valid': yes_no_maybeso, 'validator': user}})
    return get_next_record(action_taken)


# # # REVIEW SPECIFIC FUNCTIONS # # #


def get_specific_records(yes_no_maybeso):
    '''
    Returns a cursor object of all images in fingerprints collection that has has a specific value for `valid`
    :param yes_no_maybeso:
    :return: Pymongo Cursor Object
    '''
    return local_collection.find({'valid': yes_no_maybeso})


def get_records_to_review(yes_no_maybeso):
    '''
    Sets the global `records_to_review` variable if it is not already set
    :param yes_no_maybeso:
    :return:
    '''
    global records_to_review
    if not records_to_review:
        records_to_review = get_specific_records(yes_no_maybeso)
    return records_to_review


@app.route("/review/<string:yes_no_maybeso>/<string:image_id>/")
def review_change_verify(yes_no_maybeso, image_id):
    '''
    Endpoint that updates existing fingerprint record with a visual validation status (yes/no/inconclusive)
    :param yes_no_maybeso:
    :param image_id:
    :return: html string
    '''
    action_taken = 'You chose {} for {}'.format(yes_no_maybeso, image_id)
    local_collection.update({'imageId': ObjectId(image_id)}, {'$set': {'valid': yes_no_maybeso, 'validator': user}})
    return review_records(yes_no_maybeso, action_taken)


@app.route("/review")
def review(message=None):
    '''
    Endpoint that presents user with links in order to review existing record's visual validation
    status (yes/no/inconclusive)
    :param message:
    :return:
    '''
    global records_to_review
    records_to_review = None
    html = get_header(message)
    html += '<tr><td><a href="/review/yes">YES</a>&nbsp;&nbsp;&nbsp;</td><td>' \
            '<a href="/review/no">NO</a>&nbsp;&nbsp;&nbsp;</td><td>' \
            '<a href="/review/inconclusive">INCONCLUSIVE</a></td></tr>'
    html += get_footer()
    return html


@app.route("/review/<string:yes_no_maybeso>")
def review_records(yes_no_maybeso, action_taken=None):
    '''
    Endpoint that presents user with a specific fingerprint record, allowing them to move to the next
    record, or allowing them to change the visual validation status (yes/no/inconclusive)
    :param yes_no_maybeso:
    :param action_taken:
    :return:
    '''
    try:
        doc = get_records_to_review(yes_no_maybeso).next()
        if doc:
            html = get_header(action_taken)
            html += str(TABLE_ROW.format(target=doc.get('target'),
                                         type=doc.get('type'),
                                         image=doc.get('imageId'),
                                         page='review'))
            html += '<td>&nbsp;&nbsp;&nbsp;<a href="/review/{}">NEXT</a></td>'.format(yes_no_maybeso)
            html += '<td>&nbsp;&nbsp;&nbsp;<a href="/review">RESET WEBPAGE</a></td>'
            html += get_footer()
            return html
    except StopIteration:
        global records_to_review
        records_to_review = None
        return review()


if __name__ == '__main__':
    app.run()
