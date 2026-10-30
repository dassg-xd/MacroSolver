import Registro from "./features/auth/Registro";
import "./App.css";

function App() {
  function continuarRegistro(datos: {
    nombre: string;
    correo: string;
    contrasena: string;
  }) {
    console.log("Datos de cuenta para el paso 2:", datos);
  }

  return <Registro onContinuar={continuarRegistro} />;
}

export default App;
