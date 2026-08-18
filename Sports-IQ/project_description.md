# 🏏 SportsAI Cricket Assistant

 Project Description

Sports AI Assistant is an AI-powered cricket assistant developed using a Cricket API, Retrieval-Augmented Generation (RAG), and Ollama. The project retrieves real-time cricket information such as ongoing matches, match details, scores, and live commentary through an API. RAG is used to retrieve relevant cricket-related information, while Ollama is used as the local Large Language Model (LLM) to understand the user's query and generate an appropriate response. The project also includes voice interaction, allowing users to interact with the Sports AI Assistant system using voice input and receive AI-generated responses. The overall aim of the project is to provide users with a simple AI-based system for accessing and understanding live cricket information.

---

 Technologies Used

* **Python** – Main programming language used for developing the project.
* **Cricket API** – Used to retrieve live cricket match information, scores, match details, and commentary.
* **RAG (Retrieval-Augmented Generation)** – Used to retrieve relevant information from the available cricket knowledge/data before generating an answer.
* **Ollama** – Used to run the Large Language Model locally and generate natural-language responses.
* **Voice Processing** – Used for voice-based interaction with the Sports IQ assistant.
* **Jupyter Notebook** – Used for developing and testing the project.

---

## 📚 Libraries / Modules Used

The project uses Python libraries/modules for different tasks, including:

* **Requests** – Used for sending requests to the Cricket API and receiving data.
* **JSON** – Used for handling API responses and structured data.
* **Ollama** – Used to communicate with the locally running Ollama model.
* **RAG-related libraries/modules** – Used for retrieving relevant information and providing context to the language model.
* **Voice-related libraries/modules** – Used for speech input/output and voice interaction.

> **Note:** The exact library names and versions can be listed in `requirements.txt`.

---

## ⚙️ Main Functions Used

The project contains functions for different parts of the Sports AI Assistant system. The main functions include:

### 1. API Functions

Used to connect to the Cricket API and retrieve:

* Live matches
* Match information
* Scores
* Teams and players
* Live commentary

### 2. Data Processing Functions

Used to process and organize the information received from the API so that it can be displayed or provided to the AI model.

### 3. RAG Functions

Used to:

* Retrieve relevant cricket information
* Find useful context for a user's question
* Provide the retrieved context to the language model

### 4. Ollama Functions

Used to:

* Send the user's question along with relevant context to the Ollama model
* Generate a natural-language response

### 5. Voice Functions

Used to:

* Receive the user's voice input
* Convert speech into text
* Process the question using Sports AI Assistant
* Provide the generated response through voice output

---

## 🔄 How the Project Works

The overall workflow of Sports AI Assistant is:

```text
User Query
     ↓
Sports AI Assistant
     ↓
┌─────────────────────────────┐
│ Cricket API                 │
│ Live matches & commentary   │
└─────────────────────────────┘
     ↓
Relevant Information
     ↓
RAG Retrieval
     ↓
Relevant Context
     ↓
Ollama LLM
     ↓
AI-Generated Response
     ↓
User
```

For voice interaction:

```text
🎤 Voice Input
      ↓
Speech-to-Text
      ↓
Sports AI Assistant
      ↓
RAG + Ollama
      ↓
AI Response
      ↓
🔊 Voice Output
```

---

## 💡 Example

### Example 1 – Live Match

**User:**

> What cricket matches are currently live?

**Sports AI Assistant:**
The system sends a request to the Cricket API, retrieves the currently available live matches, and displays the relevant match information.

---

### Example 2 – Commentary

**User:**

> What happened in the latest ball?

**Sports AI Assistant:**
The system retrieves the latest commentary from the Cricket API and provides the relevant information to the user.

---

### Example 3 – Cricket Question

**User:**

> What is a powerplay in cricket?

**Sports AI Assistant:**
RAG retrieves relevant cricket information and provides the context to Ollama. Ollama then generates an easy-to-understand answer for the user.

---

### Example 4 – Voice Interaction

**User:** 🎤

> What is the current score?

**Sports AI Assistant:**
The voice input is converted into text, the system retrieves the relevant match information, and Ollama generates the response, which can then be provided through voice output.

---

## 🎯 Project Objective

The main objective of Sports AI Assistantis to combine **real-time cricket data, information retrieval, and a local AI language model** into a single intelligent cricket assistant that can answer cricket-related questions and provide live match information through text and voice interaction.

