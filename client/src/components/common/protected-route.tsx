import type React from "react";
import { Navigate, Outlet } from "react-router";
import { useAuth } from "@/context/auth-context";

const ProtectedRoute: React.FC = () => {
    const { user, loading } = useAuth();

    // While rehydrating from sessionStorage, render nothing to avoid a flash redirect
    if (loading) return null;

    return user ? <Outlet /> : <Navigate to="/login" replace />;
};

export default ProtectedRoute;