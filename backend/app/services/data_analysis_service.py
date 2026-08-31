import pandas as pd



class DataAnalysisService:


    # ======================================
    # DATASET SUMMARY
    # ======================================

    def dataset_summary(self, df):

        return {

            "rows": len(df),

            "columns": list(df.columns)

        }



    # ======================================
    # UNIQUE VALUES
    # ======================================

    def unique_values(self, df, column):


        if column not in df.columns:

            return {

                "error":
                f"Column '{column}' was not found.",

                "available_columns":
                list(df.columns)

            }



        values = (

            df[column]

            .dropna()

            .astype(str)

            .unique()

            .tolist()

        )


        return {

            "column": column,

            "values": values[:50],

            "total_unique": len(values)

        }




    # ======================================
    # AVERAGE
    # ======================================

    def average(self, df, column):


        if column not in df.columns:

            return {

                "error":
                f"Column '{column}' was not found."

            }



        numeric = pd.to_numeric(
            df[column],
            errors="coerce"
        )


        return {

            "column": column,

            "average":
            float(numeric.mean())

        }




    # ======================================
    # MEDIAN
    # ======================================

    def median(self, df, column):


        if column not in df.columns:

            return {

                "error":
                f"Column '{column}' was not found."

            }



        numeric = pd.to_numeric(
            df[column],
            errors="coerce"
        )


        return {

            "column": column,

            "median":
            float(numeric.median())

        }




    # ======================================
    # ROW COUNT
    # ======================================

    def count_rows(self, df):

        return {

            "total_records":
            len(df)

        }





    # ======================================
    # MAX VALUE
    # ======================================

    def max_value(self, df, column=None):


        # No column provided
        # Search all numeric columns

        if column is None:


            numeric_df = df.apply(
                pd.to_numeric,
                errors="coerce"
            )


            max_column = (
                numeric_df.max()
                .idxmax()
            )


            maximum = (
                numeric_df[max_column]
                .max()
            )


            return {

                "column":
                max_column,

                "maximum":
                float(maximum)

            }




        if column not in df.columns:

            return {

                "error":
                f"Column '{column}' was not found.",

                "available_columns":
                list(df.columns)

            }



        numeric = pd.to_numeric(

            df[column],

            errors="coerce"

        )


        index = numeric.idxmax()



        return {


            "column":

            column,


            "maximum":

            float(
                numeric.max()
            ),


            "row":

            df.loc[index]
            .fillna("")
            .to_dict()

        }





    # ======================================
    # MIN VALUE
    # ======================================

    def min_value(self, df, column):


        if column not in df.columns:

            return {

                "error":
                f"Column '{column}' was not found."

            }



        numeric = pd.to_numeric(

            df[column],

            errors="coerce"

        )


        index = numeric.idxmin()



        return {

            "column":

            column,


            "minimum":

            float(
                numeric.min()
            ),


            "row":

            df.loc[index]
            .fillna("")
            .to_dict()

        }





    # ======================================
    # VARIABLE PROFILE
    # ======================================

    def variable_profile(self, df, column):


        if column not in df.columns:

            return {

                "error":
                f"Column '{column}' was not found."

            }



        data = df[column]


        result = {


            "column":

            column,


            "data_type":

            str(
                data.dtype
            ),


            "missing":

            int(
                data.isna().sum()
            ),


            "unique":

            int(
                data.nunique()
            )

        }




        numeric = pd.to_numeric(

            data,

            errors="coerce"

        )



        if numeric.notna().any():


            result.update({

                "minimum":

                float(
                    numeric.min()
                ),


                "maximum":

                float(
                    numeric.max()
                ),


                "average":

                float(
                    numeric.mean()
                ),


                "median":

                float(
                    numeric.median()
                )

            })



        return result





analysis_service = DataAnalysisService()