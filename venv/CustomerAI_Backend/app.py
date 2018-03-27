from flask import make_response, jsonify
import json
import requests
from bson.json_util import dumps
from flask import Flask, render_template, url_for, request, session, redirect
from  flask_pymongo import PyMongo
from bson.json_util import dumps
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
#twilio
account_sid='AC5f660e731991961655ef6f3a50a0dc3d'
account_token='32b39da1fe163b19562aca72344fa1b5'
client=Client(account_sid,account_token)
#microsoft
subscription_key = '50e92c9bfb5b491a8184f3255618a911'
assert subscription_key
text_analytics_base_url = "https://westcentralus.api.cognitive.microsoft.com/text/analytics/v2.0/"
sentiment_api_url = text_analytics_base_url + "sentiment"
#flask
app = Flask(__name__)
app.config['MONGO_DBNAME']='connect'
app.config['MONGO_URI']='mongodb://dhiraj:root@ds123499.mlab.com:23499/connect'
mongo=PyMongo(app)

@app.route('/')
def my_form():
    return render_template('Dashboard_Front.html')

@app.route("/",methods=['GET','POST'])
def home():
    name = request.form['name']
    number = '+1'+request.form['number']
    type = request.form['type']
    add(number,type,name)
    intro = request.form['intro']
    pos = request.form['pos']
    neg = request.form['neg']
    processedText=processIt(name,type,intro)
    client.messages.create(
        to=number,
        from_='+13238864616',#(323) 886-4616
        body=processedText
    )
    generics=mongo.db.generics
    temp=generics.find_one({'doc_id':'1'})
    if temp:
        temp['pos']=pos
        temp['neg']=neg
        generics.save(temp)
    else:
        generics.insert({ 'doc_id':'1','pos':pos,'neg':neg})
    print('message sent to the user')
    return ''


@app.route("/analysis",methods=['GET','POST'])
def analysis():
    analyze=mongo.db.analyze
    return dumps(analyze.find())

def processIt(name,type,intro):
    intro=intro.replace('&lt;productType&gt;',type)
    intro=intro.replace('&lt;firstName&gt;',name)
    print('processed')
    return intro

#feedback:false means waiting
def add(number,type,name):
    transac=mongo.db.transac
    transac.insert({ 'Product_name':type,'Customer_no':number,'feedback':'false','Cust_name':name})
    print('added')
    #return 'added'

@app.route("/sms", methods=['GET', 'POST'])
def incoming_sms():
    """Send a dynamic reply to an incoming text message"""
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    sender=request.values.get('From', None)
    documents = {'documents' : [
      {'id': '1', 'language': 'en', 'text': body}

    ]}
    headers   = {"Ocp-Apim-Subscription-Key": subscription_key}
    response  = requests.post(sentiment_api_url, headers=headers, json=documents)
    sentiments = response.json()
    score=sentiments['documents'][0]['score']
    resp = MessagingResponse()
    transac=mongo.db.transac
    #first=transac.find()
    print(sender)
    first=transac.find_one({'Customer_no':sender,'feedback':'false'})
    print(first)
    #if  first['feedback']=='false':
    first['feedback']='true'
    transac.save(first)
    Product_name=first['Product_name']
    Customer_name=first['Cust_name']
    generics=mongo.db.generics
    temp=generics.find_one({'doc_id':'1'})
#Lets do it!
    analyze=mongo.db.analyze

    temp2=analyze.find_one()
    #print(temp2)
    if not temp2:
        print("inside")
        analyze.insert({ 'Product_name':'Cherry','Pos':'0','Neg':'0'})
        analyze.insert({ 'Product_name':'Vanilla','Pos':'0','Neg':'0'})
        analyze.insert({ 'Product_name':'Lime','Pos':'0','Neg':'0'})
    analyze=mongo.db.analyze
    temp1=analyze.find_one({'Product_name':Product_name})
    if score<0.5:
        val=int(temp1['Neg'])
        val=val+1
        temp1['Neg']=str(val)
        analyze.save(temp1)
        processedText=processIt(Customer_name,Product_name,temp['neg'])
    else:
        val=int(temp1['Pos'])
        val=val+1
        temp1['Pos']=str(val)
        analyze.save(temp1)
        processedText=processIt(Customer_name,Product_name,temp['pos'])
    resp.message(processedText)
    return str(resp)

if __name__ == "__main__":
    app.run(debug = True,port=80)

