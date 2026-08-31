import pandas as pd

from app.services.csv_service import csv_service
from app.services.data_analysis_service import analysis_service
from app.services.codebook_service import codebook_service


class CSVAIService:


    def remove_non_statistical_columns(self, df):

        numeric_df = df.select_dtypes(include="number")

        numeric_df = numeric_df[
            [
                col for col in numeric_df.columns
                if not any(
                    word in col.lower()
                    for word in [
                        "id",
                        "code",
                        "serial"
                    ]
                )
            ]
        ]

        return numeric_df



    def find_dataset(self, question):

        for dataset in csv_service.list_datasets():

            if dataset.lower() in question:

                return dataset

        return None



    def find_column(self, df, question):

        for column in df.columns:

            if column.lower() in question:

                return column

        return None



    def answer(self, question: str):

        question = question.lower()



        # =========================
        # List datasets
        # =========================

        if "dataset" in question and (
            "list" in question
            or "available" in question
            or "show" in question
        ):

            return {
                "answer":
                "Available datasets:\n\n"
                +
                "\n".join(
                    f"• {d}"
                    for d in csv_service.list_datasets()
                )
            }



        dataset = self.find_dataset(question)



        if dataset is None:

            return {
                "answer":
                "Please specify a valid dataset.\n\n"
                "Available datasets:\n"
                +
                "\n".join(
                    f"• {d}"
                    for d in csv_service.list_datasets()
                )
            }



        df = csv_service.get_dataset(dataset)



        # =========================
        # Count people / rows
        # =========================

        if (
            "count" in question
            or "row" in question
            or "record" in question
            or "people" in question
            or "number of" in question
            or "how many" in question
        ):


            result = analysis_service.count_rows(df)


            return {
                "answer":
                f"{dataset} contains "
                f"{result['total_records']} records."
            }





        # =========================
        # Unique values
        # =========================

        if "unique" in question:


            column = self.find_column(
                df,
                question
            )


            if column is None:

                return {
                    "answer":
                    "Please specify a valid column.\n\n"
                    "Available columns:\n"
                    +
                    "\n".join(
                        f"• {c}"
                        for c in df.columns
                    )
                }



            result = analysis_service.unique_values(
                df,
                column
            )


            return {
                "answer":
                f"Unique values of {column} "
                f"in {dataset} dataset:\n\n"
                +
                ", ".join(
                    map(
                        str,
                        result["values"]
                    )
                )
                +
                f"\n\nTotal unique values: "
                f"{result['total_unique']}"
            }





        # =========================
        # Average
        # =========================

        if "average" in question:


            column = self.find_column(
                df,
                question
            )


            if column is None:

                return {
                    "answer":
                    "Please specify a valid column."
                }


            result = analysis_service.average(
                df,
                column
            )


            return {
                "answer":
                f"The average {column} "
                f"in {dataset} is "
                f"{result['average']}."
            }





        # =========================
        # Maximum
        # =========================

        if (
            "maximum" in question
            or "max" in question
        ):


            column = self.find_column(
                df,
                question
            )


            if column:


                result = analysis_service.max_value(
                    df,
                    column
                )


                return {
                    "answer":
                    f"The maximum {column} "
                    f"in {dataset} is "
                    f"{result['maximum']}."
                }



            numeric_df = self.remove_non_statistical_columns(df)


            if numeric_df.empty:

                return {
                    "answer":
                    "No numeric columns found."
                }



            values = numeric_df.max()


            column = values.idxmax()


            return {
                "answer":
                f"The maximum value in {dataset} "
                f"is {values[column]} "
                f"(column: {column})."
            }





        # =========================
        # Minimum
        # =========================

        if (
            "minimum" in question
            or "min" in question
        ):


            column = self.find_column(
                df,
                question
            )


            if column:

                result = analysis_service.min_value(
                    df,
                    column
                )


                return {
                    "answer":
                    f"The minimum {column} "
                    f"in {dataset} is "
                    f"{result['minimum']}."
                }




            numeric_df = self.remove_non_statistical_columns(df)


            column = numeric_df.min().idxmin()


            return {
                "answer":
                f"The minimum value in {dataset} "
                f"is {numeric_df[column].min()} "
                f"(column: {column})."
            }





        # =========================
        # Variable profile
        # =========================

        column = self.find_column(
            df,
            question
        )


        if column:


            info = analysis_service.variable_profile(
                df,
                column
            )


            codebook = codebook_service.get_variable(
                column
            )


            answer = (
                f"{column}\n\n"
            )


            if codebook:

                answer += (
                    "Description:\n"
                    +
                    codebook["description"]
                    +
                    "\n\n"
                )


            answer += (
                f"Data type: {info['data_type']}\n"
                f"Missing values: {info['missing']}\n"
                f"Unique values: {info['unique']}"
            )


            if "minimum" in info:

                answer += (
                    f"\nMinimum: {info['minimum']}"
                    f"\nMaximum: {info['maximum']}"
                    f"\nAverage: {info['average']:.2f}"
                    f"\nMedian: {info['median']}"
                )


            return {
                "answer": answer
            }




        return {
            "answer":
            "Sorry, I couldn't understand your CSV question."
        }



csv_ai_service = CSVAIService()