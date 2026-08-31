function Message({ role, text, sources }) {

  return (
    <div className={`message ${role}`}>

      <p>{text}</p>


      {Array.isArray(sources) && sources.length > 0 && (

        <div className="sources">

          <strong>Sources:</strong>


          {sources.map((source, index) => {


            // Object source from backend
            if (typeof source === "object" && source !== null) {


              const document =
                source.document || "Unknown source";


              const category =
                source.category || "Source";


              const page =
                source.page;


              const distance =
                source.distance;



              const isCsv =
                category.toLowerCase() === "csv";



              return (

                <div
                  key={index}
                  className="source-item"
                >


                  <div className="source-title">

                    {isCsv ? "📊" : "📄"}

                    {" "}

                    {document}

                  </div>



                  <div className="source-details">


                    <span>
                      Category: {category}
                    </span>



                    {page && (

                      <span>
                        {" | "}
                        Page: {page}
                      </span>

                    )}



                    {distance && (

                      <span>
                        {" | "}
                        Match: {(1 - distance).toFixed(2)}
                      </span>

                    )}


                  </div>


                </div>

              );

            }



            // If source is plain text

            return (

              <div
                key={index}
                className="source-item"
              >

                📄 {source}

              </div>

            );


          })}


        </div>

      )}


    </div>
  );
}


export default Message;
