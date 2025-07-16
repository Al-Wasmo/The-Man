
from google import genai
from utils import env
import utils


# used to automate some model prompting and debugging
class Model:
    def __init__(self):
        self.client =  genai.Client(api_key=env["gemini_api_key"])

    def do(self,text):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=text
        )        

        timestamp = utils.get_timestamp()
        with open("output/model/" + timestamp,"w") as f:
            f.write("prompt:\n") 
            f.write(text+"\n\n") 
            f.write("response:\n") 
            f.write(response.text) 

        return response.text

