import os, json, anthropic
from utils import ANTHROPIC_API_KEY

class TravelDb:
    def __init__(self):
        self.cars = {
            "toronto": [
                {"id": "a1", "model": "honda civic 2022"},
                {"id": "a2", "model": "honda civic 2022"},
                {"id": "a3", "model": "honda civic 2022"}
            ]
        }
        self.bookings = {}
        self.faq = open("car_rental_faq.md").read()

    def list_car_rental(self, location: str, time: str):
        if location.lower() not in self.cars:
            return f"we have no stocks of cars at {location}"
        return self.cars[location.lower()]

    def get_car_rental(self, car_id):
        if car_id not in self.bookings:
            return f"we have no booking for id {car_id}"
        return self.bookings[car_id]
    
    def book_car_rental(self, car_id):
        self.bookings[car_id] = True

    def cancel_car_rental(self, car_id):
        self.bookings[car_id] = False

    def get_faq(self):
        return self.faq

    def change_car_rental(self, car_id, new_car_id):
        self.cars[new_car_id] = self.cars[car_id]
        del self.cars[car_id]

    def has_side_effect(self, tool_name):
        return tool_name in [
            "book_car_rental",
            "cancel_car_rental"
        ]

    def tools_call(self, tool_name, tool_input):
        if tool_name == "list_car_rental":
            return self.list_car_rental(tool_input["location"], tool_input["time"])
        elif tool_name == "get_car_rental":
            return self.get_car_rental(tool_input["car_id"])
        elif tool_name == "book_car_rental":
            return self.book_car_rental(tool_input["car_id"])
        elif tool_name == "cancel_car_rental":
            return self.cancel_car_rental(tool_input["car_id"])

    def tools(self):
        return [
            {
                "name": "list_car_rental",
                "description": "List car rental info",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string"},
                        "location": {"type": "string"},
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_car_rental",
                "description": "Get car rental info",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "car_id": {"type": "string"}
                    },
                    "required": ["car_id"]
                }
            },
            {
                "name": "book_car_rental",
                "description": "Book a car rental",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "car_id": {"type": "string"}
                    },
                    "required": ["car_id"]
                }
            },
            {
                "name": "cancel_car_rental",
                "description": "Cancel a car rental",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "car_id": {"type": "string"}
                    },
                    "required": ["car_id"]
                }
            },
            {
                "name": "faq",
                "description": "Answer a question based on the FAQ",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        ]


class SomeCarRentalAi:
    def __init__(self):
        self.db = TravelDb()
        self.msgs = []
        self.model = "claude-3-5-haiku-latest"
        self.max_tokens = 2000
        self.temperature = 0.1
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def reset(self):
        self.msgs = []
        self.db = TravelDb()
        
    # wait for user input
    def get_confirmation(self, query):
        user_input = input(query)
        if user_input.lower().strip() in ["yes", "y", "yey"]:
            return True
        else:
            return False

    def simple_faq_query(self, query):
        faq = self.db.get_faq()
        sys_prompt = f"""
        You are a helpful assistant that can answer questions about the car rental FAQ.
        Here is the FAQ:
        {faq}
        """

        user_prompt = f"""
        Please answer the following question based on the provided FAQ. 
        If you don't know the answer, or are not sure, say "I don't know".
        
        {query}
        """

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=sys_prompt,
            messages=[
                {"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    def query(self, query):
        if query:
            self.msgs.append({
                "role": "user",
                "content": query
            })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=self.msgs,
            tools=self.db.tools()
        )

        if response.stop_reason == "tool_use":
            tool_use = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use.name
            tool_input = tool_use.input

            if self.db.has_side_effect(tool_use.name):
                wait_for_confirmation = self.get_confirmation(f"Are you sure you want to {tool_use.name} {tool_input}?")
                if not wait_for_confirmation:
                    return

            print(f"calling {tool_name} with {tool_input}")
            self.msgs.append({
                "role": "assistant",
                "content": response.content
            })

            if tool_name == "faq":
                response = self.simple_faq_query(tool_input["query"])
            else:
                response = self.db.tools_call(tool_name, tool_input)
            print(f"calling {tool_name} with {tool_input}, got: {response}")

            self.msgs.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(response)
                    }
                ]
            })

            return self.query(None)
        
        final_response = next((block.text for block in response.content if hasattr(block, "text")), None)
        print(final_response)
        return final_response
