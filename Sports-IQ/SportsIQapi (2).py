#!/usr/bin/env python
# coding: utf-8

# In[ ]:


get_ipython().system('pip install requests')


# In[4]:


import requests
import os

API_KEY = os.getenv("CRICKET_API_KEY")

url = "https://api.cricapi.com/v1/currentMatches"

params = {
    "apikey": API_KEY,
    "offset": 0
}

response = requests.get(url, params=params)

print("Status Code:", response.status_code)


# In[ ]:


data = response.json()

print(data)


# In[7]:


print(data.keys())


# In[ ]:


data["data"]


# In[9]:


print(data.keys())


# In[10]:


print(len(data["data"]))


# In[ ]:


match = data["data"][0]

print(match)


# In[ ]:


data["data"][0]


# In[13]:


print("Team 1:", match["teams"][0])
print("Team 2:", match["teams"][1])

print("\nScores:")

for score in match["score"]:
    print(
        score["inning"],
        "→",
        score["r"], "runs/",
        score["w"], "wickets in",
        score["o"], "overs"
    )

print("\nResult:", match["status"])


# In[14]:


live_matches = []

for match in data["data"]:
    if match["matchStarted"] and not match["matchEnded"]:
        live_matches.append(match)

print("Live matches:", len(live_matches))


# In[16]:


for match in live_matches:
    print(match["name"])


# In[17]:


live_match = live_matches[0]

print("🏏 MATCH:", live_match["name"])
print("📍 VENUE:", live_match["venue"])
print("📅 DATE:", live_match["date"])
print("📌 STATUS:", live_match["status"])
print("🏁 STARTED:", live_match["matchStarted"])
print("🏆 ENDED:", live_match["matchEnded"])


# In[18]:


print("Team 1:", live_match["teams"][0])
print("Team 2:", live_match["teams"][1])


# In[19]:


print("SCORES:")

for score in live_match["score"]:
    print(
        score["inning"],
        "→",
        score["r"], "runs/",
        score["w"], "wickets in",
        score["o"], "overs"
    )


# In[20]:


print(len(live_match["score"]))


# In[21]:


innings = live_match["score"][0]

print("Innings:", innings["inning"])
print("Runs:", innings["r"])
print("Wickets:", innings["w"])
print("Overs:", innings["o"])


# In[22]:


if len(live_match["score"]) == 1:
    print("🏏 First innings is currently in progress.")
else:
    print("🏏 Second innings is currently in progress.")


# In[23]:


team = innings["inning"].replace(" Inning 1", "")

runs = innings["r"]
wickets = innings["w"]
overs = innings["o"]

print("🏏 SPORTS IQ — LIVE MATCH")
print("==========================")
print("Team:", team)
print("Score:", f"{runs}/{wickets}")
print("Overs:", overs)
print("Status: 🔴 LIVE")


# In[24]:


def calculate_required_run_rate(target, current_runs, balls_remaining):
    runs_needed = target - current_runs
    
    if balls_remaining <= 0:
        return 0
    
    required_run_rate = (runs_needed / balls_remaining) * 6
    
    return required_run_rate


# In[25]:


target = 181
current_runs = 145
balls_remaining = 22

rrr = calculate_required_run_rate(
    target,
    current_runs,
    balls_remaining
)

print("Runs needed:", target - current_runs)
print("Balls remaining:", balls_remaining)
print("Required Run Rate:", round(rrr, 2))


# In[28]:


def win_estimate(current_rr, required_rr, wickets_remaining, balls_remaining):
    
    if required_rr <= current_rr:
        probability = 75
    elif required_rr <= current_rr + 2:
        probability = 60
    elif required_rr <= current_rr + 4:
        probability = 40
    else:
        probability = 20
    
    # Adjust slightly for wickets in hand
    if wickets_remaining >= 7:
        probability += 5
    elif wickets_remaining <= 2:
        probability -= 10
    
    # Keep probability between 5 and 95
    probability = max(5, min(probability, 95))
    
    return probability


# In[29]:


current_rr = 10.2
required_rr = 9.8
wickets_remaining = 7
balls_remaining = 22

probability = win_estimate(
    current_rr,
    required_rr,
    wickets_remaining,
    balls_remaining
)

print("Chasing Team Win Estimate:", probability, "%")
print("Other Team:", 100 - probability, "%")


# In[30]:


import requests

ollama_url = "http://localhost:11434/api/generate"

payload = {
    "model": "llama3.2",
    "prompt": "Explain cricket in one simple sentence.",
    "stream": False
}

response = requests.post(ollama_url, json=payload)

print(response.status_code)


# In[31]:


result = response.json()

print(result["response"])


# In[32]:


team = innings["inning"].replace(" Inning 1", "")

runs = innings["r"]
wickets = innings["w"]
overs = innings["o"]

match_summary = f"""
You are Sports IQ, an intelligent cricket analyst.

LIVE MATCH DATA:
Batting Team: {team}
Score: {runs}/{wickets}
Overs: {overs}

Analyze this match like a live television cricket analyst.

Give:
• Current match situation
• Key observation
• What the batting team should do next
• One exciting commentary-style sentence

Keep it concise, exciting and easy to understand.
Do not invent statistics that are not provided.
"""


# In[42]:


payload = {
    "model": "llama3.2",
    "prompt": match_summary,
    "stream": False
}

response = requests.post(
    "http://localhost:11434/api/generate",
    json=payload
)

result = response.json()

print(result["response"])


# In[ ]:


get_ipython().system('pip install edge-tts')


# In[36]:


import edge_tts

communicate = edge_tts.Communicate(
    "Welcome to Sports IQ. Your AI cricket analyst is ready.",
    "en-US-GuyNeural"
)

