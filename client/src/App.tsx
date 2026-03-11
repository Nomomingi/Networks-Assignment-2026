import { Home, Login, ProtectedRoute, SignUp } from "./routes";
import { AuthProvider } from "@/context/auth-context";

import './App.css'
import { Route, Routes } from "react-router";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/sign-up" element={<SignUp />} />
        <Route path="/" element={<ProtectedRoute />}>
          <Route path="/" element={<Home />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

export default App;
