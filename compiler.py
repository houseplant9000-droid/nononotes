import os, requests, time
from bs4 import BeautifulSoup
from groq import Groq

GROQ_KEY = os.environ["GROQ_KEY"]
client = Groq(api_key=GROQ_KEY)

with open("queue.txt") as f:
    queue = [l.strip() for l in f if l.strip()]

if not queue:
    print("Queue empty")
    exit()

task = queue[0]
with open("queue.txt", "w") as f:
    f.write("\n".join(queue[1:]))

book_id, surah, ayah = map(int, task.split("|"))
print(f"Processing book {book_id}, {surah}:{ayah}")

def fetch(book_id, start, count=10):
    text = ""
    for p in range(start, start + count):
        try:
            r = requests.get(f"https://shamela.ws/book/{book_id}/{p}", timeout=10)
            s = BeautifulSoup(r.text, "html.parser")
            nass = s.find("div", class_="nass")
            if nass:
                text += f"\n--- p{p} ---\n" + nass.get_text(separator="\n", strip=True)
            time.sleep(0.15)
        except: pass
    return text

text = fetch(book_id, 40, 15)
if not text:
    print("No text"); exit()

response = client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[
        {"role": "system", "content": "Extract every distinct point. Do not summarize. Structure as readable notes."},
        {"role": "user", "content": f"Compile tafsir notes for {surah}:{ayah}:\n\n{text[:3500]}"}
    ],
    max_tokens=1000
)

note = response.choices[0].message.content
os.makedirs("notes", exist_ok=True)
with open(f"notes/{surah}_{ayah}.md", "w", encoding="utf-8") as f:
    f.write(note)
print(f"Saved notes/{surah}_{ayah}.md")
