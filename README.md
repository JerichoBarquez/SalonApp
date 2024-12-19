RetellAI - Phone Agent for The Color Bar Salon

Steps to run in localhost
1. First install dependencies
   pip3 install -r requirements.txt
2. Create .env for your API keys.
   OPENAI_API_KEY - need to create an account in OpenAI
   OPENAI_ORGANIZATION_ID - it is available once you created your openai account
   OPENAI_LLM_MODEL - in my case, i used gpt-3.5-turbo.
   RETELL_API_KEY - need to create retell ai account to get the api key
3. In another bash, use ngrok to expose this port to public network
   ngrok http 8080
4. Start the websocket server/python app in your IDE
   uvicorn app.server:app --reload --port=8080
5. In retell ai account, I selected the custom LLM. Ngrok will provide the URL to be entered in Retell AI LLM URL.
   I used the retell AI to test my agent instead. I was not able to use the https://github.com/RetellAI for my custom LLM agent. I was only able to use and test it when i am using the single prompt agent.
   Websocket URL should be something like this. wss://XXXXXXX.ngrok-free.app/llm-websocket
   
