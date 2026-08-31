import json
import os


class CodebookService:

    def __init__(self):

        self.codebook = {}

        self.load()



    def load(self):

        # Get current file location:
        # backend/app/services/codebook_service.py

        current_dir = os.path.dirname(
            os.path.abspath(__file__)
        )


        # Go from:
        # backend/app/services
        #
        # back to:
        # ESS-AI-WebBot/data/codebook.json

        path = os.path.join(
            current_dir,
            "../../../data/codebook.json"
        )


        if os.path.exists(path):

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                self.codebook = json.load(file)


            print("✅ Codebook loaded:")
            print(path)


        else:

            print("❌ Codebook file not found:")
            print(path)



    def get_variable(self, name):

        return self.codebook.get(
            name.lower()
        )



codebook_service = CodebookService()