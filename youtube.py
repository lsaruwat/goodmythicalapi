import requests
import json
import falcon
from gmm_api import GmmApi


class Youtube(GmmApi):

	def __init__(self):
		super().__init__()

		self.cached_ids = {}
		self.youtubeApiKey = self.config.get('youtubeApiKey')
		self.youtubeBaseUrl = "https://www.googleapis.com/youtube/v3/videos"


	def getVideoDetails(self, postData):
		try:
			#mandatory params
			videoId = postData['id']

			#optional params
			pass
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Missing required fields"})
			return (code, body)

		if self.cached_ids.get(videoId) and self.cached_ids.get(videoId) != '':
			code = falcon.HTTP_200
			body = self.schemaResponse("success", code, self.cached_ids[videoId])
			return (code, body)
		else:# go get the data from youtube
			params = {
				'part' : 'snippet',
				'id' : videoId,
				'key' : self.youtubeApiKey
			}
			try:
				response = requests.get(self.youtubeBaseUrl, params=params)
			except Exception as e:
				self.logger.error("REQUESTS ERROR: %s" % e)
				code = falcon.HTTP_503
				body = self.schemaResponse("error", code, {"details": "Youtube aint happy"})
				return (code, body)

			if response.status_code == 200:
				data = json.loads(response.text)
				items = data.get('items')
				if items and len(items):
					code = falcon.HTTP_200
					body = self.schemaResponse("success", code, {"items" : items})
					self.cached_ids[videoId] = items
				else:
					code = falcon.HTTP_404
					body = self.schemaResponse("error", code, {"items" : items})

				return (code, body)
			else:
				self.logger.error("Youtube Angry: %s-%s" % (response.status_code, response.text))
				code = response.status_code
				body = self.schemaResponse("error", code, {"details" : "Youtube aint happy"})
				return (code, body)

