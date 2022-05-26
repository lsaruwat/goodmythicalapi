import requests
import json
import falcon
from time import time
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
		self.seasonArr = self.giantDataSet.gmmArray # hard coded values from my old scraping attempts
		self.playlistArr = self.giantDataSet.playListLinks
		self.buildCacheFromFile()

		allIdsFromFile = self.readAllEpisodeIds()
		if len(allIdsFromFile):
			self.logger.info("%s SEASONS RESTORED FROM FILE" % len(allIdsFromFile))
			self.seasonArr = allIdsFromFile

	def getAllEpisodeIds(self, postData):
		# optional params
		writeToFile = postData.get('writeToFile')
		live = postData.get('live')


		if live:
			self.seasonArr = []
			for i in range(len(self.playlistArr)):
				seasonIds = self.schemaToDict(self.getPlaylistBySeason({'season' : i+1}))
				idArr = []
				for id in seasonIds:
					idArr.append(id)
				self.seasonArr.append(idArr)

		if writeToFile:
			with open('data/allIds.json', 'w') as file:
				file.write(json.dumps(self.seasonArr))

		code = falcon.HTTP_200
		body = self.schemaResponse("success", code, self.seasonArr)
		return (code, body)

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
			body = self.schemaResponse("success", code, self.cached_ids[videoId])
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
					body = self.schemaResponse("success", code, items)
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
			body = self.schemaResponse("error", code, {"details": "Missing required fields: %s" % e})
			return (code, body)

		try:
			season = int(season)
			seasonIds = self.seasonArr[season-1]
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

		if len(responses) == len(seasonIds):
			#responses = self.cacheToResponseify(responses)
			#combined = self.combineResults(responses)
			code = falcon.HTTP_200
			body = self.schemaResponse("success", code, responses)
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

	def searchRealTimeVideoDescription(self, postData):
		try:
			# mandatory params
			searchStr = postData['searchStr']

			# optional params
			pass
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Missing required fields: %s" % e})
			return (code, body)

		self.logger.info("Searching video descriptions for '%s'" % searchStr)

		responses = []
		temp = []
		allIds = []
		seasonArr = self.seasonArr[1:]
		# check cache first
		for season in seasonArr:
			for id in season:
				allIds.append(id)
				if self.isSomething(self.cached_ids.get(id)):
					string = self.cached_ids[id]['searchWords']
					if self.searchAString(string, searchStr):
						responses.append(self.cached_ids[id])
				else:
					temp.append(id)
		start = time()
		end = time()
		total = end - start
		self.logger.info("responseify took %ss to complete" % total)

		if len(responses) == len(allIds):
			responses = self.cacheToResponseify(responses)
			combined = self.combineResults(responses)
			code = falcon.HTTP_200
			body = self.schemaResponse("success", code, combined)
			return (code, body)
		if len(temp):
			allIds = temp

		pages = self.getMaxPages(len(allIds), self.idLimit)
		for i in range(pages):
			pageIds = allIds[:self.idLimit]  # get a slice of ids
			allIds = allIds[self.idLimit:]  # now cut those from the list
			params = {
				'part': 'snippet,contentDetails,statistics',
				'id': self.listToCsvParams(pageIds),
				'key': self.youtubeApiKey
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
						string = self.cached_ids[id]['snippet']['description']
						if self.searchAString(string, searchStr):
							responses.append(data)
				else:
					self.logger.error("404: %s" % pageIds)
					code = falcon.HTTP_404
					body = self.schemaResponse("error", code, data)
					return (code, body)
			else:
				self.logger.error("Youtube Angry: %s-%s" % (response.status_code, response.text))
				code = response.status_code
				body = self.schemaResponse("error", code, {"details": "Youtube aint happy"})
				return (code, body)

		if len(responses) == 0:
			code = falcon.HTTP_404
			body = self.schemaResponse("error", code, {"details": "No videos matched"})
			return (code, body)

		combined = self.combineResults(responses)
		code = falcon.HTTP_200
		body = self.schemaResponse("success", code, combined)
		return (code, body)

	def searchVideoDescription(self, postData):
		try:
			# mandatory params
			searchStr = postData['searchStr']

			# optional params
			pass
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Missing required fields"})
			return (code, body)

		self.logger.info("Searching video descriptions for '%s'" % searchStr)

		responses = []
		# check cache first
		for season in self.seasonArr:
			for id in season:
				if self.isSomething(self.cached_ids.get(id)):
					string = self.cached_ids[id]['snippet']['description']
					if self.searchAString(string, searchStr):
						responses.append(self.cached_ids[id])

		responses = self.simplify(responses)
		#responses = self.cacheToResponseify(responses)
		code = falcon.HTTP_200
		body = self.schemaResponse("success", code, responses)
		return (code, body)

	def searchVideoTags(self, postData):
		try:
			# mandatory params
			searchStr = postData['searchStr']

			# optional params
			pass
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Missing required fields: %s" % e})
			return (code, body)

		self.logger.info("Searching video descriptions for '%s'" % searchStr)

		responses = []
		for season in self.seasonArr:
			for id in season:
				if self.isSomething(self.cached_ids.get(id)):
					string = ' '.join(self.cached_ids[id]['snippet']['tags'])
					if self.searchAString(string, searchStr):
						responses.append(self.cached_ids[id])


		responses = self.cacheToResponseify(responses)
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
			seasonIds = self.seasonArr[season-1]
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

	def getPlaylistIdsBySeason(self, postData):
		"EAAaBlBUOkNESQ"
		try:
			# mandatory params
			season = postData['season']

			# optional params
			pass
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Missing required fields"})
			return (code, body)

		try:
			season = int(season)
			playlistId = self.playlistArr[season-1]
		except Exception as e:
			self.logger.error(e)
			code = falcon.HTTP_406
			body = self.schemaResponse("error", code, {"details": "Invalid Season %s"%season})
			return (code, body)

		self.logger.info("getting ids for season %s" % season)

		params = {
			'part': 'snippet',
			'playlistId': playlistId,
			'key': self.youtubeApiKey,
			'maxResults': 50
		}

		videoIds = []
		stuffToGet = True
		try:
			url = self.youtubeBaseUrl + '/playlistItems'
			while stuffToGet:
				response = requests.get(url, params=params)
				if response.status_code == 200:
					data = json.loads(response.text)

					items = data.get('items') if self.isSomething(data.get('items')) else False
					nextPageToken = data.get('nextPageToken') if self.isSomething(data.get('nextPageToken')) else False

					for item in items:
						videoIds.append({
							'index' : item['snippet']['position'],
							'id' : item['snippet']['resourceId']['videoId']
						})
					if nextPageToken:
						params['pageToken'] = nextPageToken
					else:
						stuffToGet = False
				else:
					self.logger.info(url)
					self.logger.info(params)
					self.logger.error("ERROR: %s-%s" % (response.status_code, response.text))
					code = falcon.HTTP_503
					body = self.schemaResponse("error", code, {"details": "Youtube aint happy"})
					return (code, body)

		except Exception as e:
			self.logger.error("REQUESTS ERROR: %s" % e)
			code = falcon.HTTP_503
			body = self.schemaResponse("error", code, {"details": "Youtube aint happy"})
			return (code, body)

		# Results should be in order from youtube but who knows so just sort by position
		sortedByPosition = sorted(videoIds, key=lambda d: d['index'])
		simpleList = []
		for item in sortedByPosition:
			simpleList.append(item['id'])

		code = falcon.HTTP_200
		body = self.schemaResponse("success", code, simpleList)
		return (code, body)

	def dumpCache(self, postData):
		with open('data/savedData.json', 'w') as file:
			file.write(json.dumps(self.cached_ids))
		code = falcon.HTTP_200
		body = self.schemaResponse("success", code, {"details": "Dumped %s items to file" % len(self.cached_ids)})
		return (code, body)

	def clearCache(self, postData):
		code = falcon.HTTP_200
		body = self.schemaResponse("success", code, {"details": "Cleared %s items from cache" % len(self.cached_ids)})
		self.cached_ids = {}
		return (code, body)



	###
	# INTERNAL METHODS, NOT CALLABLE
	###
	def readAllEpisodeIds(self):
		try:
			with open('data/allIds.json') as file:
				ids = file.read()
		except Exception as e:
			return []
		return json.loads(ids)

	def buildCacheFromFile(self):
		try:
			with open('data/savedData.json') as file:
				fileData = file.read()
			self.cached_ids = json.loads(fileData)
			self.logger.info("CACHE BUILT WITH %s ITEMS" % len(self.cached_ids))
		except Exception as e:
			self.logger.info("CACHE FILE MISSING")

	def buildSearchFields(self):
		for id,item in self.cached_ids.items():
			if self.isNoneOrEmpty(item.get('searchSet')):
				temp = set()
				tempStr = ''
				lower = item['snippet']['description'].lower()
				words = lower.split(' ')
				simpleWords = filter(str.isalnum, words)
				for word in simpleWords:
					temp.add(word)
				for i in temp:
					tempStr+= i+' '
				tempStr = tempStr[:-1]
				self.cached_ids[id]['searchSet'] = temp
				self.cached_ids[id]['searchWords'] = tempStr

	def cacheToResponseify(self, cacheResponse):
		responsified = [{'items' : [], 'pageInfo' : {'totalResults' : len(cacheResponse)}}]
		for item in cacheResponse:
			item['cached'] = True
			responsified[0]['items'].append(item)
		return responsified

	def simplify(self, responses):
		simplified = {'totalResults' : len(responses), 'items' : []}
		for item in responses:
			simplified['items'].append({
				'id' : item['id'],
				'cached' : item.get('cached'),
				'title': item['snippet']['title'],
				'publishedAt' : item['snippet']['publishedAt'],
				'channelId': item['snippet']['channelId'],
				'channelTitle': item['snippet']['channelTitle'],
				'statistics': item['statistics'],
				'description': item['snippet']['description'],
			})
		return simplified

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