await communicate.save("test_voice.mp3")


# In[37]:


from IPython.display import Audio

Audio("test_voice.mp3", autoplay=True)


# In[39]:


commentary = result["response"]

print(commentary)


# In[40]:


import edge_tts

communicate = edge_tts.Communicate(
    commentary,
    "en-US-GuyNeural"
)

await communicate.save("ai_commentary.mp3")


# In[49]:


from IPython.display import Audio

Audio("ai_commentary.mp3", autoplay=True)


# In[51]:


def get_cricket_data():
    response = requests.get(
        "https://api.cricapi.com/v1/currentMatches",
        params={"apikey": API_KEY}
    )
    
    return response.json()


# In[52]:


data = get_cricket_data()

print("Matches received:", len(data["data"]))


# In[53]:


def get_live_matches(data):
    live_matches = []

    for match in data["data"]:
        if match["matchStarted"] and not match["matchEnded"]:
            live_matches.append(match)

    return live_matches


# In[54]:


live_matches = get_live_matches(data)

print("Live matches:", len(live_matches))

for match in live_matches:
    print(match["name"])


# In[55]:


import time

for i in range(3):
    
    data = get_cricket_data()
    live_matches = get_live_matches(data)
    
    print("\n🔴 LIVE MATCHES")
    
    for match in live_matches:
        print(match["name"])
        
        for score in match["score"]:
            print(
                score["inning"],
                "→",
                score["r"], "/",
                score["w"],
                "in",
                score["o"],
                "overs"
            )
    
    print("\nChecking again...")
    time.sleep(10)


# In[56]:


def detect_turning_point(old_score, new_score):
    
    old_runs = old_score["r"]
    new_runs = new_score["r"]
    
    old_wickets = old_score["w"]
    new_wickets = new_score["w"]
    
    if new_wickets > old_wickets:
        return "WICKET"
    
    elif new_runs > old_runs:
        runs_added = new_runs - old_runs
        return f"{runs_added} RUNS ADDED"
    
    else:
        return None


# In[57]:


old_score = {
    "r": 116,
    "w": 2,
    "o": 16.4
}

new_score = {
    "r": 116,
    "w": 3,
    "o": 16.5
}


# In[58]:


event = detect_turning_point(old_score, new_score)

print("Event:", event)


# In[59]:


turning_point_prompt = f"""
You are Sports IQ, a live cricket analyst.

A turning point has just occurred:

Event: {event}

Previous score: {old_score["r"]}/{old_score["w"]}
New score: {new_score["r"]}/{new_score["w"]}

Explain why this event could be important to the match.

Give a short, exciting cricket commentary.
Do not invent player names or statistics.
"""


# In[60]:


payload = {
    "model": "llama3.2",
    "prompt": turning_point_prompt,
    "stream": False
}

response = requests.post(
    "http://localhost:11434/api/generate",
    json=payload
)

turning_point_commentary = response.json()["response"]

print(turning_point_commentary)


# In[61]:


communicate = edge_tts.Communicate(
    turning_point_commentary,
    "en-US-GuyNeural"
)

await communicate.save("turning_point.mp3")


# In[62]:


Audio("turning_point.mp3", autoplay=True)


# In[63]:


cricket_knowledge = """
UGANDA WOMEN:
Uganda Women are a cricket team that participate in international women's cricket.
Their matches can include T20 and other limited-overs formats.

TANZANIA WOMEN:
Tanzania Women participate in international women's cricket.
They compete in women's limited-overs cricket.

CRICKET ANALYSIS:
In a chase, the required run rate is an important indicator.
A lower required run rate generally means less scoring pressure.
Wickets remaining are also important because losing wickets can increase pressure.

TURNING POINTS:
A wicket can become a turning point when it changes the momentum of a match.
A large scoring over can also change momentum.
A batting collapse, where several wickets fall quickly, can significantly change a team's position.

SPORTS IQ:
Sports IQ combines live cricket data, statistical calculations and AI-generated analysis.
It should not invent player names, scores or match events that are not present in the available data.
"""


# In[64]:


def retrieve_knowledge(question):
    question = question.lower()
    
    relevant_info = []
    
    for paragraph in cricket_knowledge.split("\n\n"):
        if any(word in paragraph.lower() for word in question.split()):
            relevant_info.append(paragraph)
    
    return "\n\n".join(relevant_info)


# In[65]:


question = "What is a turning point in cricket?"

context = retrieve_knowledge(question)

print(context)


# In[66]:


question = "What is a turning point in cricket?"


# In[67]:


context = retrieve_knowledge(question)

print("Retrieved Knowledge:")
print(context)


# In[68]:


rag_prompt = f"""
You are Sports IQ, an intelligent cricket assistant.

Use the following retrieved cricket knowledge to answer the user's question.

RETRIEVED KNOWLEDGE:
{context}

USER QUESTION:
{question}

Instructions:
- Answer using the retrieved knowledge.
- Keep the explanation simple.
- Do not invent cricket facts.
- If the knowledge does not contain the answer, say that the information is not available.
"""

payload = {
    "model": "llama3.2",
    "prompt": rag_prompt,
    "stream": False
}

response = requests.post(
    "http://localhost:11434/api/generate",
    json=payload
)

rag_result = response.json()

print(rag_result["response"])


# In[69]:


rag_answer = rag_result["response"]

print(rag_answer)


# In[70]:


communicate = edge_tts.Communicate(
    rag_answer,
    "en-US-GuyNeural"
)

await communicate.save("rag_answer.mp3")


# In[71]:


Audio("rag_answer.mp3", autoplay=True)


# In[ ]:




