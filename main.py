import falcon
import os

from gmm_api import GmmApi
from youtube import Youtube
#from test import TestService

env = os.environ.get('ENV')
if env and env == 'prod':
    prod = True
else:
    prod = False

api = application = falcon.App()
api.req_options.auto_parse_form_urlencoded = True
api.req_options.strip_url_path_trailing_slash = True

core = GmmApi()
youtube = Youtube()
#test = TestService(prod=prod)

#
api.add_route("/youtube/{method}", youtube)
#api.add_route("/test/{method}", test)
api.add_route("/{method}", core)