---
Grading Notes
ML - 70 points max, 15 items max
Following Directions - 20 points max
Project Cohesion and Motivation - 20 points max
---

# Pokepedai

The general idea is a pokemon chat bot. If I wanted to make it cooler, could add an upload image to identify a pokemon, but that an extension I don't think I have to do. 

## Point Plan

### ML (70, from 15 items)
- [ ] (10) Solo Project
- [ ] (10) Functional Web Application with UI
- [ ] (10) Deployment with rate limiting?/monitoring?/caching?, error handling, logging
- [ ] (10) RAG system 
- [ ] (10) Constructed data set through web scraping, manual annotation/labeling, custom curration
- [ ] (7) System guardrails against toxicity or inappropriate use employing at least two techniques (e.g., fine-tuning, system prompt, toxicity classifier, etc.) with evidence of impact 
- [ ] (5) Conducted ablation study demonstrating impact of at least two design choices with quantitative comparison (5 pts)
  - basically use this to explain why you used RAG / SFT
- [ ] (5) Compared multiple model architectures or approaches quantitatively (5 pts)
  - bert vs sentence tokenizer
  - which chatgpt model

- Built multi-turn conversation system with context management and history tracking (7 pts)??

- some of these overlap with other ones (i.e. sentence embedding matching, system prompts ...)
  - Applied prompt engineering with evaluation of multiple prompt designs (evidence: comparison table) (3 pts)
    - In this, maybe? Applied in-context learning with few short examples or chain of thought prompting (5 pts)
  - Used sentence embeddings for semantic similarity or retrieval (5 pts)
  - Used or fine-tuned a transformer language model (7 pts)

### Following Direction (20)
- [ ] (3) Submit assigment on time
- [ ] (3) Self Assessment
- [ ] (2) Setup.md
- [ ] (2) Attribution.md
- [ ] (2) requirements.txt / environment .yml
- [ ] (2) Demo video
- [ ] (2) Technical walkthrough
- [ ] (1) What it Does
- [ ] (1) Quick Start
- [ ] (1) Video Links
- [ ] (1) Evaluation

### Project Cohesion and Motivation (20)
- [ ] (3) Readme states unified project goal
- [ ] (3) Demo video effectively communicates why project matter
- [ ] (3) Project addresses a real world problem
- [ ] (3) Technical walkthrough show synergy in components
- [ ] (3) Project show progression from problem - approach - solution - evaluation
- [ ] (3) Design choices explicitly justified
- [ ] (3) Evaluation metrics directly measure stated project objectives
- [ ] (3) None of the major components awarded rubric items are superflous to larger goal of project
- [ ] (3) Clean codebase with readable code

Need 7/9 for full points

## Plan

### Part 1: Implement a RAG system for retriving pokemon information

#### Web Scraping and Labeling Pokemon Set

#### Connect to OpenAI GPT AI

### Part 2: Improve Answering Questions

#### Supervise-Fine Tune for Most Common Questions

#### Improve System Prompt - Prevent Bad Actors

### Part 3: Create Website 

#### Rate Limiting

#### Error Handling

### Part 4: CNN Pokemon Recognition from Image?? (if needed)

## Submission Requirements

- [ ] Repository
  - Required Files (Top Level)
    - README.md
      - Project Title and short 1-3 description of what it is
      - What it Does
        - One paragraph of what ur project does
      - Quick Start
        - How to run your project (but short)
      - Video Links
        - links to demo and walkthrough
      - Evaluation 
        - any quantitative results, accuracy metrics, or qualitative outcomes from testing
    - SETUP.md
      - clear installation and setup instructions for running your project
      - basically make it so a grader can run ur project themselves
    - ATTRIBUTION.md
      - AI generated code, external libraries, datasets ...
  - Directory Structure 
    - /src
      - any code not in jupytr notebooks
    - /data
      - data files or data access scripts
    - /models
      - any trained models, model figures, model learning scripts
    - /notebooks
      - any jupytr notebooks
    - /videos
      - demo and walkthrough
    - /docs
      - any additional documentation other than the required ones
    -   environment.yml / txt
      - dependency management
- [ ] Project Demo
  - 3-5 min
  - What project does and why it matters to a non coder
  - Include in repo and linked in README
- [ ] Technical Walkthrugh
  - 5-10 min
  - How code works / where ml concepts are applied
  - What parts are challenging / the main technical parts
  - Include in repo and linked in README