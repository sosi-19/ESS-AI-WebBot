import axios from "axios";

const API_URL = "http://localhost:8000";


export async function loginUser(email, password) {

    const response = await axios.post(
        `${API_URL}/auth/login`,
        {
            email: email,
            password: password
        }
    );

    localStorage.setItem(
        "token",
        response.data.access_token
    );

    return response.data;
}



export async function registerUser(
    full_name,
    email,
    password
) {

    const response = await axios.post(
        `${API_URL}/auth/register`,
        {
            full_name,
            email,
            password
        }
    );

    return response.data;
}



export function logoutUser(){

    localStorage.removeItem("token");

}



export function getToken(){

    return localStorage.getItem("token");

}