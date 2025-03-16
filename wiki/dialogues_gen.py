import os
import re
from openai import OpenAI

# New prompt template for conversation generation

CONVERSATION_PROMPT ="""

Create a natural and engaging Persian (Farsi) conversation between two individuals by incorporating the provided elements as follows:

Title: Establishes the overall theme or subject of the conversation.  
Text: Provides background information or context to guide the dialogue’s development.  
Dialogue Style: Defines the tone, formality, and manner of speech, ensuring consistency in the interaction.  
Dialogue Starter: Serves as the initial exchange to set the conversation in motion.  

The conversation should flow smoothly, feel authentic and culturally appropriate, and maintain logical coherence throughout.  

### **Inputs:**  
- **Title:** "{title}"  
- **Text:** "{text}"  
- **Dialogue Style (English):** "{selected_style}"  
- **Dialogue Starter (Persian):** "{selected_starter}"  

### **Instructions:**  
To successfully complete this task, follow these structured steps:  

1. **Extract Key Information**  
   - Identify 2-3 key ideas from the **Title** and **Text** to shape the conversation.  
   - Ensure that all newly generated dialogue is strictly derived from the given **Text** and does not introduce unrelated information.  

2. **Define Characters**  
   - Create two personas that match the selected **Dialogue Style**.  

3. **Construct the Conversation**  
   - Start with the given Persian dialogue starter:  
     **"{selected_starter}"**  
   - Generate at least six exchanges (each turn = one response per character).  
   - Maintain a natural, logical, and engaging flow.  
   - If relevant, incorporate questions, disagreements, or problem-solving.  
   - Ensure all statements, opinions, and discussions originate from the **Text** provided.  

4. **Ensure Persian Cultural Authenticity**  
   - Use natural spoken Farsi, incorporating common Persian expressions and polite norms.  

5. **Provide a Meaningful Conclusion**  
   - End with either a logical resolution or a prompt for further discussion.  

6. **Output Format (JSON)**  
   - Provide the conversation in a valid JSON format, without any additional content.  
   - The text should be entirely in Farsi (Persian).  
   - Maintain logical coherence and consistency in the conversation.  
   - Do not include any English commentary.  

### **Expected JSON Output Format:**  

```json
{{
  "conversation": [
    {{
      "speaker": "شخص اول",
      "text": "{selected_starter}"
    }},
    {{
      "speaker": "شخص دوم",
      "text": "{{response_1}}"
    }},
    ...
  ]
}}
"""



def generate_conversation(text, title, selected_style, selected_starter):
    """Generates a conversation based on the given input parameters."""
    prompt = CONVERSATION_PROMPT.format(
        text=text, title=title, selected_style=selected_style, selected_starter=selected_starter
    )

    api_key = 

    client = OpenAI(api_key=api_key)

    messages = [
        {"role": "system", "content": "You are a conversational AI assistant."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
        n=1
    )
    response_text = response.choices[0].message.content.strip()
    return response_text 
