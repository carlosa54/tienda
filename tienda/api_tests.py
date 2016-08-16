import requests

base_url = "http://127.0.0.1:8000/api/"
login_url = base_url + "auth/token/"

products_url = base_url + "products/"
refresh_url = login_url + "refresh/"
cart_url = base_url + "cart/"

# requests.post(login_url, data=None, headers=None, params=None)

data = {
	"username": "carlos",
	"password": "5454",
}

login_r = requests.post(login_url, data=data)

login_r.text
json_data = login_r.json()

import json

print(json.dumps(json_data, indent=2))

token = json_data["token"]
print token

headers = {
	"Authorization": "JWT %s" %(token),
}
p_r = requests.get(products_url, headers=headers)
print json.dumps(p_r.json(), indent=2)

#Refresh token test
data = {
	"token": token
}
refresh_r = requests.post(refresh_url, data=data)

print refresh_r.json()

token = refresh_r.json()["token"]

cart_r = requests.get(cart_url)

cart_token = cart_r.json()["token"]

new_cart_url = cart_url + "?token=" + cart_token + "&item=15&qty=3&delete=True"

new_cart_r = requests.get(new_cart_url)

print new_cart_r.json()