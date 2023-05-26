from flask import Flask, render_template, request
from py2neo import Graph
from datetime import date
import json
import pyaiml21
import nltk
from nltk.tokenize import word_tokenize
from glob import glob
from pyaiml21 import Kernel
from textblob import TextBlob
import socket
import openai
import requests
import spacy
from bs4 import BeautifulSoup

nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
graph = Graph(password="12345678")
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

print(ip_address)
question_words = ["what", "why", "when", "where",
             "name", "is", "how", "do", "does",
             "which", "are", "could", "would",
             "should", "has", "have", "whom", "whose", "don't"]
#for web scrapping
def is_google(text):
    user_query = text
    print(user_query)
    URL = 'https://www.google.com/search?q=' + user_query
    headers = {
        'User-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
    }
    page = requests.get(URL, headers=headers)
    wiki_page = BeautifulSoup(page.content, 'html.parser')
    try:
        all_paragraph = wiki_page.find(class_='Z0LcW t2b5Cf').getText()
        return all_paragraph

    except Exception:
        doc = nlp(user_query)
        nounfind = [token.lemma_ for token in doc if token.pos_ == "NOUN"]
        PRnounfind = [token.lemma_ for token in doc if token.pos_ == "PROPN"]
        if nounfind:
            noun = nounfind[0]
            print(type(nounfind))
            url = f'https://en.wikipedia.org/wiki/{noun}'
            wikpage = requests.get(url)
            p_page = BeautifulSoup(wikpage.text, 'html.parser')
            all_pg = p_page.find_all('p')
            fp = all_pg[1]
            return fp.text
            print(fp)
        elif PRnounfind:
            print(PRnounfind)
            ppnoun = PRnounfind[0]
            url = f'https://en.wikipedia.org/wiki/{ppnoun}'
            wikpage = requests.get(url)
            p_page = BeautifulSoup(wikpage.text, 'html.parser')
            all_pg = p_page.find_all('p')
            fp = all_pg[1]
            return fp.text
            print(fp)
        else:
            return ("Sorry I dont know")

def episodic_memory(user, bot, s_analysis):
    i = 0
    j = 0

    q = """MATCH (n:Person) - [HAS]->(m) WHERE n.email = $useremail  RETURN m.session_count"""
    counter = graph.run(q, useremail = z).data()
    print(type(counter))
    counting = counter[0]
    print(counting)
    counterr = counting.get('m.session_count')
    counterr = counterr+1
    episodes = "episode" + str(counterr)

    ep = {

    }
    chat = {

        "human" + str(i) : user,
        "Bot"   + str(i) : bot,
        "emotion" : s_analysis
        }
    i=i+1
    j = j+1
    interaction_count = "interaction_count" + str(j)
    ep[interaction_count] = chat
    epp = json.dumps(ep)
    q = """MATCH (n:Person) - [HAS]->(m) WHERE n.email = $useremail SET m.{} = $sc RETURN m""".format(episodes)
    ep_memory = graph.run(q, useremail= z, sc = epp)
    q = """MATCH (n:Person) - [HAS]->(m) WHERE n.email = $useremail SET m.session_count = $sc RETURN m""".format(ep)
    ep_memory = graph.run(q, useremail=z, sc=counterr)

#for openai
"""def is_unknown(text):
    openai.api_key = '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'
    messages = [
        { "role": "system", "content": "You are a kind helpful assistant"},
    ]
    message = text
    if message:
        messages.append(
            {
                "role": "user", "content": message},
        )
        chat = openai.ChatCompletion.create(
               model="gpt-3.5-turbo", messsages = messages
            )
    reply = chat.choices[0].message.content
    #print(f"chatgpt: {reply}")
    messages.append({"role": "assistant", "content": reply})
    return reply
"""
#for social networking
def is_social(socialnetwork,email):

    relation = graph.run(f"MATCH (n:Person),(m:Person) WHERE n.ip = \"{ip_address}\" and  n.email <> \"{email}\" and  m.ip = \"{ip_address}\" and  m.email = \"{email}\" CREATE (n)-[r:related]->(m) RETURN r")
    print(relation)

def original_sent(text):
    nlpt = TextBlob(text)
    print("original", nlpt)
    modified = nlpt.correct()
    print("modified", modified)
    return modified

def is_sentimental(text):
    blob = TextBlob(text)
    sentimental = blob.sentiment.polarity # -1 to 1
    print(sentimental)
    return sentimental

@app.route("/")
def login():
    return render_template("sign-in.html")


@app.route("/register")
def register():
    return render_template("registration.html")


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/get")
def get_bot_response():
    Bot = Kernel()
    for name in glob("profiles.aiml"):
        Bot.learn_aiml(name)
    while True:
        query = request.args.get('msg')
        #user = str(original_sent(query))
        user = query
        question = user.lower()
        question = word_tokenize(question)
        if any(x in question[0] for x in question_words):
            print("This is a question!")
        else:
            print("This is not a question!")
            #sentimental analysis
        senty = is_sentimental(user)

        response = Bot.respond(user, 'User1')

        if response == "unknown":
            response = is_google(user)

        print('<Bot>', response)
        episodic_memory(query, response, senty)
        if response:
            return (str(response))
        else:
            return (str(":)"))


@app.route('/', methods=['POST', 'DELETE'])
def getvalue():
    username = request.form.get('username')
    email = request.form.get('email')
    pass1 = request.form.get('pass1')
    graph = Graph(password="12345678")
    n = graph.run(f"CREATE (n:Person {{name: \"{username}\", email: \"{email}\", password: {pass1}, ip: \"{ip_address}\"}}) RETURN n")
    m = """ CREATE (m:memory{name:"memory", email : $z, session_count : 0}) RETURN m"""
    graph.run(m, z=email)
    memory = """ MATCH (n:Person), (m:memory) WHERE n.email = $e AND m.email = $e1 CREATE (n)-[r:HAS]->(m) RETURN r """
    graph.run(memory, e = email, e1 = email)
    return render_template("sign-in.html")


@app.route('/gett', methods=['POST', 'DELETE'])
def gettingvalue():
    global y
    global z
    email = request.form.get('email')
    pass1 = request.form.get('pass1')
    graph = Graph(password="12345678")
    # result = graph.run("MATCH (n:Person) RETURN n")
    result = graph.run(f"MATCH (n:Person) WHERE n.email = \"{email}\"  and n.password = {pass1} RETURN n").data()
    # convert it into list
    social = result.copy()
    social = str(social)
    socialnetwork = social
    y = socialnetwork
    z = email

    if len(result) == 0:
        print("unmatched")
        return render_template("sign-in.html")
    else:
        print("matched")
        return render_template("home.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
