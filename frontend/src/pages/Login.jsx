import {useState} from "react";
import {loginUser} from "../services/auth";
import {useNavigate} from "react-router-dom";
import "../styles/Login.css";
import {Link} from "react-router-dom";

function Login(){

    const [email,setEmail] = useState("");
    const [password,setPassword] = useState("");

    const navigate = useNavigate();


    async function handleLogin(e){

        e.preventDefault();

        try{

            await loginUser(
                email,
                password
            );


            alert("Login successful 🎉");

            navigate("/");


        }catch(error){

            alert(
              "Login failed. Check email or password"
            );

        }

    }


    return(

        <div className="login-container">

            <form
              className="login-box"
              onSubmit={handleLogin}
            >

                <h2>
                    🤖 ESS AI Assistant
                </h2>


                <p>
                    Login to save your chat history
                </p>


                <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={
                    e=>setEmail(e.target.value)
                }
                />


                <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={
                    e=>setPassword(e.target.value)
                }
                />


                <button>
                    Login
                </button>
<Link to="/register">

Create new account

</Link>


<Link to="/">

Continue as Guest 👤

</Link>

            </form>

        </div>

    );

}


export default Login;