import falcon
import json
import logging
import datetime
import decimal


class GmmApi(object):

    def __init__(self):
        logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                            datefmt='%Y-%m-%d:%H:%M:%S',
                            level=logging.INFO)

        self.logger = logging.getLogger(__name__)

        try:
            with open("config.json") as file:
                self.config = json.loads(file.read())
        except Exception as e:
            self.logger.error("Failed to get config: %s" % e)




    def schemaResponse(self, status, code, data=None):
        code = str(code)
        if len(code) > 3:#more than just an HTTP status code
            code = code[:3]

        responseSchema = {
            "status": status,
            "statusCode": code,
            "data": data
        }
        return json.dumps(responseSchema, default=self.json_helper)

    def schemaToDict(self, schemaResponse):
        code, data = schemaResponse
        dataDict = json.loads(data)
        return dataDict['data']

    def json_helper(self, field):
        if isinstance(field, set):
            return list(field)
        elif isinstance(field, datetime):
            return str(field)
        elif isinstance(field, decimal.Decimal):
            return str(field)

    def on_get(self, req, resp, method, detail=None):
            self.on_post(req, resp, method, detail)

    def on_post(self, req, resp, method, detail=None):
        #
        # GET POST DATA
        #
        try:
            route = "method %s" % method
            self.logger.info(route)
            postData = req.params
            if detail:
                postData['detail'] = detail

            #no form data sent, default to json
            if not postData and req.content_length and req.content_type == 'application/json':
                try:
                    postData = json.loads(req.stream.read())
                except Exception as e:
                    resp.status = falcon.HTTP_400
                    resp.text = self.schemaResponse("error", falcon.HTTP_400, {"details": "Invalid JSON"})
                    return

            #logging traffic
            self.logger.info(postData)

        except Exception as e:
            self.logger.error("There was a problem getting data: %s" % str(e))
            resp.status = falcon.HTTP_400
            resp.text = self.schemaResponse("error", falcon.HTTP_400, {"details" : "Routing error"})
            return

        resp.set_header('Access-Control-Allow-Origin', '*')  # so the browser can consume it

        #
        # CALL THE FUNCTION NAME OF THE ROUTE
        # Add routes you support to child classes
        #
        try:
            methodCall = eval("self.%s" % method)
            status, body = methodCall(postData)
        except TypeError as naw:
            self.logger.error(naw)
            resp.status = falcon.HTTP_400
            resp.text = json.dumps({
                "status": "failed",
                "response": "Route not supported"
            })
            return
        resp.status = status
        resp.text = body



    def debug(self, postData):

        code = falcon.HTTP_200
        body = self.schemaResponse("success", code, {"details" : postData})
        return (code, body)

    @staticmethod
    def isNoneOrEmpty(thing):
        if thing and thing !='':
            return False
        return True

    @staticmethod
    def isSomething(thing):
        if thing and thing !='':
            return True
        return False

    @staticmethod
    def getMaxPages(listSize, limit):
        pages = listSize // limit
        if listSize % limit != 0:
            pages+=1
        return pages

    @staticmethod
    def listToCsvParams(list):
        csv = ''
        for i in list:
            csv += (i + ',')
        return csv[:-1]

    @staticmethod
    def searchAString(string, searchStr):
        string = string.lower()
        searchStr = searchStr.lower()
        words = searchStr.split(' ')
        if searchStr not in string:
            for word in words:
                if word not in string:
                    return False
        return True

    @staticmethod
    def searchASet(_set, searchStr):
        words = searchStr.split(' ')
        for word in words:
            if word not in _set:
                return False
        return True

    @staticmethod
    def trimGarbage(list):
        temp = []
        for i in list:
            if i is not None:
                temp.append(i)
        return temp

