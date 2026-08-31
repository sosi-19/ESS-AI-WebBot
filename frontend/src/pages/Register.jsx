import {useState} from "react";
import {registerUser} from "../services/auth";
import {useNavigate} from "react-router-dom";


function Register(){

const navigate = useNavigate();


const [name,setName]=useState("");
const [email,setEmail]=useState("");
const [password,setPassword]=useState("");



async function handleRegister(e){

e.preventDefault();


try{


await registerUser(
name,
email,
password
);


alert("Account created 🎉");

navigate("/login");


}
catch(error){

alert("Registration failed");

}


}



return(

<div className="login-container">


<form 
className="login-box"
onSubmit={handleRegister}
>


<h2>
Create Account
</h2>


<input
placeholder="Full Name"
value={name}
onChange={
e=>setName(e.target.value)
}
/>


<input
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
Register
</button>


</form>


</div>


)


}


export default Register;