import os
import pandas as pd


class CSVService:

    def __init__(self):
        self.datasets = {}
        self.load_all()


    def load_all(self):

        base_path = "../data/csv"

        for root, dirs, files in os.walk(base_path):

            for file in files:

                if file.endswith(".csv"):

                    path = os.path.join(root, file)

                    name = file.replace(".csv", "").lower()

                    try:

                        self.datasets[name] = pd.read_csv(
                            path,
                            low_memory=False
                        )

                        print(f"Loaded {name}")

                    except Exception as e:

                        print(
                            f"Failed loading {name}: {e}"
                        )


    def list_datasets(self):

        return list(self.datasets.keys())


    def get_dataset(self, name):

        name = name.lower()

        return self.datasets.get(name)



    # ==========================================
    # DATASET INFO
    # ==========================================

    def get_info(self, name):

        df = self.get_dataset(name)


        if df is None:

            return {
                "answer":
                f"Dataset '{name}' not found.\n\n"
                "Available datasets:\n"
                +
                "\n".join(
                    f"• {x}"
                    for x in self.list_datasets()
                )
            }



        return {

            "answer":
            f"{name} contains {len(df)} records "
            f"with {len(df.columns)} columns.",

            "rows": len(df),

            "columns":
            list(df.columns)
        }



    # ==========================================
    # ROW COUNT
    # ==========================================

    def get_row_count(self, name):

        df = self.get_dataset(name)


        if df is None:

            return {
                "answer":
                "Dataset not found."
            }


        return {

            "answer":
            f"{name} contains {len(df)} records."

        }



    # ==========================================
    # COLUMNS
    # ==========================================

    def get_columns(self, name):

        df = self.get_dataset(name)


        if df is None:

            return []


        return list(df.columns)



    # ==========================================
    # UNIQUE VALUES
    # ==========================================

    def get_unique_values(
        self,
        dataset_name,
        column
    ):


        df = self.get_dataset(dataset_name)


        if df is None:

            return {
                "answer":
                "Dataset not found."
            }



        if column not in df.columns:

            return {

                "answer":
                f"Column '{column}' not found.\n\n"
                "Available columns:\n"
                +
                "\n".join(
                    f"• {c}"
                    for c in df.columns
                )

            }



        values = (
            df[column]
            .dropna()
            .unique()
            .tolist()
        )


        return {

            "answer":
            f"Unique values of '{column}' "
            f"in {dataset_name}:\n\n"
            +
            "\n".join(
                f"• {v}"
                for v in values[:50]
            )

        }



    # ==========================================
    # MAX VALUE
    # ==========================================

    def get_max_value(
        self,
        dataset_name,
        column=None
    ):


        df = self.get_dataset(dataset_name)


        if df is None:

            return {

                "answer":
                "Dataset not found."

            }



        # automatic numeric search

        if column is None:


            numeric = df.select_dtypes(
                include="number"
            )


            if numeric.empty:

                return {

                    "answer":
                    "No numeric columns found."

                }



            result = numeric.max().idxmax()

            value = numeric[result].max()


            return {

                "answer":
                f"The maximum value in {dataset_name} "
                f"is {value} from column '{result}'."

            }




        if column not in df.columns:

            return {

                "answer":
                f"Column '{column}' not found."

            }



        value = df[column].max()


        return {

            "answer":
            f"The maximum value of '{column}' "
            f"in {dataset_name} dataset is {value}."

        }



# Create service

csv_service = CSVService()



