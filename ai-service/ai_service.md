🌾 AGRICHAIN – AI Decision Engine (Backend Service)

📌 Overview



This module is the AI backend service for the AGRICHAIN platform.

It provides intelligent, role-based agricultural decision support using:



📈 Price Prediction Model



🌱 Yield Estimation Model



🤖 LLM-powered Explanation Engine (Gemini)



🌍 Multilingual Output Support



⚖ Deterministic Decision + Confidence Logic



The system separates numeric logic (backend-controlled) from AI explanation (LLM-controlled) for reliability and production safety.



🏗 Architecture

Frontend (Swagger / Web App)

&nbsp;       ↓

FastAPI Backend

&nbsp;       ↓

Role Router

&nbsp;       ↓

---------------------------------

| Price Model (Forecasting)     |

| Yield Model (Estimation)      |

| Decision + Confidence Logic   |

---------------------------------

&nbsp;       ↓

LLM Engine (Explanation Only)

&nbsp;       ↓

Final Structured Response

🔐 Important Design Principle



Backend calculates:



Price delta



Decision



Confidence score



LLM only explains reasoning



LLM cannot override numeric values



⚙️ Features

1️⃣ Price Prediction



Forecasts next market price



Computes weekly average



Calculates % price change



2️⃣ Yield Estimation



Based on:



Land size



Soil quality



Rainfall



3️⃣ Decision Logic (Deterministic)



For Farmer role:



Price Delta	Decision

> 5%	SELL

2% – 5%	SELL WITH CAUTION

≤ 2%	HOLD



Other roles:



MAINTAIN



4️⃣ Confidence Score Logic

Absolute Delta	Confidence

≥ 8%	90%

≥ 5%	80%

≥ 3%	70%

≥ 1%	60%

< 1%	50%

5️⃣ Multilingual Support



Supported languages:



English (en)



Tamil (ta)



Hindi (hi)



Telugu (te)



Malayalam (ml)



Kannada (kn)



Decision output is translated automatically

