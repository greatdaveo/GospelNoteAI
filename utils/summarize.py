import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def split_transcript(text:str, max_chars: int = 3000) -> list[str]:
    chunks = []
    current = ""
    for paragraph in text.split("\n"):
        if len(current) + len(paragraph) < max_chars:
            current += paragraph + "\n"
        else:
            chunks.append(current.strip())
            current = paragraph + "\n"
    if current:
        chunks.append(current.strip())

    return chunks


def generate_summary(transcript: str)-> list[str]:
    all_summary_lines = []
    chunks = split_transcript(transcript)

    for idx, chunk in enumerate(chunks):
        prompt = (
            f"""
            You are a gospel sermon note writer and summarizer. 
            
            Note the following points
            
            Based on the transcript:
            - Don't form or improvise your own words, write based on the transcript you have received.
            - Your task is to extract the key points from the following sermon transcript. 
            - Return bullet points that clearly summarize the main preaching or teaching, 
            - Highlight the Bible verses mentioned for each bullet points, and anyone mentioned separately.
            - Take note of the words; chapter, verses or verse, to, etc and correct them into a real bible verse the preacher meant.
            - If no bible verse is mentioned, don't mention by yourself 
            - Let your point not be the preacher said, no but make it expressive like, for example:
                - The way of the lord is... (Genesis 1:1) 
                - There are two types of .... (Exodus (1:1)
            - Highlight each headings or subheadings mentioned (where necessary)
            - If the preacher uses a bible verse to back up their point, please include it after you have written the key point.
            
            -If what you received is not related to a church sermon, just make it known that this is not a sermon or of God.            
            
            Sermon Transcript (Part {idx+1} of {len(chunks)})
            {chunk}
                       
            You can now summarize:
            """
        )


        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a church member that take note and summarizes sermon"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature = 0.7,
                max_tokens = 1200,
            )

            output = response.choices[0].message.content.strip()
            summary_lines = [
                line.strip("•- \n") for line in output.split("\n") if line.strip()
            ]

            print(f"PART {idx+1} Summary: ", summary_lines)

            all_summary_lines.extend(summary_lines)

        except Exception as e:
            raise  Exception(f"Error generating sermon summary part {idx+1}: {str(e)}")

    return  all_summary_lines
