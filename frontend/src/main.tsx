import React, { Suspense } from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { AuthProvider } from "./context/AuthContext";
import { BrowserRouter } from "react-router-dom";
import { ToastProvider, ToastViewport } from "./components/ui/toast";
import { Loader2 } from "lucide-react";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Suspense
            fallback={
              <div className="min-h-screen flex items-center justify-center bg-[#0A0F1C]">
                <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
              </div>
            }
          >
            <App />
          </Suspense>
          <ToastViewport />
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  </React.StrictMode>
);
