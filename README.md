# Emotion Flow Analyzer

A Python website that analyzes emotion sentence by sentence and shows:

- an emoji timeline
- transition detection between sentences
- an emotional journey map
- a fingerprint summary of the full text

## Project Files

- [app.py](C:\Users\HP\Documents\New project\app.py)
- [requirements.txt](C:\Users\HP\Documents\New project\requirements.txt)

## Step-by-Step Setup

### 1. Open the project folder

In PowerShell:

```powershell
cd "C:\Users\HP\Documents\New project"
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate it

```powershell
.venv\Scripts\activate
```

### 4. Install packages

```powershell
pip install -r requirements.txt
```

### 5. Run the website

```powershell
streamlit run app.py
```

### 6. Open it in your browser

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

## How It Works

1. You paste text into the input box.
2. The app splits the text into sentences using NLTK.
3. A local Python classifier scores each sentence across multiple emotions.
4. The app renders:
   - sentence-level results
   - emoji timeline
   - transition cards
   - journey charts
   - fingerprint summary

## Notes

- This version avoids heavy `torch` dependencies so it runs more reliably on Windows.
- If you want, we can later switch back to a transformer model after your environment is stable.
