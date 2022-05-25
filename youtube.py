import requests
import json
import falcon
import urllib
from gmm_api import GmmApi
from gmm_data import GmmData


class Youtube(GmmApi):

	def __init__(self):
		super().__init__()

		self.cached_ids = {}
		self.youtubeApiKey = self.config.get('youtubeApiKey')
		self.youtubeBaseUrl = "https://www.googleapis.com/youtube/v3"
		self.idLimit = 50
		# self.seasonIds = ['PL5D1D48359CF4BDE0', 'PL96EFA802DBFF1938', 'PLJ49NV73ttrunKAJ3MkV_gtADTrArl93Q', 'PLJ49NV73ttrvh20nQGPgPaCHqLgpJN7YZ', 'PLJ49NV73ttrtoqgGHymxdrJHdjJ9BubUi', 'PLJ49NV73ttrvoHn0pn-Bv-rOcaye2gF1G', 'PLJ49NV73ttrtQP_nY7NTldYfEsYmlCV2L', 'PLJ49NV73ttrs52WlwbXLctNtOMxlbZ3VO', 'PLJ49NV73ttrvdeqDBaqtbdE18ClnJ8tCL', 'PLJ49NV73ttruZ_iJ77VfhiuRB0NP7xgYQ', 'PLJ49NV73ttrv9JMidbDMUoENpoNWfWz-R', 'PLJ49NV73ttrvRH9MQ3ef6_Gw7T23RdOea', 'PLJ49NV73ttrusg4BUW4T7vszHPhk_rHbd', 'PLJ49NV73ttrtsw6FZ-J6h-5N3WhPM0uJX', 'PLJ49NV73ttrsQNXWud_2LQ3G-4shrz2hH', 'PLJ49NV73ttrvCQhgIj1Ovt3g0PBlO18s2', 'PLJ49NV73ttrvKwXQjGntFUjtYdhLcXaiu', 'PLJ49NV73ttru4iSmiDijuaoegvuQZmT6l','PLJ49NV73ttrvOBbw-tskTJaBf4dR9sVQH', 'PLJ49NV73ttruUDlp4LgOiIK_Heox_l5IC', 'PLJ49NV73ttrup0H8B6jSpnvuBfPQSMaL2']
		self.giantDataSet = GmmData()
		self.seasonArr = self.giantDataSet.seasonArray
		self.buildCacheFromFile()
		self.logger.info("CACHE BUILT WITH %s ITEMS" % len(self.cached_ids))

	def buildCacheFromFile(self):
		with open('data/savedData.json') as file:
			fileData = file.read()
		self.cached_ids = json.loads(fileData)

	def cacheToResponseify(self, cacheResponse):
		responsified = [{'items' : [], 'pageInfo' : {'totalResults' : len(cacheResponse)}}]
		for item in cacheResponse:
			item['cached'] = True
			responsified[0]['items'].append(item)
		return responsified

	def combineResults(self, results):
		items = []
		itemCount = 0
		for result in results:
			items.append(result.get('items'))
			itemCount+= int(result.get('pageInfo').get('totalResults'))
		combined = {
			'items' : items,
			'totalResults' : itemCount
		}
		return combined


	def getVideoDetailsById(self, postData):
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

		if self.isSomething(self.cached_ids.get(videoId)):
			code = falcon.HTTP_200
			body = self.schemaResponse("success", code, {"items" : self.cached_ids[videoId]})
			return (code, body)
		else:# go get the data from youtube
			params = {
				'part' : 'snippet',
				'id' : videoId,
				'key' : self.youtubeApiKey
			}
			try:
				url = self.youtubeBaseUrl + '/videos'
				response = requests.get(url, params=params)
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
					body = self.schemaResponse("success", code, data)
					self.cached_ids[videoId] = data
				else:
					code = falcon.HTTP_404
					body = self.schemaResponse("error", code, data)

				return (code, body)
			else:
				self.logger.error("Youtube Angry: %s-%s" % (response.status_code, response.text))
				code = response.status_code
				body = self.schemaResponse("error", code, {"details" : "Youtube aint happy"})
				return (code, body)

	# def getVideoDetailsBySearch(self, postData):
	# 	try:
	# 		#mandatory params
	# 		searchStr = postData['search']
	#
	# 		#optional params
	# 		pass
	# 	except Exception as e:
	# 		self.logger.error(e)
	# 		code = falcon.HTTP_406
	# 		body = self.schemaResponse("error", code, {"details": "Missing required fields"})
	# 		return (code, body)
	#
	# 	if self.cached_ids.get(videoId) and self.cached_ids.get(videoId) != '':
	# 		code = falcon.HTTP_200
	# 		body = self.schemaResponse("success", code, {"items" : self.cached_ids[videoId]})
	# 		return (code, body)
	# 	else:# go get the data from youtube
	# 		params = {
	# 			'part' : 'snippet',
	# 			'id' : videoId,
	# 			'key' : self.youtubeApiKey
	# 		}
	# 		try:
	# 			url = self.youtubeBaseUrl + '/videos'
	# 			response = requests.get(url, params=params)
	# 		except Exception as e:
	# 			self.logger.error("REQUESTS ERROR: %s" % e)
	# 			code = falcon.HTTP_503
	# 			body = self.schemaResponse("error", code, {"details": "Youtube aint happy"})
	# 			return (code, body)
	#
	# 		if response.status_code == 200:
	# 			data = json.loads(response.text)
	# 			items = data.get('items')
	# 			if items and len(items):
	# 				code = falcon.HTTP_200
	# 				body = self.schemaResponse("success", code, data)
	# 				self.cached_ids[videoId] = data
	# 			else:
	# 				code = falcon.HTTP_404
	# 				body = self.schemaResponse("error", code, data)
	#
	# 			return (code, body)
	# 		else:
	# 			self.logger.error("Youtube Angry: %s-%s" % (response.status_code, response.text))
	# 			code = response.status_code
	# 			body = self.schemaResponse("error", code, {"details" : "Youtube aint happy"})
	# 			return (code, body)

	def getVideoDetailsBySeason(self, postData):
		'https://youtube.googleapis.com/youtube/v3/playlistItems?id=efasdfasdf&'
		try:
			#mandatory params
			season = postData['season']

			#optional params
			page = postData.get('page')
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Missing required fields"})
			return (code, body)

		try:
			season = int(season)
			seasonIds = self.seasonArr[season]
			self.logger.info("GETTING SEASON %s episodes %s" % (season, len(seasonIds)))
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Invalid Season %s"%season})
			return (code, body)

		responses = []
		temp = []
		# check cache first
		for id in seasonIds:
			if self.isSomething(self.cached_ids.get(id)):
					responses.append(self.cached_ids[id])
			else:
				temp.append(id)

		responses = self.cacheToResponseify(responses)

		if len(responses) == len(seasonIds):
			combined = self.combineResults(responses)
			code = falcon.HTTP_200
			body = self.schemaResponse("success", code, combined)
			return (code, body)
		if len(temp):
			seasonIds = temp

		pages = self.getMaxPages(len(seasonIds), self.idLimit)
		for i in range(pages):
			pageIds = seasonIds[:self.idLimit]# get a slice of ids
			seasonIds = seasonIds[self.idLimit:]# now cut those from the list
			params = {
				'part' : 'snippet,contentDetails,statistics',
				'id' : self.listToCsvParams(pageIds),
				'key' : self.youtubeApiKey
			}
			try:
				url = self.youtubeBaseUrl + '/videos'
				response = requests.get(url, params=params)
			except Exception as e:
				self.logger.error("REQUESTS ERROR: %s" % e)
				code = falcon.HTTP_503
				body = self.schemaResponse("error", code, {"details": "Youtube aint happy"})
				return (code, body)

			if response.status_code == 200:
				data = json.loads(response.text)
				items = data.get('items')
				if items and len(items):
					for item in items:
						self.cached_ids[item['id']] = item
					responses.append(data)
				else:
					self.logger.error("404: %s" % pageIds)
					code = falcon.HTTP_404
					body = self.schemaResponse("error", code, data)
					return (code, body)
			else:
				self.logger.error("Youtube Angry: %s-%s" % (response.status_code, response.text))
				code = response.status_code
				body = self.schemaResponse("error", code, {"details" : "Youtube aint happy"})
				return (code, body)

		combined = self.combineResults(responses)
		code = falcon.HTTP_200
		body = self.schemaResponse("success", code, combined)
		return (code, body)

	def saveVideoDetailsBySeason(self, postData):
		'https://youtube.googleapis.com/youtube/v3/playlistItems?id=efasdfasdf&'
		try:
			#mandatory params
			season = postData['season']

			#optional params
			page = postData.get('page')
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Missing required fields"})
			return (code, body)

		try:
			season = int(season)
			seasonIds = self.seasonArr[season]
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Invalid Season %s"%season})
			return (code, body)

		pages = self.getMaxPages(len(seasonIds), self.idLimit)
		responses =[]
		videoDict = {}
		for i in range(pages):
			pageIds = seasonIds[:self.idLimit]# get a slice of ids
			seasonIds = seasonIds[self.idLimit:]# now cut those from the list
			#check cache first
			if self.cached_ids.get(hash(str(pageIds))) and self.cached_ids.get(hash(str(pageIds))) != '':
				responses.append(self.cached_ids[hash(str(pageIds))])
				continue
			params = {
				'part' : 'snippet,contentDetails,statistics',
				'id' : self.listToCsvParams(pageIds),
				'key' : self.youtubeApiKey
			}
			try:
				url = self.youtubeBaseUrl + '/videos'
				response = requests.get(url, params=params)
			except Exception as e:
				self.logger.error("REQUESTS ERROR: %s" % e)
				code = falcon.HTTP_503
				body = self.schemaResponse("error", code, {"details": "Youtube aint happy"})
				return (code, body)

			if response.status_code == 200:
				data = json.loads(response.text)
				items = data.get('items')
				if items and len(items):
					for item in items:
						videoDict[item['id']] = item
						self.cached_ids[item['id']] = item
				else:
					self.logger.error("404: %s" % pageIds)
					code = falcon.HTTP_404
					body = self.schemaResponse("error", code, data)
					return (code, body)
			else:
				self.logger.error("Youtube Angry: %s-%s" % (response.status_code, response.text))
				code = response.status_code
				body = self.schemaResponse("error", code, {"details" : "Youtube aint happy"})
				return (code, body)

		try:
			with open("data/savedData.json", 'r') as file:
				savedData = file.read()
				savedData = json.loads(savedData)

			for key, value in videoDict.items():
				if self.isNoneOrEmpty(savedData.get(key)):
					savedData[key] = value

			with open('data/savedData.json', 'w') as file:
				file.write(json.dumps(savedData))
		except Exception as e:
			self.logger.error("FILE IO PROBLEM: %s" % e)
			code = falcon.HTTP_503
			body = self.schemaResponse("error", code, {"details": "File io error %s" % e})
			return (code, body)
		code = falcon.HTTP_200
		body = self.schemaResponse("success", code, {"details" : "Saved Season %s to disk" % season})
		return (code, body)

	def getVideoDetailsBySeasonAndEpisode(self, postData):
		try:
			#mandatory params
			episode = postData['episode']
			season = postData['season']

			#optional params
			pass
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Missing required fields"})
			return (code, body)

		try:
			season = int(season)
			episode = int(episode)
			videoId = self.seasonArr[season][episode]
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Invalid Season %s"%season})
			return (code, body)

		if self.cached_ids.get(videoId) and self.cached_ids.get(videoId) != '':
			code = falcon.HTTP_200
			body = self.schemaResponse("success", code, {"items" : self.cached_ids[videoId]})
			return (code, body)
		else:# go get the data from youtube
			params = {
				'part' : 'snippet',
				'id' : videoId,
				'key' : self.youtubeApiKey
			}
			try:
				url = self.youtubeBaseUrl + '/videos'
				response = requests.get(url, params=params)
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

