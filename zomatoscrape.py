import requests as rq
import json, subprocess, re
from bs4 import BeautifulSoup
from urllib import request, parse


USER_AGENT = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
NUM_GROUPS_RE = "\d+"

def extractReviews(id,count):
	payload = {
		"res_id" : id,
		"sort" : "reviews-dd",
		"limit" : count
	}
	try :
		request_data = subprocess.check_output("http -f -b POST  https://www.zomato.com/php/filter_reviews.php res_id={0} limit={1} sort={2}".format(payload["res_id"],payload["limit"],payload["sort"]),shell=True)
		#rq.post("https://www.zomato.com/php/filter_reviews.php", headers = USER_AGENT, data = payload).json
	except Exception as e:
		print(e)
		return []
	return json.loads(request_data.decode('utf-8'))["html"].rstrip()

def parseReviews(html_data):
	soup = BeautifulSoup(html_data,"html.parser")
	reviews = []

	for review in soup.find_all("div",class_="res-review"):
		catch_num_groups = re.findall(NUM_GROUPS_RE, review.find("span",class_="fontsize5").text.strip())

		review_format = {
			"name" : review.find("div",class_="header").text.strip(),
			"num_reviews" : catch_num_groups[0],
			"datetime" : review.find("time")['datetime'],
			"rating" : float(review.find("div", class_="tooltip")['aria-label'].replace("Rated","").strip()),
			"body" : review.find("div",class_="rev-text").text.strip(),
			"expert" : review.find("div",class_="export-label") is not None
		}

		try:
			review_format["num_followers"] = catch_num_groups[1]
		except Exception as e:
			pass

		reviews.append(review_format)

	return reviews
		


def scrapePlace(url):
	try:
		html_data = request_data = subprocess.check_output("http -b GET "+ url, shell=True).decode('utf-8')
	except Exception as e:
		print(e)
		return dict()

	soup = BeautifulSoup(html_data,"html.parser")
	rating_div = soup.find("div",class_="rating-div")

	try:
		num_reviews = int(soup.find("span",class_="rating-votes-div").text.replace("votes","").strip())
	except Exception as e:
		num_reviews = 0

	res_id = int(rating_div['data-res-id'])

	data = {
		"place_name" : soup.find("h1",class_="mb0").text.strip(),
		"place_addr" : soup.find("div",class_="mb5").find("a").text.strip(),
		"zomato_id" : res_id,
		"aggregated_rating" : list(map(float,rating_div.text.strip().split("/"))),
		"num_reviews" : num_reviews,
		"reviews" : parseReviews(extractReviews(res_id,num_reviews))
	}

	return data

def main():
	outfile = open("dump.json","w")
	dump = []

	for url in open("input","r"):
		print("Scraping "+url)
		dump.append(scrapePlace(url))

	outfile.write(json.dumps(dump,indent=4))
	outfile.close()

if __name__ == "__main__":
	main()