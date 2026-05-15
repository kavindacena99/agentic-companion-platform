# Companio

**The AI person who understands you.**

Companio is an AI agent persons platform designed to create emotionally intelligent digital companions such as a Best Friend, Girlfriend, or Boyfriend. The goal of the project is to build a public mobile app where users can create a profile, select an AI person, and interact with an agent that can remember, understand, support, and continue conversations naturally over time.

Companio is not planned as a basic chatbot. It is designed as an Agentic RAG-based platform with persona memory, user memory, conversation memory, safe agent behavior, and configurable LLM provider support.

---

## Product Vision

The vision of Companio is to create AI persons that feel personal, consistent, and emotionally intelligent while maintaining clear ethical boundaries.

Users should be able to:

- Create a personal profile
- Select an AI person type
- Chat with the selected AI agent
- Experience memory-based conversation continuity
- Manage privacy and memory settings
- Report unsafe responses
- Use the app through free or subscription-based plans

---

## Core Agent Types

The initial version of Companio focuses on three main AI person types:

- **Best Friend Agent**
- **Girlfriend Agent**
- **Boyfriend Agent**

Each agent type will have its own relationship style, personality, tone, memory rules, and safety boundaries.

---

## Core System Design

Companio is based on five major foundations:

### 1. Persona Memory

Each agent has its own personality, relationship type, speaking style, boundaries, backstory, likes/dislikes, and emotional behavior.

### 2. User Memory

The system remembers important user details such as goals, studies, work, mood patterns, favorite topics, routines, dreams, struggles, and important life events.

### 3. Conversation Memory

The agent remembers previous conversations using summaries and retrieved memory, allowing natural continuity across sessions.

### 4. Agentic Behavior

The agent can decide when to comfort, motivate, ask follow-up questions, suggest an activity, remind the user, or continue an emotional topic.

### 5. RAG Architecture

Relevant memories are retrieved before generating a reply, instead of sending the full conversation history every time.

---

## Internal Agent Flow

The expected internal workflow is:

```text
User message
    ↓
Classify intent and emotion
    ↓
Retrieve user memory + persona memory + conversation summary
    ↓
Generate safe response
    ↓
Decide whether to save new memory
    ↓
Update memory if needed