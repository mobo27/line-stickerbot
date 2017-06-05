import json
import logging
from threading import Thread
from time import sleep
import urllib.request
import urllib.parse
import requests
import cssutils
from bs4 import BeautifulSoup
from wand.image import Image
from zipfile import ZipFile
from OpenSSL import SSL
import os

cssutils.log.setLevel(logging.CRITICAL)


# This will mark the last update we've checked
with open('updatefile', 'r') as f:
    last_update = int(f.readline().strip())
# Here, insert the token BotFather gave you for your bot.
TOKEN = '<token>'
# This is the url for communicating with your bot
URL = 'https://api.telegram.org/bot%s/' % TOKEN

# The Line store URL format.
LINE_URL = "https://store.line.me/stickershop/product/"

# The text to display when the sent URL doesn't match.
WRONG_URL_TEXT = ("That doesn't appear to be a valid URL. "
                  "To start, send me a URL that starts with " + LINE_URL)

def dl_stickers(sticker_id, page):
    print("DL Stickers")
    images = page.find_all('span', attrs={"style": not ""})
    for i in images:
        imageurl = i['style']
        imageurl = cssutils.parseStyle(imageurl)
        imageurl = imageurl['background-image']
        imageurl = imageurl.replace('url(', '').replace(')', '')
        imageurl = imageurl[1:-15]
#        print("Downloading Image:" + imageurl)
#        response = urllib.request.urlopen(imageurl)
#        resize_sticker(sticker_id, response, imageurl)
        thread = Thread(target = dl_resize_sticker, args = (sticker_id, imageurl))
        thread.start()
    if len(images) == 0:
        print("No images")
        requests.get(URL + 'sendMessage', params=dict(chat_id=update['message']['chat']['id'], text="No Images"))



def dl_resize_sticker(sticker_id, imageurl):
    print("Downloading Image:" + imageurl)
    image = urllib.request.urlopen(imageurl)
    filen = imageurl.split('/')[6]+imageurl[-4:]
    directory = "downloads/line_sticker_"+sticker_id+"/"
    try:
        os.stat(directory)
    except:
        os.mkdir(directory)

    with Image(file=image) as img:
        ratio = 1
        if img.width > img.height:
            ratio = 512.0/img.width
            newWidth  = 512.0
            newHeight = int(img.height*ratio)
        else:
            ratio = 512.0/img.height
            newWidth  = int(img.width*ratio)
            newHeight = 512.0
#        print("W: {0} H: {1} Ratio: {2} newW:{3} newH:{4}".format(img.width, img.height, ratio, img.width*ratio, img.height*ratio))
        img.resize(int(newWidth), int(newHeight), 'mitchell')
        img.save(filename=(directory + filen))
        requests.post(URL + 'sendDocument', params=dict(
            chat_id = update['message']['chat']['id']
        ), files=dict(
            document = open(directory + filen, 'rb')
        ))


def send_stickers(sticker_id, page):
    dl_stickers(sticker_id, page)
    with ZipFile('packed_stickers/line_stickers'+sticker_id+'.zip', 'w') as stickerzip:
        for root, dirs, files in os.walk("downloads/"):
            for file in files:
                stickerzip.write(os.path.join(root, file))
                os.remove(os.path.join(root, file))
    requests.post(URL + 'sendDocument', params=dict(
        chat_id = update['message']['chat']['id']
    ), files=dict(
        document = open('packed_stickers/line_stickers'+sticker_id+'.zip', 'rb')
    ))
    print("snet;)")


# We want to keep checking for updates. So this must be a never ending loop
while True:
    # My chat is up and running, I need to maintain it! Get me all chat updates
    get_updates = json.loads(requests.get(URL + 'getUpdates',
                                          params=dict(offset=last_update)).content.decode())
    # Ok, I've got 'em. Let's iterate through each one
    for update in get_updates['result']:
        # First make sure I haven't read this update yet
        if last_update < update['update_id']:
            last_update = update['update_id']
            f = open('updatefile', 'w')
            f.write(str(last_update))
            f.close()
            # I've got a new update. Let's see what it is.
            if 'message' in update:
                if update['message']['text'][:42] == LINE_URL:
                    # It's a message! Let's send it back :D
                    sticker_url = update['message']['text']
                    sticker_id = sticker_url.split('/')[5]
                    user = update['message']['chat']['id']
                    request = requests.get(sticker_url).text
                    stickerpage = BeautifulSoup(request, "html.parser")
                    stickertitle = stickerpage.title.string
                    name = update['message']['from']['first_name']
                    requests.get(URL + 'sendMessage',
                                 params=dict(chat_id=update['message']['chat']['id'],
                                             text="Fetching \"" + stickertitle + "\""))
                    print(name + " (" + str(user) + ")"+ " requested " + sticker_url)
                    dl_stickers(sticker_id, stickerpage)
#                    send_stickers(sticker_id, stickerpage)
                else:
                    requests.get(URL + 'sendMessage',
                                 params=dict(chat_id=update['message']['chat']['id'],
                                             text=WRONG_URL_TEXT))
    # Let's wait a few seconds for new updates
    sleep(1)


