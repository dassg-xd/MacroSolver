import { BrowserRouter } from "react-router-dom";

import { SesionProvider } from "./features/auth/SesionProvider";
import { RutasApp } from "./routes/RutasApp";

function App() {
  return (
    <BrowserRouter>
      <SesionProvider>
        <RutasApp />
      </SesionProvider>
    </BrowserRouter>
  );
}

export default App;
