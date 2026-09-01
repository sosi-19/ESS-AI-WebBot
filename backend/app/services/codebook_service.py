import json
import os


class CodebookService:

    def __init__(self):

        self.codebook = {}

        self.load()


    def load(self):

        # -------------------------------------------------
        # Project structure:
        #
        # ESS-AI-WebBot/
        # ├── backend/
        # │   └── app/
        # │       └── services/
        # │           └── codebook_service.py
        # └── data/
        #     └── codebook.json
        #
        # Docker:
        # /app/
        # ├── app/
        # └── data/
        # -------------------------------------------------

        current_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        # Try the project path first
        local_path = os.path.abspath(
            os.path.join(
                current_dir,
                "../../../data/codebook.json"
            )
        )

        # Docker path
        docker_path = "/app/data/codebook.json"

        if os.path.exists(local_path):

            path = local_path

        elif os.path.exists(docker_path):

            path = docker_path

        else:

            print("❌ Codebook file not found:")
            print("Tried:")
            print(local_path)
            print(docker_path)

            return


        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                self.codebook = json.load(file)


            print("✅ Codebook loaded:")
            print(path)


        except Exception as e:

            print("❌ Failed to load codebook:")
            print(e)


    def get_variable(self, name):

        return self.codebook.get(
            name.lower()
        )


codebook_service = CodebookService()