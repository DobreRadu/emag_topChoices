from urllib.request import urlopen
import urllib
import hashlib

from bs4 import BeautifulSoup
from pymongo import MongoClient

#CONSTANTS
MONGO_URI = "mongodb://localhost:27017"
netlocGlobal = "http://www.emag.ro"
#Comment the next line and uncomment the other to test on microphones.
hrefGlobal = "/routere_wireless/filter/tip-produs-f8795,sistem-mesh-v-7395518/c?ref=hp_menu_quick-nav_23_40&type=filter"
#hrefGlobal="/microfoane-pc/c?ref=hp_menu_quick-nav_23_28&type=category"
client = MongoClient(MONGO_URI)
db = client.mydb

def encrypt_string(hash_string):
    sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

def gatherInformation():

    #for megamenu
    mainPage = urllib.request.urlopen(netlocGlobal)
    htmlMainPage = mainPage.read().decode("utf-8")
    soup = BeautifulSoup(htmlMainPage, features="html.parser")
    megamenu = soup.find("div", {"class":"megamenu-details-department collapse-group"})

    #We need to hove over the elements in the megamenu so they appear.
    #Cum ar fi trebuit sa mearga pentru ca o matrice si verificam "Nou" sau "Promo"
    #for i in megamenu.find_all("div",{"class":"megamenu-details-department collapse-group"}):
     #   for j in i.find_all("a"):
      #      print(j.text)

    #for specififc category
    link = netlocGlobal + hrefGlobal
    currentPage = 1

    #We need to keep track of links because by testing I find that they are random on different pages and may appear again.
    foundOnThis = []
    categorie = ""
    while link is not None:
        page = urllib.request.urlopen(link)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, features="html.parser")

        #This is were each item is loacted
        gridDiv = soup.find("div", id="card_grid")
        count = 0
        jsonArray=[]
        #Getting each div content on page
        for index in gridDiv.find_all("div"):
            jsonObjectTemp={}

            #Finding the thumbnail where there is Super Pret or Top Favorite
            for specificIndex in index.find_all("a",{"data-zone":"thumbnail"}):
                href = specificIndex["href"]

                if specificIndex.find("span", text="Super Pret") is not None:
                    if href not in foundOnThis:
                        categorie=index["data-category-trail"]
                        jsonObjectTemp=createObject("Super Pret",index,href)
                        foundOnThis.append(href)
                        count = count + 1
                elif specificIndex.find("span", text="Top Favorite") is not None:
                    if href not in foundOnThis:
                        categorie=index["data-category-trail"]
                        jsonObjectTemp=createObject("Top Favorite",index,href)
                        foundOnThis.append(href)
                        count = count + 1

                if jsonObjectTemp !={}:
                    jsonArray.append(jsonObjectTemp)

        if count !=0:
            print("On page "+str(currentPage)+" in category \""+categorie+"\" there are="+str(count)+" product(s)")
            print(jsonArray)
            #Replace the colection with a new one
            db[categorie + "/" + str(currentPage)].drop()
            for item in jsonArray:
                db[categorie+"/"+str(currentPage)].insert_one(item)
        else:
            print("Nothing on these page "+str(currentPage)+" in category: "+categorie)


        #Finding the next page
        currentPage = currentPage + 1
        #This is the div where the links are located,it will go until the last page
        listingPanel=soup.find("div",{"class":"col-xs-12 col-lg-9 text-sm-center text-xs-center text-lg-right"})
        link = listingPanel.find("a", text=currentPage)
        if link is not None:
            link=netlocGlobal + link["href"]
        print("===============================================================")


def createObject(type,index,href):
    jsonObjectTemp={}
    jsonObjectTemp["promotie"] = type
    jsonObjectTemp["categorie"] = index["data-category-trail"]
    jsonObjectTemp["produs"] = index["data-name"]
    jsonObjectTemp["pret"] = index.find("p", {"class": "product-new-price"}).text
    jsonObjectTemp["link"] = href
    return jsonObjectTemp


if __name__ == '__main__':
    option = int(input("1.Login\n2.Sign up\n>"))
    if option == 1:
        username = encrypt_string(input("Please input your username:"))
        password = encrypt_string(input("Please input your password:"))

        user = db.credentials.find_one({"username": username})
        if user is not None:
            if user["password"] != password:
                print("Username or password is wrong!")
                exit()
            else:
                print("You are in!\n")
                gatherInformation()
        else:
            print("User doesn't exists!")
            exit()
    elif option == 2:
        # TODO verify if user and pass are good (!="",user!=pass,etc)
        username = encrypt_string(input("Please input your username:"))
        password = encrypt_string(input("Please input your password:"))
        repassword = encrypt_string(input("Please input your password again for verification:"))
        if password != repassword:
            print("Please verify your password!")
            exit()
        else:
            db.credentials.insert_one({
                "username": username,
                "password": password
            })
            print("Your account is ready!\n")
            gatherInformation()
            exit()






