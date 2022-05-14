import falcon
import json
import logging
import datetime
import decimal


class GmmApi(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

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

        # for key in data:
        #     responseSchema[key] = data[key]
        self.logger.info(responseSchema)
        return json.dumps(responseSchema, default=self.json_helper)
        #return json.dumps(responseSchema)

    def json_helper(self, field):
        if(isinstance(field, datetime)):
            return str(field)
        elif(isinstance(field, decimal.Decimal)):
            #self.logger.info("Decimal:%s" % field)
            #newnew = (str(x) for x in [field])
            #return newnew
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
            logData = postData.copy()
            #don't log password fields as they are not hashed
            try:
                del logData["password"]
            except KeyError as k:
                #long hair don't care
                pass

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
        except AttributeError as naw:
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