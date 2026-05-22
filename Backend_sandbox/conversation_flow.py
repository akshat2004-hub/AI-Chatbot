class ConversationManager:
    def __init__(self):
        self.state = "GREETING"
        self.user_data = {}

    def next_step(self, user_input):
        if self.state == "GREETING":
            self.state = "INTENT"
            return "Hi 👋 What are you looking to build today?"

        elif self.state == "INTENT":
            if "mobile" in user_input.lower():
                self.state = "TECH_SELECTION"
                return {
                    "text": "Great choice 🚀 Mobile Apps!",
                    "options": [
                        "⚡ Flutter – Fast & scalable",
                        "🔥 React Native – Cost-efficient",
                        "🤔 Something else"
                    ]
                }

        elif self.state == "LEAD_NAME":
            self.user_data["name"] = user_input
            self.state = "LEAD_EMAIL"
            return "Nice to meet you! Where should we send your project plan? 📩"

        # continue same pattern...class ConversationManager:
    def __init__(self):
        self.state = "GREETING"
        self.user_data = {}

    def next_step(self, user_input):
        if self.state == "GREETING":
            self.state = "INTENT"
            return "Hi 👋 What are you looking to build today?"

        elif self.state == "INTENT":
            if "mobile" in user_input.lower():
                self.state = "TECH_SELECTION"
                return {
                    "text": "Great choice 🚀 Mobile Apps!",
                    "options": [
                        "⚡ Flutter – Fast & scalable",
                        "🔥 React Native – Cost-efficient",
                        "🤔 Something else"
                    ]
                }

        elif self.state == "LEAD_NAME":
            self.user_data["name"] = user_input
            self.state = "LEAD_EMAIL"
            return "Nice to meet you! Where should we send your project plan? 📩"

        # continue same pattern...
