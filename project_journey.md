# 🧠 Developer's Log: The Building of Pulse AI

**Author:** Atharva Shinde (BCA2302297)
**Date:** April 2026
**Project:** Pulse AI: The Medical Explainer

---

## 🌱 The Origin

What started as a standard concept for a *"Medical Report Explainer and AI Prescription Reader"* evolved into something much bigger. The goal was simple on the surface: help patients understand their complex clinical data. But beneath the surface, the challenge was immense.

- How do you process sensitive medical data securely?
- How do you prevent an AI from hallucinating medical advice?
- How do you read a doctor's cursive handwriting?

---

## 🏗️ The Architecture Shift

The real breakthrough was realizing this couldn't just be a standard API wrapper. It needed an **Enterprise-Grade Hybrid Privacy Architecture.**

- **The Local Safe Zone:** The actual semantic search and vector storage (`all-MiniLM-L6-v2` + ChromaDB) happened entirely on local hardware.
- **The Cloud Engine:** Only anonymized, highly specific text chunks ever crossed the API gateway to the Groq LPUs (Llama 3.3 and Llama 4 Scout).

---

## 🔧 The "ENTERPRISE" Refinements

The project reached maturity during the final review phases leading up to the **April 30th internship conclusion.** Feedback from mentor pushed the system from a *"student project"* to a *"production-ready enterprise tool."* Three massive engineering hurdles were tackled:

### 1. 📄 The 20-Page "Blind Test" — Token Limits
Real hospitals don't generate neat 1-page PDFs. When faced with massive reports, the system initially struggled.

**The Fix:** 3500-character Header Truncation. By dynamically extracting just the metadata first and chunking the rest locally, the app became capable of handling enterprise-scale pathology reports without crashing.

### 2. 🌐 The Multilingual Prescription Bug — Selective Translation
A critical safety issue emerged: translating a prescription into Hindi also translated the **chemical names of drugs**, which could cause fatal errors at a pharmacy.

**The Fix:** A *Selective Translation Protocol* for the Vision Agent — it translates patient instructions for clarity, but strictly enforces English for medication names and dosages.

### 3. 🧠 The "Hallucination" Lock — Temperature & Grounding
AI models naturally want to give advice. In medicine, that's a liability.

**The Fix:** Global service temperature locked to `0.1` + strict **Context-Locked Prompts** = the **Zero-Hallucination Protocol.** If the diet advice wasn't in the PDF, Pulse AI wouldn't invent it.

---

## 🏁 The Finish Line

By late April, the messy terminal outputs and noisy `position_ids` warnings were silenced. The Streamlit UI was clean. The architecture diagrams were precise.

The tool was rebranded to **Pulse AI: The Medical Explainer.**

It wasn't just a script anymore — it was a **secure, scalable framework** ready for real-world application.

---

## 🔑 Key Technical Decisions Summary

| Challenge | Solution |
|---|---|
| Large PDF handling | 3500-char header truncation + local chunking |
| Drug name mistranslation | Selective Translation Protocol |
| AI hallucination risk | Temperature `0.1` + Context-Locked Prompts |
| Data privacy | Local vector search (ChromaDB) + anonymized cloud calls |
| Handwriting (prescriptions) | Vision Agent (Groq Llama 4 Scout) |

---

*Built as a BCA final internship project to solve the medical literacy gap for non-English speaking patients in India.*
