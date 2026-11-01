import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "./api";

export default function Login() {
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await login(correo, password);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("rol", data.rol);
      navigate("/");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div data-theme="emerald" className="hero min-h-screen bg-[#F6F7F9] flex items-center justify-center p-4">
      
      <div className="w-full h-[28rem] max-w-4xl bg-base-100 shadow-2xl rounded-2xl overflow-hidden flex flex-col md:flex-row">
        
        
        <div className="w-full md:w-1/2 bg-[#248C7E] flex flex-col items-center  p-8 text-primary">
          <h2 className="text-xl font-bold text-center !mt-[6%]">BIENVENIDO</h2>
          <img className="mt-[19%]" src="../public/field.svg"></img>
        </div>

        
        <div className="w-full md:w-1/2 p-8 flex flex-col justify-center">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <h2 className=" !text-[#37313B] !mb-[8%] ">Iniciar Sesión</h2>

            <label className="label font-medium">Email</label>
            <input 
              type="email" 
              className="input input-bordered w-full"
              placeholder="nombre@correo.edu.uy" 
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              required
            />

            <label className="label font-medium">Password</label>
            <input 
              type="password" 
              className="input input-bordered w-full" 
              placeholder="********" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <button type="submit" className="btn btn-neutral mt-4 w-full">Entrar</button>
            
            {error && <p className="text-error text-sm mt-2">{error}</p>}
          </form>
        </div>

      </div>
    </div>
  );
}