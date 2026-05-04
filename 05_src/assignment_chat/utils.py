from openai import OpenAI
from agent_framework_openai import OpenAIChatClient
from dotenv import load_dotenv
import os

load_dotenv()

def get_client(dev: bool = False):
    if dev:
        return OpenAI(api_key=os.getenv('DEV_KEY'))
    
    else:
        return OpenAI(base_url='https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1', 
                api_key='any value',
                default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')})
    
def get_agent_client(dev: bool=False):
    if dev:
        return  OpenAIChatClient(
        base_url="https://models.github.ai/inference/v1",
        api_key=os.environ["GITHUB_TOKEN"],
        model=os.getenv("GITHUB_MODEL", "openai/gpt-4.1-mini"),
    )
    else:
        return OpenAIChatClient(
            base_url='https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1', 
                api_key='any value',
                default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')},
                model="gpt-4o-mini"
        )
